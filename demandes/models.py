from django.db import models
from etudiants.models import Etudiant


class Demande(models.Model):
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('validee', 'Validée'),
        ('rejetee', 'Rejetée'),
    ]
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, related_name='demandes')
    date_demande = models.DateTimeField(auto_now_add=True)
    session = models.CharField(max_length=50)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')

    class Meta:
        verbose_name = 'Demande'
        verbose_name_plural = 'Demandes'
        ordering = ['-date_demande']

    def __str__(self):
        return f"{self.etudiant.matricule} - {self.session} - {self.statut}"
