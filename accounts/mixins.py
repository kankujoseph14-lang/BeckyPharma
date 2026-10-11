from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


class AdminRequiredMixin(UserPassesTestMixin):
    """S'assure que seul un administrateur accède à la vue."""

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin_role()


class AgentRequiredMixin(UserPassesTestMixin):
    """S'assure que seul un agent accède à la vue."""

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_agent_role()


class PharmacyQuerySetMixin(LoginRequiredMixin):
    """
    Mixin central d'isolation des données :
    - Si c'est un AGENT, filtre les objets pour n'afficher QUE ceux de sa pharmacie.
    - Si c'est un ADMIN, laisse l'accès global (ou filtré si un paramètre 'pharmacy_id' est transmis).
    """

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if user.is_agent_role():
            if not user.pharmacy:
                raise PermissionDenied("Aucune pharmacie n'est attribuée à cet agent.")
            return queryset.filter(pharmacy=user.pharmacy)

        # Si c'est un admin et qu'un filtre par pharmacie est appliqué
        pharmacy_id = self.request.GET.get('pharmacy_id')
        if pharmacy_id and user.is_admin_role():
            return queryset.filter(pharmacy_id=pharmacy_id)

        return queryset

