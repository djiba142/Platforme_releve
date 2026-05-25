from django.contrib import admin
from .models import Demande


@admin.register(Demande)
class DemandeAdmin(admin.ModelAdmin):
    list_display = ['etudiant', 'session', 'statut', 'date_demande']
    search_fields = ['etudiant__matricule']
    list_filter = ['statut', 'session']
    list_editable = ['statut']
