from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from notes.models import Note
import os
from django.conf import settings


def generer_releve(demande):
    """Générer un relevé de notes PDF professionnel"""
    etudiant = demande.etudiant
    notes = Note.objects.filter(etudiant=etudiant, session=demande.session)

    # Chemin du fichier PDF
    nom_fichier = f"releve_{etudiant.matricule}_{demande.session.replace(' ', '_')}.pdf"
    dossier = os.path.join(settings.MEDIA_ROOT, 'releves')
    os.makedirs(dossier, exist_ok=True)
    chemin = os.path.join(dossier, nom_fichier)

    doc = SimpleDocTemplate(chemin, pagesize=A4,
                            topMargin=1.5 * cm, bottomMargin=1.5 * cm)
    elements = []

    # Couleurs
    NAVY = colors.HexColor('#1A2744')
    TEAL = colors.HexColor('#00C3A3')
    LIGHT = colors.HexColor('#EFF4FB')

    # Styles
    titre_style = ParagraphStyle(
        'titre', fontSize=16, textColor=NAVY,
        alignment=TA_CENTER, fontName='Helvetica-Bold',
        spaceAfter=6
    )
    sous_titre_style = ParagraphStyle(
        'sous_titre', fontSize=11, textColor=TEAL,
        alignment=TA_CENTER, fontName='Helvetica-Bold',
        spaceAfter=20
    )
    label_style = ParagraphStyle(
        'label', fontSize=10, textColor=NAVY,
        fontName='Helvetica-Bold'
    )
    doc_titre = ParagraphStyle(
        'doc_titre', fontSize=14, textColor=NAVY,
        alignment=TA_CENTER, fontName='Helvetica-Bold',
        spaceAfter=15
    )

    # ── En-tête université ──
    elements.append(Paragraph("UNIVERSITÉ DE CONAKRY", titre_style))
    elements.append(Paragraph("Service de la Scolarité", sous_titre_style))

    # Ligne de séparation
    elements.append(Table(
        [['']],
        colWidths=[17 * cm],
        style=TableStyle([('LINEBELOW', (0, 0), (-1, -1), 2, NAVY)])
    ))
    elements.append(Spacer(1, 0.5 * cm))

    # Titre document
    elements.append(Paragraph("RELEVÉ DE NOTES", doc_titre))
    elements.append(Spacer(1, 0.3 * cm))

    # ── Infos étudiant ──
    info_data = [
        ['Nom & Prénom :', f"{etudiant.prenom} {etudiant.nom}"],
        ['Matricule :', etudiant.matricule],
        ['Filière :', etudiant.filiere],
        ['Niveau :', etudiant.niveau],
        ['Session :', demande.session],
    ]
    info_table = Table(info_data, colWidths=[5 * cm, 12 * cm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), LIGHT),
        ('TEXTCOLOR', (0, 0), (0, -1), NAVY),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [LIGHT, colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D4E0F0')),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.6 * cm))

    # ── Tableau des notes ──
    elements.append(Paragraph("Détail des notes", label_style))
    elements.append(Spacer(1, 0.3 * cm))

    entete = [['N°', 'Matière', 'Note /20', 'Résultat']]
    lignes = []
    for i, note in enumerate(notes, 1):
        resultat = 'Validé' if note.note >= 10 else 'Ajourné'
        lignes.append([str(i), note.matiere, f"{note.note}/20", resultat])

    if not lignes:
        lignes = [['—', 'Aucune note disponible', '—', '—']]

    table_notes = Table(entete + lignes, colWidths=[1.5 * cm, 9 * cm, 3.5 * cm, 3 * cm])
    table_notes.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT]),
        ('ALIGN', (2, 1), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D4E0F0')),
        ('PADDING', (0, 0), (-1, -1), 7),
    ]))
    elements.append(table_notes)
    elements.append(Spacer(1, 0.5 * cm))

    # ── Moyenne & Décision ──
    if notes.exists():
        moyenne = sum(n.note for n in notes) / notes.count()
        decision = "ADMIS(E)" if moyenne >= 10 else "AJOURNÉ(E)"
        decision_color = colors.HexColor('#198754') if moyenne >= 10 else colors.HexColor('#DC3545')
    else:
        moyenne = 0
        decision = "—"
        decision_color = colors.grey

    moy_data = [
        ['Moyenne générale :', f"{round(moyenne, 2)} / 20",
         'Décision :', decision]
    ]
    moy_table = Table(moy_data, colWidths=[4.5 * cm, 4 * cm, 3.5 * cm, 5 * cm])
    moy_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT),
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, 0), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
        ('TEXTCOLOR', (1, 0), (1, 0), NAVY),
        ('FONTNAME', (3, 0), (3, 0), 'Helvetica-Bold'),
        ('TEXTCOLOR', (3, 0), (3, 0), decision_color),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D4E0F0')),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    elements.append(moy_table)
    elements.append(Spacer(1, 1.5 * cm))

    # ── Signature ──
    sig_data = [
        ['Date de délivrance :', 'Signature & Cachet :'],
        [f"{demande.date_demande.strftime('%d/%m/%Y')}", ''],
    ]
    sig_table = Table(sig_data, colWidths=[8.5 * cm, 8.5 * cm])
    sig_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, 0), NAVY),
        ('LINEBELOW', (1, 1), (1, 1), 1, NAVY),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(sig_table)

    doc.build(elements)
    return f"releves/{nom_fichier}"
