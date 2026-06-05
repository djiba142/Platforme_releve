from django.db import models
from django.contrib.auth.models import User


class Departement(models.Model):
    nom  = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = 'Département'
        verbose_name_plural = 'Départements'

    def __str__(self):
        return self.nom


class Niveau(models.Model):
    departement = models.ForeignKey(Departement, on_delete=models.CASCADE, related_name='niveaux')
    nom         = models.CharField(max_length=50)
    slug        = models.SlugField(unique=True)

    class Meta:
        verbose_name = 'Niveau'
        verbose_name_plural = 'Niveaux'

    def __str__(self):
        return f"{self.departement.slug.upper()} - {self.nom}"


class Session(models.Model):
    niveau = models.ForeignKey(Niveau, on_delete=models.CASCADE, related_name='sessions')
    nom    = models.CharField(max_length=50)
    slug   = models.SlugField(unique=True)

    class Meta:
        verbose_name = 'Session'
        verbose_name_plural = 'Sessions'

    def __str__(self):
        return f"{self.niveau.departement.slug.upper()} - {self.niveau.nom} - {self.nom}"


class Etudiant(models.Model):
    user                = models.OneToOneField(User, on_delete=models.CASCADE)
    matricule           = models.CharField(max_length=20, unique=True)
    nom                 = models.CharField(max_length=100)
    prenom              = models.CharField(max_length=100)
    departement         = models.ForeignKey(Departement, on_delete=models.SET_NULL, null=True, blank=True, related_name='etudiants')
    niveau              = models.ForeignKey(Niveau, on_delete=models.SET_NULL, null=True, blank=True, related_name='etudiants')
    mot_de_passe_change = models.BooleanField(default=False)
    # Workflow de validation : chef valide → DG/DGA active
    est_valide          = models.BooleanField(default=False, verbose_name="Compte actif")
    valide_par_chef     = models.BooleanField(default=False, verbose_name="Pré-validé par chef département")
    date_inscription    = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Étudiant'
        verbose_name_plural = 'Étudiants'
        ordering = ['matricule']

    def __str__(self):
        return f"{self.matricule} - {self.nom} {self.prenom}"

    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"

    @property
    def statut_inscription(self):
        if self.est_valide:
            return 'actif'
        elif self.valide_par_chef:
            return 'en_attente_dg'
        else:
            return 'en_attente_chef'

    def save(self, *args, **kwargs):
        # Auto-affecter département selon le préfixe matricule
        if not self.departement and self.matricule:
            if self.matricule.startswith('6642'):
                try:
                    self.departement = Departement.objects.get(slug='ntic')
                except Departement.DoesNotExist:
                    pass
            elif self.matricule.startswith('6644'):
                try:
                    self.departement = Departement.objects.get(slug='dl')
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

    user      = models.OneToOneField(User, on_delete=models.CASCADE)
    role      = models.CharField(max_length=20, choices=ROLE_CHOICES)
    nom       = models.CharField(max_length=100)
    prenom    = models.CharField(max_length=100)
    email     = models.EmailField()
    telephone = models.CharField(max_length=20, blank=True, null=True)
    signature = models.ImageField(upload_to='signatures/', blank=True, null=True)

    def __str__(self):
        return f"{self.get_role_display()} — {self.prenom} {self.nom}"

    def get_role_label(self):
        labels = {
            'admin':     'Administrateur Système',
            'dg':        'Directeur Général',
            'dga':       'Directeur Général Adjoint',
            'chef_ntic': 'Chef Département NTIC',
            'chef_dl':   'Chef Département DL',
        }
        return labels.get(self.role, self.role)

    class Meta:
        verbose_name = "Profil Administrateur"
