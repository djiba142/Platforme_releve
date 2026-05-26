from django.contrib import admin
from .models import Etudiant


@admin.register(Etudiant)
class EtudiantAdmin(admin.ModelAdmin):
    list_display = ['matricule', 'nom', 'prenom', 'departement', 'niveau']
    search_fields = ['matricule', 'nom', 'prenom']
    list_filter = ['departement', 'niveau']
