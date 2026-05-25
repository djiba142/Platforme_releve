from django.contrib import admin
from .models import Releve


@admin.register(Releve)
class ReleveAdmin(admin.ModelAdmin):
    list_display = ['demande', 'fichier_pdf', 'date_generation']
