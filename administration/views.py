from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from etudiants.models import Etudiant, Departement, Niveau, Session, ProfilAdmin
from notes.models import Note, ImportNotes
from demandes.models import Demande
from releves.models import Releve
from etudiants.permissions import (
    est_admin, est_directeur,
    est_chef_dept, get_filiere_admin
)
from releves.utils.generate_pdf import generer_releve

def verifier_admin(user):
    """Vérifie que l'utilisateur est bien un admin."""
    try:
        return hasattr(user, 'profiladmin') and user.profiladmin is not None
    except:
        return False

def get_profil(user):
    try:
        return user.profiladmin
    except:
        return None

@login_required
def admin_dashboard(request):
    if not verifier_admin(request.user):
        messages.error(request, 'Accès réservé à l\'administration.')
        return redirect('login_admin')

    profil   = get_profil(request.user)
    filiere  = get_filiere_admin(request.user)

    # ── Statistiques selon le rôle ──
    if filiere:
        # Chef de département → voit seulement sa filière
        etudiants = Etudiant.objects.filter(matricule__startswith=filiere)
        demandes = Demande.objects.filter(etudiant__matricule__startswith=filiere).order_by('-date_demande')
    else:
        # DG/DGA → voit tout
        etudiants = Etudiant.objects.all()
        demandes  = Demande.objects.all().order_by('-date_demande')

    total_etudiants      = etudiants.count()
    total_demandes       = demandes.count()
    demandes_en_attente  = demandes.filter(statut='en_attente').count()
    demandes_validees    = demandes.filter(statut='validee').count()
    demandes_rejetees    = demandes.filter(statut='rejetee').count()
    total_releves        = Releve.objects.count()
    total_notes          = Note.objects.count()

    # Dernières demandes
    dernieres_demandes = demandes[:8]

    return render(request, 'administration/dashboard.html', {
        'profil':               profil,
        'nb_etudiants':         total_etudiants,
        'nb_demandes':          total_demandes,
        'nb_attente':           demandes_en_attente,
        'nb_validees':          demandes_validees,
        'nb_rejetees':          demandes_rejetees,
        'nb_releves':           total_releves,
        'nb_notes':             total_notes,
        'dernières_demandes':   dernieres_demandes,
        'est_directeur':        est_directeur(request.user),
        'est_chef':             est_chef_dept(request.user),
    })

@login_required
def liste_etudiants(request):
    """Liste des étudiants"""
    if not verifier_admin(request.user):
        return redirect('login_admin')

    profil  = get_profil(request.user)
    filiere = get_filiere_admin(request.user)

    if filiere:
        etudiants = Etudiant.objects.filter(matricule__startswith=filiere).order_by('matricule')
    else:
        etudiants = Etudiant.objects.all().order_by('matricule')

    return render(request, 'administration/liste_etudiants.html', {
        'etudiants': etudiants,
        'profil': profil,
        'est_directeur': est_directeur(request.user),
        'est_chef': est_chef_dept(request.user),
    })

@login_required
def ajouter_etudiant(request):
    """Ajouter un étudiant"""
    if not verifier_admin(request.user):
        return redirect('login_admin')

    if request.method == 'POST':
        matricule = request.POST.get('matricule', '').strip()
        nom = request.POST.get('nom', '').strip()
        prenom = request.POST.get('prenom', '').strip()
        departement = request.POST.get('departement', '').strip()
        niveau = request.POST.get('niveau', '').strip()
        password = request.POST.get('password', '').strip()

        if Etudiant.objects.filter(matricule=matricule).exists():
            messages.error(request, f'Le matricule {matricule} existe déjà.')
            return redirect('ajouter_etudiant')

        try:
            user = User.objects.create_user(
                username=matricule,
                password=password or 'changeme123'
            )
            Etudiant.objects.create(
                user=user,
                matricule=matricule,
                nom=nom,
                prenom=prenom,
                departement_id=departement,
                niveau_id=niveau
            )
            messages.success(request, f'Étudiant {prenom} {nom} ajouté avec succès.')
            return redirect('liste_etudiants')
        except Exception as e:
            messages.error(request, f'Erreur : {str(e)}')

    departements = Departement.objects.all()
    niveaux = Niveau.objects.all()
    return render(request, 'administration/ajouter_etudiant.html', {
        'departements': departements,
        'niveaux': niveaux,
        'profil': get_profil(request.user),
        'est_directeur': est_directeur(request.user),
        'est_chef': est_chef_dept(request.user),
    })

@login_required
def supprimer_etudiant(request, etudiant_id):
    """Supprimer un étudiant"""
    if not verifier_admin(request.user):
        return redirect('login_admin')

    etudiant = get_object_or_404(Etudiant, id=etudiant_id)
    user = etudiant.user
    nom = f"{etudiant.prenom} {etudiant.nom}"
    etudiant.delete()
    user.delete()
    messages.success(request, f'Étudiant {nom} supprimé.')
    return redirect('liste_etudiants')

@login_required
def gestion_notes(request):
    """Gestion des notes"""
    if not verifier_admin(request.user):
        return redirect('login_admin')

    profil  = get_profil(request.user)
    filiere = get_filiere_admin(request.user)

    if filiere:
        notes = Note.objects.filter(etudiant__matricule__contains=filiere).select_related('etudiant', 'session').order_by('-id')[:100]
        etudiants = Etudiant.objects.filter(matricule__contains=filiere)
    else:
        notes = Note.objects.all().select_related('etudiant', 'session').order_by('-id')[:100]
        etudiants = Etudiant.objects.all()

    sessions = Session.objects.all()
    return render(request, 'administration/gestion_notes.html', {
        'notes': notes,
        'etudiants': etudiants,
        'sessions': sessions,
        'profil': profil,
        'est_directeur': est_directeur(request.user),
        'est_chef': est_chef_dept(request.user),
    })

@login_required
def ajouter_note(request):
    """Ajouter une note"""
    if not verifier_admin(request.user):
        return redirect('login_admin')

    if request.method == 'POST':
        etudiant_id = request.POST.get('etudiant')
        matiere = request.POST.get('matiere', '').strip()
        note_val = request.POST.get('note')
        session = request.POST.get('session', '').strip()
        annee = request.POST.get('annee', '').strip()

        try:
            etudiant = Etudiant.objects.get(id=etudiant_id)
            session_obj = Session.objects.get(id=session)
            Note.objects.create(
                etudiant=etudiant,
                matiere=matiere,
                note=float(note_val),
                session=session_obj,
                annee=annee
            )
            messages.success(request, 'Note ajoutée avec succès.')
        except Exception as e:
            messages.error(request, f'Erreur : {str(e)}')

    return redirect('gestion_notes')

@login_required
def gestion_demandes(request):
    """Gestion des demandes"""
    if not verifier_admin(request.user):
        return redirect('login_admin')

    profil  = get_profil(request.user)
    filiere = get_filiere_admin(request.user)

    if filiere:
        # Chef voit seulement sa filière
        demandes = Demande.objects.filter(
            etudiant__matricule__contains=filiere
        ).select_related('etudiant').order_by('-date_demande')
    else:
        # DG/DGA voit tout
        demandes = Demande.objects.all().select_related('etudiant').order_by('-date_demande')

    return render(request, 'administration/gestion_demandes.html', {
        'demandes': demandes,
        'profil': profil,
        'est_directeur': est_directeur(request.user),
        'est_chef': est_chef_dept(request.user),
    })

@login_required
def valider_demande(request, demande_id):
    """Valider une demande et générer le PDF"""
    if not verifier_admin(request.user):
        return redirect('login_admin')

    demande = get_object_or_404(Demande, id=demande_id)
    demande.statut = 'validee'
    demande.save()

    # Générer le PDF automatiquement
    try:
        chemin_pdf = generer_releve(demande)
        Releve.objects.get_or_create(
            demande=demande,
            defaults={'fichier_pdf': chemin_pdf}
        )
        messages.success(request, f'Demande validée et relevé PDF généré pour {demande.etudiant.matricule}.')
    except Exception as e:
        messages.warning(request, f'Demande validée mais erreur PDF : {str(e)}')

    return redirect('gestion_demandes')

@login_required
def rejeter_demande(request, demande_id):
    """Rejeter une demande"""
    if not verifier_admin(request.user):
        return redirect('login_admin')

    demande = get_object_or_404(Demande, id=demande_id)
    demande.statut = 'rejetee'
    demande.save()
    messages.success(request, f'Demande rejetée pour {demande.etudiant.matricule}.')
    return redirect('gestion_demandes')


# ════════════════════════════════════════
# DASHBOARD ÉTUDIANT
# ════════════════════════════════════════
@login_required
def profil_etudiant(request):
    try:
        etudiant = Etudiant.objects.get(user=request.user)
    except:
        return redirect('login')

    notes    = Note.objects.filter(etudiant=etudiant)
    demandes = Demande.objects.filter(
        etudiant=etudiant
    ).order_by('-date_demande')

    moyenne = 0
    if notes.exists():
        moyenne = sum([n.note for n in notes]) / notes.count()

    nb_valides  = demandes.filter(statut='validee').count()
    nb_attente  = demandes.filter(statut='en_attente').count()

    return render(request, 'dashboards/etudiant.html', {
        'etudiant':   etudiant,
        'notes':      notes[:5],
        'demandes':   demandes[:5],
        'moyenne':    round(moyenne, 2),
        'nb_valides': nb_valides,
        'nb_attente': nb_attente,
        'nb_notes':   notes.count(),
        'admis': moyenne >= 5,
    })


# ════════════════════════════════════════
# DASHBOARD CHEF DÉPARTEMENT
# ════════════════════════════════════════
@login_required
def dashboard_chef(request):
    profil = get_profil(request.user)
    if not profil or profil.role not in [
        'chef_ntic', 'chef_dl'
    ]:
        return redirect('login')

    # Filière du chef
    filiere = 'NTIC' if profil.role == 'chef_ntic' else 'DL'
    nom_filiere = (
        'Nouvelles Technologies de l\'Information '
        'et de la Communication'
        if filiere == 'NTIC'
        else 'Développement Logiciel'
    )
    search_filiere = '6642' if profil.role == 'chef_ntic' else '6644'

    # Données de sa filière uniquement
    etudiants = Etudiant.objects.filter(
        matricule__startswith=search_filiere
    )
    notes     = Note.objects.filter(
        etudiant__matricule__startswith=search_filiere
    )
    imports   = ImportNotes.objects.filter(
        filiere=search_filiere
    ).order_by('-date_depot')

    # Stats imports
    nb_deposes   = imports.filter(statut='depose').count()
    nb_valides   = imports.filter(statut='valide_dg').count()
    nb_rejetes   = imports.filter(statut='rejete').count()
    nb_dga       = imports.filter(statut='valide_dga').count()

    return render(request, 'dashboards/chef.html', {
        'profil':       profil,
        'filiere':      filiere,
        'nom_filiere':  nom_filiere,
        'nb_etudiants': etudiants.count(),
        'nb_notes':     notes.count(),
        'nb_imports':   imports.count(),
        'nb_deposes':   nb_deposes,
        'nb_valides':   nb_valides,
        'nb_rejetes':   nb_rejetes,
        'nb_dga':       nb_dga,
        'derniers_imports': imports[:6],
    })


# ════════════════════════════════════════
# DASHBOARD DGA
# ════════════════════════════════════════
@login_required
def dashboard_dga(request):
    profil = get_profil(request.user)
    if not profil or profil.role != 'dga':
        return redirect('login')

    # Imports à valider par DGA
    imports_attente = ImportNotes.objects.filter(
        statut='depose'
    ).order_by('-date_depot')

    # Imports déjà traités
    imports_traites = ImportNotes.objects.filter(
        statut__in=['valide_dga', 'rejete', 'valide_dg']
    ).order_by('-date_depot')

    # Stats générales
    total_etudiants = Etudiant.objects.count()
    total_notes     = Note.objects.count()
    nb_nt = Etudiant.objects.filter(
        matricule__startswith='6642'
    ).count()
    nb_dl = Etudiant.objects.filter(
        matricule__startswith='6644'
    ).count()

    return render(request, 'dashboards/dga.html', {
        'profil':           profil,
        'imports_attente':  imports_attente,
        'imports_traites':  imports_traites,
        'nb_attente':       imports_attente.count(),
        'nb_traites':       imports_traites.count(),
        'total_etudiants':  total_etudiants,
        'total_notes':      total_notes,
        'nb_nt':            nb_nt,
        'nb_dl':            nb_dl,
    })


# ════════════════════════════════════════
# DASHBOARD DG
# ════════════════════════════════════════
@login_required
def dashboard_dg(request):
    profil = get_profil(request.user)
    if not profil or profil.role != 'dg':
        return redirect('login')

    # Imports validés DGA — en attente DG
    imports_a_valider = ImportNotes.objects.filter(
        statut='valide_dga'
    ).order_by('-date_depot')

    # Tout l'historique
    tous_imports = ImportNotes.objects.all().order_by(
        '-date_depot'
    )

    # Stats complètes
    total_etudiants = Etudiant.objects.count()
    total_notes     = Note.objects.count()
    total_demandes  = Demande.objects.count()
    total_releves   = Releve.objects.count()
    nb_nt = Etudiant.objects.filter(
        matricule__startswith='6642'
    ).count()
    nb_dl = Etudiant.objects.filter(
        matricule__startswith='6644'
    ).count()
    imports_actifs = ImportNotes.objects.filter(
        statut='valide_dg'
    ).count()

    return render(request, 'dashboards/dg.html', {
        'profil':             profil,
        'imports_a_valider':  imports_a_valider,
        'nb_a_valider':       imports_a_valider.count(),
        'tous_imports':       tous_imports[:8],
        'total_etudiants':    total_etudiants,
        'total_notes':        total_notes,
        'total_demandes':     total_demandes,
        'total_releves':      total_releves,
        'nb_nt':              nb_nt,
        'nb_dl':              nb_dl,
        'imports_actifs':     imports_actifs,
    })
