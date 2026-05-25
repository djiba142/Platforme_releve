from django.db import models
from django.contrib.auth.models import User


class Etudiant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    matricule = models.CharField(max_length=20, unique=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    filiere = models.CharField(max_length=100)
    niveau = models.CharField(max_length=20)

    class Meta:
        verbose_name = 'Étudiant'
        verbose_name_plural = 'Étudiants'
        ordering = ['matricule']

    def __str__(self):
        return f"{self.matricule} - {self.nom} {self.prenom}"
