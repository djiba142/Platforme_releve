from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse
from demandes.models import Demande
from .models import Releve
from .utils.generate_pdf import generer_releve
import os
from django.conf import settings


@login_required
def telecharger_releve(request, demande_id):
    """Télécharger le relevé PDF"""
    demande = get_object_or_404(Demande, id=demande_id)

    # Vérifier que la demande est validée
    if demande.statut != 'validee':
        messages.error(request, 'Votre demande n\'est pas encore validée.')
        return redirect('historique')

    # Générer ou récupérer le relevé
    try:
        releve = Releve.objects.get(demande=demande)
    except Releve.DoesNotExist:
        chemin_pdf = generer_releve(demande)
        releve = Releve.objects.create(
            demande=demande,
            fichier_pdf=chemin_pdf
        )

    # Servir le fichier PDF
    fichier_path = os.path.join(settings.MEDIA_ROOT, str(releve.fichier_pdf))
    if os.path.exists(fichier_path):
        return FileResponse(open(fichier_path, 'rb'), content_type='application/pdf')
    else:
        # Regénérer si le fichier n'existe pas
        chemin_pdf = generer_releve(demande)
        releve.fichier_pdf = chemin_pdf
        releve.save()
        fichier_path = os.path.join(settings.MEDIA_ROOT, chemin_pdf)
        return FileResponse(open(fichier_path, 'rb'), content_type='application/pdf')
