/**
 * Chatbot Widget — Communication AJAX
 */
document.addEventListener('DOMContentLoaded', function () {
    const toggle = document.getElementById('chatbot-toggle');
    const window_ = document.getElementById('chatbot-window');
    const input = document.getElementById('chatbot-input');
    const sendBtn = document.getElementById('chatbot-send');
    const messagesDiv = document.getElementById('chatbot-messages');

    if (!toggle) return;

    // Toggle chatbot
    toggle.addEventListener('click', function () {
        const isOpen = window_.classList.toggle('open');
        toggle.classList.toggle('active');
        toggle.innerHTML = isOpen
            ? '<i class="fa-solid fa-xmark"></i>'
            : '<i class="fa-solid fa-robot"></i>';

        if (isOpen && messagesDiv.children.length === 0) {
            addBotMessage("👋 Bonjour ! Je suis votre assistant virtuel.<br><br>" +
                "Tapez <strong>bonjour</strong> pour commencer ou <strong>aide</strong> pour voir les commandes.");
        }
        if (isOpen) input.focus();
    });

    // Send message
    function sendMessage() {
        const msg = input.value.trim();
        if (!msg) return;

        addUserMessage(msg);
        input.value = '';

        // Show typing
        const typingEl = showTyping();

        // AJAX call
        fetch('/chatbot/api/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({ message: msg })
        })
            .then(res => res.json())
            .then(data => {
                removeTyping(typingEl);
                addBotMessage(data.reponse);
            })
            .catch(err => {
                removeTyping(typingEl);
                addBotMessage("❌ Erreur de connexion. Réessayez.");
            });
    }

    sendBtn.addEventListener('click', sendMessage);
    input.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') sendMessage();
    });

    function addUserMessage(text) {
        const div = document.createElement('div');
        div.className = 'chat-msg chat-msg-user';
        div.textContent = text;
        messagesDiv.appendChild(div);
        scrollToBottom();
    }

    function addBotMessage(html) {
        const div = document.createElement('div');
        div.className = 'chat-msg chat-msg-bot';
        div.innerHTML = html;
        messagesDiv.appendChild(div);
        scrollToBottom();
    }

    function showTyping() {
        const div = document.createElement('div');
        div.className = 'typing-dots';
        div.innerHTML = '<span></span><span></span><span></span>';
        messagesDiv.appendChild(div);
        scrollToBottom();
        return div;
    }

    function removeTyping(el) {
        if (el && el.parentNode) el.parentNode.removeChild(el);
    }

    function scrollToBottom() {
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }

    function getCSRFToken() {
        const cookies = document.cookie.split(';');
        for (let c of cookies) {
            c = c.trim();
            if (c.startsWith('csrftoken=')) {
                return c.substring('csrftoken='.length);
            }
        }
        // Fallback: hidden input
        const el = document.querySelector('[name=csrfmiddlewaretoken]');
        return el ? el.value : '';
    }
});
