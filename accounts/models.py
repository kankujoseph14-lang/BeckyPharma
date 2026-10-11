from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrateur'
        AGENT = 'AGENT', 'Agent'

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.AGENT)
    pharmacy = models.ForeignKey(
        'pharmacies.Pharmacy',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='agents',
        help_text="Pharmacie à laquelle l'agent est affecté (laisser vide pour l'Admin)"
    )

    def is_admin_role(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    def is_agent_role(self):
        return self.role == self.Role.AGENT
    