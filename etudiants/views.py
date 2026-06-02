from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Etudiant, Departement, Niveau


def accueil_view(request):
    """Page d'accueil publique"""
    if request.user.is_authenticated:
        if hasattr(request.user, 'etudiant'):
            return redirect('profil')
        elif request.user.is_staff:
            return redirect('admin_dashboard')
    return render(request, 'etudiants/accueil.html')

def inscription_etudiant(request):
    """Plateforme d'inscription pour les étudiants"""
    if request.user.is_authenticated:
        return redirect('accueil')

    if request.method == 'POST':
        matricule = request.POST.get('matricule', '').strip()
        nom = request.POST.get('nom', '').strip()
        prenom = request.POST.get('prenom', '').strip()
        departement_id = request.POST.get('departement', '').strip()
        niveau_id = request.POST.get('niveau', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')

        # Validations basiques
        if password != password_confirm:
            messages.error(request, 'Les mots de passe ne correspondent pas.')
            return redirect('inscription')
        if len(password) < 6:
            messages.error(request, 'Le mot de passe doit contenir au moins 6 caractères.')
            return redirect('inscription')

        if Etudiant.objects.filter(matricule=matricule).exists() or User.objects.filter(username=matricule).exists():
            messages.error(request, 'Ce matricule est déjà utilisé ou en attente de validation.')
            return redirect('inscription')

        try:
            user = User.objects.create_user(
                username=matricule,
                password=password
            )
            # Créer l'étudiant avec est_valide=False par défaut
            Etudiant.objects.create(
                user=user,
                matricule=matricule,
                nom=nom,
                prenom=prenom,
                departement_id=departement_id if departement_id else None,
                niveau_id=niveau_id if niveau_id else None,
                mot_de_passe_change=True, # Pas besoin de les forcer à changer, ils viennent de le définir
                est_valide=False
            )
            messages.success(request, "Inscription réussie ! Votre compte est en attente de validation par l'administration.")
            return redirect('login')
        except Exception as e:
            messages.error(request, f"Erreur lors de l'inscription : {str(e)}")
            return redirect('inscription')

    departements = Departement.objects.all()
    niveaux = Niveau.objects.all()
    return render(request, 'etudiants/inscription.html', {
        'departements': departements,
        'niveaux': niveaux
    })

def landing_page(request):
    """Ancienne page d'accueil (conservée par sécurité)"""
    return redirect('accueil')

def login_etudiant(request):
    """Connexion unifiée — détecte automatiquement étudiant ou admin"""
    if request.user.is_authenticated:
        if hasattr(request.user, 'etudiant'):
            return redirect('profil')
        elif request.user.is_staff:
            return redirect('admin_dashboard')

    if request.method == 'POST':
        identifiant = request.POST.get('matricule', '').strip()
        password = request.POST.get('password', '')

        # 1) Essayer en tant qu'étudiant (matricule)
        try:
            etudiant = Etudiant.objects.get(matricule=identifiant)
            user = authenticate(request,
                                username=etudiant.user.username,
                                password=password)
            if user:
                # Vérifier si le compte est validé
                if not etudiant.est_valide:
                    messages.error(request, "Votre compte est en attente de validation par l'administration.")
                    logout(request)
                    return redirect('login')

                login(request, user)

                # Vérifier si c'est la première connexion
                if not etudiant.mot_de_passe_change:
                    messages.info(request, "Veuillez changer votre mot de passe par défaut pour continuer.")
                    return redirect('changer_mot_de_passe')

                messages.success(request, f'Bienvenue {etudiant.prenom} !')
                return redirect('profil')
            else:
                messages.error(request, 'Mot de passe incorrect.')
                return render(request, 'etudiants/login.html')
        except Etudiant.DoesNotExist:
            pass

        # 2) Essayer en tant qu'admin (username)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            admin_user = User.objects.get(username=identifiant, is_staff=True)
            user = authenticate(request, username=identifiant, password=password)
            if user and user.is_staff:
                login(request, user)
                messages.success(request, f'Bienvenue !')
                try:
                    profil = user.profiladmin
                    redirections = {
                        'chef_ntic': 'dashboard_chef',
                        'chef_dl':   'dashboard_chef',
                        'dga':       'dashboard_dga',
                        'dg':        'dashboard_dg',
                    }
                    url = redirections.get(profil.role, 'admin_dashboard')
                    return redirect(url)
                except:
                    return redirect('admin_dashboard')
            else:
                messages.error(request, 'Mot de passe incorrect.')
                return render(request, 'etudiants/login.html')
        except User.DoesNotExist:
            pass

        # 3) Rien trouvé
        messages.error(request, 'Identifiant introuvable. Vérifiez votre matricule ou nom d\'utilisateur.')

    return render(request, 'etudiants/login.html')


def login_admin(request):
    """Connexion administration"""
    if request.user.is_authenticated and request.user.is_staff:
        try:
            role = request.user.profiladmin.role
            return redirect('dashboard_chef' if role in ['chef_ntic', 'chef_dl'] else f'dashboard_{role}')
        except:
            return redirect('admin_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)
        if user and user.is_staff:
            login(request, user)
            messages.success(request, f'Bienvenue Administrateur !')
            try:
                profil = user.profiladmin
                redirections = {
                    'chef_ntic': 'dashboard_chef',
                    'chef_dl':   'dashboard_chef',
                    'dga':       'dashboard_dga',
                    'dg':        'dashboard_dg',
                }
                url = redirections.get(profil.role, 'admin_dashboard')
                return redirect(url)
            except:
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


@login_required
def changer_mot_de_passe(request):
    """Vue pour forcer le changement de mot de passe"""
    try:
        etudiant = Etudiant.objects.get(user=request.user)
    except Etudiant.DoesNotExist:
        messages.error(request, "Seuls les étudiants peuvent changer leur mot de passe ici.")
        return redirect('accueil')

    if request.method == 'POST':
        ancien = request.POST.get('ancien')
        nouveau = request.POST.get('nouveau')
        confirmation = request.POST.get('confirmation')

        # Vérifier ancien mot de passe
        if not request.user.check_password(ancien):
            messages.error(request, 'Ancien mot de passe incorrect.')
            return redirect('changer_mot_de_passe')

        # Vérifier que nouveau != ancien
        if nouveau == ancien:
            messages.error(request, 'Le nouveau mot de passe doit être différent de l\'ancien.')
            return redirect('changer_mot_de_passe')

        # Vérifier confirmation
        if nouveau != confirmation:
            messages.error(request, 'Les mots de passe ne correspondent pas.')
            return redirect('changer_mot_de_passe')

        # Vérifier longueur
        if len(nouveau) < 6:
            messages.error(request, 'Le mot de passe doit contenir au moins 6 caractères.')
            return redirect('changer_mot_de_passe')

        # Sauvegarder le nouveau mot de passe
        request.user.set_password(nouveau)
        request.user.save()

        # Mettre à jour la session pour éviter la déconnexion
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, request.user)

        # Marquer comme changé
        etudiant.mot_de_passe_change = True
        etudiant.save()

        messages.success(request, 'Votre mot de passe a été modifié avec succès !')
        return redirect('profil')

    return render(request, 'etudiants/changer_mot_de_passe.html', {
        'etudiant': etudiant
    })
