import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from etudiants.models import Departement, Niveau

def clean_and_populate():
    # 1. Supprimer les départements corrompus (avec '??' ou autres dans le nom ou mauvais slug)
    print("Nettoyage de la base de données...")
    corrupted_depts = Departement.objects.filter(nom__contains='??')
    count = corrupted_depts.count()
    if count > 0:
        corrupted_depts.delete()
        print(f"{count} départements corrompus supprimés.")
    
    # 2. S'assurer d'avoir les 2 départements corrects
    depts = [
        {"nom": "Nouvelle Technologie de l'Information et de la Communication", "slug": "ntic"},
        {"nom": "Développement Logiciel", "slug": "dl"},
    ]
    
    departement_objs = []
    for d in depts:
        dept, created = Departement.objects.get_or_create(
            slug=d["slug"],
            defaults={"nom": d["nom"]}
        )
        if not created and dept.nom != d["nom"]:
            dept.nom = d["nom"]
            dept.save()
        departement_objs.append(dept)
    
    # 3. Supprimer les autres départements qui ne sont ni ntic ni dl (pour être sûr)
    # Caution: ne le fait que si les ID sont différents
    valid_ids = [d.id for d in departement_objs]
    others = Departement.objects.exclude(id__in=valid_ids)
    if others.exists():
        print(f"Suppression de {others.count()} anciens ou autres départements...")
        others.delete()

    # 4. Assurer les niveaux exacts pour les deux
    niveaux_def = [
        {"nom": "Licence 1 (L1)", "slug_suffix": "l1"},
        {"nom": "Licence 2 (L2)", "slug_suffix": "l2"},
        {"nom": "Licence 3 (L3)", "slug_suffix": "l3"},
        {"nom": "Master", "slug_suffix": "master"},
        {"nom": "Doctorat", "slug_suffix": "doctorat"}
    ]
    
    for dept in departement_objs:
        valid_niveau_ids = []
        for n in niveaux_def:
            slug = f"{dept.slug}-{n['slug_suffix']}"
            niveau, created = Niveau.objects.get_or_create(
                slug=slug,
                defaults={"nom": n["nom"], "departement": dept}
            )
            # Mise à jour si nécessaire
            if not created and (niveau.nom != n["nom"] or niveau.departement != dept):
                niveau.nom = n["nom"]
                niveau.departement = dept
                niveau.save()
            valid_niveau_ids.append(niveau.id)
            
        # Supprimer les niveaux en trop pour ce desc
        extra_niveaux = Niveau.objects.filter(departement=dept).exclude(id__in=valid_niveau_ids)
        if extra_niveaux.exists():
            print(f"Suppression de {extra_niveaux.count()} niveaux en trop pour {dept.nom}.")
            extra_niveaux.delete()

    print("Base de données Departement/Niveau propre et à jour.")

if __name__ == '__main__':
    clean_and_populate()
