from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, HttpResponse
from django.contrib import messages
from demandes.models import Demande
from releves.models import Releve
from releves.utils.generate_pdf import generer_releve
from etudiants.models import Etudiant
import os


@login_required
def telecharger_releve(request, demande_id):
    """Télécharger ou générer le relevé PDF d'une demande validée."""
    try:
        etudiant = Etudiant.objects.get(user=request.user)
    except Etudiant.DoesNotExist:
        messages.error(request, "Profil introuvable.")
        return redirect('accueil')

    demande = get_object_or_404(Demande, id=demande_id, etudiant=etudiant)

    if demande.statut != 'validee':
        messages.error(request, "Votre demande n'est pas encore validée par l'administration.")
        return redirect('historique_demandes')

    # Générer ou récupérer le PDF
    try:
        chemin_pdf = generer_releve(demande)
    except Exception as e:
        messages.error(request, f"Erreur lors de la génération du PDF : {str(e)}")
        return redirect('historique_demandes')

    if not os.path.exists(chemin_pdf):
        messages.error(request, "Fichier PDF non trouvé. Contactez l'administration.")
        return redirect('historique_demandes')

    try:
        response = FileResponse(
            open(chemin_pdf, 'rb'),
            content_type='application/pdf'
        )
        nom_fichier = f"releve_{etudiant.matricule}_{demande.session.replace(' ', '_')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{nom_fichier}"'
        return response
    except Exception as e:
        messages.error(request, f"Impossible d'ouvrir le fichier : {str(e)}")
        return redirect('historique_demandes')
