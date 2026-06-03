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
    msg_lower = msg.lower()
    
    # 7. Salutation
    if any(m in msg_lower for m in ['bonjour', 'salut', 'hello', 'cc', 'coucou']):
        return 'salutation'
    
    # 8. Remerciement
    if any(m in msg_lower for m in ['merci', 'thanks', 'cool']):
        return 'remerciement'
        
    # 1. Demande relevé
    if any(m in msg_lower for m in ['relevé', 'releve', 'pdf']):
        return 'demande_releve'
        
    # 2. Consulter notes
    if any(m in msg_lower for m in ['note', 'notes', 'résultat', 'moyenne', 'afficher']):
        if 'relev' not in msg_lower:
            return 'consulter_notes'
            
    # 3. Oubli mot de passe
    if any(m in msg_lower for m in ['oubli', 'mot de passe', 'mdp', 'réinitialiser']):
        return 'oubli_mot_de_passe'
        
    # 4. Informations filière
    if any(m in msg_lower for m in ['ntic', 'dl', 'filière', 'filiere', 'parlez-moi', 'information', 'département']):
        # Cas spécial pour router correctement si le msg contient "NTIC" ou "DL"
        if 'ntic' in msg_lower:
            return 'info_ntic'
        if 'dl' in msg_lower or 'logiciel' in msg_lower:
            return 'info_dl'
        return 'informations_filiere'
        
    # 5. Contact Scolarité
    if any(m in msg_lower for m in ['contact', 'scolarité', 'scolarite', 'appeler', 'téléphone', 'mail', 'joindre']):
        return 'contact_scolarite'
        
    # 6. Aide connexion
    if any(m in msg_lower for m in ['connecter', 'connexion', 'bloqué', 'marche pas']):
        return 'aide_connexion'
        
    # 9. Hors-périmètre (ex: coupe du monde)
    if 'coupe du monde' in msg_lower or 'qui a gagné' in msg_lower or 'météo' in msg_lower:
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
    
    if intent in ['salutation', 'remerciement', 'hors_perimetre']:
        if intent == 'salutation':
            reponse = """
Bonjour 👋<br><br>
Je suis UGANC Assistant, votre assistant académique.<br><br>
Je peux vous aider pour :<br>
• Consulter vos notes<br>
• Obtenir votre relevé de notes<br>
• Réinitialiser votre mot de passe<br>
• Obtenir des informations sur les filières<br>
• Contacter l'administration
"""
            return reponse, 'accueil', {}
        elif intent == 'remerciement':
            reponse = """
Je vous en prie 😊.<br><br>
N'hésitez pas à me solliciter si vous avez besoin d'une assistance académique.
"""
            return reponse, 'accueil', {}
        elif intent == 'hors_perimetre':
            reponse = """
Je suis l'assistant académique du Centre Informatique de l'UGANC.<br><br>
Je peux uniquement répondre aux questions concernant :<br>
• les relevés de notes,<br>
• les notes,<br>
• les inscriptions,<br>
• les filières,<br>
• les services académiques,<br>
• l'assistance à la connexion.
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
Je ne suis pas sûr de comprendre.<br><br>
Je peux vous aider pour :<br>
• Consulter vos notes<br>
• Obtenir votre relevé de notes<br>
• Réinitialiser votre mot de passe<br>
• Obtenir des informations sur les filières<br>
• Contacter l'administration
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
            notes = Note.objects.filter(etudiant=etudiant)
            if notes.exists():
                moyenne = sum([n.note for n in notes]) / notes.count()
                lignes = "".join([f"• {n.matiere} : {n.note}/20<br>" for n in notes])
                reponse = f"""
✅ Étudiant identifié : {etudiant.nom} {etudiant.prenom}<br><br>
Voici vos résultats :<br><br>
{lignes}<br>
📊 Moyenne générale : {moyenne:.2f}/20
"""
            else:
                reponse = f"✅ Étudiant identifié : {etudiant.nom} {etudiant.prenom}<br><br>❌ Aucune note n'est disponible pour l'instant."
            
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
