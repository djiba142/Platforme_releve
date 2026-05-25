from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Etudiant


def accueil_view(request):
    """Page d'accueil publique"""
    if request.user.is_authenticated:
        if hasattr(request.user, 'etudiant'):
            return redirect('profil')
        elif request.user.is_staff:
            return redirect('admin_dashboard')
    return render(request, 'etudiants/accueil.html')

def landing_page(request):
    """Ancienne page d'accueil (conservée par sécurité)"""
    return redirect('accueil')

def login_etudiant(request):
    """Connexion étudiant avec matricule"""
    if request.user.is_authenticated:
        return redirect('profil')

    if request.method == 'POST':
        matricule = request.POST.get('matricule', '').strip()
        password = request.POST.get('password', '')

        try:
            etudiant = Etudiant.objects.get(matricule=matricule)
            user = authenticate(request,
                                username=etudiant.user.username,
                                password=password)
            if user:
                login(request, user)
                messages.success(request, f'Bienvenue {etudiant.prenom} !')
                return redirect('profil')
            else:
                messages.error(request, 'Mot de passe incorrect.')
        except Etudiant.DoesNotExist:
            messages.error(request, 'Matricule introuvable.')

    return render(request, 'etudiants/login.html')


def login_admin(request):
    """Connexion administration"""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)
        if user and user.is_staff:
            login(request, user)
            messages.success(request, f'Bienvenue Administrateur !')
            return redirect('admin_dashboard')
        elif user:
            messages.error(request, 'Vous n\'êtes pas administrateur.')
        else:
            messages.error(request, 'Identifiants incorrects.')

    return render(request, 'etudiants/login_admin.html')


def logout_view(request):
    """Déconnexion"""
    logout(request)
    return redirect('accueil')


@login_required
def profil_view(request):
    """Dashboard / Profil étudiant"""
    try:
        etudiant = Etudiant.objects.get(user=request.user)
    except Etudiant.DoesNotExist:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        messages.error(request, 'Profil étudiant non trouvé.')
        return redirect('accueil')

    from notes.models import Note
    from demandes.models import Demande

    notes = Note.objects.filter(etudiant=etudiant)
    demandes = Demande.objects.filter(etudiant=etudiant).order_by('-date_demande')[:5]

    moyenne = 0
    if notes.exists():
        moyenne = round(sum(n.note for n in notes) / notes.count(), 2)

    context = {
        'etudiant': etudiant,
        'notes': notes,
        'demandes': demandes,
        'moyenne': moyenne,
        'nb_notes': notes.count(),
        'nb_demandes': Demande.objects.filter(etudiant=etudiant).count(),
        'nb_validees': Demande.objects.filter(etudiant=etudiant, statut='validee').count(),
    }
    return render(request, 'etudiants/profil.html', context)
