from django.urls import path
from . import views

urlpatterns = [
    path('',
         views.liste_notes,
         name='liste_notes'),
    path('deposer/',
         views.deposer_notes,
         name='deposer_notes'),
    path('imports/',
         views.gestion_imports,
         name='gestion_imports'),
    path('imports/valider-dga/<int:import_id>/',
         views.valider_notes_dga,
         name='valider_notes_dga'),
    path('imports/valider-dg/<int:import_id>/',
         views.valider_notes_dg,
         name='valider_notes_dg'),
    path('imports/rejeter/<int:import_id>/',
         views.rejeter_notes,
         name='rejeter_notes'),
]
