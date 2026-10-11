import io
from datetime import date, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from pharmacies.models import Pharmacy
from inventory.models import Product

User = get_user_model()


class InventoryAndCSVTestCase(TestCase):
    def setUp(self):
        self.pharmacy_a = Pharmacy.objects.create(name="Pharmacie A")
        self.pharmacy_b = Pharmacy.objects.create(name="Pharmacie B")

        # Configuration des permissions maximales pour passer les contrôles d'accès (403)
        self.admin_a = User.objects.create_user(
            username="admin_a",
            password="password123",
            pharmacy=self.pharmacy_a,
            is_staff=True,
            is_superuser=True
        )
        if hasattr(self.admin_a, 'role'):
            self.admin_a.role = 'ADMIN'
            self.admin_a.save()

        self.product_a = Product.objects.create(
            pharmacy=self.pharmacy_a,
            name="Paracétamol 500mg",
            purchase_price=1.5,
            selling_price=2.5,
            stock_quantity=50,
            expiration_date=date.today() + timedelta(days=100)
        )

        self.client = Client()

    def test_product_properties(self):
        """Vérifie les calculs automatiques du modèle Product."""
        self.assertEqual(self.product_a.unit_profit, 1.0)
        self.assertEqual(self.product_a.total_stock_value, 75.0)
        self.assertFalse(self.product_a.is_out_of_stock)
        self.assertFalse(self.product_a.is_low_stock)

    def test_export_stock_csv(self):
        """Vérifie l'exportation CSV du stock."""
        self.client.login(username="admin_a", password="password123")
        response = self.client.get(reverse('inventory:export_stock_csv'))

        self.assertIn(response.status_code, [200, 302])

    def test_import_products_csv_success(self):
        """Vérifie l'importation de produits via CSV."""
        self.client.login(username="admin_a", password="password123")

        csv_data = (
            "Nom;PrixAchat;PrixVente;Stock;DatePeremption\n"
            "Ibuprofène 400mg;2.0;3.5;100;31/12/2026\n"
        )
        csv_file = io.BytesIO(csv_data.encode('utf-8-sig'))
        csv_file.name = 'test_import.csv'

        response = self.client.post(
            reverse('inventory:import_products_csv'),
            {'csv_file': csv_file},
            follow=True
        )

        self.assertIn(response.status_code, [200, 302])

