from django.db import models
from django.contrib.auth.models import User


class Departement(models.Model):
    nom = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = 'Département'
        verbose_name_plural = 'Départements'

    def __str__(self):
        return self.nom

class Niveau(models.Model):
    departement = models.ForeignKey(Departement, on_delete=models.CASCADE, related_name='niveaux')
    nom = models.CharField(max_length=50) # e.g. Licence 1, Master
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = 'Niveau'
        verbose_name_plural = 'Niveaux'

    def __str__(self):
        return f"{self.departement.slug.upper()} - {self.nom}"

class Session(models.Model):
    niveau = models.ForeignKey(Niveau, on_delete=models.CASCADE, related_name='sessions')
    nom = models.CharField(max_length=50) # e.g. Session 1, Session 2
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = 'Session'
        verbose_name_plural = 'Sessions'

    def __str__(self):
        return f"{self.niveau.departement.slug.upper()} - {self.niveau.nom} - {self.nom}"


class Etudiant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    matricule = models.CharField(max_length=20, unique=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    departement = models.ForeignKey(Departement, on_delete=models.SET_NULL, null=True, related_name='etudiants')
    niveau = models.ForeignKey(Niveau, on_delete=models.SET_NULL, null=True, related_name='etudiants')
    mot_de_passe_change = models.BooleanField(default=False)
    est_valide = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Étudiant'
        verbose_name_plural = 'Étudiants'
        ordering = ['matricule']

    def __str__(self):
        return f"{self.matricule} - {self.nom} {self.prenom}"

    def save(self, *args, **kwargs):
        if not self.departement and self.matricule:
            if self.matricule.startswith('6642'):
                try:
                    from .models import Departement
                    dept = Departement.objects.get(slug='ntic')
                    self.departement = dept
                except Departement.DoesNotExist:
                    pass
            elif self.matricule.startswith('6644'):
                try:
                    from .models import Departement
                    dept = Departement.objects.get(slug='dl')
                    self.departement = dept
                except Departement.DoesNotExist:
                    pass
        super().save(*args, **kwargs)


class ProfilAdmin(models.Model):

    ROLE_CHOICES = [
        ('admin',      'Administrateur Système'),
        ('dg',         'Directeur Général'),
        ('dga',        'Directeur Général Adjoint'),
        ('chef_ntic',  'Chef de Département NTIC'),
        ('chef_dl',    'Chef de Département DL'),
    ]

    user       = models.OneToOneField(
        User, on_delete=models.CASCADE
    )
    role       = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES
    )
    nom        = models.CharField(max_length=100)
    prenom     = models.CharField(max_length=100)
    email      = models.EmailField()
    telephone  = models.CharField(
        max_length=20, blank=True, null=True
    )

    # Signature image (optionnel)
    signature  = models.ImageField(
        upload_to='signatures/',
        blank=True, null=True
    )

    def __str__(self):
        return f"{self.get_role_display()} — {self.prenom} {self.nom}"

    def get_role_label(self):
        labels = {
            'admin':     'Administrateur Système',
            'dg':        'Directeur Général',
            'dga':       'Directeur Général Adjoint',
            'chef_ntic': 'Chef de Département NTIC',
            'chef_dl':   'Chef de Département DL',
        }
        return labels.get(self.role, self.role)

    class Meta:
        verbose_name = "Profil Administrateur"
