import os
import django
import re
import sys

# Initialisation de Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from etudiants.models import Etudiant, Departement, Niveau
from django.contrib.auth.models import User
from django.utils.text import slugify

raw_data = """
1 664228662347BAH ALPHA OUMAR M 6,25 9 9,25 8 
2 664224582265BAH ALPHA YAGHOUBAM 7,5 7,5 8 8 
3 664232192366BAH DJENABOU F 3 7,75 7,5 6 
4 664231492377BAH KADIATOU F 4 9 8 7 
5 664224172398BALDE ADAMA DIAN F 7,5 7 7,5 7 
6 664225302346BARRY IBRAHIMA M 5,25 2 
7 664217742389BARRY MAMADOU M 7,5 9,5 9 9 
8 664216252383BONGONO THOMAS M 7 9 8 8 
9 664224032272CAMARA ABDOUL GADIRI M 5,5 9 8 8 
10 664232612382CAMARA AMINATA SITA F 0 
11 664281472391CAMARA BOUBACAR M 5,5 9 8 8 
12 664217242375CONDE LAYE OUMAR M 9,5 9 6 
13 664260492345CONTE FATOUMATA F 6,25 9 8 8 
14 664220892286DIALLO AMINATA F 9 8 6 
15 664229002365DIALLO BOUBACAR M 4,5 7,5 8 7 
16 664214252399DIALLO ELHADJ OUMAR M 6,5 9 9 8 
17 664220092332DIALLO FANTA F 5,5 7,5 7 7 
18 664214302377DIALLO HADJIRATOU F 7,75 7,5 5 
19 664224152336DIALLO HALIMATOU F 9 8 6 
20 664214322323DIALLO IBRAHIMA TALIBE M 9 8 6 
21 664292612387DIALLO KADIATOU F 6 7 7 7 
22 664224852374DIALLO MAMADOU HADY M 3,5 1 
23 664212672327DIALLO MAMADOU LAMARANA M 6,25 7 7 7 
24 664217812359DIALLO MAMADOU SAMBA M 6,5 7 7 7 
25 664221472371DIALLO MARIAMA TABARA F 7,5 9 8 8 
26 664232642340DIALLO MARIAME F 4 9 8 7 
27 664209622335DIALLO THIERNO SOULEYMANE M 6 7,75 7,5 7 
28 664295042320DIALLO ZAKARIA
"""

def importer_donnees():
    departement = "NTIC"
    niveau = "LICENCE 3"
    
    compteur_ajouts = 0
    lignes = raw_data.strip().split("\n")
    
    for ligne in lignes:
        ligne = ligne.strip()
        if not ligne:
            continue
            
        # Extraction du numéro de début
        parts = ligne.split(" ", 1)
        if len(parts) < 2:
            continue
            
        # Le reste de la chaîne (ex: "664228662347BAH ALPHA OUMAR M 6,25 9 9,25 8")
        reste = parts[1]
        
        # Le matricule fait toujours 12 caractères et commence par 6642
        if not reste.startswith("6642"):
            continue
            
        matricule = reste[:12]
        
        # Texte après le matricule (ex: "BAH ALPHA OUMAR M 6,25 9 9,25 8")
        suite = reste[12:].strip()
        
        # Utiliser une regex pour extraire le nom/prénom (lettres/espaces) avant les notes/genre
        # On nettoie un peu car parfois le genre "M" ou "F" est collé au prénom
        match_nom = re.match(r'^([A-Z\s]+)', suite)
        if not match_nom:
            continue
            
        nom_complet = match_nom.group(1).strip()
        
        # Parfois le genre (M/F) est collé à la fin du prénom (ex: YAGHOUBAM -> YAGHOUBA)
        if nom_complet.endswith(" M") or nom_complet.endswith(" F"):
            nom_complet = nom_complet[:-2].strip()
        elif nom_complet.endswith("M") and len(nom_complet) > 1 and nom_complet[-2] != ' ':
            nom_complet = nom_complet[:-1].strip()
        elif nom_complet.endswith("F") and len(nom_complet) > 1 and nom_complet[-2] != ' ':
            nom_complet = nom_complet[:-1].strip()
            
        # Séparation classique Nom / Prénom (le premier mot est le nom de famille)
        parts_nom = nom_complet.split(" ", 1)
        nom = parts_nom[0]
        prenom = parts_nom[1] if len(parts_nom) > 1 else ""
        
        print(f"Extraction -> Matricule: {matricule} | Nom: {nom} | Prénom: {prenom}")
        
        # Création dans la base de données
        # 1. On crée le User s'il n'existe pas
        user, created = User.objects.get_or_create(
            username=matricule,
            defaults={
                'first_name': prenom[:30],
                'last_name': nom[:30],
                'email': f"{matricule}@univ.edu"
            }
        )
        if created:
            user.set_password(matricule) # Mot de passe par défaut = matricule
            user.save()
            
        departement_slug = slugify(departement)
        dep_obj, _ = Departement.objects.get_or_create(slug=departement_slug, defaults={'nom': departement})
        
        niveau_slug = slugify(f"{departement_slug}-{niveau}")
        niv_obj, _ = Niveau.objects.get_or_create(slug=niveau_slug, defaults={'departement': dep_obj, 'nom': niveau})

        # 2. On crée l'Étudiant associé
        etudiant, etu_created = Etudiant.objects.get_or_create(
            matricule=matricule,
            defaults={
                'user': user,
                'nom': nom,
                'prenom': prenom,
                'departement': dep_obj,
                'niveau': niv_obj
            }
        )
        
        if etu_created:
            compteur_ajouts += 1

    print(f"\n--- IMPORTATION TERMINÉE ---")
    print(f"{compteur_ajouts} nouveaux étudiants ajoutés à la base !")

if __name__ == "__main__":
    importer_donnees()
