from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Demande
from etudiants.models import Etudiant
from notes.models import Note, ImportNotes


def notes_validees_dg(etudiant, session):
    """
    Vérifie si les notes de cet étudiant
    pour cette session ont été validées par le DG.
    """
    matricule = etudiant.matricule.upper()
    if matricule.startswith('6642') or 'NT' in matricule:
        filiere = 'NTIC'
    elif matricule.startswith('6644') or 'DL' in matricule:
        filiere = 'DL'
    else:
        filiere = None

    if not filiere:
        return False

    return ImportNotes.objects.filter(
        filiere=filiere,
        session=session,
        statut='valide_dg'
    ).exists()


@login_required
def creer_demande(request):
    etudiant = Etudiant.objects.get(user=request.user)

    if request.method == 'POST':
        session = request.POST.get('session')

        # ── Vérifier que les notes sont validées par DG ──
        if not notes_validees_dg(etudiant, session):
            messages.error(
                request,
                f'Les notes pour {session} ne sont pas encore '
                f'disponibles. Contactez l\'administration.'
            )
            return redirect('historique')

        # ── Vérifier doublon ──
        if Demande.objects.filter(
            etudiant=etudiant,
            session=session
        ).exists():
            messages.warning(
                request,
                'Vous avez déjà une demande pour cette session.'
            )
            return redirect('historique')

        # ── Notes disponibles → demande validée AUTOMATIQUEMENT ──
        demande = Demande.objects.create(
            etudiant=etudiant,
            session=session,
            statut='validee'
        )

        messages.success(
            request,
            f'Relevé disponible ! Demande #{demande.id:04d} générée.'
        )
        return redirect('historique')

    return render(request, 'demandes/creer_demande.html', {
        'etudiant': etudiant
    })


@login_required
def historique(request):
    etudiant = Etudiant.objects.get(user=request.user)
    demandes = Demande.objects.filter(
        etudiant=etudiant
    ).order_by('-date_demande')

    nb_attente = demandes.filter(statut='en_attente').count()
    nb_validees = demandes.filter(statut='validee').count()

    return render(request, 'demandes/historique.html', {
        'demandes': demandes,
        'etudiant': etudiant,
        'nb_attente': nb_attente,
        'nb_validees': nb_validees,
    })
