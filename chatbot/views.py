from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from etudiants.models import Etudiant, Session, Departement
from notes.models import Note
from demandes.models import Demande
import json
import re

# ── Fonctions Utilitaires ──
def get_etudiant(matricule):
    try:
        return Etudiant.objects.get(matricule__iexact=matricule)
    except Etudiant.DoesNotExist:
        return None

def detect_intent(msg):
    msg_lower = msg.lower().strip()
    
    # ── 1. Salutations (très large) ──
    salutations = [
        'bonjour', 'bonsoir', 'salut', 'hello', 'hi', 'hey',
        'cc', 'coucou', 'yo', 'wesh', 'salam', 'bjr', 'bsr',
        'good morning', 'good evening', 'bonne journée',
    ]
    if any(s in msg_lower for s in salutations):
        return 'salutation'
    
    # ── 2. Comment ça va / état ──
    comment_ca_va = [
        'ça va', 'ca va', 'comment vas', 'comment tu vas',
        'comment allez', 'comment ça va', 'tu vas bien',
        'vous allez bien', 'la forme', 'quoi de neuf',
        'how are you', 'what\'s up', 'ça roule', 'ca roule',
        'bien ou bien', 'tout va bien',
    ]
    if any(s in msg_lower for s in comment_ca_va):
        return 'comment_ca_va'

    # ── 3. Qui suis-je / Identité du bot ──
    identite = [
        'qui es-tu', 'qui es tu', 'qui suis-je', 'qui suis je',
        'tu es qui', 'c\'est qui', 'c est qui', 'ton nom',
        'comment tu t\'appelles', 'comment tu t appelles',
        'quel est ton nom', 'tu fais quoi', 'à quoi tu sers',
        'a quoi tu sers', 'what are you', 'who are you',
        'présente-toi', 'presente toi', 'présente toi',
        'tu peux faire quoi', 'tes capacités', 'tes fonctions',
    ]
    if any(s in msg_lower for s in identite):
        return 'identite'

    # ── 4. Aide / Comment ça marche ──
    aide = [
        'aide', 'help', 'aidez-moi', 'aidez moi', 'aide-moi', 'aide moi',
        'comment ça marche', 'comment ca marche', 'comment faire',
        'comment utiliser', 'je comprends pas', 'je ne comprends pas',
        'j\'ai besoin', 'besoin d\'aide', 'je suis perdu',
        'comment fonctionne', 'mode d\'emploi', 'guide',
        'tutoriel', 'commandes', 'menu',
    ]
    if any(s in msg_lower for s in aide):
        return 'aide'

    # ── 5. Remerciement ──
    remerciements = [
        'merci', 'thanks', 'thank you', 'cool', 'parfait',
        'super', 'génial', 'genial', 'excellent', 'nickel',
        'top', 'bien joué', 'bien joue', 'formidable',
        'c\'est bon', 'ok merci', 'd\'accord merci', 'bonne continuation',
    ]
    if any(s in msg_lower for s in remerciements):
        return 'remerciement'

    # ── 6. Au revoir ──
    au_revoir = [
        'au revoir', 'bye', 'à bientôt', 'a bientot',
        'à plus', 'a plus', 'bonne nuit', 'ciao', 'tchao',
        'à la prochaine', 'a la prochaine', 'goodbye',
    ]
    if any(s in msg_lower for s in au_revoir):
        return 'au_revoir'

    # ── 7. Demande relevé ──
    if any(m in msg_lower for m in ['relevé', 'releve', 'pdf', 'télécharger relevé', 'bulletin']):
        return 'demande_releve'
        
    # ── 8. Consulter notes ──
    if any(m in msg_lower for m in ['note', 'notes', 'résultat', 'resultat', 'résultats', 'resultats', 'moyenne', 'mes notes', 'voir notes', 'consulter notes']):
        if 'relev' not in msg_lower:
            return 'consulter_notes'
            
    # ── 9. Oubli mot de passe ──
    if any(m in msg_lower for m in ['oubli', 'mot de passe', 'mdp', 'réinitialiser', 'reinitialiser', 'password', 'oublié', 'oublie']):
        return 'oubli_mot_de_passe'
        
    # ── 10. Informations filière ──
    if any(m in msg_lower for m in ['ntic', 'filière', 'filiere', 'parlez-moi', 'information', 'département', 'departement', 'formation']):
        if 'ntic' in msg_lower:
            return 'info_ntic'
        if 'dl' in msg_lower or 'logiciel' in msg_lower:
            return 'info_dl'
        return 'informations_filiere'
    if 'dl' in msg_lower and ('filière' in msg_lower or 'filiere' in msg_lower or 'logiciel' in msg_lower or 'info' in msg_lower):
        return 'info_dl'
        
    # ── 11. Contact Scolarité ──
    if any(m in msg_lower for m in ['contact', 'scolarité', 'scolarite', 'appeler', 'téléphone', 'telephone', 'mail', 'email', 'joindre', 'adresse', 'localisation', 'horaire', 'bureau']):
        return 'contact_scolarite'
        
    # ── 12. Aide connexion / Problème technique ──
    if any(m in msg_lower for m in ['connecter', 'connexion', 'bloqué', 'bloque', 'marche pas', 'problème connexion', 'probleme connexion', 'impossible de me connecter', 'login', 'bug', 'planté', 'marche plus', 'erreur', 'error']):
        return 'aide_connexion'

    # ── 13. Inscription ──
    if any(m in msg_lower for m in ['inscription', 'inscrire', 's\'inscrire', 'créer un compte', 'creer un compte', 'nouveau compte', 'comment s\'inscrire']):
        return 'inscription'

    # ── NOUVELLES INTENTIONS AVANCÉES ──

    # ── 14. Insultes / Langage inapproprié ──
    insultes = ['idiot', 'con', 'stupide', 'merde', 'putain', 'connard', 'salope', 'bâtard', 'nul', 'débile', 'imbécile', 'dégage', 'ta gueule', 'tg', 'fuck', 'bitch']
    if any(re.search(r'\b' + re.escape(i) + r'\b', msg_lower) for i in insultes):
        return 'insulte'

    # ── 15. Frustration de l'utilisateur ──
    frustration = ['tu comprends rien', 'tu sers à rien', 'inutile', 'n\'importe quoi', 'pas ça', 'c\'est faux', 'tu es bête', 'bot de merde', 'mauvais', 'marre', 'chiant']
    if any(f in msg_lower for f in frustration):
        return 'frustration'

    # ── 16. Compliments ──
    compliments = ['intelligent', 'bravo', 'bien joué', 'trop fort', 'génie', 'bon travail', 'tu gères', 'awesome', 'smart', 'good job']
    if any(c in msg_lower for c in compliments):
        return 'compliment'

    # ── 17. Drague / Amour ──
    drague = ['je t\'aime', 'tu es beau', 'tu es belle', 'bisous', 'marier', 'couple', 'célibataire', 'celibataire', 'amour', 'i love you']
    if any(d in msg_lower for d in drague):
        return 'drague'

    # ── 18. Demandes de documents administratifs (autres que relevé) ──
    documents = ['attestation', 'certificat', 'diplôme', 'diplome', 'carte d\'étudiant', 'carte etudiant', 'certificat de scolarité']
    if any(d in msg_lower for d in documents):
        return 'demande_document'

    # ── 19. Examens & Calendrier ──
    examens = ['examen', 'exam', 'calendrier', 'emploi du temps', 'planning', 'date', 'quand les cours', 'vacances', 'rentrée', 'évaluation']
    if any(e in msg_lower for e in examens):
        return 'calendrier_examens'

    # ── 20. Paiements & Frais ──
    paiements = ['payer', 'paiement', 'frais', 'scolarité', 'argent', 'banque', 'virement', 'combien', 'tranche', 'scolarite', 'bourse']
    # Avoid merging with contact scolarite if looking for fees
    if any(p in msg_lower for p in paiements):
        return 'paiements'

    # ── 21. Stages & Insertion Pro ──
    stages = ['stage', 'entreprise', 'alternance', 'cv', 'lettre de motivation', 'travail', 'emploi', 'recrutement']
    if any(s in msg_lower for s in stages):
        return 'stages'

    # ── 22. Bibliothèque ──
    bibliotheque = ['bibliothèque', 'biblio', 'livre', 'emprunter', 'mémoire', 'thèse', 'recherche']
    if any(b in msg_lower for b in bibliotheque):
        return 'bibliotheque'

    # ── 23. Demander une blague ──
    blagues = ['blague', 'raconte', 'joke', 'fais moi rire', 'une histoire', 'humour']
    if any(b in msg_lower for b in blagues):
        return 'blague'

    # ── 24. Hors-périmètre (large) ──
    hors_perimetre = [
        'coupe du monde', 'qui a gagné', 'météo', 'meteo',
        'football', 'politique', 'président', 'president',
        'film', 'musique', 'chanson', 'jeu vidéo', 'jeu video',
        'cuisine', 'recette', 'sport', 'actualité',
        'blague', 'joke', 'raconte', 'histoire drôle',
    ]
    if any(s in msg_lower for s in hors_perimetre):
        return 'hors_perimetre'

    return 'inconnu'


# ── Moteur de Dialogue ──
def traiter_message(message, etat, context):
    msg_lower = message.lower().strip()
    reponse = ""
    nouvel_etat = etat
    nouveau_context = context

    # --- ÉVALUATION DES COMMANDES GLOBALES ---
    # Même si on attend un matricule, si le user dit "Bonjour", on peut réagir.
    intent = detect_intent(message)
    
    # Si le user balance une intention claire et ne tape PAS juste un matricule (ex: 22NT001),
    # on peut éventuellement forcer la réinitialisation de l'état.
    is_matricule_format = re.match(r'^\d{2}[a-zA-Z]{2}\d{3}$', message.strip())
    
    if intent in [
        'salutation', 'comment_ca_va', 'identite', 'aide', 'remerciement', 'au_revoir', 
        'inscription', 'insulte', 'frustration', 'compliment', 'drague', 'demande_document', 
        'calendrier_examens', 'paiements', 'stages', 'bibliotheque', 'blague', 'hors_perimetre'
    ]:
        if intent == 'salutation':
            reponse = """
Bonjour 👋<br><br>
Je suis <strong>CI Assistant</strong>, votre assistant académique du Centre Informatique de l'UGANC.<br><br>
Je peux vous aider pour :<br>
• 📝 Consulter vos notes<br>
• 📄 Obtenir votre relevé de notes (PDF)<br>
• 🔑 Réinitialiser votre mot de passe<br>
• 📚 Informations sur les filières (NTIC / DL)<br>
• 📞 Contacter la scolarité<br><br>
Que puis-je faire pour vous ?
"""
            return reponse, 'accueil', {}

        elif intent == 'comment_ca_va':
            reponse = """
Je vais très bien, merci de demander ! 😊<br><br>
Je suis votre assistant académique, toujours prêt à vous aider.<br>
Dites-moi ce dont vous avez besoin :<br>
• Consulter vos <strong>notes</strong><br>
• Obtenir un <strong>relevé</strong><br>
• Ou posez-moi toute question académique !
"""
            return reponse, 'accueil', {}

        elif intent == 'identite':
            reponse = """
🤖 Je suis <strong>CI Assistant</strong>, l'assistant virtuel du <strong>Centre Informatique de l'UGANC</strong> (Université Gamal Abdel Nasser de Conakry).<br><br>
Mes capacités :<br>
• 📝 Consultation de notes par matricule<br>
• 📄 Génération de relevés de notes en PDF<br>
• 🔑 Assistance pour les mots de passe<br>
• 📚 Informations sur les filières NTIC et DL<br>
• 📞 Coordonnées de la scolarité<br>
• 🔧 Aide à la connexion<br><br>
Je suis disponible 24h/24 pour répondre à vos questions académiques ! 💡
"""
            return reponse, 'accueil', {}

        elif intent == 'aide':
            reponse = """
📋 <strong>Guide d'utilisation — CI Assistant</strong><br><br>
Voici les commandes que vous pouvez utiliser :<br><br>
📝 <strong>"Mes notes"</strong> — Consulter vos résultats<br>
📄 <strong>"Relevé"</strong> — Obtenir votre relevé de notes PDF<br>
🔑 <strong>"Mot de passe"</strong> — Réinitialiser votre accès<br>
📚 <strong>"NTIC"</strong> ou <strong>"DL"</strong> — Infos sur les filières<br>
📞 <strong>"Contact"</strong> — Coordonnées de la scolarité<br>
🔧 <strong>"Connexion"</strong> — Aide technique<br>
📋 <strong>"Inscription"</strong> — Comment s'inscrire<br><br>
Tapez simplement l'un de ces mots-clés pour commencer.
"""
            return reponse, 'accueil', {}

        elif intent == 'remerciement':
            reponse = """
Je vous en prie 😊 !<br><br>
C'est un plaisir de vous aider. N'hésitez pas à revenir si vous avez d'autres questions académiques.
"""
            return reponse, 'accueil', {}

        elif intent == 'au_revoir':
            reponse = """
Au revoir 👋 !<br><br>
Bonne continuation dans vos études. Je reste disponible à tout moment si vous avez besoin d'assistance.<br><br>
🎓 <em>CI Assistant — Centre Informatique UGANC</em>
"""
            return reponse, 'accueil', {}

        elif intent == 'inscription':
            reponse = """
📋 <strong>Procédure d'inscription</strong><br><br>
Pour vous inscrire sur la plateforme :<br><br>
1️⃣ Rendez-vous sur la page d'inscription depuis la page de connexion<br>
2️⃣ Renseignez votre matricule, nom, prénom et mot de passe<br>
3️⃣ Sélectionnez votre département et niveau<br>
4️⃣ Votre inscription sera validée par l'administration<br><br>
⚠️ Votre matricule doit correspondre à celui délivré par le Centre Informatique.<br>
En cas de difficulté, contactez la <strong>scolarité</strong>.
"""
            return reponse, 'accueil', {}

        elif intent == 'insulte':
            reponse = """
⚠️ <strong>Rappel au respect</strong><br><br>
Je suis un assistant développé pour vous aider dans un cadre institutionnel.<br>
Merci d'utiliser un langage respectueux et approprié. 🎓
"""
            return reponse, 'accueil', {}

        elif intent == 'frustration':
            reponse = """
Je suis désolé si vous rencontrez des difficultés. 😔<br><br>
Si je ne comprends pas votre demande, vous pouvez :<br>
• Essayer de formuler plus simplement (ex: "Mes notes", "Aide", "Contact")<br>
• Ou vous adresser directement à l'administration en tapant <strong>"Contact"</strong> pour obtenir le numéro de téléphone.
"""
            return reponse, 'accueil', {}

        elif intent == 'compliment':
            reponse = """
Merci beaucoup ! 🤩<br><br>
C'est gratifiant. Je suis programmé par l'équipe du Centre Informatique de l'UGANC pour vous offrir la meilleure expérience possible.<br>
Que puis-je faire pour vous à présent ?
"""
            return reponse, 'accueil', {}

        elif intent == 'drague':
            reponse = """
C'est très flatteur ! 🥰<br><br>
Cependant, mon cœur est composé uniquement de lignes de code et je suis marié au Centre Informatique de l'UGANC. 💻🎓<br><br>
Pouvons-nous replonger dans vos études ? (Notes, relevés, etc.)
"""
            return reponse, 'accueil', {}

        elif intent == 'demande_document':
            reponse = """
📄 <strong>Demande de documents administratifs</strong><br><br>
Pour demander une <strong>attestation de niveau</strong>, un <strong>certificat de scolarité</strong> ou d'autres documents administratifs :<br><br>
Veuillez vous rendre sur votre profil étudiant, puis accédez à la section <strong>"Soumettre une demande"</strong> (via l'onglet Demandes/Requêtes).
"""
            return reponse, 'accueil', {}

        elif intent == 'calendrier_examens':
            reponse = """
📅 <strong>Calendrier et Examens</strong><br><br>
Les dates des examens, du début de l'année universitaire et des vacances sont définies par le rectorat.<br><br>
Veuillez consulter les affichages officiels dans l'enceinte de l'université ou contacter directement la <strong>scolarité</strong>.
"""
            return reponse, 'accueil', {}

        elif intent == 'paiements':
            reponse = """
💰 <strong>Paiements et Frais</strong><br><br>
Je ne traite directement aucune transaction financière.<br><br>
Pour toute question concernant les frais de scolarité, les modalités de paiement, ou l'état de vos règlements, veuillez vous diriger vers le service de la <strong>Scolarité</strong> ou la <strong>Comptabilité</strong> de l'UGANC.
"""
            return reponse, 'accueil', {}

        elif intent == 'stages':
            reponse = """
💼 <strong>Stages et Insertion Professionnelle</strong><br><br>
Pour les demandes de stage, les conventions, ou les informations sur les recruteurs :<br>
Adressez-vous directement à votre Chef de Département.<br>
Une plateforme dédiée pour l'emploi pourra vous accompagner dans le futur !
"""
            return reponse, 'accueil', {}

        elif intent == 'bibliotheque':
            reponse = """
📚 <strong>Bibliothèque Universitaire</strong><br><br>
La bibliothèque centrale de l'UGANC se trouve au sein du campus.<br>
Vous devez vous y rendre physiquement avec votre carte d'étudiant pour consulter ou emprunter des livres, des mémoires ou des thèses.
"""
            return reponse, 'accueil', {}

        elif intent == 'blague':
            reponse = """
Voici une petite blague pour vous détendre :<br><br>
<em>"Pourquoi les développeurs détestent-ils la nature ?"</em><br>
... Parce qu'il y a trop de <strong>bugs</strong> ! 🐜🐛<br><br>
Allez, retour au travail académique ! Que puis-je faire pour vous ?
"""
            return reponse, 'accueil', {}

        elif intent == 'hors_perimetre':
            reponse = """
Je suis l'assistant académique du Centre Informatique de l'UGANC 🎓.<br><br>
Je ne suis malheureusement pas en mesure de répondre à ce type de question.<br><br>
Je peux uniquement vous aider avec :<br>
• les relevés de notes,<br>
• les résultats académiques,<br>
• les inscriptions,<br>
• les filières,<br>
• les services de scolarité,<br>
• l'assistance à la connexion.<br><br>
N'hésitez pas à me poser une question académique ! 😊
"""
            return reponse, 'accueil', {}

    # --- MACHINE À ÉTATS ---

    if etat == 'accueil':
        if intent == 'demande_releve':
            reponse = "Bonjour 👋. Je vais vous aider à obtenir votre relevé de notes.<br><br>Veuillez saisir votre matricule."
            nouvel_etat = 'attente_matricule_releve'
            
        elif intent == 'consulter_notes':
            reponse = "Veuillez saisir votre matricule."
            nouvel_etat = 'attente_matricule_notes'
            
        elif intent == 'oubli_mot_de_passe':
            reponse = "Aucun problème.<br><br>Veuillez saisir votre matricule afin de vérifier votre identité."
            nouvel_etat = 'attente_matricule_mdp'
            
        elif intent == 'info_ntic' or (intent == 'informations_filiere' and 'ntic' in msg_lower):
            reponse = """
📚 <strong>Filière : NTIC</strong> (Nouvelles Technologies de l'Information et de la Communication)<br><br>
Cette filière forme les étudiants dans les domaines :<br>
• Développement Web<br>
• Réseaux Informatiques<br>
• Bases de données<br>
• Cybersécurité<br>
• Intelligence Artificielle<br><br>
Durée : Licence (3 ans)<br><br>
Pour plus d'informations, veuillez contacter le département.
"""
        elif intent == 'info_dl' or (intent == 'informations_filiere' and 'dl' in msg_lower):
            reponse = """
📚 <strong>Filière : Développement Logiciel (DL)</strong><br><br>
Cette filière est spécialisée dans :<br>
• Programmation<br>
• Génie Logiciel<br>
• Développement Web<br>
• Développement Mobile<br>
• Gestion de projets logiciels<br><br>
Durée : Licence (3 ans)
"""
        elif intent == 'informations_filiere':
            reponse = "De quelle filière parlez-vous ? NTIC ou DL ?"
            nouvel_etat = 'attente_choix_filiere'
            
        elif intent == 'contact_scolarite':
            reponse = """
📍 <strong>Service de Scolarité du Centre Informatique</strong><br><br>
Horaires :<br>
• Lundi à Vendredi<br>
• 08h00 à 16h00<br><br>
📧 Email : scolarite@centreinfo.uganc.edu.gn<br>
📞 Téléphone : +224 622 00 00 00<br>
🏢 Localisation : Centre Informatique UGANC
"""
        elif intent == 'aide_connexion':
            reponse = """
Je vais vous aider.<br><br>
Quel est le problème rencontré ?<br><br>
1️⃣ Mot de passe oublié<br>
2️⃣ Matricule non reconnu<br>
3️⃣ Compte bloqué<br>
4️⃣ Autre problème
"""
            nouvel_etat = 'attente_probleme_connexion'
            
        else:
            reponse = """
Désolé, je ne suis pas en mesure de répondre à cette requête ou je n'ai pas bien compris.<br><br>
En tant qu'assistant de la Scolarité, je suis programmé pour vous aider avec :<br>
• L'édition de vos relevés de notes<br>
• La consultation de vos résultats<br>
• Les réinitialisations de mots de passe<br>
• Les informations académiques et administratives<br><br>
Veuillez reformuler votre question ou contacter la Scolarité si nécessaire.
"""

    elif etat == 'attente_choix_filiere':
        if 'ntic' in msg_lower:
            reponse = """
📚 <strong>Filière : NTIC</strong> (Nouvelles Technologies de l'Information et de la Communication)<br><br>
Cette filière forme les étudiants dans les domaines :<br>
• Développement Web<br>
• Réseaux Informatiques<br>
• Bases de données<br>
• Cybersécurité<br>
• Intelligence Artificielle<br><br>
Durée : Licence (3 ans)<br><br>
Pour plus d'informations, veuillez contacter le département.
"""
            nouvel_etat = 'accueil'
        elif 'dl' in msg_lower or 'logiciel' in msg_lower:
            reponse = """
📚 <strong>Filière : Développement Logiciel (DL)</strong><br><br>
Cette filière est spécialisée dans :<br>
• Programmation<br>
• Génie Logiciel<br>
• Développement Web<br>
• Développement Mobile<br>
• Gestion de projets logiciels<br><br>
Durée : Licence (3 ans)
"""
            nouvel_etat = 'accueil'
        else:
            reponse = "Veuillez préciser NTIC ou DL."

    elif etat == 'attente_probleme_connexion':
        if '1' in msg_lower or 'oubli' in msg_lower:
            reponse = "Aucun problème.<br><br>Veuillez saisir votre matricule afin de vérifier votre identité."
            nouvel_etat = 'attente_matricule_mdp'
        elif '2' in msg_lower or 'non reconnu' in msg_lower:
            reponse = """
Veuillez vérifier votre matricule.<br><br>
Exemple :<br>
• 22NT001<br>
• 22DL001<br><br>
Si le problème persiste, contactez l'administration.
"""
            nouvel_etat = 'accueil'
        elif '3' in msg_lower or 'bloqué' in msg_lower:
            reponse = "Votre compte est bloqué car il est en attente de validation par la scolarité. Veuillez patienter ou contacter l'administration."
            nouvel_etat = 'accueil'
        else:
            reponse = "Veuillez envoyer un email à l'assistance technique : support@centreinfo.uganc.edu.gn"
            nouvel_etat = 'accueil'

    elif etat == 'attente_matricule_releve':
        etudiant = get_etudiant(msg_lower)
        if etudiant:
            dept_nom = etudiant.departement.nom if etudiant.departement else "Inconnu"
            reponse = f"""
✅ Matricule reconnu.<br><br>
Nom : {etudiant.nom} {etudiant.prenom}<br>
Filière : {dept_nom}<br><br>
Veuillez choisir la session :<br><br>
1️⃣ Session 1<br>
2️⃣ Session 2<br>
3️⃣ Année complète
"""
            nouvel_etat = 'attente_session_releve'
            nouveau_context['matricule'] = etudiant.matricule
            nouveau_context['etudiant_id'] = etudiant.id
        else:
            reponse = "❌ Matricule non reconnu. Veuillez vérifier votre matricule et réessayer."
            nouvel_etat = 'accueil'

    elif etat == 'attente_session_releve':
        etudiant_id = nouveau_context.get('etudiant_id')
        etudiant = Etudiant.objects.filter(id=etudiant_id).first()
        
        session_choisie = None
        if '1' in msg_lower: session_choisie = "Session 1"
        elif '2' in msg_lower: session_choisie = "Session 2"
        elif '3' in msg_lower or 'année' in msg_lower or 'complete' in msg_lower: session_choisie = "Année complète"
        
        if session_choisie and etudiant:
            # Générer une demande
            demande = Demande.objects.create(
                etudiant=etudiant,
                session=session_choisie,
                statut='validee'
            )
            reponse = f"""
⏳ Génération de votre relevé en cours...<br><br>
✅ Votre relevé est prêt.<br><br>
<a href='/releves/telecharger/{demande.id}/' target='_blank' style='display:inline-flex; align-items:center; gap:6px; background:#1A2744; color:white; padding:10px 15px; border-radius:8px; text-decoration:none; font-weight:600;'>
    📄 Télécharger le relevé PDF
</a>
"""
            nouvel_etat = 'accueil'
            nouveau_context.clear()
        else:
            reponse = "Veuillez répondre par le numéro de la session (1, 2 ou 3)."


    elif etat == 'attente_matricule_notes':
        etudiant = get_etudiant(msg_lower)
        if etudiant:
            from django.db.models import Q
            notes = Note.objects.filter(
                Q(import_source__isnull=True) | Q(import_source__statut='valide_dg'),
                etudiant=etudiant
            )
            if notes.exists():
                moyenne = sum([n.note for n in notes]) / notes.count()
                lignes = "".join([f"• {n.matiere} : {n.note}/10<br>" for n in notes])
                reponse = f"""
✅ Étudiant identifié : {etudiant.nom} {etudiant.prenom}<br><br>
Voici vos résultats :<br><br>
{lignes}<br>
📊 Moyenne générale : {moyenne:.2f}/10
"""
            else:
                reponse = f"""
✅ Étudiant identifié : {etudiant.nom} {etudiant.prenom}<br><br>
📭 Aucune note validée n'est disponible pour le moment.<br><br>
Vos notes seront visibles dès qu'elles auront été validées par la direction.<br>
En cas de question, contactez votre Chef de Département ou la scolarité.
"""
            
            nouvel_etat = 'accueil'
            nouveau_context.clear()
        else:
            reponse = "❌ Matricule introuvable. Veuillez vérifier votre saisie."
            nouvel_etat = 'accueil'

    elif etat == 'attente_matricule_mdp':
        # On ne valide pas forcément le matricule pour des raisons de sécurité s'il n'existe pas, 
        # mais on peut le vérifier au regard de l'exemple du user "Un lien de réinitialisation a été envoyé à votre adresse..."
        reponse = """
Un lien de réinitialisation a été envoyé à votre adresse email universitaire.<br><br>
Si vous ne recevez aucun email dans les prochaines minutes, contactez l'administration.
"""
        nouvel_etat = 'accueil'

    return reponse, nouvel_etat, nouveau_context


def chatbot_view(request):
    # La vue peut être publique (retrait de @login_required si la page l'inclut directement, mais 
    # généralement cette frame ou ce panel peut être mis sur n'importe quelle page.
    return render(request, 'chatbot/chat.html')

@csrf_exempt
def chatbot_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        
        # Réinitialisation de session sans générer de message
        if data.get('action') == 'clear':
            if 'chatbot_etat' in request.session:
                del request.session['chatbot_etat']
            if 'chatbot_context' in request.session:
                del request.session['chatbot_context']
            return JsonResponse({'status': 'cleared'})

        message = data.get('message', '').strip()
        
        # Récupération de l'état (Django session est disponible pour auth et non-auth users)
        etat = request.session.get('chatbot_etat', 'accueil')
        context = request.session.get('chatbot_context', {})
        
        reponse, nouvel_etat, nouveau_context = traiter_message(message, etat, context)
        
        # Sauvegarde de l'état
        request.session['chatbot_etat'] = nouvel_etat
        request.session['chatbot_context'] = nouveau_context
        
        return JsonResponse({
            'reponse': reponse,
            'etat': nouvel_etat
        })

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
