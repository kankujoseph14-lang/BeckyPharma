from django.utils import timezone
from datetime import timedelta
from .models import Product


def stock_alerts(request):
    """
    Rend les alertes de stock et de péremption disponibles dans tous les templates,
    avec une isolation stricte par pharmacie (J9).
    """
    if not request.user.is_authenticated:
        return {}

    today = timezone.now().date()
    warning_date = today + timedelta(days=30)

    user_pharmacy = getattr(request.user, 'pharmacy', None)

    # Multi-tenancy sécurisé :
    # 1. Le Superadmin a une vue globale
    # 2. L'agent ne voit QUE les produits de sa pharmacie
    # 3. Un compte sans pharmacie ne voit rien (sécurité)
    if request.user.is_superuser:
        products = Product.objects.all()
    elif user_pharmacy:
        products = Product.objects.filter(pharmacy=user_pharmacy)
    else:
        products = Product.objects.none()

    # Filtres des alertes isolés par pharmacie
    out_of_stock_products = products.filter(stock_quantity=0)
    low_stock_products = products.filter(stock_quantity__gt=0, stock_quantity__lte=5)
    expiring_products = products.filter(expiration_date__lte=warning_date)

    total_alerts_count = (
        out_of_stock_products.count() +
        low_stock_products.count() +
        expiring_products.count()
    )

    return {
        'alerts_out_of_stock': out_of_stock_products,
        'alerts_low_stock': low_stock_products,
        'alerts_expiring': expiring_products,
        'total_alerts_count': total_alerts_count,
    }