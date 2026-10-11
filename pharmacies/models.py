from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


class Pharmacy(models.Model):
    name = models.CharField(max_length=150, verbose_name="Nom de la pharmacie")
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name="Adresse")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Numéro de téléphone")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Pharmacie"
        verbose_name_plural = "Pharmacies"

    def __str__(self):
        return self.name


class CashRegister(models.Model):
    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Ouverte'
        CLOSED = 'CLOSED', 'Fermée'

    pharmacy = models.ForeignKey(Pharmacy, on_delete=models.CASCADE, related_name='cash_registers')
    agent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cash_registers')

    opening_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Montant d'ouverture")
    closing_amount_real = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True,
                                              verbose_name="Montant réel à la fermeture")

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Caisse"
        verbose_name_plural = "Caisses"
        ordering = ['-opened_at']

    def __str__(self):
        return f"Caisse {self.pharmacy.name} - {self.opened_at.strftime('%d/%m/%Y')}"

    @property
    def total_sales_normal(self):
        """Total des ventes normales réalisées pendant cette session de caisse"""
        sales = self.sales.filter(is_credit=False)
        return sum(sale.total_amount for sale in sales)

    @property
    def total_sales_credit(self):
        """Total des ventes à crédit accordées pendant cette session"""
        credits = self.sales.filter(is_credit=True)
        return sum(sale.total_amount for sale in credits)

    @property
    def theoretical_amount(self):
        """Montant théorique attendu en caisse = Ouverture + Ventes normales en espèces"""
        return self.opening_amount + self.total_sales_normal

    @property
    def gap_amount(self):
        """Écart entre montant réel et théorique (si fermée)"""
        if self.closing_amount_real is not None:
            return self.closing_amount_real - self.theoretical_amount
        return 0
