import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from etudiants.models import Departement, Niveau

def populate():
    # Définition des départements avec leur slug
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
        # S'assurer que le nom est à jour si déjà existant
        if not created and dept.nom != d["nom"]:
            dept.nom = d["nom"]
            dept.save()
        departement_objs.append(dept)
        print(f"Département {dept.nom} (slug: {dept.slug}) ajouté avec succès.")
    
    # Définition des niveaux (pour chaque département)
    niveaux_def = [
        {"nom": "Licence 1 (L1)", "slug_suffix": "l1"},
        {"nom": "Licence 2 (L2)", "slug_suffix": "l2"},
        {"nom": "Licence 3 (L3)", "slug_suffix": "l3"},
        {"nom": "Master", "slug_suffix": "master"},
        {"nom": "Doctorat", "slug_suffix": "doctorat"}
    ]
    
    for dept in departement_objs:
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
            print(f"Niveau {niveau.nom} pour {dept.slug} ajouté avec succès.")

if __name__ == '__main__':
    populate()
    print("Population terminée.")
