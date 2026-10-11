from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


class PharmacyQuerySetMixin(LoginRequiredMixin):
    """
    Mixin qui filtre automatiquement tous les QuerySets
    en fonction de la pharmacie de l'utilisateur connecté.
    """

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # Si l'utilisateur est SuperAdmin, il peut tout voir (optionnel)
        if user.is_superuser:
            return queryset

        # Vérification si l'utilisateur appartient bien à une pharmacie
        if hasattr(user, 'pharmacy') and user.pharmacy:
            return queryset.filter(pharmacy=user.pharmacy)

        # Si l'utilisateur n'a aucune pharmacie associée, accès refusé
        raise PermissionDenied("Vous n'êtes rattaché à aucune pharmacie.")