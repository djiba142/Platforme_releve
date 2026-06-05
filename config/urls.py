from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('etudiants.urls')),
    path('notes/', include('notes.urls')),
    path('demandes/', include('demandes.urls')),
    path('releves/', include('releves.urls')),
    path('chatbot/', include('chatbot.urls')),
    path('administration/', include('administration.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# ── Route raccourci recherche notes (accessible sans /notes/) ──
from notes.views import recherche_notes as _recherche_notes, pdf_par_matricule as _pdf_par_matricule
urlpatterns += [
    path('mes-notes/',  _recherche_notes,   name='mes_notes_publique'),
    path('releve-pdf/', _pdf_par_matricule,  name='releve_pdf_direct'),
]
