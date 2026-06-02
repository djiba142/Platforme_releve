from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from etudiants.models import Etudiant, Session
from notes.models import Note
from demandes.models import Demande
import json


# ── Détection filière depuis matricule ──
def detecter_filiere(matricule):
    m = matricule.upper()
    if m.startswith('6642') or 'NT' in m:
        return 'NTIC'
    if m.startswith('6644') or 'DL' in m:
        return 'Développement Logiciel'
    if 'RS' in m:
        return 'Réseaux & Systèmes'
    return 'Centre Informatique'


# ── Machine à états du chatbot ──
def traiter_message(message, etudiant, etat, session_choisie=None):
    message = message.strip()
    reponse = ""
    nouvel_etat = etat
    nouvelle_session = session_choisie

    # ════════════════════════════
    # ÉTAT 0 — ACCUEIL
    # ════════════════════════════
    if etat == 'accueil':
        filiere = detecter_filiere(etudiant.matricule)
        notes = Note.objects.filter(etudiant=etudiant)
        nb_notes = notes.count()

        reponse = f"""
<div class="bot-step">
    <div class="step-check">
        <i class="fa-solid fa-circle-check"></i>
        Matricule reconnu avec succès
    </div>
    <table class="info-table">
        <tr>
            <td><i class="fa-solid fa-user me-2"></i>Nom</td>
            <td><strong>{etudiant.prenom} {etudiant.nom}</strong></td>
        </tr>
        <tr>
            <td><i class="fa-solid fa-id-card me-2"></i>Matricule</td>
            <td><strong>{etudiant.matricule}</strong></td>
        </tr>
        <tr>
            <td><i class="fa-solid fa-graduation-cap me-2"></i>Département</td>
            <td><strong>{filiere}</strong></td>
        </tr>
        <tr>
            <td><i class="fa-solid fa-list-ol me-2"></i>Notes</td>
            <td><strong>{nb_notes} module(s)</strong></td>
        </tr>
    </table>
</div>
<br>
<strong>Que souhaitez-vous faire ?</strong><br><br>
<div class="quick-btns">
    <button class="qbtn" onclick="sendQuick('releve')">
        <i class="fa-solid fa-file-pdf"></i> Demander un relevé
    </button>
    <button class="qbtn" onclick="sendQuick('notes')">
        <i class="fa-solid fa-chart-bar"></i> Voir mes notes
    </button>
    <button class="qbtn" onclick="sendQuick('historique')">
        <i class="fa-solid fa-clock-rotate-left"></i> Historique
    </button>
    <button class="qbtn" onclick="sendQuick('aide')">
        <i class="fa-solid fa-circle-info"></i> Aide
    </button>
</div>
"""
        nouvel_etat = 'menu'

    # ════════════════════════════
    # ÉTAT MENU — CHOIX ACTION
    # ════════════════════════════
    elif etat == 'menu':
        msg = message.lower()

        if any(m in msg for m in ['relevé', 'releve', 'pdf', 'document']):
            # Build session buttons dynamically from DB
            sessions = Session.objects.all()
            btns = ""
            for s in sessions:
                btns += (
                    f"<button class='qbtn qbtn-primary'"
                    f" onclick=\"sendQuick('{s.nom}')\">"
                    f"<i class='fa-solid fa-layer-group'></i> {s.nom}"
                    f"</button>\n"
                )
            if not btns:
                btns = (
                    "<button class='qbtn qbtn-primary'"
                    " onclick=\"sendQuick('Session 1')\">"
                    "<i class='fa-solid fa-1'></i> Session 1</button>\n"
                    "<button class='qbtn qbtn-primary'"
                    " onclick=\"sendQuick('Session 2')\">"
                    "<i class='fa-solid fa-2'></i> Session 2</button>\n"
                    "<button class='qbtn qbtn-primary'"
                    " onclick=\"sendQuick('Session Rattrapage')\">"
                    "<i class='fa-solid fa-r'></i> Rattrapage</button>\n"
                )

            reponse = f"""
<strong>
    <i class="fa-solid fa-file-pdf me-1" style="color:#00C3A3;"></i>
    Demande de relevé de notes
</strong><br><br>
Choisissez la session souhaitée :<br><br>
<div class="quick-btns">
    {btns}
</div>
"""
            nouvel_etat = 'attente_session'

        elif any(m in msg for m in ['note', 'notes', 'résultat', 'moyenne']):
            notes = Note.objects.filter(etudiant=etudiant).select_related('session')
            if notes.exists():
                moyenne = sum([n.note for n in notes]) / notes.count()
                decision = "ADMIS(E) ✅" if moyenne >= 5 else "AJOURNÉ(E) ❌"
                rows = "".join([
                    f"<tr>"
                    f"<td>{n.matiere}</td>"
                    f"<td><strong>{n.note}/10</strong></td>"
                    f"<td>{n.session.nom}</td>"
                    f"<td style='color:{'#00C3A3' if n.note >= 5 else '#DC3545'};'>"
                    f"{'✓' if n.note >= 5 else '✗'}</td>"
                    f"</tr>"
                    for n in notes
                ])
                reponse = f"""
<strong>
    <i class="fa-solid fa-chart-bar me-1" style="color:#00C3A3;"></i>
    Vos notes
</strong><br><br>
<table class="notes-table">
    <thead><tr><th>Matière</th><th>Note</th><th>Session</th><th>Résultat</th></tr></thead>
    <tbody>{rows}</tbody>
</table>
<div class="moyenne-box">
    <span>Moyenne générale</span>
    <strong>{round(moyenne, 2)}/10</strong>
    <span class="decision">{decision}</span>
</div>
<br>
<div class="quick-btns">
    <button class="qbtn qbtn-primary" onclick="sendQuick('releve')">
        <i class="fa-solid fa-file-pdf"></i> Demander mon relevé
    </button>
    <button class="qbtn" onclick="sendQuick('retour')">
        <i class="fa-solid fa-arrow-left"></i> Retour
    </button>
</div>
"""
            else:
                reponse = """
<i class="fa-solid fa-circle-xmark" style="color:#DC3545;"></i>
Aucune note disponible.<br>
Contactez l'administration du Centre Informatique.
"""
            nouvel_etat = 'menu'

        elif any(m in msg for m in ['historique', 'demande', 'demandes', 'statut',
                                     'télécharger', 'telecharger', 'download']):
            demandes = Demande.objects.filter(
                etudiant=etudiant
            ).order_by('-date_demande')[:5]

            if demandes.exists():
                rows = ""
                for d in demandes:
                    color = {'en_attente': '#FFC107', 'validee': '#00C3A3',
                             'rejetee': '#DC3545'}.get(d.statut, '#64748B')
                    icone = {'en_attente': 'fa-hourglass-half', 'validee': 'fa-circle-check',
                             'rejetee': 'fa-circle-xmark'}.get(d.statut, 'fa-circle')

                    if d.statut == 'validee':
                        action = (
                            f"<a href='/releves/telecharger/{d.id}/' target='_blank'"
                            f" style='display:inline-flex;align-items:center;gap:6px;"
                            f"background:#1A2744;color:white;padding:5px 12px;"
                            f"border-radius:20px;text-decoration:none;font-size:0.78rem;"
                            f"font-weight:700;'>"
                            f"<i class='fa-solid fa-file-pdf' style='color:#00C3A3;'></i>"
                            f" Télécharger PDF</a>"
                        )
                    elif d.statut == 'en_attente':
                        action = (
                            "<span style='display:inline-flex;align-items:center;gap:5px;"
                            "background:#FFF8E1;color:#F59E0B;padding:4px 10px;"
                            "border-radius:20px;font-size:0.75rem;font-weight:600;'>"
                            "<i class='fa-solid fa-hourglass-half'></i> En attente admin</span>"
                        )
                    else:
                        action = (
                            "<span style='display:inline-flex;align-items:center;gap:5px;"
                            "background:#FEE2E2;color:#DC3545;padding:4px 10px;"
                            "border-radius:20px;font-size:0.75rem;font-weight:600;'>"
                            "<i class='fa-solid fa-xmark'></i> Rejetée</span>"
                        )

                    rows += (
                        f"<div style='background:white;border-radius:12px;padding:12px 14px;"
                        f"margin-bottom:8px;border:1px solid #E8F0FB;"
                        f"box-shadow:0 2px 8px rgba(26,39,68,0.05);'>"
                        f"<div style='display:flex;align-items:center;"
                        f"justify-content:space-between;margin-bottom:8px;'>"
                        f"<span style='font-weight:700;color:#1A2744;font-size:0.85rem;'>"
                        f"<i class='fa-solid fa-file-lines me-1' style='color:#00C3A3;'></i>"
                        f" Demande #{d.id:04d}</span>"
                        f"<span style='color:{color};font-size:0.78rem;font-weight:700;'>"
                        f"<i class='fa-solid {icone} me-1'></i> {d.get_statut_display()}</span>"
                        f"</div>"
                        f"<div style='display:flex;gap:15px;margin-bottom:10px;"
                        f"font-size:0.78rem;color:#64748B;'>"
                        f"<span><i class='fa-solid fa-layer-group me-1'></i> {d.session}</span>"
                        f"<span><i class='fa-solid fa-calendar me-1'></i>"
                        f" {d.date_demande.strftime('%d/%m/%Y')}</span>"
                        f"</div>{action}</div>"
                    )

                reponse = (
                    f"<strong style='display:flex;align-items:center;gap:8px;"
                    f"margin-bottom:12px;color:#1A2744;'>"
                    f"<i class='fa-solid fa-clock-rotate-left' style='color:#00C3A3;'></i>"
                    f" Vos demandes de relevés</strong>{rows}"
                    f"<div style='background:#EFF4FB;border-radius:10px;padding:9px 13px;"
                    f"font-size:0.78rem;color:#64748B;margin-top:5px;'>"
                    f"<i class='fa-solid fa-circle-info me-1' style='color:#1A2744;'></i>"
                    f" Les relevés <strong style='color:#00C3A3;'>validés</strong>"
                    f" sont disponibles immédiatement en PDF.</div><br>"
                    f"<div class='quick-btns'>"
                    f"<button class='qbtn qbtn-primary' onclick=\"sendQuick('releve')\">"
                    f"<i class='fa-solid fa-plus'></i> Nouvelle demande</button>"
                    f"<button class='qbtn' onclick=\"sendQuick('retour')\">"
                    f"<i class='fa-solid fa-house'></i> Menu</button></div>"
                )
            else:
                reponse = (
                    "<div style='text-align:center;padding:15px;'>"
                    "<i class='fa-solid fa-folder-open fa-2x'"
                    " style='color:#D4E0F0;margin-bottom:10px;display:block;'></i>"
                    "<strong style='color:#1A2744;'>Aucune demande pour le moment</strong><br>"
                    "<span style='color:#64748B;font-size:0.85rem;'>"
                    "Faites votre première demande de relevé</span></div><br>"
                    "<div class='quick-btns' style='justify-content:center;'>"
                    "<button class='qbtn qbtn-primary' onclick=\"sendQuick('releve')\">"
                    "<i class='fa-solid fa-file-pdf'></i> Demander mon relevé</button></div>"
                )
            nouvel_etat = 'menu'

        elif any(m in msg for m in ['aide', 'help']):
            reponse = """
<strong><i class="fa-solid fa-circle-info me-1" style="color:#00C3A3;"></i> Aide — CI Assistant</strong><br><br>
<div class="quick-btns">
    <button class="qbtn qbtn-primary" onclick="sendQuick('releve')"><i class="fa-solid fa-file-pdf"></i> Demander un relevé</button>
    <button class="qbtn" onclick="sendQuick('notes')"><i class="fa-solid fa-chart-bar"></i> Mes notes</button>
    <button class="qbtn" onclick="sendQuick('historique')"><i class="fa-solid fa-clock-rotate-left"></i> Historique</button>
</div>"""
            nouvel_etat = 'menu'

        elif any(m in msg for m in ['retour', 'menu', 'accueil']):
            reponse = """
<strong>Menu principal</strong><br><br>
<div class="quick-btns">
    <button class="qbtn qbtn-primary" onclick="sendQuick('releve')"><i class="fa-solid fa-file-pdf"></i> Demander un relevé</button>
    <button class="qbtn" onclick="sendQuick('notes')"><i class="fa-solid fa-chart-bar"></i> Mes notes</button>
    <button class="qbtn" onclick="sendQuick('historique')"><i class="fa-solid fa-clock-rotate-left"></i> Historique</button>
    <button class="qbtn" onclick="sendQuick('aide')"><i class="fa-solid fa-circle-info"></i> Aide</button>
</div>"""
            nouvel_etat = 'menu'

        else:
            reponse = """
Je n'ai pas compris. Choisissez une option :<br><br>
<div class="quick-btns">
    <button class="qbtn qbtn-primary" onclick="sendQuick('releve')"><i class="fa-solid fa-file-pdf"></i> Relevé</button>
    <button class="qbtn" onclick="sendQuick('notes')"><i class="fa-solid fa-chart-bar"></i> Notes</button>
    <button class="qbtn" onclick="sendQuick('historique')"><i class="fa-solid fa-clock-rotate-left"></i> Historique</button>
</div>"""

    # ════════════════════════════
    # ÉTAT — ATTENTE SESSION
    # ════════════════════════════
    elif etat == 'attente_session':
        msg_lower = message.lower().strip()

        # Try to match session from DB
        session_obj = None
        try:
            session_obj = Session.objects.filter(nom__icontains=msg_lower).first()
        except Exception:
            pass

        # Fallback: map common inputs
        if not session_obj:
            fallback_map = {
                '1': 'Session 1', 'session 1': 'Session 1',
                '2': 'Session 2', 'session 2': 'Session 2',
                'r': 'Session Rattrapage', 'rattrapage': 'Session Rattrapage',
                'session rattrapage': 'Session Rattrapage',
            }
            for key, val in fallback_map.items():
                if key in msg_lower:
                    try:
                        session_obj = Session.objects.filter(nom__icontains=val).first()
                    except Exception:
                        pass
                    break

        if session_obj:
            session_nom = session_obj.nom
            notes_session = Note.objects.filter(
                etudiant=etudiant,
                session=session_obj
            )

            if notes_session.exists():
                rows = "".join([
                    f"<tr><td>{n.matiere}</td>"
                    f"<td><strong>{n.note}/10</strong></td>"
                    f"<td style='color:{'#00C3A3' if n.note >= 5 else '#DC3545'};'>"
                    f"{'✓ Validé' if n.note >= 5 else '✗ Ajourné'}</td></tr>"
                    for n in notes_session
                ])
                moy = sum([n.note for n in notes_session]) / notes_session.count()

                reponse = (
                    f"<strong><i class='fa-solid fa-file-lines me-1'"
                    f" style='color:#00C3A3;'></i> {session_nom} — Aperçu</strong><br><br>"
                    f"<table class='notes-table'><thead><tr>"
                    f"<th>Matière</th><th>Note</th><th>Résultat</th>"
                    f"</tr></thead><tbody>{rows}</tbody></table>"
                    f"<div class='moyenne-box'><span>Moyenne</span>"
                    f"<strong>{round(moy, 2)}/10</strong>"
                    f"<span class='decision'>"
                    f"{'ADMIS(E) ✅' if moy >= 5 else 'AJOURNÉ(E) ❌'}</span></div><br>"
                    f"Confirmer la demande de relevé pour <strong>{session_nom}</strong> ?<br><br>"
                    f"<div class='quick-btns'>"
                    f"<button class='qbtn qbtn-success'"
                    f" onclick=\"sendQuick('confirmer|{session_nom}')\">"
                    f"<i class='fa-solid fa-check'></i> Oui, confirmer</button>"
                    f"<button class='qbtn qbtn-danger' onclick=\"sendQuick('annuler')\">"
                    f"<i class='fa-solid fa-xmark'></i> Annuler</button></div>"
                )
                nouvel_etat = 'confirmation'
                nouvelle_session = session_nom
            else:
                reponse = (
                    f"<i class='fa-solid fa-triangle-exclamation' style='color:#FFC107;'></i>"
                    f" Aucune note trouvée pour <strong>{session_nom}</strong>.<br>"
                    f"Contactez l'administration.<br><br>"
                    f"<div class='quick-btns'>"
                    f"<button class='qbtn' onclick=\"sendQuick('releve')\">"
                    f"<i class='fa-solid fa-rotate-left'></i> Choisir une autre session</button></div>"
                )
                nouvel_etat = 'menu'
        else:
            sessions = Session.objects.all()
            btns = ""
            for s in sessions:
                btns += (
                    f"<button class='qbtn qbtn-primary'"
                    f" onclick=\"sendQuick('{s.nom}')\">"
                    f"<i class='fa-solid fa-layer-group'></i> {s.nom}</button>\n"
                )
            reponse = f"Veuillez choisir une session valide :<br><br><div class='quick-btns'>{btns}</div>"

    # ════════════════════════════
    # ÉTAT — CONFIRMATION
    # ════════════════════════════
    elif etat == 'confirmation':
        if message.startswith('confirmer|'):
            session_finale = message.split('|')[1]

            # ── Vérifier notes validées DG ──
            from notes.models import ImportNotes

            matricule = etudiant.matricule.upper()
            if 'NT' in matricule or matricule.startswith('6642'):
                filiere = 'NTIC'
            elif 'DL' in matricule:
                filiere = 'DL'
            else:
                filiere = None

            notes_ok = False
            if filiere:
                notes_ok = ImportNotes.objects.filter(
                    filiere=filiere,
                    session=session_finale,
                    statut='valide_dg'
                ).exists()

            if not notes_ok:
                reponse = f"""
<div style='
    background:#FFF8E1;
    border:1.5px solid #FFC107;
    border-radius:10px;
    padding:13px 15px;'>
    <i class='fa-solid fa-triangle-exclamation'
       style='color:#FFC107;margin-right:8px;'></i>
    <strong>Notes non disponibles</strong><br><br>
    <span style='color:#64748B;font-size:0.88rem;'>
        Les notes pour <strong>{session_finale}</strong>
        ne sont pas encore validées par la Direction.<br>
        Revenez ultérieurement ou contactez
        l'administration.
    </span>
</div>
<br>
<div class='quick-btns'>
    <button class='qbtn' onclick="sendQuick('retour')">
        <i class='fa-solid fa-house'></i> Menu
    </button>
</div>
"""
                nouvel_etat = 'menu'

            else:
                # ── Notes OK → Demande validée automatiquement ──

                # Vérifier doublon
                demande_exist = Demande.objects.filter(
                    etudiant=etudiant,
                    session=session_finale
                ).exists()

                if demande_exist:
                    demande_obj = Demande.objects.filter(
                        etudiant=etudiant,
                        session=session_finale
                    ).first()
                    
                    # On force le statut à validée si c'était bloqué en "en_attente" auparavant
                    if demande_obj.statut != 'validee':
                        demande_obj.statut = 'validee'
                        demande_obj.save()
                        
                    reponse = f"""
<div style='
    background:#FFF8E1;
    border:1.5px solid #FFC107;
    border-radius:10px;
    padding:12px 15px;'>
    <i class='fa-solid fa-triangle-exclamation'
       style='color:#FFC107;'></i>
    Vous avez déjà un relevé pour
    <strong>{session_finale}</strong>.
</div>
<br>
<div class='quick-btns'>
    <button class='qbtn qbtn-primary'
            onclick="sendQuick('historique')">
        <i class='fa-solid fa-file-pdf'></i>
        Télécharger mon relevé
    </button>
    <button class='qbtn' onclick="sendQuick('retour')">
        <i class='fa-solid fa-house'></i> Menu
    </button>
</div>
"""
                else:
                    # ── Créer demande validée automatiquement ──
                    demande_obj = Demande.objects.create(
                        etudiant=etudiant,
                        session=session_finale,
                        statut='validee'  # ← Direct !
                    )

                    reponse = f"""
<div style='
    background:rgba(0,195,163,0.1);
    border:1.5px solid #00C3A3;
    border-radius:10px;
    padding:13px 15px;'>
    <i class='fa-solid fa-circle-check'
       style='color:#00C3A3;font-size:1.1rem;
              margin-right:8px;'></i>
    <strong style='color:#00796B;'>
        Relevé disponible !
    </strong>
</div>
<br>
<table class='info-table'>
    <tr>
        <td>N° Relevé</td>
        <td><strong>#{demande_obj.id:04d}</strong></td>
    </tr>
    <tr>
        <td>Session</td>
        <td><strong>{session_finale}</strong></td>
    </tr>
    <tr>
        <td>Statut</td>
        <td style='color:#00C3A3;font-weight:700;'>
            ✅ Disponible
        </td>
    </tr>
</table>
<br>
<a href='/releves/telecharger/{demande_obj.id}/'
   target='_blank'
   style='
       display:inline-flex;
       align-items:center;gap:8px;
       background:#1A2744;color:white;
       padding:10px 20px;border-radius:25px;
       text-decoration:none;font-weight:700;
       font-size:0.9rem;'>
    <i class='fa-solid fa-file-pdf'
       style='color:#00C3A3;'></i>
    Télécharger mon relevé PDF
</a>
<br><br>
<div class='quick-btns'>
    <button class='qbtn'
            onclick="sendQuick('historique')">
        <i class='fa-solid fa-clock-rotate-left'></i>
        Historique
    </button>
    <button class='qbtn' onclick="sendQuick('retour')">
        <i class='fa-solid fa-house'></i> Menu
    </button>
</div>
"""
                nouvel_etat = 'menu'
                nouvelle_session = None

        elif message.lower() == 'annuler':
            reponse = (
                "<i class='fa-solid fa-ban' style='color:#DC3545;'></i>"
                " Demande annulée.<br><br>"
                "<div class='quick-btns'>"
                "<button class='qbtn qbtn-primary' onclick=\"sendQuick('releve')\">"
                "<i class='fa-solid fa-rotate-left'></i> Recommencer</button>"
                "<button class='qbtn' onclick=\"sendQuick('retour')\">"
                "<i class='fa-solid fa-house'></i> Menu</button></div>"
            )
            nouvel_etat = 'menu'
            nouvelle_session = None

    return reponse, nouvel_etat, nouvelle_session


@login_required
def chatbot_view(request):
    etudiant = Etudiant.objects.get(user=request.user)
    return render(request, 'chatbot/chat.html', {
        'etudiant': etudiant
    })


@csrf_exempt
@login_required
def chatbot_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        etat = data.get('etat', 'accueil')
        session = data.get('session', None)

        etudiant = Etudiant.objects.get(user=request.user)

        reponse, nouvel_etat, nouvelle_session = traiter_message(
            message, etudiant, etat, session
        )

        return JsonResponse({
            'reponse': reponse,
            'etat': nouvel_etat,
            'session': nouvelle_session,
        })

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
