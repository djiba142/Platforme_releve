from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('chef/', views.dashboard_chef, name='dashboard_chef'),
    path('dga/', views.dashboard_dga, name='dashboard_dga'),
    path('dg/', views.dashboard_dg, name='dashboard_dg'),
    path('utilisateurs/creer/', views.creer_utilisateur, name='creer_utilisateur'),
    path('utilisateurs/toggle/<int:user_id>/', views.toggle_utilisateur, name='toggle_utilisateur'),
    path('etudiants/', views.liste_etudiants, name='liste_etudiants'),
    path('etudiants/ajouter/', views.ajouter_etudiant, name='ajouter_etudiant'),
    path('etudiants/supprimer/<int:etudiant_id>/', views.supprimer_etudiant, name='supprimer_etudiant'),
    path('inscriptions/', views.gestion_inscriptions, name='gestion_inscriptions'),
    path('inscriptions/valider/<int:etudiant_id>/', views.valider_inscription, name='valider_inscription'),
    path('inscriptions/rejeter/<int:etudiant_id>/', views.rejeter_inscription, name='rejeter_inscription'),
    path('notes/', views.gestion_notes, name='gestion_notes'),
    path('notes/ajouter/', views.ajouter_note, name='ajouter_note'),
    path('demandes/', views.gestion_demandes, name='gestion_demandes'),
    path('demandes/valider/<int:demande_id>/', views.valider_demande, name='valider_demande'),
    path('demandes/rejeter/<int:demande_id>/', views.rejeter_demande, name='rejeter_demande'),
]
