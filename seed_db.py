"""
Initialise la base de données avec les données de test.
Lance avec : USE_SQLITE=1 python3 seed_db.py
"""
import os, sys, django

os.environ.setdefault('USE_SQLITE', '1')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth.models import User
from etudiants.models import Etudiant, Departement, Niveau, Session, ProfilAdmin
from notes.models import Note
from demandes.models import Demande


def run():
    print("🌱 Seeding database...")

    # ── Départements ──
    ntic, _ = Departement.objects.get_or_create(nom='Nouvelles Technologies de l\'Information et de la Communication', slug='ntic')
    dl,   _ = Departement.objects.get_or_create(nom='Développement Logiciel', slug='dl')

    # ── Niveaux ──
    def mk_niveau(dept, nom, slug):
        return Niveau.objects.get_or_create(departement=dept, nom=nom, slug=slug)[0]

    niv_l1_ntic = mk_niveau(ntic, 'Licence 1', 'ntic-l1')
    niv_l2_ntic = mk_niveau(ntic, 'Licence 2', 'ntic-l2')
    niv_l3_ntic = mk_niveau(ntic, 'Licence 3', 'ntic-l3')
    niv_l1_dl   = mk_niveau(dl,   'Licence 1', 'dl-l1')
    niv_l2_dl   = mk_niveau(dl,   'Licence 2', 'dl-l2')
    niv_l3_dl   = mk_niveau(dl,   'Licence 3', 'dl-l3')

    # ── Sessions ──
    for niv, slug_prefix in [(niv_l1_ntic,'ntic-l1'),(niv_l2_ntic,'ntic-l2'),(niv_l3_ntic,'ntic-l3'),
                              (niv_l1_dl,'dl-l1'),(niv_l2_dl,'dl-l2'),(niv_l3_dl,'dl-l3')]:
        Session.objects.get_or_create(niveau=niv, nom='Session 1', slug=f'{slug_prefix}-s1')
        Session.objects.get_or_create(niveau=niv, nom='Session 2', slug=f'{slug_prefix}-s2')

    print(f"  ✅ {Departement.objects.count()} départements | {Niveau.objects.count()} niveaux | {Session.objects.count()} sessions")

    # ── Super Admin ──
    if not User.objects.filter(username='admin').exists():
        u = User.objects.create_superuser('admin','admin@uganc.gn','admin123')
        ProfilAdmin.objects.create(user=u,role='admin',nom='Administrateur',prenom='Super',email='admin@uganc.gn')
        print("  ✅ superadmin  : admin / admin123")

    # ── Chef NTIC ──
    if not User.objects.filter(username='diallo.mamadou').exists():
        u = User.objects.create_user('diallo.mamadou','chef.ntic@uganc.gn','chef123',
                                     first_name='Mamadou',last_name='Diallo',is_staff=True)
        ProfilAdmin.objects.create(user=u,role='chef_ntic',nom='Diallo',prenom='Mamadou',email='chef.ntic@uganc.gn')
        print("  ✅ chef NTIC   : diallo.mamadou / chef123")

    # ── Chef DL ──
    if not User.objects.filter(username='bah.fatoumata').exists():
        u = User.objects.create_user('bah.fatoumata','chef.dl@uganc.gn','chef123',
                                     first_name='Fatoumata',last_name='Bah',is_staff=True)
        ProfilAdmin.objects.create(user=u,role='chef_dl',nom='Bah',prenom='Fatoumata',email='chef.dl@uganc.gn')
        print("  ✅ chef DL     : bah.fatoumata / chef123")

    # ── DGA ──
    if not User.objects.filter(username='camara.ibrahima').exists():
        u = User.objects.create_user('camara.ibrahima','dga@uganc.gn','dga123',
                                     first_name='Ibrahima',last_name='Camara',is_staff=True)
        ProfilAdmin.objects.create(user=u,role='dga',nom='Camara',prenom='Ibrahima',email='dga@uganc.gn')
        print("  ✅ DGA         : camara.ibrahima / dga123")

    # ── DG ──
    if not User.objects.filter(username='barry.cellou').exists():
        u = User.objects.create_user('barry.cellou','dg@uganc.gn','dg123',
                                     first_name='Cellou',last_name='Barry',is_staff=True)
        ProfilAdmin.objects.create(user=u,role='dg',nom='Barry',prenom='Cellou',email='dg@uganc.gn')
        print("  ✅ DG          : barry.cellou / dg123")

    # ── Étudiant NTIC validé (démo) ──
    if not User.objects.filter(username='6642001').exists():
        import random; random.seed(42)
        u = User.objects.create_user('6642001','etu.ntic@uganc.gn','etudiant123',
                                     first_name='Moussa',last_name='Kouyaté')
        etu = Etudiant.objects.create(user=u,matricule='6642001',nom='Kouyaté',prenom='Moussa',
                                      departement=ntic,niveau=niv_l3_ntic,
                                      est_valide=True,valide_par_chef=True,mot_de_passe_change=True)
        sess1 = Session.objects.get(slug='ntic-l3-s1')
        sess2 = Session.objects.get(slug='ntic-l3-s2')
        matieres = ['Algorithmique','Bases de Données','Réseaux','Développement Web','Systèmes d\'exploitation','Mathématiques']
        for mat in matieres:
            Note.objects.get_or_create(etudiant=etu,matiere=mat,session=sess1,annee='2024-2025',defaults={'note':round(random.uniform(6,19),2)})
            Note.objects.get_or_create(etudiant=etu,matiere=mat,session=sess2,annee='2024-2025',defaults={'note':round(random.uniform(6,19),2)})
        Demande.objects.get_or_create(etudiant=etu,session='Session 1',defaults={'statut':'validee'})
        print("  ✅ étudiant    : 6642001 / etudiant123 (compte actif, notes + demande validée)")

    # ── Étudiant en attente chef (démo workflow) ──
    if not User.objects.filter(username='6642100').exists():
        u = User.objects.create_user('6642100','etu.attente@uganc.gn','etudiant123',
                                     first_name='Aissatou',last_name='Sow')
        Etudiant.objects.create(user=u,matricule='6642100',nom='Sow',prenom='Aissatou',
                                departement=ntic,niveau=niv_l2_ntic,
                                est_valide=False,valide_par_chef=False,mot_de_passe_change=True)
        print("  ✅ étudiant att chef : 6642100 / etudiant123 (en attente validation chef)")

    # ── Étudiant en attente DGA (démo workflow) ──
    if not User.objects.filter(username='6642101').exists():
        u = User.objects.create_user('6642101','etu.attente2@uganc.gn','etudiant123',
                                     first_name='Kadiatou',last_name='Barry')
        Etudiant.objects.create(user=u,matricule='6642101',nom='Barry',prenom='Kadiatou',
                                departement=ntic,niveau=niv_l1_ntic,
                                est_valide=False,valide_par_chef=True,mot_de_passe_change=True)
        print("  ✅ étudiant att DGA  : 6642101 / etudiant123 (pré-validé chef, attente DGA)")

    print(f"\n✅ Seed terminé !")
    print(f"   Étudiants: {Etudiant.objects.count()} | Notes: {Note.objects.count()} | Demandes: {Demande.objects.count()}")
    print("\n📋 Comptes de démonstration :")
    print("   🔑 Admin système : admin / admin123")
    print("   🏫 Chef NTIC     : diallo.mamadou / chef123")
    print("   🏫 Chef DL       : bah.fatoumata / chef123")
    print("   👔 DGA           : camara.ibrahima / dga123")
    print("   👔 DG            : barry.cellou / dg123")
    print("   🎓 Étudiant actif: 6642001 / etudiant123")
    print("   ⏳ Att. chef     : 6642100 / etudiant123")
    print("   ⏳ Att. DGA      : 6642101 / etudiant123")


if __name__ == '__main__':
    run()
