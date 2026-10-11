import json
import csv
from datetime import timedelta

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.utils import timezone
from django.core.exceptions import PermissionDenied

# Décorateur de sécurité Custom (J11)
from accounts.decorators import admin_required

# Modèles et utilitaires
from inventory.models import Product
from .models import Sale, SaleItem
from .services import process_sale
from .utils import generate_invoice_pdf


def _get_user_pharmacy(user):
    """Helper interne pour récupérer la pharmacie d'un utilisateur de façon sécurisée."""
    return getattr(user, 'pharmacy', None)


# ==========================================
# J3 : TERMINAL POS ET API
# ==========================================

@login_required
def pos_terminal(request):
    """Affiche l'interface principale du terminal de vente."""
    user_pharmacy = _get_user_pharmacy(request.user)
    if not user_pharmacy and not request.user.is_superuser:
        raise PermissionDenied("Vous devez être rattaché à une pharmacie pour accéder au POS.")
    return render(request, 'sales/pos.html')


@login_required
def search_products(request):
    """API de recherche dynamique de produits (AJAX)."""
    query = request.GET.get('q', '').strip()
    user_pharmacy = _get_user_pharmacy(request.user)

    # Multi-tenancy : Superadmin voit tout, l'agent voit uniquement sa pharmacie
    if request.user.is_superuser:
        products = Product.objects.filter(stock_quantity__gt=0)
    elif user_pharmacy:
        products = Product.objects.filter(pharmacy=user_pharmacy, stock_quantity__gt=0)
    else:
        return JsonResponse({'products': []})

    if query:
        products = products.filter(name__icontains=query)

    products = products[:10]

    data = [{
        'id': p.id,
        'name': p.name,
        'price': float(p.selling_price),
        'stock': p.stock_quantity,
    } for p in products]

    return JsonResponse({'products': data})


@login_required
@require_POST
def complete_sale(request):
    """Reçoit le panier en JSON et enregistre la vente de façon atomique."""
    try:
        user_pharmacy = _get_user_pharmacy(request.user)
        if not user_pharmacy and not request.user.is_superuser:
            return JsonResponse({'success': False, 'error': "Aucune pharmacie associée à votre compte."}, status=403)

        data = json.loads(request.body)
        items_data = data.get('items', [])
        payment_method = data.get('payment_method', 'CASH')

        if not items_data:
            return JsonResponse({'success': False, 'error': 'Le panier est vide.'}, status=400)

        items = []
        for item in items_data:
            if request.user.is_superuser:
                product = Product.objects.get(id=item['id'])
            else:
                product = Product.objects.get(id=item['id'], pharmacy=user_pharmacy)

            items.append({
                'product': product,
                'quantity': int(item['qty'])
            })

        pharmacy_for_sale = user_pharmacy or (items[0]['product'].pharmacy if items else None)

        # Transmet 'agent' au service pour garantir la cohérence
        sale = process_sale(
            agent=request.user,
            pharmacy=pharmacy_for_sale,
            items=items,
            payment_method=payment_method
        )

        return JsonResponse({
            'success': True,
            'message': 'Vente enregistrée avec succès !',
            'sale_id': sale.id,
            'total_amount': float(sale.total_amount)
        })

    except Product.DoesNotExist:
        return JsonResponse(
            {'success': False, 'error': 'Un des produits n’existe pas ou n’appartient pas à votre pharmacie.'},
            status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ==========================================
# J4 : HISTORIQUE ET REÇUS
# ==========================================
@login_required
def sales_history(request):
    selected_date = request.GET.get('date')

    # Filtrage par pharmacie (multi-tenancy)
    if request.user.is_superuser or request.user.is_admin_role:
        sales = Sale.objects.all()
    else:
        sales = Sale.objects.filter(pharmacy=request.user.pharmacy)

    # Filtrage par date si renseigné
    if selected_date:
        sales = sales.filter(created_at__date=selected_date)

    sales = sales.order_by('-created_at')

    # Calcul du total pour le bandeau récapitulatif
    total_sum = sales.aggregate(Sum('total_amount'))['total_amount__sum'] or 0.00

    context = {
        'sales': sales,
        'selected_date': selected_date,
        'total_sum': total_sum,
    }
    return render(request, 'sales/sales_history.html', context)


@login_required
def sale_detail(request, sale_id):
    """Affiche le détail d'une vente spécifique avec vérification des droits."""
    user_pharmacy = _get_user_pharmacy(request.user)

    if request.user.is_superuser:
        sale = get_object_or_404(Sale, id=sale_id)
    else:
        sale = get_object_or_404(Sale, id=sale_id, pharmacy=user_pharmacy)

    context = {
        'sale': sale,
        'items': sale.items.all()
    }
    return render(request, 'sales/sale_detail.html', context)


# ==========================================
# J5 : IMPRESSION FACTURE PDF
# ==========================================

@login_required
def print_invoice_view(request, sale_id):
    """Génère et affiche le fichier PDF de la facture."""
    user_pharmacy = _get_user_pharmacy(request.user)

    if request.user.is_superuser:
        sale = get_object_or_404(Sale, id=sale_id)
    else:
        sale = get_object_or_404(Sale, id=sale_id, pharmacy=user_pharmacy)

    pdf_buffer = generate_invoice_pdf(sale)

    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Facture_BeckyPharma_{sale.id}.pdf"'
    return response


# ==========================================
# J7 & J11 : TABLEAU DE BORD ANALYTICS & STOCK (SÉCURISÉ)
# ==========================================
@login_required
@admin_required
def dashboard_analytics_view(request):
    """Calcul des KPIs ventes, métriques financières du stock, alertes et données graphiques (J2, J5 & J7)."""
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    user_pharmacy = _get_user_pharmacy(request.user)

    # Multi-tenancy Ventes & Produits
    if request.user.is_superuser:
        sales_qs = Sale.objects.all()
        items_qs = SaleItem.objects.all()
        products_qs = Product.objects.all()
    elif user_pharmacy:
        sales_qs = Sale.objects.filter(pharmacy=user_pharmacy)
        items_qs = SaleItem.objects.filter(sale__pharmacy=user_pharmacy)
        products_qs = Product.objects.filter(pharmacy=user_pharmacy)
    else:
        sales_qs = Sale.objects.none()
        items_qs = SaleItem.objects.none()
        products_qs = Product.objects.none()

    # --- KPIs VENTES ---
    today_sales = sales_qs.filter(created_at__date=today)
    month_sales = sales_qs.filter(created_at__date__gte=start_of_month)

    total_today = today_sales.aggregate(total=Sum('total_amount'))['total'] or 0
    total_month = month_sales.aggregate(total=Sum('total_amount'))['total'] or 0
    count_today = today_sales.count()

    top_products = (
        items_qs.values('product__name')
        .annotate(total_qty=Sum('quantity'))
        .order_by('-total_qty')[:5]
    )

    top_product_names = [p['product__name'] for p in top_products]
    top_product_counts = [p['total_qty'] for p in top_products]

    # --- ÉVOLUTION DES VENTIES (7 DERNIERS JOURS) ---
    last_7_days_labels = []
    last_7_days_totals = []

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_sales = sales_qs.filter(created_at__date=day)
        day_total = day_sales.aggregate(total=Sum('total_amount'))['total'] or 0

        last_7_days_labels.append(day.strftime('%d/%m'))
        last_7_days_totals.append(float(day_total))

    # --- KPIs & CALCULS FINANCIERS STOCK (J2) ---
    purchase_value_expr = ExpressionWrapper(
        F('purchase_price') * F('stock_quantity'),
        output_field=DecimalField()
    )
    margin_value_expr = ExpressionWrapper(
        (F('selling_price') - F('purchase_price')) * F('stock_quantity'),
        output_field=DecimalField()
    )

    total_stock_value = products_qs.aggregate(
        val=Sum(purchase_value_expr)
    )['val'] or 0

    total_potential_profit = products_qs.aggregate(
        val=Sum(margin_value_expr)
    )['val'] or 0

    # --- ALERTES STOCK ---
    # Seuil d'alerte fixé à 5 (car alert_threshold n'existe pas sur Product)
    low_stock_products = products_qs.filter(stock_quantity__lte=5)
    low_stock_count = low_stock_products.count()

    expired_products = products_qs.filter(expiration_date__lte=today)
    expired_count = expired_products.count()

    context = {
        # Ventes
        'total_today': total_today,
        'total_month': total_month,
        'count_today': count_today,
        'top_product_names': top_product_names,
        'top_product_counts': top_product_counts,
        'last_7_days_labels': last_7_days_labels,
        'last_7_days_totals': last_7_days_totals,

        # Stock (J2)
        'total_stock_value': total_stock_value,
        'total_potential_profit': total_potential_profit,
        'low_stock_count': low_stock_count,
        'low_stock_products': low_stock_products[:5],  # 5 premières alertes
        'expired_count': expired_count,
        'expired_products': expired_products[:5],
    }
    return render(request, 'sales/dashboard_analytics.html', context)


# ==========================================
# J12 : EXPORTATION CSV / EXCEL DES VENTIES
# ==========================================

@login_required
@admin_required
def export_sales_csv(request):
    """Exporte l'historique complet des ventes au format CSV / Excel."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="ventes_beckypharma.csv"'

    # UTF-8 BOM pour la prise en charge d'Excel
    response.write(u'\ufeff'.encode('utf8'))

    writer = csv.writer(response, delimiter=';')
    writer.writerow(['ID Vente', 'Date & Heure', 'Pharmacie', 'Caissier / Agent', 'Total ($)'])

    user_pharmacy = _get_user_pharmacy(request.user)

    if request.user.is_superuser or not user_pharmacy:
        sales = Sale.objects.all().select_related('pharmacy', 'agent')
    else:
        sales = Sale.objects.filter(pharmacy=user_pharmacy).select_related('pharmacy', 'agent')

    for sale in sales.order_by('-created_at'):
        agent_name = sale.agent.username if getattr(sale, 'agent', None) else 'N/A'

        writer.writerow([
            sale.id,
            sale.created_at.strftime('%d/%m/%Y %H:%M'),
            sale.pharmacy.name if sale.pharmacy else 'Globale',
            agent_name,
            sale.total_amount
        ])

    return response