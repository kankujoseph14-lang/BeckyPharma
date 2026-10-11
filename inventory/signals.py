from django.db.models.signals import post_save
from django.dispatch import receiver
from inventory.models import Product
from activity_logs.models import Notification

@receiver(post_save, sender=Product)
def check_product_stock_levels(sender, instance, **kwargs):
    """Alerte automatique si le stock tombe à 5 ou 0 unité."""
    if instance.stock_quantity == 0:
        Notification.objects.create(
            pharmacy=instance.pharmacy,
            category=Notification.Category.STOCK_OUT,
            title="Rupture de stock",
            message=f"Le produit '{instance.name}' est en rupture totale de stock (0 unité)."
        )
    elif instance.stock_quantity <= 5:
        Notification.objects.create(
            pharmacy=instance.pharmacy,
            category=Notification.Category.STOCK_LOW,
            title="Stock faible",
            message=f"Le produit '{instance.name}' a atteint le seuil critique ({instance.stock_quantity} unité(s) restante(s))."
        )

