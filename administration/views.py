from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from etudiants.models import Etudiant
from notes.models import Note
from demandes.models import Demande
from releves.models import Releve
from releves.utils.generate_pdf import generer_releve


def admin_required(view_func):
    """Décorateur pour vérifier que l'utilisateur est admin"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            messages.error(request, 'Accès réservé à l\'administration.')
            return redirect('login_admin')
        return view_func(request, *args, **kwargs)
    return wrapper


@admin_required
def admin_dashboard(request):
    """Dashboard administration"""
    context = {
        'nb_etudiants': Etudiant.objects.count(),
        'nb_notes': Note.objects.count(),
        'nb_demandes': Demande.objects.count(),
        'nb_attente': Demande.objects.filter(statut='en_attente').count(),
        'nb_validees': Demande.objects.filter(statut='validee').count(),
        'nb_rejetees': Demande.objects.filter(statut='rejetee').count(),
        'nb_releves': Releve.objects.count(),
        'dernières_demandes': Demande.objects.all().order_by('-date_demande')[:10],
    }
    return render(request, 'administration/dashboard.html', context)


@admin_required
def liste_etudiants(request):
    """Liste des étudiants"""
    etudiants = Etudiant.objects.all().order_by('matricule')
    return render(request, 'administration/liste_etudiants.html', {
        'etudiants': etudiants
    })


@admin_required
def ajouter_etudiant(request):
    """Ajouter un étudiant"""
    if request.method == 'POST':
        matricule = request.POST.get('matricule', '').strip()
        nom = request.POST.get('nom', '').strip()
        prenom = request.POST.get('prenom', '').strip()
        filiere = request.POST.get('filiere', '').strip()
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
                filiere=filiere,
                niveau=niveau
            )
            messages.success(request, f'Étudiant {prenom} {nom} ajouté avec succès.')
            return redirect('liste_etudiants')
        except Exception as e:
            messages.error(request, f'Erreur : {str(e)}')

    return render(request, 'administration/ajouter_etudiant.html')


@admin_required
def supprimer_etudiant(request, etudiant_id):
    """Supprimer un étudiant"""
    etudiant = get_object_or_404(Etudiant, id=etudiant_id)
    user = etudiant.user
    nom = f"{etudiant.prenom} {etudiant.nom}"
    etudiant.delete()
    user.delete()
    messages.success(request, f'Étudiant {nom} supprimé.')
    return redirect('liste_etudiants')


@admin_required
def gestion_notes(request):
    """Gestion des notes"""
    notes = Note.objects.all().select_related('etudiant').order_by('-id')[:100]
    etudiants = Etudiant.objects.all()
    return render(request, 'administration/gestion_notes.html', {
        'notes': notes,
        'etudiants': etudiants
    })


@admin_required
def ajouter_note(request):
    """Ajouter une note"""
    if request.method == 'POST':
        etudiant_id = request.POST.get('etudiant')
        matiere = request.POST.get('matiere', '').strip()
        note_val = request.POST.get('note')
        session = request.POST.get('session', '').strip()
        annee = request.POST.get('annee', '').strip()

        try:
            etudiant = Etudiant.objects.get(id=etudiant_id)
            Note.objects.create(
                etudiant=etudiant,
                matiere=matiere,
                note=float(note_val),
                session=session,
                annee=annee
            )
            messages.success(request, 'Note ajoutée avec succès.')
        except Exception as e:
            messages.error(request, f'Erreur : {str(e)}')

    return redirect('gestion_notes')


@admin_required
def gestion_demandes(request):
    """Gestion des demandes"""
    demandes = Demande.objects.all().select_related('etudiant').order_by('-date_demande')
    return render(request, 'administration/gestion_demandes.html', {
        'demandes': demandes
    })


@admin_required
def valider_demande(request, demande_id):
    """Valider une demande et générer le PDF"""
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


@admin_required
def rejeter_demande(request, demande_id):
    """Rejeter une demande"""
    demande = get_object_or_404(Demande, id=demande_id)
    demande.statut = 'rejetee'
    demande.save()
    messages.success(request, f'Demande rejetée pour {demande.etudiant.matricule}.')
    return redirect('gestion_demandes')
