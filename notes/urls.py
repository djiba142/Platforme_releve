from django.urls import path
from . import views

urlpatterns = [
    # Étudiant connecté
    path('',                                    views.liste_notes,        name='liste_notes'),
    # Recherche par matricule (page UI)
    path('recherche/',                          views.recherche_notes,    name='recherche_notes'),
    # Génération PDF directe par matricule (téléchargement)
    path('pdf/',                                views.pdf_par_matricule,  name='pdf_par_matricule'),

    # Chef de département — import CSV
    path('deposer/',                            views.deposer_notes,      name='deposer_notes'),

    # Workflow validation
    path('imports/',                            views.gestion_imports,    name='gestion_imports'),
    path('imports/valider-dga/<int:import_id>/',views.valider_notes_dga,  name='valider_import_dga'),
    path('imports/valider-dg/<int:import_id>/', views.valider_notes_dg,   name='valider_import_dg'),
    path('imports/rejeter/<int:import_id>/',    views.rejeter_notes,      name='rejeter_import'),
    path('imports/consulter/<int:import_id>/',  views.consulter_import,   name='consulter_import'),
]
