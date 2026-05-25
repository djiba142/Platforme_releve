from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Note
from etudiants.models import Etudiant
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

            colonnes = ['matricule', 'matiere', 'note', 'session', 'annee']
            for col in colonnes:
                if col not in df.columns:
                    messages.error(request, f'Colonne manquante : {col}')
                    return redirect('import_csv')

            compteur = 0
            erreurs = 0
            for _, row in df.iterrows():
                try:
                    etudiant = Etudiant.objects.get(matricule=str(row['matricule']).strip())
                    Note.objects.create(
                        etudiant=etudiant,
                        matiere=str(row['matiere']).strip(),
                        note=float(row['note']),
                        session=str(row['session']).strip(),
                        annee=str(row['annee']).strip()
                    )
                    compteur += 1
                except Etudiant.DoesNotExist:
                    erreurs += 1
                except (ValueError, KeyError):
                    erreurs += 1

            messages.success(request,
                             f'{compteur} notes importées avec succès. {erreurs} erreurs ignorées.')

        except Exception as e:
            messages.error(request, f'Erreur lors de l\'import : {str(e)}')

        return redirect('import_csv')

    return render(request, 'notes/import_csv.html')
