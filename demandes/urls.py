from django.urls import path
from . import views

urlpatterns = [
    path('creer/',       views.creer_demande,      name='creer_demande'),
    path('historique/',  views.historique_demandes, name='historique_demandes'),
]
