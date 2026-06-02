from django.contrib.auth.models import User
from etudiants.models import Etudiant, Departement, Niveau, ProfilAdmin
from datetime import date

# Ensure departments exist
dept_ntic, _ = Departement.objects.get_or_create(nom='NTIC', defaults={'slug': 'ntic'})
dept_dl, _ = Departement.objects.get_or_create(nom='Développement Logiciel', defaults={'slug': 'dl'})

# Ensure levels exist
niv_l3_ntic, _ = Niveau.objects.get_or_create(nom='Licence 3', departement=dept_ntic, defaults={'slug': 'ntic-l3'})
niv_l3_dl, _ = Niveau.objects.get_or_create(nom='Licence 3', departement=dept_dl, defaults={'slug': 'dl-l3'})

# 1. DG
user_dg, _ = User.objects.get_or_create(username='dg')
user_dg.set_password('dg2026')
user_dg.is_staff = True
user_dg.save()
ProfilAdmin.objects.update_or_create(user=user_dg, defaults={'role': 'dg', 'nom': 'Directeur', 'prenom': 'Général'})

# 2. DGA
user_dga, _ = User.objects.get_or_create(username='dga')
user_dga.set_password('dga2026')
user_dga.is_staff = True
user_dga.save()
ProfilAdmin.objects.update_or_create(user=user_dga, defaults={'role': 'dga', 'nom': 'Directeur', 'prenom': 'Adjoint'})

# 3. Chef NTIC
user_chef_nt, _ = User.objects.get_or_create(username='chefnt')
user_chef_nt.set_password('chef2026')
user_chef_nt.is_staff = True
user_chef_nt.save()
ProfilAdmin.objects.update_or_create(user=user_chef_nt, defaults={'role': 'chef_ntic', 'nom': 'Chef', 'prenom': 'NTIC'})

# 4. Chef DL
user_chef_dl, _ = User.objects.get_or_create(username='chefdl')
user_chef_dl.set_password('chef2026')
user_chef_dl.is_staff = True
user_chef_dl.save()
ProfilAdmin.objects.update_or_create(user=user_chef_dl, defaults={'role': 'chef_dl', 'nom': 'Chef', 'prenom': 'DL'})

# 5. Etudiant NTIC (Real Matricule)
user_et_nt_real, _ = User.objects.get_or_create(username='664215632396')
user_et_nt_real.set_password('etud2026')
user_et_nt_real.save()
Etudiant.objects.update_or_create(
    user=user_et_nt_real,
    defaults={
        'matricule': '664215632396',
        'nom': 'Camara',
        'prenom': 'Lamine',
        'departement': dept_ntic,
        'niveau': niv_l3_ntic
    }
)

# 6. Etudiant DL (Real Matricule)
user_et_dl_real, _ = User.objects.get_or_create(username='664478967890')
user_et_dl_real.set_password('etud2026')
user_et_dl_real.save()
Etudiant.objects.update_or_create(
    user=user_et_dl_real,
    defaults={
        'matricule': '664478967890',
        'nom': 'Diallo',
        'prenom': 'Fatoumata',
        'departement': dept_dl,
        'niveau': niv_l3_dl
    }
)

print("ALL REAL USERS CREATED SUCCESSFULLY!")
