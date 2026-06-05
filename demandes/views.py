from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Demande
from etudiants.models import Etudiant, Session


@login_required
def creer_demande(request):
    """L'étudiant soumet une demande de relevé."""
    try:
        etudiant = Etudiant.objects.get(user=request.user)
    except Etudiant.DoesNotExist:
        messages.error(request, "Profil étudiant non trouvé.")
        return redirect('accueil')

    sessions = Session.objects.filter(niveau=etudiant.niveau) if etudiant.niveau else Session.objects.all()

    if request.method == 'POST':
        session_nom = request.POST.get('session', '').strip()
        if not session_nom:
            messages.error(request, "Veuillez sélectionner une session.")
        elif Demande.objects.filter(etudiant=etudiant, session=session_nom, statut__in=['en_attente', 'validee']).exists():
            messages.warning(request, f"Une demande pour la session '{session_nom}' est déjà en cours ou validée.")
        else:
            Demande.objects.create(etudiant=etudiant, session=session_nom, statut='en_attente')
            messages.success(request, f"✅ Demande soumise pour la session « {session_nom} ». En attente de validation.")
            return redirect('historique_demandes')

    return render(request, 'demandes/creer_demande.html', {
        'etudiant': etudiant,
        'sessions': sessions,
    })


@login_required
def historique_demandes(request):
    """Historique des demandes de l'étudiant."""
    try:
        etudiant = Etudiant.objects.get(user=request.user)
    except Etudiant.DoesNotExist:
        messages.error(request, "Profil introuvable.")
        return redirect('accueil')

    demandes = Demande.objects.filter(etudiant=etudiant).order_by('-date_demande')
    return render(request, 'demandes/historique.html', {
        'demandes': demandes,
        'etudiant': etudiant,
    })
