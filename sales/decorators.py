from django.core.exceptions import PermissionDenied
from functools import wraps


def admin_required(view_func):
    """Décorateur réservé aux Administrateurs / Gérants de pharmacie."""

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return view_func(request, *args, **kwargs)

        # Vérification du rôle Admin ou Superuser
        if request.user.is_superuser or getattr(request.user, 'is_admin_role', False) or request.user.is_staff:
            return view_func(request, *args, **kwargs)

        raise PermissionDenied("Accès refusé : réservé aux administrateurs.")

    return _wrapped_view

