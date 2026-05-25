from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_POST
import json
from .engine import traiter_message


@login_required
def chatbot_page(request):
    """Page du chatbot (optionnel, le chatbot est aussi en widget flottant)"""
    return render(request, 'chatbot/chatbot.html')


@login_required
@require_POST
def chatbot_api(request):
    """API endpoint pour le chatbot (AJAX)"""
    try:
        data = json.loads(request.body)
        message = data.get('message', '')
    except (json.JSONDecodeError, AttributeError):
        message = request.POST.get('message', '')

    if not message.strip():
        return JsonResponse({
            'reponse': '❓ Veuillez taper un message.',
            'status': 'error'
        })

    # Récupérer/initialiser les données de session du chatbot
    session_data = request.session.get('chatbot_data', {'etape': 'accueil'})

    # Traiter le message
    resultat = traiter_message(request.user, message, session_data)

    # Sauvegarder l'état dans la session
    request.session['chatbot_data'] = resultat['session_data']
    request.session.modified = True

    return JsonResponse({
        'reponse': resultat['reponse'],
        'status': 'ok'
    })
