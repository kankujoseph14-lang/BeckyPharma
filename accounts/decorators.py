
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import UserPassesTestMixin
from functools import wraps


def admin_required(view_func):
    """
    Décorateur pour les vues basées sur des fonctions (FBV).
    Refuse l'accès si l'utilisateur n'est pas Administrateur ou Superadmin.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_admin_role():
            return view_func(request, *args, **kwargs)
        raise PermissionDenied("Accès réservé aux administrateurs de la pharmacie.")
    return _wrapped_view


class AdminRequiredMixin(UserPassesTestMixin):
    """
    Mixin pour les vues basées sur des classes (CBV).
    """
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin_role()