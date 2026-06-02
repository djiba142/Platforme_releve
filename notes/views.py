from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Note, ImportNotes
from etudiants.models import Etudiant, Session, ProfilAdmin
from etudiants.permissions import (
    est_directeur, est_chef_dept, get_filiere_admin
)
import pandas as pd
from django.utils.text import slugify


@login_required
def liste_notes(request):
    etudiant = Etudiant.objects.get(user=request.user)
    notes    = Note.objects.filter(etudiant=etudiant)

    if notes:
        moyenne = sum([n.note for n in notes]) / len(notes)
    else:
        moyenne = 0

    return render(request, 'notes/liste_notes.html', {
        'notes':    notes,
        'moyenne':  round(moyenne, 2),
        'etudiant': etudiant,
    })


# ── CHEF DE DÉPARTEMENT — Téléverse le fichier ──
@login_required
def deposer_notes(request):
    """
    Réservé aux Chefs de Département.
    Ils déposent le fichier Excel regroupé.
    """
    try:
        profil = request.user.profiladmin
    except:
        messages.error(request, 'Accès refusé.')
        return redirect('dashboard')

    if profil.role not in ['chef_ntic', 'chef_dl']:
        messages.error(
            request,
            'Seuls les Chefs de Département peuvent déposer des notes.'
        )
        return redirect('dashboard')

    # Filière du chef
    filiere = get_filiere_admin(request.user)

    if request.method == 'POST':
        fichier  = request.FILES.get('fichier')
        session_val  = request.POST.get('session')
        annee    = request.POST.get('annee')

        if not fichier:
            messages.error(request, 'Aucun fichier sélectionné.')
            return redirect('deposer_notes')

        try:
            # Lecture fichier
            if fichier.name.endswith('.csv'):
                df = pd.read_csv(fichier)
            else:
                df = pd.read_excel(fichier)

            colonnes_base = ['matricule', 'nom', 'prenom', 'departement', 'niveau']

            # Sauvegarder l'import
            import_obj = ImportNotes.objects.create(
                fichier=fichier,
                filiere=filiere,
                session=session_val,
                annee=annee,
                depose_par=request.user,
                statut='depose'
            )

            # Importer les notes en base
            compteur = 0
            erreurs  = 0
            for _, row in df.iterrows():
                try:
                    col_mat = next((c for c in df.columns if str(c).lower().strip() == 'matricule'), None)
                    if not col_mat or pd.isna(row[col_mat]):
                        continue
                        
                    matricule = str(row[col_mat]).strip()
                    etudiant = Etudiant.objects.get(matricule=matricule)
                    
                    session_slug = slugify(f"{etudiant.niveau.slug}-{session_val}")
                    session_obj, _ = Session.objects.get_or_create(
                        slug=session_slug,
                        defaults={'niveau': etudiant.niveau, 'nom': session_val}
                    )

                    notes_ajoutees = False
                    for col in df.columns:
                        if str(col).lower().strip() not in colonnes_base:
                            val = row[col]
                            if pd.notna(val) and str(val).strip() != '':
                                try:
                                    note_val = float(str(val).replace(',', '.').replace(' ', ''))
                                    Note.objects.update_or_create(
                                        etudiant=etudiant,
                                        matiere=str(col).strip(),
                                        session=session_obj,
                                        annee=annee,
                                        defaults={'note': note_val}
                                    )
                                    compteur += 1
                                    notes_ajoutees = True
                                except ValueError:
                                    pass
                except Etudiant.DoesNotExist:
                    erreurs += 1

            import_obj.nb_notes_importees = compteur
            import_obj.save()

            messages.success(
                request,
                f'{compteur} notes déposées avec succès. En attente de validation DGA.'
            )

        except Exception as e:
            messages.error(request, f'Erreur : {str(e)}')

        return redirect('deposer_notes')

    # Historique des imports du chef
    mes_imports = ImportNotes.objects.filter(
        depose_par=request.user
    ).order_by('-date_depot')

    return render(request, 'notes/deposer_notes.html', {
        'profil':      request.user.profiladmin,
        'filiere':     filiere,
        'mes_imports': mes_imports,
    })


# ── DGA — Valide les notes ──
@login_required
def valider_notes_dga(request, import_id):
    """Réservé au DGA."""
    try:
        profil = request.user.profiladmin
    except:
        return redirect('dashboard')

    if profil.role != 'dga':
        messages.error(request, 'Réservé au DGA.')
        return redirect('dashboard')

    import_obj = get_object_or_404(ImportNotes, id=import_id)
    import_obj.statut         = 'valide_dga'
    import_obj.valide_par_dga = request.user
    import_obj.date_validation_dga = timezone.now()
    import_obj.save()

    messages.success(
        request,
        f'Notes {import_obj.filiere} — {import_obj.session} validées. En attente du DG.'
    )
    return redirect('gestion_imports')


# ── DG — Validation finale ──
@login_required
def valider_notes_dg(request, import_id):
    """Réservé au DG."""
    try:
        profil = request.user.profiladmin
    except:
        return redirect('dashboard')

    if profil.role != 'dg':
        messages.error(request, 'Réservé au DG.')
        return redirect('dashboard')

    import_obj = get_object_or_404(ImportNotes, id=import_id)

    if import_obj.statut != 'valide_dga':
        messages.error(
            request,
            'Cet import doit d\'abord être validé par le DGA.'
        )
        return redirect('gestion_imports')

    import_obj.statut        = 'valide_dg'
    import_obj.valide_par_dg = request.user
    import_obj.date_validation_dg = timezone.now()
    import_obj.save()

    messages.success(
        request,
        f'Notes {import_obj.filiere} — {import_obj.session} validées définitivement. Les étudiants peuvent demander leurs relevés.'
    )
    return redirect('gestion_imports')


# ── Rejeter un import ──
@login_required
def rejeter_notes(request, import_id):
    try:
        profil = request.user.profiladmin
    except:
        return redirect('dashboard')

    if profil.role not in ['dga', 'dg']:
        return redirect('dashboard')

    import_obj = get_object_or_404(ImportNotes, id=import_id)
    commentaire = request.POST.get('commentaire', '')
    import_obj.statut      = 'rejete'
    import_obj.commentaire = commentaire
    import_obj.save()

    messages.warning(
        request,
        f'Import rejeté. Le Chef de Département sera notifié.'
    )
    return redirect('gestion_imports')


# ── Vue gestion imports (DGA + DG) ──
@login_required
def gestion_imports(request):
    try:
        profil = request.user.profiladmin
    except:
        return redirect('dashboard')

    if profil.role == 'dga':
        # DGA voit les imports déposés par les chefs
        imports = ImportNotes.objects.filter(
            statut='depose'
        ).order_by('-date_depot')
        titre = "Imports à valider — DGA"

    elif profil.role == 'dg':
        # DG voit les imports validés par DGA
        imports = ImportNotes.objects.filter(
            statut='valide_dga'
        ).order_by('-date_depot')
        titre = "Imports à valider définitivement — DG"

    else:
        return redirect('dashboard')

    return render(request, 'notes/gestion_imports.html', {
        'imports': imports,
        'profil':  profil,
        'titre':   titre,
    })
