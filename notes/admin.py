from django.contrib import admin
from .models import Note


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ['etudiant', 'matiere', 'note', 'session', 'annee']
    search_fields = ['etudiant__matricule', 'matiere']
    list_filter = ['session', 'annee']
