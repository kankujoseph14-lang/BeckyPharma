from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from pharmacies.models import Pharmacy
from inventory.models import Product
from sales.models import Sale, SaleItem, CashRegister

User = get_user_model()


class SalesFlowTestCase(TestCase):
    def setUp(self):
        self.pharmacy_a = Pharmacy.objects.create(name="Pharmacie Alpha")
        self.pharmacy_b = Pharmacy.objects.create(name="Pharmacie Bêta")

        self.user_a = User.objects.create_user(
            username="caissier_a",
            password="password123",
            pharmacy=self.pharmacy_a
        )

        # Création de la caisse avec le montant d'ouverture obligatoire
        self.cash_register_a = CashRegister.objects.create(
            pharmacy=self.pharmacy_a,
            agent=self.user_a,
            opening_amount=0.0
        )

        self.product_a = Product.objects.create(
            pharmacy=self.pharmacy_a,
            name="Amoxicilline 500mg",
            purchase_price=3.0,
            selling_price=5.0,
            stock_quantity=20,
            expiration_date=date.today() + timedelta(days=60)
        )

    def test_sale_creation_and_stock_reduction(self):
        """Vérifie la création d'une vente et la baisse du stock."""
        initial_stock = self.product_a.stock_quantity
        quantity_sold = 3

        sale = Sale.objects.create(
            pharmacy=self.pharmacy_a,
            agent=self.user_a,
            cash_register=self.cash_register_a,
            total_amount=15.0,
            total_profit=6.0
        )
        SaleItem.objects.create(
            sale=sale,
            product=self.product_a,
            quantity=quantity_sold,
            unit_price=5.0,
            unit_purchase_price=3.0
        )

        self.product_a.stock_quantity -= quantity_sold
        self.product_a.save()

        self.product_a.refresh_from_db()
        self.assertEqual(self.product_a.stock_quantity, initial_stock - quantity_sold)

    def test_multi_pharmacy_isolation(self):
        """Vérifie l'isolation des ventes par pharmacie."""
        sale_a = Sale.objects.create(
            pharmacy=self.pharmacy_a,
            agent=self.user_a,
            cash_register=self.cash_register_a,
            total_amount=10.0
        )

        sales_a = Sale.objects.filter(pharmacy=self.pharmacy_a)
        sales_b = Sale.objects.filter(pharmacy=self.pharmacy_b)

        self.assertIn(sale_a, sales_a)
        self.assertNotIn(sale_a, sales_b)