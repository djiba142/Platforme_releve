# -*- coding: utf-8 -*-
import os
import django
from django.utils.text import slugify
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from etudiants.models import Departement, Niveau, Session
departements_data = ['Développement Logiciel', "Nouvelle Technologie de l'Information et de la Communication"]
niveaux_data = ['Licence 1', 'Licence 2', 'Licence 3', 'Master 1', 'Master 2', 'Doctorat']
sessions_data = ['Session 1', 'Session 2', 'Session Rattrapage']
for dep_nom in departements_data:
    dep_slug = 'dl' if 'Logiciel' in dep_nom else 'ntic'
    dep_obj, _ = Departement.objects.get_or_create(slug=dep_slug, defaults={'nom': dep_nom})
    for niv_nom in niveaux_data:
        niv_slug = slugify(f'{dep_slug}-{niv_nom}')
        niv_obj, _ = Niveau.objects.get_or_create(slug=niv_slug, defaults={'departement': dep_obj, 'nom': niv_nom})
        for sess_nom in sessions_data:
            sess_slug = slugify(f'{niv_slug}-{sess_nom}')
            Session.objects.get_or_create(slug=sess_slug, defaults={'niveau': niv_obj, 'nom': sess_nom})
print('Database seeded!')
