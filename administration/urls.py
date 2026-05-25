from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('etudiants/', views.liste_etudiants, name='liste_etudiants'),
    path('etudiants/ajouter/', views.ajouter_etudiant, name='ajouter_etudiant'),
    path('etudiants/supprimer/<int:etudiant_id>/', views.supprimer_etudiant, name='supprimer_etudiant'),
    path('notes/', views.gestion_notes, name='gestion_notes'),
    path('notes/ajouter/', views.ajouter_note, name='ajouter_note'),
    path('demandes/', views.gestion_demandes, name='gestion_demandes'),
    path('demandes/valider/<int:demande_id>/', views.valider_demande, name='valider_demande'),
    path('demandes/rejeter/<int:demande_id>/', views.rejeter_demande, name='rejeter_demande'),
]
