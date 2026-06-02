from django.contrib import admin
from .models import Note, ImportNotes

@admin.register(ImportNotes)
class ImportNotesAdmin(admin.ModelAdmin):
    list_display = ['filiere', 'session', 'statut', 'date_depot']
    list_filter = ['statut', 'filiere'] 

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ['etudiant', 'matiere', 'note', 'session', 'annee']
    search_fields = ['etudiant__matricule', 'matiere']
    list_filter = ['session', 'annee']
