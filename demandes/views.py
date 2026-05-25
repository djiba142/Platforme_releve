from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Demande
from etudiants.models import Etudiant


@login_required
def creer_demande(request):
    """Créer une nouvelle demande de relevé"""
    etudiant = Etudiant.objects.get(user=request.user)

    if request.method == 'POST':
        session = request.POST.get('session')

        demande_existante = Demande.objects.filter(
            etudiant=etudiant,
            session=session,
            statut='en_attente'
        ).exists()

        if demande_existante:
            messages.warning(request,
                             'Une demande est déjà en attente pour cette session.')
        else:
            Demande.objects.create(
                etudiant=etudiant,
                session=session
            )
            messages.success(request, 'Demande envoyée avec succès !')

        return redirect('historique')

    return render(request, 'demandes/creer_demande.html', {
        'etudiant': etudiant
    })


@login_required
def historique(request):
    """Historique des demandes de l'étudiant"""
    etudiant = Etudiant.objects.get(user=request.user)
    demandes = Demande.objects.filter(etudiant=etudiant).order_by('-date_demande')

    nb_attente = demandes.filter(statut='en_attente').count()
    nb_validees = demandes.filter(statut='validee').count()

    return render(request, 'demandes/historique.html', {
        'demandes': demandes,
        'etudiant': etudiant,
        'nb_attente': nb_attente,
        'nb_validees': nb_validees,
    })
