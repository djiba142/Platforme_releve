from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Note
from etudiants.models import Etudiant, Departement, Niveau, Session
from django.utils.text import slugify
import pandas as pd


@login_required
def liste_notes(request):
    """Afficher les notes de l'étudiant connecté"""
    etudiant = Etudiant.objects.get(user=request.user)
    notes = Note.objects.filter(etudiant=etudiant)

    moyenne = 0
    if notes.exists():
        moyenne = round(sum(n.note for n in notes) / notes.count(), 2)

    return render(request, 'notes/liste_notes.html', {
        'notes': notes,
        'moyenne': moyenne,
        'etudiant': etudiant
    })


@login_required
def import_csv(request):
    """Import de notes via CSV ou Excel (admin uniquement)"""
    if not request.user.is_staff:
        messages.error(request, 'Accès réservé à l\'administration.')
        return redirect('profil')

    if request.method == 'POST':
        fichier = request.FILES.get('fichier')
        session_val = request.POST.get('session', 'Session 1').strip()
        annee_val = request.POST.get('annee', '2023-2024').strip()

        if not fichier:
            messages.error(request, 'Aucun fichier sélectionné.')
            return redirect('import_csv')

        try:
            if fichier.name.endswith('.csv'):
                df = pd.read_csv(fichier)
            elif fichier.name.endswith('.xlsx'):
                df = pd.read_excel(fichier)
            else:
                messages.error(request, 'Format non supporté. Utilisez CSV ou Excel.')
                return redirect('import_csv')

            # Colonnes de base attendues : 
            # matricule, nom, prenom, departement, niveau
            # Toutes les autres colonnes seront traitées comme des matières !
            
            from django.contrib.auth.models import User

            compteur = 0
            erreurs = 0
            
            # Normaliser les noms de colonnes pour trouver facilement les colonnes de base
            colonnes_base = ['matricule', 'nom', 'prenom', 'departement', 'niveau']
            
            for _, row in df.iterrows():
                try:
                    # Trouver la colonne matricule (insensible à la casse)
                    col_mat = next((c for c in df.columns if str(c).lower().strip() == 'matricule'), None)
                    if not col_mat or pd.isna(row[col_mat]):
                        continue
                        
                    matricule = str(row[col_mat]).strip()
                    
                    # Extraire les champs de base (insensible à la casse)
                    nom_val = ''
                    col_nom = next((c for c in df.columns if str(c).lower().strip() == 'nom'), None)
                    if col_nom and pd.notna(row[col_nom]): nom_val = str(row[col_nom]).strip()
                        
                    prenom_val = ''
                    col_prenom = next((c for c in df.columns if str(c).lower().strip() == 'prenom'), None)
                    if col_prenom and pd.notna(row[col_prenom]): prenom_val = str(row[col_prenom]).strip()

                    # 1. Créer/Récupérer le User
                    user, created_user = User.objects.get_or_create(
                        username=matricule,
                        defaults={
                            'first_name': prenom_val,
                            'last_name': nom_val,
                        }
                    )
                    
                    if created_user:
                        user.set_password("Ntic2026")
                        user.save()

                    # 2. Créer/Récupérer l'Etudiant
                    departement_raw = ''
                    col_dep = next((c for c in df.columns if str(c).lower().strip() == 'departement'), None)
                    if col_dep and pd.notna(row[col_dep]): departement_raw = str(row[col_dep]).strip().upper()
                        
                    if 'DEVELOPPEMENT' in departement_raw or 'LOGICIEL' in departement_raw or 'DL' in departement_raw:
                        departement_finale = 'Développement Logiciel'
                    else:
                        departement_finale = 'Nouvelle Technologie de l\'Information et de la Communication'

                    departement_slug = slugify(departement_finale[:40]) if departement_finale else 'inconnu'
                    departement_obj, _ = Departement.objects.get_or_create(
                        slug=departement_slug,
                        defaults={'nom': departement_finale or 'Inconnu'}
                    )

                    niveau_val = ''
                    col_niv = next((c for c in df.columns if str(c).lower().strip() == 'niveau'), None)
                    if col_niv and pd.notna(row[col_niv]): niveau_val = str(row[col_niv]).strip()

                    niveau_slug = slugify(f"{departement_slug}-{niveau_val}") if niveau_val else f"{departement_slug}-inconnu"
                    niveau_obj, _ = Niveau.objects.get_or_create(
                        slug=niveau_slug,
                        defaults={'departement': departement_obj, 'nom': niveau_val or 'Inconnu'}
                    )

                    etudiant, created_etu = Etudiant.objects.get_or_create(
                        matricule=matricule,
                        defaults={
                            'user': user,
                            'nom': nom_val,
                            'prenom': prenom_val,
                            'departement': departement_obj,
                            'niveau': niveau_obj,
                        }
                    )
                    
                    # Si l'étudiant existe déjà mais n'est pas lié à ce user (sécurité)
                    if not created_etu and etudiant.user != user:
                        etudiant.user = user
                        etudiant.save()

                    # 3. Créer les Notes pour chaque colonne Matière
                    session_slug = slugify(f"{niveau_slug}-{session_val}")
                    session_obj, _ = Session.objects.get_or_create(
                        slug=session_slug,
                        defaults={'niveau': niveau_obj, 'nom': session_val}
                    )

                    notes_ajoutees = False
                    for col in df.columns:
                        if str(col).lower().strip() not in colonnes_base:
                            val = row[col]
                            if pd.notna(val) and str(val).strip() != '':
                                try:
                                    # Gestion des virgules et espaces
                                    note_val = float(str(val).replace(',', '.').replace(' ', ''))
                                    Note.objects.create(
                                        etudiant=etudiant,
                                        matiere=str(col).strip(),
                                        note=note_val,
                                        session=session_obj,
                                        annee=annee_val
                                    )
                                    compteur += 1
                                    notes_ajoutees = True
                                except ValueError:
                                    # La valeur n'est pas un nombre, on ignore cette cellule
                                    pass

                    if created_etu and not notes_ajoutees:
                        compteur += 1

                except Exception as e:
                    erreurs += 1
                    print(f"Erreur ligne {row.name}: {str(e)}")

            messages.success(request,
                             f'{compteur} entrées traitées avec succès. {erreurs} erreurs.')

        except Exception as e:
            messages.error(request, f'Erreur lors de l\'import : {str(e)}')

        return redirect('import_csv')

    return render(request, 'notes/import_csv.html')
