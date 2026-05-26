from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, HRFlowable, Image
)
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import KeepTogether
from notes.models import Note
import os
from django.conf import settings
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode import qr


# ── COULEURS OFFICIELLES UGANC ──────────────────────────
BORDEAUX      = colors.HexColor('#7B1C2E')
BORDEAUX_DARK = colors.HexColor('#5A1220')
ORANGE        = colors.HexColor('#D4520A')
BLEU_CI       = colors.HexColor('#1565C0')
BLEU_LIGHT    = colors.HexColor('#E3F0FF')
LIGHT_BG      = colors.HexColor('#FDF8F6')
LIGHT_BORDER  = colors.HexColor('#EDD5CC')
GRAY          = colors.HexColor('#64748B')
DARK          = colors.HexColor('#1A0A0E')
WHITE         = colors.white
GREEN         = colors.HexColor('#1B7A3E')
RED           = colors.HexColor('#C0392B')


def detecter_departement(matricule):
    """Détecte automatiquement la filière depuis le matricule."""
    matricule = matricule.upper()
    if matricule.startswith('6642'):
        return 'NTIC', 'Nouvelles Technologies de l\'Information et de la Communication'
    # TODO: Ajouter le code pour DL plus tard si connu.
    else:
        return 'CI', 'Centre Informatique'


def detecter_annee(matricule):
    """L'année n'étant plus dans le matricule, retourne l'année en cours."""
    return "2026"


def generer_releve(demande):
    etudiant  = demande.etudiant
    notes     = Note.objects.filter(
        etudiant=etudiant,
        session=demande.session
    )

    # Détection automatique filière depuis matricule
    code_departement, nom_departement = detecter_departement(etudiant.matricule)
    annee_entree = detecter_annee(etudiant.matricule)

    # Calcul moyenne
    if notes.exists():
        moyenne = sum([n.note for n in notes]) / notes.count()
        decision = "ADMIS(E)" if moyenne >= 5.0 else "AJOURNÉ(E)"
        decision_color = GREEN if moyenne >= 5.0 else RED
        mention = get_mention(moyenne)
    else:
        moyenne = 0
        decision = "—"
        decision_color = GRAY
        mention = "—"

    # ── Chemin fichier ──
    nom_fichier = (
        f"releve_{etudiant.matricule}_"
        f"{demande.session.replace(' ', '_')}.pdf"
    )
    dossier = os.path.join(settings.MEDIA_ROOT, 'releves')
    os.makedirs(dossier, exist_ok=True)
    chemin   = os.path.join(dossier, nom_fichier)

    # ── Document ──
    doc = SimpleDocTemplate(
        chemin,
        pagesize=A4,
        topMargin=1.2*cm,
        bottomMargin=1.5*cm,
        leftMargin=1.8*cm,
        rightMargin=1.8*cm
    )

    elements = []

    # ════════════════════════════════════
    # EN-TÊTE OFFICIEL
    # ════════════════════════════════════
    
    # ── EN-TÊTE avec logos UGANC + CI ──
    NAVY  = colors.HexColor('#1A2744')
    TEAL  = colors.HexColor('#00C3A3')
    LIGHT = colors.HexColor('#EFF4FB')

    # Bande teal en haut
    elements.append(Table(
        [['']],
        colWidths=[17.4*cm],
        rowHeights=[0.2*cm],
        style=TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), TEAL),
        ])
    ))
    elements.append(Spacer(1, 0.3*cm))

    # Logos + Nom université
    logo_uganc = os.path.join(
        settings.BASE_DIR, 'static', 'image', 'logos_uganc.png'
    )
    logo_ci = os.path.join(
        settings.BASE_DIR, 'static', 'image', 'logosCI.png'
    )

    entete_data = [[
        Image(logo_uganc, width=2.2*cm, height=2.2*cm)
        if os.path.exists(logo_uganc) else '',

        Table([
            [Paragraph(
                "UNIVERSITÉ GAMAL ABDEL NASSER DE CONAKRY",
                ParagraphStyle('uni', fontSize=12,
                               textColor=NAVY,
                               fontName='Helvetica-Bold',
                               alignment=TA_CENTER)
            )],
            [Paragraph(
                "CENTRE INFORMATIQUE",
                ParagraphStyle('ci', fontSize=10,
                               textColor=colors.HexColor('#1565C0'),
                               fontName='Helvetica-Bold',
                               alignment=TA_CENTER,
                               spaceBefore=3)
            )],
            [Paragraph(
                "Service de la Scolarité — Conakry, Guinée",
                ParagraphStyle('scol', fontSize=8.5,
                               textColor=colors.HexColor('#64748B'),
                               alignment=TA_CENTER,
                               spaceBefore=2)
            )],
        ], colWidths=[12*cm]),

        Image(logo_ci, width=2*cm, height=2*cm)
        if os.path.exists(logo_ci) else '',
    ]]

    entete_table = Table(
        entete_data,
        colWidths=[2.5*cm, 12.5*cm, 2.5*cm]
    )
    entete_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(entete_table)
    elements.append(Spacer(1, 0.25*cm))

    # Ligne séparation navy + teal
    elements.append(Table(
        [['', '']],
        colWidths=[14*cm, 3.4*cm],
        rowHeights=[0.07*cm],
        style=TableStyle([
            ('BACKGROUND', (0,0), (0,0), NAVY),
            ('BACKGROUND', (1,0), (1,0), TEAL),
        ])
    ))
    elements.append(Spacer(1, 0.4*cm))

    # ════════════════════════════════════
    # TITRE DU DOCUMENT
    # ════════════════════════════════════

    titre_style = ParagraphStyle(
        'titre_doc',
        fontSize=15,
        textColor=BORDEAUX_DARK,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        spaceAfter=4
    )
    sous_titre_style = ParagraphStyle(
        'sous_titre_doc',
        fontSize=10,
        textColor=GRAY,
        fontName='Helvetica',
        alignment=TA_CENTER,
        spaceAfter=10
    )

    elements.append(Paragraph("RELEVÉ DE NOTES OFFICIEL", titre_style))
    elements.append(Paragraph(
        f"Année Académique {annee_entree} — {int(annee_entree)+1}  |  "
        f"Département : {code_departement}  |  {demande.session}",
        sous_titre_style
    ))

    # Bordure décorative titre
    elements.append(Table(
        [['']],
        colWidths=[17.4*cm],
        rowHeights=[0.06*cm],
        style=TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), ORANGE),
        ])
    ))
    elements.append(Spacer(1, 0.5*cm))

    # ════════════════════════════════════
    # INFORMATIONS ÉTUDIANT
    # ════════════════════════════════════

    label_style = ParagraphStyle(
        'lbl', fontSize=9, textColor=BORDEAUX_DARK,
        fontName='Helvetica-Bold'
    )
    value_style = ParagraphStyle(
        'val', fontSize=9.5, textColor=DARK,
        fontName='Helvetica'
    )
    value_bold_style = ParagraphStyle(
        'val_bold', fontSize=10, textColor=BORDEAUX_DARK,
        fontName='Helvetica-Bold'
    )

    info_data = [
        # En-tête section
        [
            Paragraph("INFORMATIONS DE L'ÉTUDIANT", ParagraphStyle(
                'info_header', fontSize=9, textColor=WHITE,
                fontName='Helvetica-Bold', alignment=TA_CENTER
            )),
            '', '', ''
        ],
        # Ligne 1
        [
            Paragraph("Nom & Prénom :", label_style),
            Paragraph(
                f"{etudiant.prenom.upper()} {etudiant.nom.upper()}",
                value_bold_style
            ),
            Paragraph("Matricule :", label_style),
            Paragraph(etudiant.matricule, value_bold_style),
        ],
        # Ligne 2
        [
            Paragraph("Département :", label_style),
            Paragraph(nom_departement, value_style),
            Paragraph("Niveau :", label_style),
            Paragraph(
                getattr(etudiant, 'niveau', 'L3'),
                value_style
            ),
        ],
        # Ligne 3
        [
            Paragraph("Code Département :", label_style),
            Paragraph(code_departement, value_style),
            Paragraph("Année d'entrée :", label_style),
            Paragraph(annee_entree, value_style),
        ],
    ]

    info_table = Table(
        info_data,
        colWidths=[3.5*cm, 5.2*cm, 3.5*cm, 5.2*cm]
    )
    info_table.setStyle(TableStyle([
        # En-tête
        ('SPAN', (0,0), (3,0)),
        ('BACKGROUND', (0,0), (3,0), BORDEAUX_DARK),
        ('TEXTCOLOR', (0,0), (3,0), WHITE),
        ('ALIGN', (0,0), (3,0), 'CENTER'),
        ('FONTNAME', (0,0), (3,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (3,0), 9),
        ('TOPPADDING', (0,0), (3,0), 7),
        ('BOTTOMPADDING', (0,0), (3,0), 7),
        # Corps
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [LIGHT_BG, WHITE]),
        ('GRID', (0,0), (-1,-1), 0.5, LIGHT_BORDER),
        ('PADDING', (0,1), (-1,-1), 7),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        # Labels
        ('BACKGROUND', (0,1), (0,-1), colors.HexColor('#F5EBE8')),
        ('BACKGROUND', (2,1), (2,-1), colors.HexColor('#F5EBE8')),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.5*cm))

    # ════════════════════════════════════
    # TABLEAU DES NOTES
    # ════════════════════════════════════

    notes_header_style = ParagraphStyle(
        'notes_hdr', fontSize=9, textColor=WHITE,
        fontName='Helvetica-Bold', alignment=TA_CENTER
    )

    # En-tête tableau
    entete_notes = [[
        Paragraph("N°", notes_header_style),
        Paragraph("MATIÈRE / MODULE", notes_header_style),
        Paragraph("NOTE /10", notes_header_style),
        Paragraph("CRÉDITS", notes_header_style),
        Paragraph("RÉSULTAT", notes_header_style),
        Paragraph("OBSERVATION", notes_header_style),
    ]]

    # Lignes notes
    lignes_notes = []
    if notes.exists():
        for i, note in enumerate(notes, 1):
            resultat = "Validé" if note.note >= 5.0 else "Ajourné"
            result_color = GREEN if note.note >= 5.0 else RED
            obs = get_observation(note.note)

            # Alternance couleurs
            bg = LIGHT_BG if i % 2 == 0 else WHITE

            lignes_notes.append([
                Paragraph(
                    str(i),
                    ParagraphStyle('num', fontSize=9,
                                   alignment=TA_CENTER,
                                   fontName='Helvetica')
                ),
                Paragraph(
                    note.matiere,
                    ParagraphStyle('mat', fontSize=9,
                                   fontName='Helvetica')
                ),
                Paragraph(
                    f"<b>{note.note}</b> / 10",
                    ParagraphStyle('note_val', fontSize=10,
                                   alignment=TA_CENTER,
                                   fontName='Helvetica-Bold',
                                   textColor=BORDEAUX_DARK)
                ),
                Paragraph(
                    "3",
                    ParagraphStyle('cred', fontSize=9,
                                   alignment=TA_CENTER,
                                   fontName='Helvetica')
                ),
                Paragraph(
                    resultat,
                    ParagraphStyle('res', fontSize=9,
                                   alignment=TA_CENTER,
                                   fontName='Helvetica-Bold',
                                   textColor=result_color)
                ),
                Paragraph(
                    obs,
                    ParagraphStyle('obs', fontSize=8.5,
                                   alignment=TA_CENTER,
                                   fontName='Helvetica-Oblique',
                                   textColor=GRAY)
                ),
            ])
    else:
        lignes_notes.append([
            Paragraph("—", ParagraphStyle('empty', alignment=TA_CENTER)),
            Paragraph(
                "Aucune note disponible pour cette session",
                ParagraphStyle('empty2', fontSize=9, textColor=GRAY)
            ),
            Paragraph("—", ParagraphStyle('e', alignment=TA_CENTER)),
            Paragraph("—", ParagraphStyle('e', alignment=TA_CENTER)),
            Paragraph("—", ParagraphStyle('e', alignment=TA_CENTER)),
            Paragraph("—", ParagraphStyle('e', alignment=TA_CENTER)),
        ])

    notes_table = Table(
        entete_notes + lignes_notes,
        colWidths=[1*cm, 6.5*cm, 2.5*cm, 2*cm, 2.5*cm, 2.9*cm]
    )

    # Style dynamique avec couleurs alternées
    style_notes = [
        # En-tête
        ('BACKGROUND', (0,0), (-1,0), BORDEAUX),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,0), 8),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        # Corps
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 9),
        ('GRID', (0,0), (-1,-1), 0.5, LIGHT_BORDER),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LIGHT_BG]),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,1), (-1,-1), 7),
        ('BOTTOMPADDING', (0,1), (-1,-1), 7),
        ('ALIGN', (0,1), (0,-1), 'CENTER'),
        ('ALIGN', (2,1), (-1,-1), 'CENTER'),
        # Bordure gauche colorée
        ('LINEAFTER', (1,1), (1,-1), 0.5, LIGHT_BORDER),
    ]
    notes_table.setStyle(TableStyle(style_notes))
    elements.append(notes_table)
    elements.append(Spacer(1, 0.5*cm))

    # ════════════════════════════════════
    # BILAN — MOYENNE & DÉCISION
    # ════════════════════════════════════

    bilan_data = [[
        Paragraph("BILAN DE SESSION", ParagraphStyle(
            'bilan_hdr', fontSize=9, textColor=WHITE,
            fontName='Helvetica-Bold', alignment=TA_CENTER
        )),
        '', '', ''
    ]]

    bilan_table1 = Table(
        bilan_data,
        colWidths=[17.4*cm]
    )
    bilan_table1.setStyle(TableStyle([
        ('SPAN', (0,0), (3,0)),
        ('BACKGROUND', (0,0), (-1,-1), BORDEAUX),
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
    ]))
    elements.append(bilan_table1)

    # Ligne bilan détaillée
    nb_matieres   = notes.count()
    nb_validees   = sum(1 for n in notes if n.note >= 5.0)
    nb_ajournees  = nb_matieres - nb_validees

    bilan_details = [[
        Paragraph(
            f"<b>Modules évalués :</b><br/>{nb_matieres}",
            ParagraphStyle('bd', fontSize=10, alignment=TA_CENTER,
                           textColor=BORDEAUX_DARK,
                           fontName='Helvetica')
        ),
        Paragraph(
            f"<b>Modules validés :</b><br/>"
            f"<font color='#1B7A3E'>{nb_validees}</font>",
            ParagraphStyle('bd2', fontSize=10, alignment=TA_CENTER,
                           fontName='Helvetica')
        ),
        Paragraph(
            f"<b>Modules ajournés :</b><br/>"
            f"<font color='#C0392B'>{nb_ajournees}</font>",
            ParagraphStyle('bd3', fontSize=10, alignment=TA_CENTER,
                           fontName='Helvetica')
        ),
        Paragraph(
            f"<b>Moyenne générale :</b><br/>"
            f"<font color='#7B1C2E' size='13'>"
            f"<b>{round(moyenne, 2)} / 10</b></font>",
            ParagraphStyle('bd4', fontSize=10, alignment=TA_CENTER,
                           fontName='Helvetica')
        ),
        Paragraph(
            f"<b>Mention :</b><br/>{mention}",
            ParagraphStyle('bd5', fontSize=10, alignment=TA_CENTER,
                           fontName='Helvetica',
                           textColor=BLEU_CI)
        ),
        Paragraph(
            f"<b>Décision :</b><br/>"
            f"<font color='{'#1B7A3E' if moyenne >= 5.0 else '#C0392B'}'>"
            f"<b>{decision}</b></font>",
            ParagraphStyle('bd6', fontSize=10, alignment=TA_CENTER,
                           fontName='Helvetica-Bold')
        ),
    ]]

    bilan_details_table = Table(
        bilan_details,
        colWidths=[2.9*cm, 2.9*cm, 2.9*cm, 3.2*cm, 2.7*cm, 2.8*cm]
    )
    bilan_details_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), LIGHT_BG),
        ('GRID', (0,0), (-1,-1), 0.5, LIGHT_BORDER),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('BACKGROUND', (3,0), (3,0),
         colors.HexColor('#F5EBE8')),
        ('BACKGROUND', (5,0), (5,0),
         colors.HexColor('#E8F5EC')
         if moyenne >= 5.0 else colors.HexColor('#FDECEA')),
    ]))
    elements.append(bilan_details_table)
    elements.append(Spacer(1, 0.6*cm))

    # ════════════════════════════════════
    # SIGNATURES
    # ════════════════════════════════════

    sig_data = [[
        Table([
            [Paragraph("L'Étudiant(e)", ParagraphStyle(
                's1', fontSize=9, textColor=BORDEAUX_DARK,
                fontName='Helvetica-Bold', alignment=TA_CENTER
            ))],
            [Spacer(1, 1.5*cm)],
            [Table([['']],
                   colWidths=[4*cm],
                   style=TableStyle([
                       ('LINEABOVE', (0,0), (-1,-1), 1, BORDEAUX)
                   ]))],
            [Paragraph(
                f"{etudiant.prenom} {etudiant.nom}",
                ParagraphStyle('sn1', fontSize=8.5, textColor=GRAY,
                               alignment=TA_CENTER)
            )],
        ]),

        Table([
            [Paragraph("Date de délivrance", ParagraphStyle(
                's2', fontSize=9, textColor=BORDEAUX_DARK,
                fontName='Helvetica-Bold', alignment=TA_CENTER
            ))],
            [Paragraph(
                demande.date_demande.strftime('%d %B %Y'),
                ParagraphStyle('sdate', fontSize=11,
                               textColor=BORDEAUX_DARK,
                               fontName='Helvetica-Bold',
                               alignment=TA_CENTER)
            )],
            [Spacer(1, 0.2*cm)],
            [Drawing(40, 40, transform=[40/100, 0, 0, 40/100, 0, 0], contents=[qr.QrCodeWidget(f"UGANC-{etudiant.matricule}-{demande.session}")] )],
            [Paragraph(
                f"N° Demande : #{demande.id:04d}",
                ParagraphStyle('snum', fontSize=8, textColor=GRAY,
                               alignment=TA_CENTER)
            )],
        ]),

        Table([
            [Paragraph("Le Responsable Académique", ParagraphStyle(
                's3', fontSize=9, textColor=BORDEAUX_DARK,
                fontName='Helvetica-Bold', alignment=TA_CENTER
            ))],
            [Paragraph(
                "Cachet & Signature",
                ParagraphStyle('scach', fontSize=8.5, textColor=GRAY,
                               fontName='Helvetica-Oblique',
                               alignment=TA_CENTER)
            )],
            [Spacer(1, 1.2*cm)],
            [Table([['']],
                   colWidths=[4*cm],
                   style=TableStyle([
                       ('LINEABOVE', (0,0), (-1,-1), 1, BORDEAUX)
                   ]))],
        ]),
    ]]

    sig_table = Table(
        sig_data,
        colWidths=[5.5*cm, 6.4*cm, 5.5*cm]
    )
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('PADDING', (0,0), (-1,-1), 8),
        ('BOX', (0,0), (-1,-1), 0.5, LIGHT_BORDER),
        ('BACKGROUND', (1,0), (1,0), colors.HexColor('#F5EBE8')),
    ]))
    elements.append(sig_table)
    elements.append(Spacer(1, 0.4*cm))

    # ════════════════════════════════════
    # PIED DE PAGE
    # ════════════════════════════════════

    # Ligne décorative
    elements.append(Table(
        [['', '', '']],
        colWidths=[2*cm, 13.4*cm, 2*cm],
        rowHeights=[0.06*cm],
        style=TableStyle([
            ('BACKGROUND', (0,0), (0,0), ORANGE),
            ('BACKGROUND', (1,0), (1,0), BORDEAUX),
            ('BACKGROUND', (2,0), (2,0), ORANGE),
        ])
    ))
    elements.append(Spacer(1, 0.2*cm))

    footer_data = [[
        Paragraph(
            "Ce document est officiel et délivré par le "
            "Centre Informatique de l'UGANC.",
            ParagraphStyle('foot1', fontSize=7.5, textColor=GRAY,
                           alignment=TA_CENTER)
        ),
    ], [
        Paragraph(
            f"Université Gamal Abdel Nasser de Conakry — "
            f"Centre Informatique — Conakry, République de Guinée  |  "
            f"ci@uganc.edu.gn  |  Généré le "
            f"{demande.date_demande.strftime('%d/%m/%Y à %H:%M')}",
            ParagraphStyle('foot2', fontSize=7, textColor=GRAY,
                           alignment=TA_CENTER)
        )
    ]]

    footer_table = Table(footer_data, colWidths=[17.4*cm])
    footer_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    elements.append(footer_table)

    # ── Build ──
    doc.build(elements)
    return f"releves/{nom_fichier}"


def get_mention(moyenne):
    if moyenne >= 8:
        return "Très Bien"
    elif moyenne >= 7:
        return "Bien"
    elif moyenne >= 6:
        return "Assez Bien"
    elif moyenne >= 5.0:
        return "Passable"
    else:
        return "Insuffisant"


def get_observation(note):
    if note >= 8:
        return "Excellent"
    elif note >= 7:
        return "Très bien"
    elif note >= 6:
        return "Bien"
    elif note >= 5.0:
        return "Passable"
    elif note >= 4:
        return "Insuffisant"
    else:
        return "Très insuffisant"
