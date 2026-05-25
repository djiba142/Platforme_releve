from django.urls import path
from . import views

urlpatterns = [
    path('', views.liste_notes, name='liste_notes'),
    path('import/', views.import_csv, name='import_csv'),
]
