from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Etudiant, Departement, Niveau, ProfilAdmin


# ── Helpers ──────────────────────────────────

def _redirect_apres_login(user):
    """Renvoie vers la bonne URL selon le rôle."""
    if hasattr(user, 'etudiant'):
        return redirect('profil')
    if user.is_staff:
        try:
            role = user.profiladmin.role
            mapping = {
                'admin':     'admin_dashboard',
                'dg':        'dashboard_dg',
                'dga':       'dashboard_dga',
                'chef_ntic': 'dashboard_chef',
                'chef_dl':   'dashboard_chef',
            }
            return redirect(mapping.get(role, 'admin_dashboard'))
        except Exception:
            return redirect('admin_dashboard')
    return redirect('accueil')


# ── Pages publiques ───────────────────────────

def accueil_view(request):
    if request.user.is_authenticated:
        return _redirect_apres_login(request.user)
    return render(request, 'etudiants/accueil.html')


def landing_page(request):
    return redirect('accueil')


# ── Inscription étudiant ──────────────────────

def inscription_etudiant(request):
    if request.user.is_authenticated:
        return _redirect_apres_login(request.user)

    departements = Departement.objects.all()
    niveaux      = Niveau.objects.all()

    if request.method == 'POST':
        matricule        = request.POST.get('matricule', '').strip().upper()
        nom              = request.POST.get('nom', '').strip()
        prenom           = request.POST.get('prenom', '').strip()
        departement_id   = request.POST.get('departement', '').strip()
        niveau_id        = request.POST.get('niveau', '').strip()
        password         = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')

        # Validations
        if not all([matricule, nom, prenom, password]):
            messages.error(request, 'Tous les champs obligatoires doivent être remplis.')
            return render(request, 'etudiants/inscription.html', {'departements': departements, 'niveaux': niveaux})

        if password != password_confirm:
            messages.error(request, 'Les mots de passe ne correspondent pas.')
            return render(request, 'etudiants/inscription.html', {'departements': departements, 'niveaux': niveaux})

        if len(password) < 6:
            messages.error(request, 'Le mot de passe doit contenir au moins 6 caractères.')
            return render(request, 'etudiants/inscription.html', {'departements': departements, 'niveaux': niveaux})

        if Etudiant.objects.filter(matricule=matricule).exists() or User.objects.filter(username=matricule).exists():
            messages.error(request, 'Ce matricule est déjà utilisé ou en attente de validation.')
            return render(request, 'etudiants/inscription.html', {'departements': departements, 'niveaux': niveaux})

        try:
            user = User.objects.create_user(username=matricule, password=password)
            Etudiant.objects.create(
                user=user,
                matricule=matricule,
                nom=nom,
                prenom=prenom,
                departement_id=departement_id or None,
                niveau_id=niveau_id or None,
                mot_de_passe_change=True,   # BUG FIX : l'étudiant définit lui-même son mdp
                est_valide=False,            # en attente de validation
                valide_par_chef=False,       # le chef de dept doit d'abord valider
            )
            messages.success(
                request,
                "✅ Inscription soumise ! Votre demande sera d'abord examinée par votre "
                "Chef de Département, puis activée par la Direction."
            )
            return redirect('login')
        except Exception as e:
            messages.error(request, f"Erreur lors de l'inscription : {str(e)}")

    return render(request, 'etudiants/inscription.html', {
        'departements': departements,
        'niveaux': niveaux
    })


# ── Login unifié ──────────────────────────────

def login_etudiant(request):
    if request.user.is_authenticated:
        return _redirect_apres_login(request.user)

    if request.method == 'POST':
        identifiant = request.POST.get('matricule', '').strip()
        password    = request.POST.get('password', '')

        # 1) Étudiant via matricule
        try:
            etudiant = Etudiant.objects.get(matricule__iexact=identifiant)
            user     = authenticate(request, username=etudiant.user.username, password=password)
            if user:
                statut = etudiant.statut_inscription
                if statut == 'en_attente_chef':
                    messages.error(request, "⏳ Votre inscription est en attente de validation par votre Chef de Département.")
                    return render(request, 'etudiants/login.html')
                elif statut == 'en_attente_dg':
                    messages.error(request, "⏳ Votre inscription a été validée par le Chef de Département et attend l'activation par la Direction.")
                    return render(request, 'etudiants/login.html')
                # Compte actif
                login(request, user)
                if not etudiant.mot_de_passe_change:
                    messages.info(request, "Veuillez changer votre mot de passe par défaut.")
                    return redirect('changer_mot_de_passe')
                messages.success(request, f'Bienvenue {etudiant.prenom} !')
                return redirect('profil')
            else:
                messages.error(request, 'Mot de passe incorrect.')
                return render(request, 'etudiants/login.html')
        except Etudiant.DoesNotExist:
            pass

        # 2) Admin / cadre via username
        try:
            admin_user = User.objects.get(username=identifiant, is_staff=True)
            user = authenticate(request, username=identifiant, password=password)
            if user and user.is_staff:
                login(request, user)
                messages.success(request, 'Bienvenue !')
                return _redirect_apres_login(user)
            else:
                messages.error(request, 'Mot de passe incorrect.')
                return render(request, 'etudiants/login.html')
        except User.DoesNotExist:
            pass

        messages.error(request, "Identifiant introuvable. Vérifiez votre matricule ou votre identifiant.")

    return render(request, 'etudiants/login.html')


def login_admin(request):
    """Connexion dédiée administration."""
    if request.user.is_authenticated and request.user.is_staff:
        return _redirect_apres_login(request.user)

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user and user.is_staff:
            login(request, user)
            messages.success(request, 'Bienvenue !')
            return _redirect_apres_login(user)
        elif user:
            messages.error(request, "Vous n'êtes pas autorisé à accéder à l'administration.")
        else:
            messages.error(request, 'Identifiants incorrects.')

    return render(request, 'etudiants/login_admin.html')


def logout_view(request):
    logout(request)
    return redirect('accueil')


# ── Profil étudiant ───────────────────────────

@login_required
def profil_view(request):
    try:
        etudiant = Etudiant.objects.get(user=request.user)
    except Etudiant.DoesNotExist:
        if request.user.is_staff:
            return _redirect_apres_login(request.user)
        messages.error(request, 'Profil étudiant non trouvé.')
        return redirect('accueil')

    from notes.models import Note
    from demandes.models import Demande
    from django.db.models import Q

    notes    = Note.objects.filter(etudiant=etudiant)
    demandes = Demande.objects.filter(etudiant=etudiant).order_by('-date_demande')[:5]
    moyenne  = round(sum(n.note for n in notes) / notes.count(), 2) if notes.exists() else 0

    return render(request, 'etudiants/profil.html', {
        'etudiant':     etudiant,
        'notes':        notes,
        'demandes':     demandes,
        'moyenne':      moyenne,
        'nb_notes':     notes.count(),
        'nb_demandes':  Demande.objects.filter(etudiant=etudiant).count(),
        'nb_validees':  Demande.objects.filter(etudiant=etudiant, statut='validee').count(),
    })


@login_required
def changer_mot_de_passe(request):
    try:
        etudiant = Etudiant.objects.get(user=request.user)
    except Etudiant.DoesNotExist:
        messages.error(request, "Profil non trouvé.")
        return redirect('accueil')

    if request.method == 'POST':
        ancien       = request.POST.get('ancien', '')
        nouveau      = request.POST.get('nouveau', '')
        confirmation = request.POST.get('confirmation', '')

        if not request.user.check_password(ancien):
            messages.error(request, 'Ancien mot de passe incorrect.')
            return redirect('changer_mot_de_passe')
        if len(nouveau) < 6:
            messages.error(request, 'Le nouveau mot de passe doit contenir au moins 6 caractères.')
            return redirect('changer_mot_de_passe')
        if nouveau != confirmation:
            messages.error(request, 'Les nouveaux mots de passe ne correspondent pas.')
            return redirect('changer_mot_de_passe')

        request.user.set_password(nouveau)
        request.user.save()
        etudiant.mot_de_passe_change = True
        etudiant.save()
        messages.success(request, 'Mot de passe modifié avec succès !')
        user = authenticate(request, username=request.user.username, password=nouveau)
        if user:
            login(request, user)
        return redirect('profil')

    return render(request, 'etudiants/changer_mot_de_passe.html', {'etudiant': etudiant})
