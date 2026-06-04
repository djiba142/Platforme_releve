from django.conf import settings
from django.shortcuts import redirect


class LoginRequiredMiddleware:
    """Exige que l'utilisateur soit authentifié pour accéder à la plupart des pages.

    Exempte les chemins statiques, médias, l'URL de connexion et l'administration.
    Redirige vers la page de connexion en ajoutant `?next=`.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.login_url = settings.LOGIN_URL or '/login/'
        # chemins qui ne nécessitent pas d'authentification
        self.exempt_starts = [
            self.login_url,
            getattr(settings, 'LOGOUT_REDIRECT_URL', '/'),
            '/admin/',
            settings.STATIC_URL if hasattr(settings, 'STATIC_URL') else '/static/',
            settings.MEDIA_URL if hasattr(settings, 'MEDIA_URL') else '/media/',
            '/favicon.ico',
            '/robots.txt',
        ]

    def __call__(self, request):
        path = request.path

        # Allow if already authenticated
        if request.user.is_authenticated:
            return self.get_response(request)

        # Allow exempt paths
        for prefix in self.exempt_starts:
            if prefix and path.startswith(prefix):
                return self.get_response(request)

        # Allow healthchecks or other simple GETs if configured via settings
        extra_exempts = getattr(settings, 'LOGIN_EXEMPT_URLS', [])
        for pref in extra_exempts:
            if path.startswith(pref):
                return self.get_response(request)

        # Otherwise redirect to login
        return redirect(f"{self.login_url}?next={request.path}")
