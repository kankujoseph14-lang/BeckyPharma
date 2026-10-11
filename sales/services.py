from django.db import transaction
from .models import Sale, SaleItem
from pharmacies.models import CashRegister
from activity_logs.utils import log_activity
from activity_logs.models import ActivityLog


def process_sale(user, pharmacy, items, payment_method='CASH'):
    """
    Traite la vente de manière atomique en respectant la structure de Sale, SaleItem et CashRegister.
    """
    with transaction.atomic():
        # 1. Récupération d'une caisse ouverte (recherche par status='OPEN' ou statut actif, sinon première caisse)
        cash_register = CashRegister.objects.filter(
            pharmacy=pharmacy,
            status='OPEN'
        ).first()

        if not cash_register:
            # Fallback : prend la première caisse associée à la pharmacie
            cash_register = CashRegister.objects.filter(pharmacy=pharmacy).first()

        if not cash_register:
            raise ValueError("Aucune caisse n'a été configurée pour cette pharmacie.")

        # 2. Calcul des montants globaux (Total & Bénéfice)
        total_amount = sum(item['product'].selling_price * item['quantity'] for item in items)
        total_profit = sum(
            (item['product'].selling_price - item['product'].purchase_price) * item['quantity']
            for item in items
        )

        # 3. Création de la Vente (Sale)
        sale = Sale.objects.create(
            pharmacy=pharmacy,
            agent=user,
            cash_register=cash_register,
            total_amount=total_amount,
            total_profit=total_profit,
            is_credit=False
        )

        # 4. Création des lignes de vente (SaleItem) et mise à jour du stock
        for item in items:
            product = item['product']
            quantity = item['quantity']

            if product.stock_quantity < quantity:
                raise ValueError(f"Stock insuffisant pour {product.name} (Disponible: {product.stock_quantity})")

            SaleItem.objects.create(
                sale=sale,
                product=product,
                quantity=quantity,
                unit_price=product.selling_price,
                unit_purchase_price=product.purchase_price
            )

            product.stock_quantity -= quantity
            product.save()

        # 5. Enregistrement dans le journal d'activités
        log_activity(
            user=user,
            action_type=ActivityLog.ActionType.SALE_CREATE,
            description=f"Vente #{sale.id} effectuée par {user.username}. Total : {sale.total_amount} FCFA."
        )

        return sale