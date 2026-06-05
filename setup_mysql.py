"""
Script d'initialisation MySQL pour la plateforme UGANC CI.
À exécuter UNE FOIS sur le serveur MySQL.

Utilisation :
    python3 setup_mysql.py

Prérequis :
    - MySQL installé et en cours d'exécution
    - Les variables dans .env configurées

Ce script :
    1. Crée la base de données MySQL si elle n'existe pas
    2. Crée l'utilisateur MySQL avec les droits nécessaires
    3. Applique toutes les migrations Django
    4. Insère les données de démarrage (seed)
"""

import os, sys

# ── Lecture du .env ──
env = {}
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                env[k.strip()] = v.strip()
else:
    print("❌ Fichier .env introuvable. Créez-le d'abord.")
    sys.exit(1)

DB_NAME = env.get('DB_NAME', 'chatbot_db')
DB_USER = env.get('DB_USER', 'mamadou_barry')
DB_PASS = env.get('DB_PASSWORD', '')
DB_HOST = env.get('DB_HOST', '127.0.0.1')
DB_PORT = int(env.get('DB_PORT', '3306'))

print(f"📊 Configuration MySQL : {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

# ── Connexion MySQL avec root pour créer DB/user ──
ROOT_PASS = input("Mot de passe MySQL root (laisser vide si aucun) : ").strip()

try:
    import pymysql
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user='root',
        password=ROOT_PASS,
        charset='utf8mb4'
    )
    cursor = conn.cursor()

    # Créer la base de données
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    print(f"✅ Base de données '{DB_NAME}' créée/vérifiée")

    # Créer l'utilisateur
    try:
        cursor.execute(f"CREATE USER IF NOT EXISTS '{DB_USER}'@'%' IDENTIFIED BY '{DB_PASS}';")
        cursor.execute(f"GRANT ALL PRIVILEGES ON `{DB_NAME}`.* TO '{DB_USER}'@'%';")
        cursor.execute("FLUSH PRIVILEGES;")
        print(f"✅ Utilisateur '{DB_USER}' créé avec tous les droits sur '{DB_NAME}'")
    except Exception as e:
        print(f"⚠️  Utilisateur déjà existant ou erreur : {e}")

    conn.close()
    print("✅ Connexion MySQL root fermée")

except ImportError:
    print("❌ pymysql non installé. Lancez : pip install pymysql")
    sys.exit(1)
except Exception as e:
    print(f"❌ Erreur connexion MySQL root : {e}")
    print("   Essayez de créer manuellement la base et l'utilisateur avec phpMyAdmin ou MySQL Workbench.")
    sys.exit(1)

# ── Migrations Django ──
print("\n⚙️  Application des migrations Django...")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import django
    django.setup()
    from django.core.management import call_command
    call_command('migrate', '--run-syncdb', verbosity=1)
    print("✅ Migrations appliquées")
except Exception as e:
    print(f"❌ Erreur migration : {e}")
    sys.exit(1)

# ── Seed des données de démarrage ──
print("\n🌱 Insertion des données de démarrage...")
try:
    exec(open('seed_db.py').read())
    print("✅ Données de démarrage insérées")
except Exception as e:
    print(f"⚠️  Erreur seed : {e} (ignoré)")

print("\n" + "="*55)
print("🎉 Installation MySQL terminée !")
print(f"   Base   : {DB_NAME}")
print(f"   User   : {DB_USER}")
print(f"   Host   : {DB_HOST}:{DB_PORT}")
print()
print("🔑 Comptes de démo créés :")
print("   admin       / admin123   (Super Admin)")
print("   diallo.mamadou / chef123   (Chef NTIC)")
print("   camara.ibrahima / dga123  (DGA)")
print("   barry.cellou   / dg123   (DG)")
print("   6642001        / etudiant123  (Étudiant actif)")
