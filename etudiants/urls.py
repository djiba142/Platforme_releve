from django.urls import path
from . import views

urlpatterns = [
    path('',                       views.accueil_view,          name='accueil'),
    path('inscription/',           views.inscription_etudiant,  name='inscription'),
    path('login/',                 views.login_etudiant,        name='login'),
    path('login/admin/',           views.login_admin,           name='login_admin'),
    path('logout/',                views.logout_view,           name='logout'),
    path('profil/',                views.profil_view,           name='profil'),
    path('changer-mot-de-passe/',  views.changer_mot_de_passe,  name='changer_mot_de_passe'),
]
