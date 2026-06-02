from django.db import models
from etudiants.models import Etudiant


class Note(models.Model):
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, related_name='notes')
    matiere = models.CharField(max_length=100)
    note = models.FloatField()
    session = models.ForeignKey('etudiants.Session', on_delete=models.CASCADE, related_name='notes')
    annee = models.CharField(max_length=10)

    class Meta:
        verbose_name = 'Note'
        verbose_name_plural = 'Notes'
        ordering = ['matiere']

    def __str__(self):
        return f"{self.etudiant.matricule} - {self.matiere} - {self.note}"


class ImportNotes(models.Model):

    STATUT_CHOICES = [
        ('depose',             'Déposé par Chef Département'),
        ('valide_dga',         'Validé par DGA'),
        ('valide_dg',          'Validé par DG — Actif'),
        ('rejete',             'Rejeté'),
    ]

    fichier        = models.FileField(
        upload_to='imports/'
    )
    filiere        = models.CharField(max_length=10)
    session        = models.CharField(max_length=50)
    annee          = models.CharField(max_length=10)
    depose_par     = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='imports_deposes'
    )
    date_depot     = models.DateTimeField(auto_now_add=True)
    statut         = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='depose'
    )
    valide_par_dga = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='imports_valides_dga'
    )
    date_validation_dga = models.DateTimeField(
        null=True, blank=True
    )
    valide_par_dg  = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='imports_valides_dg'
    )
    date_validation_dg  = models.DateTimeField(
        null=True, blank=True
    )
    nb_notes_importees  = models.IntegerField(default=0)
    commentaire         = models.TextField(
        blank=True, null=True
    )

    def __str__(self):
        return (
            f"Import {self.filiere} — "
            f"{self.session} — {self.statut}"
        )

    class Meta:
        verbose_name = "Import de Notes"
