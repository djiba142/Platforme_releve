from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, Image
)
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from notes.models import Note
import os
from django.conf import settings

# ── COULEURS ──
NAVY          = colors.HexColor('#1A2744')
TEAL          = colors.HexColor('#00C3A3')
LIGHT         = colors.HexColor('#EFF4FB')
LIGHT_BORDER  = colors.HexColor('#D4E0F0')
GRAY          = colors.HexColor('#64748B')
WHITE         = colors.white
GREEN         = colors.HexColor('#1B7A3E')
RED           = colors.HexColor('#C0392B')
DARK          = colors.HexColor('#1A0A0E')


def detecter_filiere(matricule):
    """Détecte automatiquement la filière depuis le matricule."""
    m = matricule.upper()
    if m.startswith('6642') or 'NT' in m:
        return (
            'NTIC',
            'Nouvelles Technologies de l\'Information '
            'et de la Communication'
        )
    elif m.startswith('6644') or 'DL' in m:
        return 'DL', 'Développement Logiciel'
    elif 'RS' in m:
        return 'RS', 'Réseaux et Systèmes'
    elif 'IA' in m:
        return 'IA', 'Intelligence Artificielle'
    else:
        return 'CI', 'Centre Informatique'


def detecter_annee(matricule):
    try:
        return f"20{matricule[:2]}"
    except:
        return "2024"


def get_mention(moyenne):
    """Mention sur 10."""
    if moyenne >= 9:
        return "Très Bien"
    elif moyenne >= 8:
        return "Bien"
    elif moyenne >= 7:
        return "Assez Bien"
    elif moyenne >= 5:
        return "Passable"
    else:
        return "Insuffisant"


def get_observation(note):
    """Observation sur 10."""
    if note >= 9:
        return "Excellent"
    elif note >= 8:
        return "Très bien"
    elif note >= 7:
        return "Bien"
    elif note >= 5:
        return "Passable"
    elif note >= 4:
        return "Insuffisant"
    else:
        return "Très insuffisant"


def generer_releve(demande):
    etudiant     = demande.etudiant
    notes        = Note.objects.filter(
        etudiant=etudiant,
        session__nom=demande.session
    ).select_related('session')

    # Détections automatiques
    code_filiere, nom_filiere = detecter_filiere(etudiant.matricule)
    annee_entree = detecter_annee(etudiant.matricule)

    # ── Calculs sur 10 ──
    if notes.exists():
        moyenne  = sum([n.note for n in notes]) / notes.count()
        admis    = moyenne >= 5
        decision = "ADMIS(E)" if admis else "AJOURNÉ(E)"
        dec_col  = GREEN if admis else RED
        mention  = get_mention(moyenne)
    else:
        moyenne  = 0
        admis    = False
        decision = "—"
        dec_col  = GRAY
        mention  = "—"

    # ── Fichier PDF ──
    nom_fichier = (
        f"releve_{etudiant.matricule}_"
        f"{demande.session.replace(' ','_')}.pdf"
    )
    dossier = os.path.join(settings.MEDIA_ROOT, 'releves')
    os.makedirs(dossier, exist_ok=True)
    chemin  = os.path.join(dossier, nom_fichier)

    doc = SimpleDocTemplate(
        chemin, pagesize=A4,
        topMargin=1.2*cm, bottomMargin=1.5*cm,
        leftMargin=1.8*cm, rightMargin=1.8*cm
    )
    elements = []

    # ════════════════════════════════════
    # BANDE TEAL EN-TÊTE
    # ════════════════════════════════════
    elements.append(Table(
        [['']],
        colWidths=[17.4*cm], rowHeights=[0.25*cm],
        style=TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), TEAL),
        ])
    ))
    elements.append(Spacer(1, 0.3*cm))

    # ════════════════════════════════════
    # LOGOS + NOM UNIVERSITÉ
    # ════════════════════════════════════
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
                ParagraphStyle(
                    'uni', fontSize=12, textColor=NAVY,
                    fontName='Helvetica-Bold',
                    alignment=TA_CENTER
                )
            )],
            [Paragraph(
                "CENTRE INFORMATIQUE",
                ParagraphStyle(
                    'ci', fontSize=10,
                    textColor=colors.HexColor('#1565C0'),
                    fontName='Helvetica-Bold',
                    alignment=TA_CENTER, spaceBefore=3
                )
            )],
            [Paragraph(
                "Service de la Scolarité — Conakry, "
                "République de Guinée",
                ParagraphStyle(
                    'scol', fontSize=8.5, textColor=GRAY,
                    alignment=TA_CENTER, spaceBefore=2
                )
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
        ('ALIGN',  (0,0), (-1,-1), 'CENTER'),
        ('PADDING',(0,0), (-1,-1), 5),
    ]))
    elements.append(entete_table)
    elements.append(Spacer(1, 0.25*cm))

    # Ligne séparation
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
    # TITRE DOCUMENT
    # ════════════════════════════════════
    elements.append(Paragraph(
        "RELEVÉ DE NOTES OFFICIEL",
        ParagraphStyle(
            'titre', fontSize=15, textColor=NAVY,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER, spaceAfter=4
        )
    ))
    elements.append(Paragraph(
        f"Année Académique {annee_entree}–{int(annee_entree)+1}  "
        f"|  Filière : {code_filiere}  |  {demande.session}",
        ParagraphStyle(
            'sous_titre', fontSize=9.5, textColor=GRAY,
            alignment=TA_CENTER, spaceAfter=8
        )
    ))

    # Ligne orange sous titre
    elements.append(Table(
        [['']],
        colWidths=[17.4*cm], rowHeights=[0.06*cm],
        style=TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), TEAL),
        ])
    ))
    elements.append(Spacer(1, 0.45*cm))

    # ════════════════════════════════════
    # INFOS ÉTUDIANT
    # ════════════════════════════════════
    lbl = ParagraphStyle(
        'lbl', fontSize=9, textColor=NAVY,
        fontName='Helvetica-Bold'
    )
    val = ParagraphStyle(
        'val', fontSize=9.5, textColor=DARK,
        fontName='Helvetica'
    )
    val_bold = ParagraphStyle(
        'vb', fontSize=10, textColor=NAVY,
        fontName='Helvetica-Bold'
    )

    info_data = [
        # En-tête section
        [Paragraph(
            "INFORMATIONS DE L'ÉTUDIANT",
            ParagraphStyle(
                'ih', fontSize=9, textColor=WHITE,
                fontName='Helvetica-Bold',
                alignment=TA_CENTER
            )
        ), '', '', ''],
        # Données
        [
            Paragraph("Nom & Prénom :", lbl),
            Paragraph(
                f"{etudiant.prenom.upper()} "
                f"{etudiant.nom.upper()}", val_bold
            ),
            Paragraph("Matricule :", lbl),
            Paragraph(etudiant.matricule, val_bold),
        ],
        [
            Paragraph("Filière :", lbl),
            Paragraph(nom_filiere, val),
            Paragraph("Abréviation :", lbl),
            Paragraph(code_filiere, val),
        ],
        [
            Paragraph("Niveau :", lbl),
            Paragraph(
                getattr(etudiant, 'niveau', 'Licence 3'), val
            ),
            Paragraph("Année d'entrée :", lbl),
            Paragraph(annee_entree, val),
        ],
    ]

    info_table = Table(
        info_data,
        colWidths=[3.5*cm, 5.2*cm, 3.5*cm, 5.2*cm]
    )
    info_table.setStyle(TableStyle([
        ('SPAN',       (0,0), (3,0)),
        ('BACKGROUND', (0,0), (3,0), NAVY),
        ('ALIGN',      (0,0), (3,0), 'CENTER'),
        ('TOPPADDING', (0,0), (3,0), 7),
        ('BOTTOMPADDING',(0,0),(3,0), 7),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[LIGHT, WHITE]),
        ('GRID',       (0,0), (-1,-1), 0.5, LIGHT_BORDER),
        ('PADDING',    (0,1), (-1,-1), 7),
        ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (0,-1),
         colors.HexColor('#E8F0FB')),
        ('BACKGROUND', (2,1), (2,-1),
         colors.HexColor('#E8F0FB')),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.45*cm))

    # ════════════════════════════════════
    # TABLEAU DES NOTES — SUR 10
    # ════════════════════════════════════
    hdr_style = ParagraphStyle(
        'hdr', fontSize=9, textColor=WHITE,
        fontName='Helvetica-Bold', alignment=TA_CENTER
    )

    entete_notes = [[
        Paragraph("N°",           hdr_style),
        Paragraph("MATIÈRE / MODULE", hdr_style),
        Paragraph("NOTE /10",     hdr_style),
        Paragraph("COEFF.",       hdr_style),
        Paragraph("RÉSULTAT",     hdr_style),
        Paragraph("OBSERVATION",  hdr_style),
    ]]

    lignes = []
    if notes.exists():
        for i, note in enumerate(notes, 1):
            # ── Admis si note >= 5/10 ──
            valide   = note.note >= 5
            res_col  = GREEN if valide else RED
            resultat = "Validé" if valide else "Ajourné"
            obs      = get_observation(note.note)

            lignes.append([
                Paragraph(str(i), ParagraphStyle(
                    'n', fontSize=9,
                    alignment=TA_CENTER,
                    fontName='Helvetica'
                )),
                Paragraph(note.matiere, ParagraphStyle(
                    'm', fontSize=9,
                    fontName='Helvetica'
                )),
                Paragraph(
                    f"<b>{note.note}</b> / 10",
                    ParagraphStyle(
                        'nv', fontSize=10,
                        alignment=TA_CENTER,
                        fontName='Helvetica-Bold',
                        textColor=NAVY
                    )
                ),
                Paragraph("2", ParagraphStyle(
                    'c', fontSize=9,
                    alignment=TA_CENTER,
                    fontName='Helvetica'
                )),
                Paragraph(resultat, ParagraphStyle(
                    'r', fontSize=9,
                    alignment=TA_CENTER,
                    fontName='Helvetica-Bold',
                    textColor=res_col
                )),
                Paragraph(obs, ParagraphStyle(
                    'o', fontSize=8.5,
                    alignment=TA_CENTER,
                    fontName='Helvetica-Oblique',
                    textColor=GRAY
                )),
            ])
    else:
        lignes.append([
            Paragraph("—", ParagraphStyle(
                'e', alignment=TA_CENTER
            )),
            Paragraph(
                "Aucune note disponible pour cette session",
                ParagraphStyle('e2', fontSize=9, textColor=GRAY)
            ),
            Paragraph("—", ParagraphStyle('e3',alignment=TA_CENTER)),
            Paragraph("—", ParagraphStyle('e4',alignment=TA_CENTER)),
            Paragraph("—", ParagraphStyle('e5',alignment=TA_CENTER)),
            Paragraph("—", ParagraphStyle('e6',alignment=TA_CENTER)),
        ])

    notes_table = Table(
        entete_notes + lignes,
        colWidths=[1*cm, 6.5*cm, 2.5*cm, 2*cm, 2.5*cm, 2.9*cm]
    )
    notes_table.setStyle(TableStyle([
        # En-tête
        ('BACKGROUND',   (0,0), (-1,0), NAVY),
        ('TEXTCOLOR',    (0,0), (-1,0), WHITE),
        ('FONTNAME',     (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',     (0,0), (-1,0), 9),
        ('ALIGN',        (0,0), (-1,0), 'CENTER'),
        ('TOPPADDING',   (0,0), (-1,0), 8),
        ('BOTTOMPADDING',(0,0), (-1,0), 8),
        # Corps
        ('FONTNAME',     (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE',     (0,1), (-1,-1), 9),
        ('ROWBACKGROUNDS',(0,1),(-1,-1), [WHITE, LIGHT]),
        ('GRID',         (0,0), (-1,-1), 0.5, LIGHT_BORDER),
        ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING',   (0,1), (-1,-1), 7),
        ('BOTTOMPADDING',(0,1), (-1,-1), 7),
        ('ALIGN',        (0,1), (0,-1), 'CENTER'),
        ('ALIGN',        (2,1), (-1,-1), 'CENTER'),
    ]))
    elements.append(notes_table)
    elements.append(Spacer(1, 0.45*cm))

    # ════════════════════════════════════
    # BILAN — SUR 10
    # ════════════════════════════════════
    nb_total    = notes.count()
    nb_valides  = sum(1 for n in notes if n.note >= 5)
    nb_ajournes = nb_total - nb_valides

    bilan_hdr = Table(
        [[Paragraph(
            "BILAN DE SESSION",
            ParagraphStyle(
                'bh', fontSize=9, textColor=WHITE,
                fontName='Helvetica-Bold',
                alignment=TA_CENTER
            )
        )]],
        colWidths=[17.4*cm]
    )
    bilan_hdr.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), NAVY),
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING',(0,0),(-1,-1), 7),
    ]))
    elements.append(bilan_hdr)

    bilan_data = [[
        Paragraph(
            f"<b>Modules évalués :</b><br/>{nb_total}",
            ParagraphStyle(
                'bd1', fontSize=10,
                alignment=TA_CENTER, fontName='Helvetica'
            )
        ),
        Paragraph(
            f"<b>Modules validés :</b><br/>"
            f"<font color='#1B7A3E'><b>{nb_valides}</b></font>",
            ParagraphStyle(
                'bd2', fontSize=10,
                alignment=TA_CENTER, fontName='Helvetica'
            )
        ),
        Paragraph(
            f"<b>Modules ajournés :</b><br/>"
            f"<font color='#C0392B'><b>{nb_ajournes}</b></font>",
            ParagraphStyle(
                'bd3', fontSize=10,
                alignment=TA_CENTER, fontName='Helvetica'
            )
        ),
        Paragraph(
            f"<b>Moyenne /10 :</b><br/>"
            f"<font color='#1A2744' size='13'>"
            f"<b>{round(moyenne,2)} / 10</b></font>",
            ParagraphStyle(
                'bd4', fontSize=10,
                alignment=TA_CENTER, fontName='Helvetica'
            )
        ),
        Paragraph(
            f"<b>Mention :</b><br/>"
            f"<font color='#1565C0'><b>{mention}</b></font>",
            ParagraphStyle(
                'bd5', fontSize=10,
                alignment=TA_CENTER, fontName='Helvetica'
            )
        ),
        Paragraph(
            f"<b>Décision :</b><br/>"
            f"<font color="
            f"'{'#1B7A3E' if admis else '#C0392B'}'>"
            f"<b>{decision}</b></font>",
            ParagraphStyle(
                'bd6', fontSize=10,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
        ),
    ]]

    bilan_table = Table(
        bilan_data,
        colWidths=[2.9*cm,2.9*cm,2.9*cm,3.2*cm,2.7*cm,2.8*cm]
    )
    bilan_table.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), LIGHT),
        ('GRID',          (0,0), (-1,-1), 0.5, LIGHT_BORDER),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING',    (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('BACKGROUND',    (3,0), (3,0),
         colors.HexColor('#E8F0FB')),
        ('BACKGROUND',    (5,0), (5,0),
         colors.HexColor('#E8F5EC')
         if admis else colors.HexColor('#FDECEA')),
    ]))
    elements.append(bilan_table)
    elements.append(Spacer(1, 0.6*cm))

    # ════════════════════════════════════
    # SIGNATURES — DG/DGA + CHEF DEPT
    # ════════════════════════════════════

    sig_style_titre = ParagraphStyle(
        'st', fontSize=9, textColor=NAVY,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER
    )
    sig_style_sous = ParagraphStyle(
        'ss', fontSize=8, textColor=GRAY,
        fontName='Helvetica-Oblique',
        alignment=TA_CENTER
    )
    sig_style_nom = ParagraphStyle(
        'sn', fontSize=8.5, textColor=GRAY,
        fontName='Helvetica',
        alignment=TA_CENTER
    )

    # En-tête signatures
    sig_hdr = Table(
        [[Paragraph(
            "SIGNATURES OFFICIELLES",
            ParagraphStyle(
                'sigh', fontSize=9, textColor=WHITE,
                fontName='Helvetica-Bold',
                alignment=TA_CENTER
            )
        )]],
        colWidths=[17.4*cm]
    )
    sig_hdr.setStyle(TableStyle([
        ('BACKGROUND',   (0,0), (-1,-1), NAVY),
        ('TOPPADDING',   (0,0), (-1,-1), 6),
        ('BOTTOMPADDING',(0,0), (-1,-1), 6),
    ]))
    elements.append(sig_hdr)

    # Ligne signature
    sig_logo_dg = os.path.join(
        settings.BASE_DIR, 'static', 'image', 'signature_dg.png'
    )
    sig_logo_chef = os.path.join(
        settings.BASE_DIR, 'static', 'image', 'signature_chef.png'
    )

    def sig_block(titre, sous_titre, nom_poste, sig_path):
        """Crée un bloc de signature."""
        content = [
            [Paragraph(titre, sig_style_titre)],
            [Paragraph(sous_titre, sig_style_sous)],
            [Spacer(1, 0.2*cm)],
        ]

        # Image signature si disponible
        if os.path.exists(sig_path):
            content.append([
                Image(sig_path, width=3*cm, height=1.2*cm)
            ])
        else:
            content.append([Spacer(1, 1.2*cm)])

        # Ligne de signature
        content.append([
            Table(
                [['']],
                colWidths=[4.5*cm],
                style=TableStyle([
                    ('LINEABOVE', (0,0), (-1,-1), 1, NAVY)
                ])
            )
        ])
        content.append([
            Paragraph(nom_poste, sig_style_nom)
        ])

        return Table(content, colWidths=[5.5*cm])

    # Colonne centrale — Date + N° demande
    centre_block = Table([
        [Paragraph(
            "Date de délivrance",
            sig_style_titre
        )],
        [Paragraph(
            demande.date_demande.strftime('%d %B %Y'),
            ParagraphStyle(
                'date', fontSize=11, textColor=NAVY,
                fontName='Helvetica-Bold',
                alignment=TA_CENTER
            )
        )],
        [Spacer(1, 0.3*cm)],
        [Paragraph(
            f"N° Relevé : <b>#{demande.id:04d}</b>",
            ParagraphStyle(
                'nrel', fontSize=9, textColor=GRAY,
                alignment=TA_CENTER
            )
        )],
        [Paragraph(
            f"Session : <b>{demande.session}</b>",
            ParagraphStyle(
                'sess', fontSize=9, textColor=GRAY,
                alignment=TA_CENTER
            )
        )],
        [Spacer(1, 0.3*cm)],
        [Paragraph(
            "🔒 Document officiel",
            ParagraphStyle(
                'off', fontSize=8, textColor=TEAL,
                fontName='Helvetica-Bold',
                alignment=TA_CENTER
            )
        )],
    ], colWidths=[5*cm])

    # Tableau 3 colonnes signatures
    sig_data = [[
        sig_block(
            "Le DG / DGA",
            "Directeur Général ou Directeur Général Adjoint",
            "Centre Informatique — UGANC",
            sig_logo_dg
        ),
        centre_block,
        sig_block(
            "Le Chef de Département",
            "Responsable du Département",
            f"Département {code_filiere} — NTIC"
            if code_filiere == 'NTIC'
            else f"Département {code_filiere}",
            sig_logo_chef
        ),
    ]]

    sig_table = Table(
        sig_data,
        colWidths=[6*cm, 5.4*cm, 6*cm]
    )
    sig_table.setStyle(TableStyle([
        ('VALIGN',  (0,0), (-1,-1), 'TOP'),
        ('ALIGN',   (0,0), (-1,-1), 'CENTER'),
        ('PADDING', (0,0), (-1,-1), 10),
        ('BOX',     (0,0), (-1,-1), 0.5, LIGHT_BORDER),
        ('BACKGROUND', (1,0), (1,0), LIGHT),
        ('LINEBEFORE',  (1,0), (1,0), 0.5, LIGHT_BORDER),
        ('LINEAFTER',   (1,0), (1,0), 0.5, LIGHT_BORDER),
    ]))
    elements.append(sig_table)
    elements.append(Spacer(1, 0.3*cm))

    # ════════════════════════════════════
    # PIED DE PAGE
    # ════════════════════════════════════
    elements.append(Table(
        [['', '']],
        colWidths=[14*cm, 3.4*cm],
        rowHeights=[0.06*cm],
        style=TableStyle([
            ('BACKGROUND', (0,0), (0,0), NAVY),
            ('BACKGROUND', (1,0), (1,0), TEAL),
        ])
    ))
    elements.append(Spacer(1, 0.2*cm))

    elements.append(Table(
        [[Paragraph(
            "Ce document est officiel et délivré par le "
            "Centre Informatique de l'UGANC. "
            "Toute falsification est passible de sanctions.",
            ParagraphStyle(
                'f1', fontSize=7.5, textColor=GRAY,
                alignment=TA_CENTER
            )
        )], [Paragraph(
            f"Université Gamal Abdel Nasser de Conakry — "
            f"Centre Informatique — Conakry, Guinée  |  "
            f"ci@uganc.edu.gn  |  "
            f"Généré le "
            f"{demande.date_demande.strftime('%d/%m/%Y à %H:%M')}",
            ParagraphStyle(
                'f2', fontSize=7, textColor=GRAY,
                alignment=TA_CENTER
            )
        )]],
        colWidths=[17.4*cm]
    ))

    doc.build(elements)
    return f"releves/{nom_fichier}"
