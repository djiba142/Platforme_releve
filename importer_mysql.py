#!/usr/bin/env python3
"""
════════════════════════════════════════════════════════
  IMPORT DONNÉES → MySQL
  Plateforme Relevés de Notes — UGANC NTIC
  
  PRÉ-REQUIS : Ton fichier .env doit contenir :
    DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
    (sans USE_SQLITE=1)
  
  USAGE :
    python3 importer_mysql.py
════════════════════════════════════════════════════════
"""
import os, sys

# ── 1. Supprimer USE_SQLITE pour forcer MySQL ──
os.environ.pop('USE_SQLITE', None)
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

import django
django.setup()

from django.contrib.auth.models import User
from django.db import connection
from etudiants.models import Etudiant, Departement, Niveau, Session
from notes.models import Note
import pandas as pd

print("\n══════════════════════════════════════════")
print("   IMPORT DONNÉES → MySQL")
print("══════════════════════════════════════════\n")

# ── 2. Vérifier la connexion MySQL ──
try:
    with connection.cursor() as cur:
        cur.execute("SELECT 1")
    db = connection.settings_dict
    print(f"✅ MySQL connecté : {db['NAME']} @ {db['HOST']}:{db['PORT']}")
except Exception as e:
    print(f"❌ Connexion MySQL échouée : {e}")
    print("\n  Vérifie ton fichier .env :")
    print("  DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT")
    print("  Et assure-toi que USE_SQLITE=1 est SUPPRIMÉ du .env")
    sys.exit(1)

# ── 3. Appliquer les migrations ──
print("\n── Application des migrations ──")
import subprocess
result = subprocess.run([sys.executable, "manage.py", "migrate"], capture_output=True, text=True)
if result.returncode != 0:
    print("❌ Erreur migrations :")
    print(result.stderr[-800:])
    sys.exit(1)
lignes = [l for l in result.stdout.split('\n') if 'Apply' in l or 'OK' in l]
print(f"✅ Migrations OK ({len(lignes)} tables créées/vérifiées)")

# ── 4. Créer les départements et niveaux ──
print("\n── Création des départements / niveaux ──")
dept_ntic, _ = Departement.objects.get_or_create(slug='ntic', defaults={'nom': 'NTIC'})
dept_dl,   _ = Departement.objects.get_or_create(slug='dl',   defaults={'nom': 'Développement Logiciel'})
for dept in [dept_ntic, dept_dl]:
    for nom in ['L1', 'L2', 'L3']:
        Niveau.objects.get_or_create(
            slug=f"{dept.slug}-{nom.lower()}",
            defaults={'departement': dept, 'nom': nom}
        )
print("✅ Départements NTIC et DL créés")

# ── 5. Créer les sessions (semestres) ──
SEMESTRES = {
    'Semestre 1': ('L1', ['Atelier Informatique','Mathematiques','Algo Prog 1','Logique','Ltc 1'],                                      '2023-2024'),
    'Semestre 2': ('L1', ['Algo Prog 2','Archi Ordi','Acsi','Tech Web 1','Ltc 2'],                                                     '2023-2024'),
    'Semestre 3': ('L2', ['Poo','Sgbd','Economie Gestion','Reseaux Info','Ltc 3'],                                                      '2024-2025'),
    'Semestre 4': ('L2', ['Admin Reseaux','Systemes Exploitation','Tech Web 2','Reseaux Mobiles','Ia Cybersecurite'],                    '2024-2025'),
    'Semestre 5': ('L3', ['Droit Securite Info','Reseaux Systemes Repartis','Genie Logiciel','Reseaux Haut Debit','Ltc 5'],             '2025-2026'),
    'Semestre 6': ('L3', ['Gestion Projets','Virtualisation Cloud','Services Reseaux Com','Gouvernance It','Stage Projet Reseaux'],     '2025-2026'),
}
for sem_nom, (niveau_nom, matieres, annee) in SEMESTRES.items():
    niveau = Niveau.objects.get(departement=dept_ntic, nom=niveau_nom)
    slug   = f"ntic-{niveau_nom.lower()}-{sem_nom.lower().replace(' ','')}"
    Session.objects.get_or_create(slug=slug, defaults={'niveau': niveau, 'nom': sem_nom})
print("✅ 6 sessions (semestres) créées")

# ── 6. Créer les comptes administrateurs ──
print("\n── Création des comptes administrateurs ──")
from etudiants.models import ProfilAdmin
ADMINS = [
    ('admin',     'SUPER',   'Admin',    'dg',       'admin@uganc.edu',     True,  True),
    ('chef_ntic', 'BARRY',   'Mamadou',  'chef_ntic','chef.ntic@uganc.edu', False, False),
    ('dga',       'BAH',     'Mamadou',  'dga',      'dga@uganc.edu',       False, False),
    ('dg',        'CAMARA',  'Ibrahima', 'dg',       'dg@uganc.edu',        False, False),
]
for username, nom, prenom, role, email, is_staff, is_su in ADMINS:
    u, created = User.objects.get_or_create(username=username)
    u.set_password('admin2026')
    u.is_staff = is_staff; u.is_superuser = is_su
    u.email = email; u.save()
    ProfilAdmin.objects.get_or_create(user=u, defaults={'nom':nom,'prenom':prenom,'email':email,'role':role})
    print(f"  {'✅ Créé' if created else '↩️  Existant'} : {username} / admin2026  [{role}]")

# ── 7. Importer les étudiants et notes depuis Excel ──
print("\n── Import étudiants + notes depuis Excel ──")

excel_candidates = [
    'Notes_NTIC_6_Semestres.xlsx',
    '../Notes_NTIC_6_Semestres.xlsx',
    '../../Notes_NTIC_6_Semestres.xlsx',
]
excel_path = next((p for p in excel_candidates if os.path.exists(p)), None)

if not excel_path:
    print("⚠️  Notes_NTIC_6_Semestres.xlsx non trouvé.")
    print("   Place le fichier dans le dossier du projet et relance :")
    print("   python3 importer_mysql.py")
else:
    df = pd.read_excel(excel_path)
    df.columns = [str(c).strip() for c in df.columns]

    # Mapping colonnes Excel → noms de matières
    COL_MAP = {
        'ATELIER_INFORMATIQUE':       ('Atelier Informatique',     'Semestre 1'),
        'MATHEMATIQUES':              ('Mathematiques',             'Semestre 1'),
        'ALGO_PROG_1':                ('Algo Prog 1',               'Semestre 1'),
        'LOGIQUE':                    ('Logique',                   'Semestre 1'),
        'LTC_1':                      ('Ltc 1',                     'Semestre 1'),
        'ALGO_PROG_2':                ('Algo Prog 2',               'Semestre 2'),
        'ARCHI_ORDI':                 ('Archi Ordi',                'Semestre 2'),
        'ACSI':                       ('Acsi',                      'Semestre 2'),
        'TECH_WEB_1':                 ('Tech Web 1',                'Semestre 2'),
        'LTC_2':                      ('Ltc 2',                     'Semestre 2'),
        'POO':                        ('Poo',                       'Semestre 3'),
        'SGBD':                       ('Sgbd',                      'Semestre 3'),
        'ECONOMIE_GESTION':           ('Economie Gestion',          'Semestre 3'),
        'RESEAUX_INFO':               ('Reseaux Info',              'Semestre 3'),
        'LTC_3':                      ('Ltc 3',                     'Semestre 3'),
        'ADMIN_RESEAUX':              ('Admin Reseaux',             'Semestre 4'),
        'SYSTEMES_EXPLOITATION':      ('Systemes Exploitation',     'Semestre 4'),
        'TECH_WEB_2':                 ('Tech Web 2',                'Semestre 4'),
        'RESEAUX_MOBILES':            ('Reseaux Mobiles',           'Semestre 4'),
        'IA_CYBERSECURITE':           ('Ia Cybersecurite',          'Semestre 4'),
        'DROIT_SECURITE_INFO':        ('Droit Securite Info',       'Semestre 5'),
        'RESEAUX_SYSTEMES_REPARTIS':  ('Reseaux Systemes Repartis', 'Semestre 5'),
        'GENIE_LOGICIEL':             ('Genie Logiciel',            'Semestre 5'),
        'RESEAUX_HAUT_DEBIT':         ('Reseaux Haut Debit',        'Semestre 5'),
        'LTC_5':                      ('Ltc 5',                     'Semestre 5'),
        'GESTION_PROJETS':            ('Gestion Projets',           'Semestre 6'),
        'VIRTUALISATION_CLOUD':       ('Virtualisation Cloud',      'Semestre 6'),
        'SERVICES_RESEAUX_COM':       ('Services Reseaux Com',      'Semestre 6'),
        'GOUVERNANCE_IT':             ('Gouvernance It',            'Semestre 6'),
        'STAGE_PROJET_RESEAUX':       ('Stage Projet Reseaux',      'Semestre 6'),
    }

    sessions_cache = {s.nom: s for s in Session.objects.filter(niveau__departement=dept_ntic)}
    ntic_l3 = Niveau.objects.get(departement=dept_ntic, nom='L3')

    nb_etud = 0; nb_notes = 0; nb_skip = 0

    for _, row in df.iterrows():
        matricule = str(row.get('Matricule', '')).strip()
        if not matricule or matricule == 'nan': continue

        nom_etud    = str(row.get('Nom',    '')).strip()
        prenom_etud = str(row.get('Prenom', '')).strip()

        # Créer ou récupérer l'utilisateur Django
        user, u_created = User.objects.get_or_create(
            username=matricule,
            defaults={'first_name': prenom_etud, 'last_name': nom_etud}
        )
        if u_created:
            user.set_password('ntic2026')
            user.save()

        # Créer ou récupérer l'étudiant
        etud, e_created = Etudiant.objects.get_or_create(
            matricule=matricule,
            defaults={
                'user':                user,
                'nom':                 nom_etud,
                'prenom':              prenom_etud,
                'departement':         dept_ntic,
                'niveau':              ntic_l3,
                'est_valide':          True,
                'valide_par_chef':     True,
                'mot_de_passe_change': True,
            }
        )
        if e_created: nb_etud += 1

        # Importer chaque note
        for col_excel, (matiere, sem_nom) in COL_MAP.items():
            if col_excel not in df.columns: continue
            val = row.get(col_excel)
            if pd.isna(val): continue
            try:
                note_val = float(str(val).replace(',', '.').strip())
                if not (0 <= note_val <= 20): continue
                sess = sessions_cache.get(sem_nom)
                if not sess: continue
                annee = SEMESTRES[sem_nom][2]
                _, created_note = Note.objects.update_or_create(
                    etudiant=etud, matiere=matiere, session=sess, annee=annee,
                    defaults={'note': note_val}
                )
                nb_notes += 1
            except (ValueError, TypeError):
                nb_skip += 1

    print(f"✅ {nb_etud} étudiants créés")
    print(f"✅ {nb_notes} notes importées en MySQL")
    if nb_skip:
        print(f"⚠️  {nb_skip} valeurs ignorées (format invalide)")

# ── 8. Résumé final ──
print("\n══════════════════════════════════════════")
print("   ✅ IMPORT TERMINÉ")
print("══════════════════════════════════════════")
print(f"   Étudiants en base : {Etudiant.objects.count()}")
print(f"   Notes en base     : {Note.objects.count()}")
print(f"   Comptes admin     : {User.objects.filter(profiladmin__isnull=False).count()}")
print("\n   Comptes disponibles :")
print("   ┌─────────────┬──────────────┬─────────────────────┐")
print("   │ Identifiant │ Mot de passe │ Rôle                │")
print("   ├─────────────┼──────────────┼─────────────────────┤")
print("   │ admin       │ admin2026    │ Directeur Général   │")
print("   │ chef_ntic   │ admin2026    │ Chef Département    │")
print("   │ dga         │ admin2026    │ Dir. Général Adjoint│")
print("   │ dg          │ admin2026    │ Directeur Général   │")
print("   │ <matricule> │ ntic2026     │ Étudiant            │")
print("   └─────────────┴──────────────┴─────────────────────┘")
print("\n   Lancer le serveur : python3 manage.py runserver")
print("══════════════════════════════════════════\n")
