from django.db import models
from demandes.models import Demande


class Releve(models.Model):
    demande = models.OneToOneField(Demande, on_delete=models.CASCADE, related_name='releve')
    fichier_pdf = models.FileField(upload_to='releves/')
    date_generation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Relevé'
        verbose_name_plural = 'Relevés'

    def __str__(self):
        return f"Relevé - {self.demande.etudiant.matricule} - {self.demande.session}"
