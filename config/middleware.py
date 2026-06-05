from django.conf import settings
from django.shortcuts import redirect


class LoginRequiredMiddleware:
    """Exige que l'utilisateur soit authentifié pour accéder à la plupart des pages."""

    EXEMPT_STARTS = [
        '/login/',
        '/inscription/',
        '/admin/',
        '/static/',
        '/media/',
        '/favicon.ico',
        '/robots.txt',
        '/',          # accueil public
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            return self.get_response(request)

        path = request.path

        # Exempter les chemins publics
        for prefix in self.EXEMPT_STARTS:
            if path == prefix or (prefix != '/' and path.startswith(prefix)):
                return self.get_response(request)

        # Exempter les URLs extra définies dans settings
        for pref in getattr(settings, 'LOGIN_EXEMPT_URLS', []):
            if path.startswith(pref):
                return self.get_response(request)

        login_url = getattr(settings, 'LOGIN_URL', '/login/')
        return redirect(f"{login_url}?next={request.path}")
