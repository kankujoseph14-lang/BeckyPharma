from django.db import models
from django.conf import settings
from pharmacies.models import Pharmacy, CashRegister
from inventory.models import Product


class Sale(models.Model):
    pharmacy = models.ForeignKey(Pharmacy, on_delete=models.CASCADE, related_name='sales')
    agent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='sales')
    cash_register = models.ForeignKey(CashRegister, on_delete=models.PROTECT, related_name='sales')

    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_credit = models.BooleanField(default=False, verbose_name="Vente à crédit")

    pdf_invoice = models.FileField(upload_to='invoices/%Y/%m/%d/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Vente"
        verbose_name_plural = "Ventes"
        ordering = ['-created_at']

    def __str__(self):
        return f"Vente #{self.id} - {self.pharmacy.name} ({self.created_at.strftime('%d/%m/%Y %H:%M')})"


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='sale_items')
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix de vente appliqué")
    unit_purchase_price = models.DecimalField(max_digits=10, decimal_places=2,
                                              verbose_name="Prix d'achat unitaire au moment de la vente")

    class Meta:
        verbose_name = "Ligne de vente"
        verbose_name_plural = "Lignes de vente"

    @property
    def total_price(self):
        return self.unit_price * self.quantity

    @property
    def total_profit(self):
        return (self.unit_price - self.unit_purchase_price) * self.quantity


class Credit(models.Model):
    sale = models.OneToOneField(Sale, on_delete=models.CASCADE, related_name='credit_details')
    client_name = models.CharField(max_length=150, verbose_name="Nom du client")
    reason = models.TextField(verbose_name="Motif du crédit")
    is_paid = models.BooleanField(default=False, verbose_name="Crédit réglé")
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Crédit"
        verbose_name_plural = "Crédits"

    def __str__(self):
        return f"Crédit - {self.client_name} ({self.sale.total_amount} FCFA/CDF)"
