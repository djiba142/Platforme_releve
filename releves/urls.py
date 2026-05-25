from django.urls import path
from . import views

urlpatterns = [
    path('telecharger/<int:demande_id>/', views.telecharger_releve, name='telecharger_releve'),
]
