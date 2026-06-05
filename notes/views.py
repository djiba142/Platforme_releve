import io, os
import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse, HttpResponse, JsonResponse
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.http import require_GET
from .models import Note, ImportNotes
from etudiants.models import Etudiant, Session, Niveau, Departement, ProfilAdmin
from etudiants.permissions import est_admin, get_filiere_admin
from releves.utils.generate_pdf import generer_releve_direct


# ─────────────────────────────────────────────────────────
# HELPER : parser une ligne CSV/Excel → notes en DB
# ─────────────────────────────────────────────────────────
COLONNES_META = {'matricule', 'nom', 'prenom', 'departement', 'niveau', 'session', 'annee'}

def _importer_lignes_df(df, import_obj, session_nom, annee):
    """
    Parcourt le DataFrame et insère/met à jour les Note en base.
    Retourne (nb_ok, nb_erreurs, messages_erreurs[]).
    """
    ok = 0
    erreurs = []

    # Normaliser les noms de colonnes
    df.columns = [str(c).strip().lower() for c in df.columns]

    col_mat = next((c for c in df.columns if 'matricule' in c), None)
    if not col_mat:
        return 0, len(df), ["Colonne 'matricule' introuvable dans le fichier."]

    # Colonnes de notes = tout ce qui n'est pas meta
    cols_notes = [c for c in df.columns if c not in COLONNES_META]

    for _, row in df.iterrows():
        raw_mat = row.get(col_mat, '')
        if pd.isna(raw_mat) or str(raw_mat).strip() == '':
            continue
        matricule = str(raw_mat).strip().upper()

        # Trouver l'étudiant
        try:
            etudiant = Etudiant.objects.get(matricule=matricule)
        except Etudiant.DoesNotExist:
            erreurs.append(f"Matricule inconnu : {matricule}")
            continue

        # Session — créer si inexistante
        niveau = etudiant.niveau
        if niveau is None:
            erreurs.append(f"{matricule} : aucun niveau défini")
            continue

        session_slug = slugify(f"{niveau.slug}-{session_nom}")
        session_obj, _ = Session.objects.get_or_create(
            slug=session_slug,
            defaults={'niveau': niveau, 'nom': session_nom}
        )

        # Insérer chaque note
        for col in cols_notes:
            val = row.get(col)
            if pd.isna(val):
                continue
            try:
                note_val = float(str(val).replace(',', '.').strip())
                if not (0 <= note_val <= 20):
                    erreurs.append(f"{matricule}/{col} : note {note_val} hors plage 0-20")
                    continue
                Note.objects.update_or_create(
                    etudiant=etudiant,
                    matiere=col.title(),
                    session=session_obj,
                    annee=annee,
                    defaults={'note': note_val, 'import_source': import_obj}
                )
                ok += 1
            except (ValueError, TypeError):
                pass

    return ok, len(erreurs), erreurs


# ─────────────────────────────────────────────────────────
# VUE 1 : Import CSV par le Chef de Département
# ─────────────────────────────────────────────────────────
@login_required
def deposer_notes(request):
    """Chef de département dépose un CSV → insertion automatique en MySQL."""
    try:
        profil = request.user.profiladmin
    except Exception:
        messages.error(request, 'Accès refusé.')
        return redirect('admin_dashboard')

    if profil.role not in ['chef_ntic', 'chef_dl']:
        messages.error(request, 'Seuls les Chefs de Département peuvent importer des notes.')
        return redirect('admin_dashboard')

    filiere = 'NTIC' if profil.role == 'chef_ntic' else 'DL'

    if request.method != 'POST':
        return redirect('dashboard_chef')

    fichier     = request.FILES.get('fichier')
    session_nom = request.POST.get('session', '').strip()
    annee       = request.POST.get('annee', '2024-2025').strip()

    # ── Validations ──
    if not fichier:
        messages.error(request, 'Aucun fichier sélectionné.')
        return redirect('dashboard_chef')
    if not session_nom:
        messages.error(request, 'La session est obligatoire (ex : Session 1).')
        return redirect('dashboard_chef')
    if not fichier.name.lower().endswith('.csv'):
        messages.error(request, 'Le fichier doit être au format CSV (.csv).')
        return redirect('dashboard_chef')

    # ── Lecture CSV ──
    try:
        content = fichier.read().decode('utf-8-sig')  # BOM-safe
        df = pd.read_csv(io.StringIO(content), sep=None, engine='python')
    except Exception as e:
        messages.error(request, f'Erreur lecture CSV : {e}')
        return redirect('dashboard_chef')

    if df.empty:
        messages.error(request, 'Le fichier CSV est vide.')
        return redirect('dashboard_chef')

    # ── Sauvegarder le fichier & créer l'objet ImportNotes ──
    fichier.seek(0)
    import_obj = ImportNotes.objects.create(
        fichier=fichier,
        filiere=filiere,
        session=session_nom,
        annee=annee,
        depose_par=request.user,
        statut='depose',
    )

    # ── Insertion automatique en base MySQL ──
    nb_ok, nb_err, err_list = _importer_lignes_df(df, import_obj, session_nom, annee)
    import_obj.nb_notes_importees = nb_ok
    import_obj.save()

    if nb_ok == 0:
        messages.error(request, f'❌ Aucune note importée. Erreurs : {"; ".join(err_list[:3])}')
    else:
        msg = f'✅ {nb_ok} note(s) insérée(s) en base MySQL (session : {session_nom}).'
        if nb_err:
            msg += f' ⚠️ {nb_err} ligne(s) ignorée(s) : {", ".join(err_list[:2])}'
        if nb_ok > 0:
            msg += ' — En attente de validation DGA.'
        messages.success(request, msg)

    return redirect('dashboard_chef')


# ─────────────────────────────────────────────────────────
# VUE 2 : Consultation des notes de l'étudiant connecté
# ─────────────────────────────────────────────────────────
@login_required
def liste_notes(request):
    try:
        etudiant = Etudiant.objects.get(user=request.user)
    except Etudiant.DoesNotExist:
        messages.error(request, 'Profil étudiant introuvable.')
        return redirect('accueil')

    notes = Note.objects.filter(etudiant=etudiant).select_related('session').order_by('session__nom', 'matiere')

    # Grouper par session
    sessions_data = {}
    for n in notes:
        key = str(n.session)
        if key not in sessions_data:
            sessions_data[key] = {'session': n.session, 'notes': [], 'total': 0, 'count': 0}
        sessions_data[key]['notes'].append(n)
        sessions_data[key]['total'] += n.note
        sessions_data[key]['count'] += 1

    for k in sessions_data:
        d = sessions_data[k]
        d['moyenne'] = round(d['total'] / d['count'], 2) if d['count'] else 0

    moyenne_gen = round(sum(n.note for n in notes) / notes.count(), 2) if notes.exists() else 0

    return render(request, 'notes/liste_notes.html', {
        'etudiant':        etudiant,
        'sessions_data':   sessions_data.values(),
        'notes':           notes,
        'moyenne_generale': moyenne_gen,
        'nb_notes':        notes.count(),
    })


# ─────────────────────────────────────────────────────────
# VUE 3 : Génération PDF automatique par matricule (API)
# L'étudiant entre son matricule → PDF généré et téléchargé
# ─────────────────────────────────────────────────────────
def pdf_par_matricule(request):
    """
    URL publique (ou protégée) : ?matricule=6642001&session=Session+1
    Génère et retourne directement le PDF du relevé.
    """
    matricule   = request.GET.get('matricule', '').strip().upper()
    session_nom = request.GET.get('session', '').strip()

    if not matricule:
        return HttpResponse(
            '<h3>Erreur</h3><p>Paramètre <code>matricule</code> manquant.</p>',
            status=400, content_type='text/html'
        )

    try:
        etudiant = Etudiant.objects.get(matricule=matricule)
    except Etudiant.DoesNotExist:
        return HttpResponse(
            f'<h3>Matricule introuvable</h3><p>{matricule} n\'existe pas dans la base de données.</p>',
            status=404, content_type='text/html'
        )

    # Récupérer notes selon session
    notes_qs = Note.objects.filter(etudiant=etudiant).select_related('session')
    if session_nom:
        notes_qs = notes_qs.filter(session__nom__iexact=session_nom)

    if not notes_qs.exists():
        return HttpResponse(
            f'<h3>Aucune note trouvée</h3>'
            f'<p>Aucune note pour le matricule <strong>{matricule}</strong>'
            f'{" — session : " + session_nom if session_nom else ""}.</p>',
            status=404, content_type='text/html'
        )

    # Générer le PDF directement sans demande formelle
    try:
        chemin_pdf = generer_releve_direct(etudiant, notes_qs, session_nom or 'Toutes sessions')
    except Exception as e:
        return HttpResponse(f'<h3>Erreur PDF</h3><p>{e}</p>', status=500, content_type='text/html')

    if not os.path.exists(chemin_pdf):
        return HttpResponse('<h3>Fichier PDF non trouvé</h3>', status=500, content_type='text/html')

    nom_fichier = f"releve_{matricule}_{(session_nom or 'all').replace(' ','_')}.pdf"
    response = FileResponse(open(chemin_pdf, 'rb'), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{nom_fichier}"'
    return response


# ─────────────────────────────────────────────────────────
# VUE 4 : Page de recherche par matricule (UI)
# ─────────────────────────────────────────────────────────
def recherche_notes(request):
    """Page publique : entrer matricule → voir/télécharger notes."""
    matricule   = request.GET.get('matricule', '').strip().upper()
    session_nom = request.GET.get('session', '').strip()
    etudiant    = None
    sessions_data = {}
    erreur = None

    if matricule:
        try:
            etudiant = Etudiant.objects.get(matricule=matricule, est_valide=True)
            notes_qs = Note.objects.filter(etudiant=etudiant).select_related('session').order_by('session__nom','matiere')
            if session_nom:
                notes_qs = notes_qs.filter(session__nom__iexact=session_nom)

            for n in notes_qs:
                key = str(n.session)
                if key not in sessions_data:
                    sessions_data[key] = {'session': n.session, 'notes': [], 'total': 0, 'count': 0}
                sessions_data[key]['notes'].append(n)
                sessions_data[key]['total'] += n.note
                sessions_data[key]['count'] += 1

            for k in sessions_data:
                d = sessions_data[k]
                d['moyenne'] = round(d['total'] / d['count'], 2) if d['count'] else 0

            if not sessions_data:
                erreur = f"Aucune note trouvée pour le matricule {matricule}."

        except Etudiant.DoesNotExist:
            erreur = f"Matricule {matricule} introuvable ou compte non activé."

    # Sessions disponibles pour le filtre
    sessions_list = Session.objects.all().order_by('nom')

    return render(request, 'notes/recherche_notes.html', {
        'matricule':     matricule,
        'session_nom':   session_nom,
        'etudiant':      etudiant,
        'sessions_data': sessions_data.values(),
        'sessions_list': sessions_list,
        'erreur':        erreur,
    })


# ─────────────────────────────────────────────────────────
# VUE 5 : Workflow validation DGA/DG
# ─────────────────────────────────────────────────────────
@login_required
def valider_notes_dga(request, import_id):
    try:
        if request.user.profiladmin.role not in ('dga', 'admin'):
            raise PermissionError
    except Exception:
        messages.error(request, 'Accès refusé.')
        return redirect('admin_dashboard')

    obj = get_object_or_404(ImportNotes, id=import_id)
    obj.statut             = 'valide_dga'
    obj.valide_par_dga     = request.user
    obj.date_validation_dga = timezone.now()
    obj.save()
    messages.success(request, f'✅ Notes validées DGA — en attente DG.')
    return redirect('dashboard_dga')


@login_required
def valider_notes_dg(request, import_id):
    try:
        if request.user.profiladmin.role not in ('dg', 'admin'):
            raise PermissionError
    except Exception:
        messages.error(request, 'Accès refusé.')
        return redirect('admin_dashboard')

    obj = get_object_or_404(ImportNotes, id=import_id)
    if obj.statut != 'valide_dga':
        messages.error(request, 'Doit d\'abord être validé par la DGA.')
        return redirect('dashboard_dg')
    obj.statut            = 'valide_dg'
    obj.valide_par_dg     = request.user
    obj.date_validation_dg = timezone.now()
    obj.save()
    messages.success(request, f'✅ Notes publiées — les étudiants peuvent générer leurs relevés.')
    return redirect('dashboard_dg')


@login_required
def rejeter_notes(request, import_id):
    try:
        if request.user.profiladmin.role not in ('dga', 'dg', 'admin'):
            raise PermissionError
    except Exception:
        return redirect('admin_dashboard')

    obj = get_object_or_404(ImportNotes, id=import_id)
    obj.statut     = 'rejete'
    obj.commentaire = request.POST.get('commentaire', '')
    obj.save()
    messages.warning(request, 'Import rejeté.')
    return redirect('dashboard_dga')


@login_required
def gestion_imports(request):
    try:
        role = request.user.profiladmin.role
        if role == 'dg':    return redirect('dashboard_dg')
        if role == 'dga':   return redirect('dashboard_dga')
    except Exception:
        pass
    return redirect('admin_dashboard')


@login_required
def consulter_import(request, import_id):
    try:
        profil = request.user.profiladmin
    except Exception:
        return redirect('admin_dashboard')

    obj   = get_object_or_404(ImportNotes, id=import_id)
    notes = obj.lignes_notes.select_related('etudiant', 'session').all()
    return render(request, 'notes/consulter_import.html', {'import_obj': obj, 'notes': notes, 'profil': profil})
