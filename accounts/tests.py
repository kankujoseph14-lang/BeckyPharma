from django.test import TestCase
from django.urls import reverse, resolve
from django.contrib.auth import get_user_model
from pharmacies.models import Pharmacy

User = get_user_model()


class AuthenticationTestCase(TestCase):
    def setUp(self):
        self.pharmacy = Pharmacy.objects.create(name="Pharmacie Test")
        self.user = User.objects.create_user(
            username="joseph_test",
            password="password123",
            pharmacy=self.pharmacy
        )

    def test_login_url_resolves(self):
        """Vérifie que le nom d'URL de connexion pointe vers la vue de login."""
        try:
            url = reverse('accounts:login')
        except:
            url = reverse('login')

        resolver = resolve(url)
        self.assertIsNotNone(resolver.func)

    def test_user_creation(self):
        """Vérifie la création de l'utilisateur et son association à la pharmacie."""
        self.assertEqual(self.user.username, "joseph_test")
        self.assertEqual(self.user.pharmacy, self.pharmacy)
