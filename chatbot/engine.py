"""
Moteur conversationnel du chatbot.
Gère le flux de dialogue étape par étape.
"""
from etudiants.models import Etudiant
from notes.models import Note
from demandes.models import Demande


def traiter_message(user, message, session_data):
    """
    Traite un message du chatbot et retourne la réponse.
    session_data est un dict stocké dans la session Django pour suivre l'état.
    """
    message = message.strip().lower()
    etape = session_data.get('etape', 'accueil')

    # ── Commandes globales ──
    if message in ['aide', 'help', '?']:
        return {
            'reponse': (
                "🤖 <strong>Commandes disponibles :</strong><br>"
                "• <strong>relevé</strong> — Demander un relevé de notes<br>"
                "• <strong>notes</strong> — Voir mes notes<br>"
                "• <strong>historique</strong> — Voir mes demandes<br>"
                "• <strong>aide</strong> — Afficher cette aide<br>"
                "• <strong>bonjour</strong> — Recommencer"
            ),
            'session_data': session_data
        }

    if message in ['bonjour', 'salut', 'hello', 'hi', 'bonsoir', 'coucou']:
        try:
            etudiant = Etudiant.objects.get(user=user)
            session_data['etape'] = 'menu'
            return {
                'reponse': (
                    f"👋 Bonjour <strong>{etudiant.prenom} {etudiant.nom}</strong> !<br><br>"
                    "Comment puis-je vous aider ?<br>"
                    "• Tapez <strong>relevé</strong> pour demander un relevé<br>"
                    "• Tapez <strong>notes</strong> pour voir vos notes<br>"
                    "• Tapez <strong>historique</strong> pour voir vos demandes"
                ),
                'session_data': session_data
            }
        except Etudiant.DoesNotExist:
            return {
                'reponse': "❌ Votre profil étudiant n'a pas été trouvé. Contactez l'administration.",
                'session_data': session_data
            }

    # ── Voir les notes ──
    if message in ['notes', 'mes notes', 'voir notes']:
        try:
            etudiant = Etudiant.objects.get(user=user)
            notes = Note.objects.filter(etudiant=etudiant)
            if notes.exists():
                moyenne = round(sum(n.note for n in notes) / notes.count(), 2)
                notes_text = "<br>".join(
                    [f"📘 {n.matiere} : <strong>{n.note}/20</strong> "
                     f"({'✅ Validé' if n.note >= 10 else '❌ Échec'})"
                     for n in notes]
                )
                decision = "✅ ADMIS" if moyenne >= 10 else "❌ AJOURNÉ"
                return {
                    'reponse': (
                        f"📊 <strong>Vos notes :</strong><br><br>"
                        f"{notes_text}<br><br>"
                        f"📈 <strong>Moyenne : {moyenne}/20</strong> — {decision}"
                    ),
                    'session_data': session_data
                }
            else:
                return {
                    'reponse': "📭 Aucune note disponible pour le moment.",
                    'session_data': session_data
                }
        except Etudiant.DoesNotExist:
            return {
                'reponse': "❌ Profil non trouvé.",
                'session_data': session_data
            }

    # ── Historique des demandes ──
    if message in ['historique', 'mes demandes', 'demandes']:
        try:
            etudiant = Etudiant.objects.get(user=user)
            demandes = Demande.objects.filter(etudiant=etudiant).order_by('-date_demande')[:5]
            if demandes.exists():
                status_icons = {
                    'en_attente': '⏳ En attente',
                    'validee': '✅ Validée',
                    'rejetee': '❌ Rejetée'
                }
                demandes_text = "<br>".join(
                    [f"📋 {d.session} — {status_icons.get(d.statut, d.statut)} "
                     f"({d.date_demande.strftime('%d/%m/%Y')})"
                     for d in demandes]
                )
                return {
                    'reponse': f"📋 <strong>Vos dernières demandes :</strong><br><br>{demandes_text}",
                    'session_data': session_data
                }
            else:
                return {
                    'reponse': "📭 Aucune demande trouvée. Tapez <strong>relevé</strong> pour en créer une.",
                    'session_data': session_data
                }
        except Etudiant.DoesNotExist:
            return {
                'reponse': "❌ Profil non trouvé.",
                'session_data': session_data
            }

    # ── Demander un relevé — Étape 1 ──
    if message in ['relevé', 'releve', 'demander', 'demande']:
        session_data['etape'] = 'choisir_session'
        return {
            'reponse': (
                "📄 <strong>Demande de relevé de notes</strong><br><br>"
                "Quelle session souhaitez-vous ?<br>"
                "• Tapez <strong>1</strong> pour Session 1<br>"
                "• Tapez <strong>2</strong> pour Session 2<br>"
                "• Tapez <strong>3</strong> pour Session Rattrapage"
            ),
            'session_data': session_data
        }

    # ── Demander un relevé — Étape 2 : Choix session ──
    if etape == 'choisir_session':
        sessions_map = {
            '1': 'Session 1',
            '2': 'Session 2',
            '3': 'Session Rattrapage',
            'session 1': 'Session 1',
            'session 2': 'Session 2',
            'session rattrapage': 'Session Rattrapage',
            'rattrapage': 'Session Rattrapage',
        }
        session_choisie = sessions_map.get(message)
        if session_choisie:
            session_data['session_choisie'] = session_choisie
            session_data['etape'] = 'confirmer'
            return {
                'reponse': (
                    f"📌 Vous avez choisi : <strong>{session_choisie}</strong><br><br>"
                    "Confirmez-vous cette demande ?<br>"
                    "• Tapez <strong>oui</strong> pour confirmer<br>"
                    "• Tapez <strong>non</strong> pour annuler"
                ),
                'session_data': session_data
            }
        else:
            return {
                'reponse': "❓ Choix non reconnu. Tapez <strong>1</strong>, <strong>2</strong> ou <strong>3</strong>.",
                'session_data': session_data
            }

    # ── Demander un relevé — Étape 3 : Confirmation ──
    if etape == 'confirmer':
        if message in ['oui', 'o', 'yes', 'ok', 'confirmer']:
            try:
                etudiant = Etudiant.objects.get(user=user)
                session_choisie = session_data.get('session_choisie', 'Session 1')

                # Vérifier doublon
                if Demande.objects.filter(etudiant=etudiant, session=session_choisie, statut='en_attente').exists():
                    session_data['etape'] = 'menu'
                    return {
                        'reponse': "⚠️ Une demande est déjà en attente pour cette session.",
                        'session_data': session_data
                    }

                Demande.objects.create(etudiant=etudiant, session=session_choisie)
                session_data['etape'] = 'menu'
                return {
                    'reponse': (
                        f"✅ <strong>Demande créée avec succès !</strong><br><br>"
                        f"📄 Session : {session_choisie}<br>"
                        "⏳ Statut : En attente de validation<br><br>"
                        "Vous serez notifié lorsque votre relevé sera prêt. "
                        "Consultez la page <strong>historique</strong> pour suivre l'avancement."
                    ),
                    'session_data': session_data
                }
            except Etudiant.DoesNotExist:
                session_data['etape'] = 'menu'
                return {
                    'reponse': "❌ Erreur : profil non trouvé.",
                    'session_data': session_data
                }
        elif message in ['non', 'n', 'no', 'annuler']:
            session_data['etape'] = 'menu'
            return {
                'reponse': "🚫 Demande annulée. Tapez <strong>relevé</strong> pour recommencer.",
                'session_data': session_data
            }
        else:
            return {
                'reponse': "❓ Répondez par <strong>oui</strong> ou <strong>non</strong>.",
                'session_data': session_data
            }

    # ── Message non reconnu ──
    session_data['etape'] = 'menu'
    return {
        'reponse': (
            "🤖 Je n'ai pas compris votre message.<br><br>"
            "Essayez :<br>"
            "• <strong>bonjour</strong> — Commencer<br>"
            "• <strong>relevé</strong> — Demander un relevé<br>"
            "• <strong>notes</strong> — Voir mes notes<br>"
            "• <strong>aide</strong> — Aide complète"
        ),
        'session_data': session_data
    }
