from django.db import models
from django.conf import settings
from pharmacies.models import Pharmacy

class ActivityLog(models.Model):
    class ActionType(models.TextChoices):
        LOGIN = 'LOGIN', 'Connexion'
        LOGOUT = 'LOGOUT', 'Déconnexion'
        OPEN_CASH = 'OPEN_CASH', 'Ouverture de caisse'
        CLOSE_CASH = 'CLOSE_CASH', 'Clôture de caisse'
        SALE_CREATE = 'SALE_CREATE', 'Vente réalisée'
        SALE_CANCEL = 'SALE_CANCEL', 'Vente annulée'
        CREDIT_GRANT = 'CREDIT_GRANT', 'Crédit accordé'
        PRODUCT_ADD = 'PRODUCT_ADD', 'Ajout de produit'
        PRODUCT_EDIT = 'PRODUCT_EDIT', 'Modification de produit'
        PRODUCT_DELETE = 'PRODUCT_DELETE', 'Suppression de produit'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    pharmacy = models.ForeignKey(Pharmacy, on_delete=models.CASCADE, null=True, blank=True)
    action_type = models.CharField(max_length=30, choices=ActionType.choices)
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Journal d'activité"
        verbose_name_plural = "Journaux d'activités"
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.timestamp.strftime('%d/%m/%Y %H:%M')}] {self.user} - {self.get_action_type_display()}"


class Notification(models.Model):
    class Category(models.TextChoices):
        STOCK_LOW = 'STOCK_LOW', 'Stock faible (<= 5)'
        STOCK_OUT = 'STOCK_OUT', 'Rupture de stock (0)'
        EXPIRATION = 'EXPIRATION', 'Proche de la date de péremption'
        CASH_EVENT = 'CASH_EVENT', 'Ouverture/Fermeture de caisse'
        AGENT_EVENT = 'AGENT_EVENT', 'Connexion/Déconnexion Agent'

    pharmacy = models.ForeignKey(Pharmacy, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    category = models.CharField(max_length=20, choices=Category.choices)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"
