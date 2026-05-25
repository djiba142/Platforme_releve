from django.db import models
from etudiants.models import Etudiant


class Note(models.Model):
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, related_name='notes')
    matiere = models.CharField(max_length=100)
    note = models.FloatField()
    session = models.CharField(max_length=50)
    annee = models.CharField(max_length=10)

    class Meta:
        verbose_name = 'Note'
        verbose_name_plural = 'Notes'
        ordering = ['matiere']

    def __str__(self):
        return f"{self.etudiant.matricule} - {self.matiere} - {self.note}"
