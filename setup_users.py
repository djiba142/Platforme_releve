import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from etudiants.models import Etudiant, ProfilAdmin, Departement

# ============================================================
# 1. STUDENTS
# ============================================================
students = [
    {"matricule": "664215632396", "nom": "Etudiant", "prenom": "NTIC", "password": "etud2026", "dept_slug": "ntic"},
    {"matricule": "664478967890", "nom": "Etudiant", "prenom": "DL", "password": "etud2026", "dept_slug": "dl"},
]

for s in students:
    User.objects.filter(username=s["matricule"]).delete()
    user = User.objects.create_user(username=s["matricule"], password=s["password"])
    dept = Departement.objects.filter(slug=s["dept_slug"]).first()
    Etudiant.objects.create(
        user=user,
        matricule=s["matricule"],
        nom=s["nom"],
        prenom=s["prenom"],
        departement=dept,
        mot_de_passe_change=True,
        est_valide=True
    )
    print("Etudiant " + s["matricule"] + " cree OK")

# ============================================================
# 2. ADMINS
# ============================================================
admins = [
    {"username": "chefnt", "password": "chef2026", "role": "chef_ntic", "nom": "Chef", "prenom": "NTIC"},
    {"username": "chefdl", "password": "chef2026", "role": "chef_dl", "nom": "Chef", "prenom": "DL"},
    {"username": "dga", "password": "dga2026", "role": "dga", "nom": "Directeur", "prenom": "Adjoint"},
    {"username": "dg", "password": "dg2026", "role": "dg", "nom": "Directeur", "prenom": "General"},
]

for a in admins:
    User.objects.filter(username=a["username"]).delete()
    user = User.objects.create_user(username=a["username"], password=a["password"])
    user.is_staff = True
    user.save()
    ProfilAdmin.objects.create(
        user=user,
        role=a["role"],
        nom=a["nom"],
        prenom=a["prenom"],
        email=a["username"] + "@uganc.edu.gn"
    )
    print("Admin " + a["username"] + " (" + a["role"] + ") cree OK")

print("\n=== VERIFICATION ===")
for u in User.objects.all():
    hp = hasattr(u, "profiladmin")
    he = hasattr(u, "etudiant")
    info = u.username + " staff=" + str(u.is_staff)
    if hp:
        info += " role=" + u.profiladmin.role
    if he:
        info += " mat=" + u.etudiant.matricule + " valid=" + str(u.etudiant.est_valide)
    print(info)
