from django.urls import path
from . import views

urlpatterns = [
    path('', views.accueil_view, name='accueil'),
    path('accueil/', views.accueil_view, name='accueil_alt'),
    path('login/', views.login_etudiant, name='login'),
    path('login/admin/', views.login_admin, name='login_admin'),
    path('logout/', views.logout_view, name='logout'),
    path('profil/', views.profil_view, name='profil'),
]
