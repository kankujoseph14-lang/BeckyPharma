from django.db import models
from django.utils import timezone
from datetime import timedelta
from pharmacies.models import Pharmacy

class Product(models.Model):
    pharmacy = models.ForeignKey(Pharmacy, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200, verbose_name="Nom complet du produit")
    stock_quantity = models.PositiveIntegerField(default=0, verbose_name="Quantité en stock")
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix d'achat unitaire")
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix de vente unitaire")
    expiration_date = models.DateField(verbose_name="Date de péremption")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.pharmacy.name})"

    # --- CALCULS AUTOMATIQUES EXIGÉS ---
    @property
    def unit_profit(self):
        """Bénéfice unitaire = Prix de vente - Prix d'achat"""
        return self.selling_price - self.purchase_price

    @property
    def total_stock_value(self):
        """Valeur totale du stock au prix d'achat"""
        return self.purchase_price * self.stock_quantity

    @property
    def potential_stock_profit(self):
        """Bénéfice potentiel sur le stock restant"""
        return self.unit_profit * self.stock_quantity

    @property
    def is_out_of_stock(self):
        return self.stock_quantity == 0

    @property
    def is_low_stock(self):
        return 0 < self.stock_quantity <= 5

    @property
    def is_near_expiration(self):
        """Produit périmé ou expirant dans moins de 30 jours"""
        today = timezone.now().date()
        warning_date = today + timedelta(days=30)
        return self.expiration_date <= warning_date


