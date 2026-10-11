# inventory/views.py
import csv
import io
from datetime import datetime, timedelta
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.db.models import F
from accounts.decorators import admin_required

from .models import Product
from .forms import ProductForm
from .utils import generate_invoice_pdf
from sales.models import Sale


def _get_user_pharmacy(user):
    """Helper interne pour récupérer la pharmacie de l'utilisateur."""
    return getattr(user, 'pharmacy', None)


def _get_alert_threshold(product):
    """Helper pour récupérer dynamiquement le seuil d'alerte du produit."""
    return (
            getattr(product, 'alert_threshold', None) or
            getattr(product, 'min_stock', None) or
            getattr(product, 'reorder_level', 5)
    )


# ==========================================
# J1 : VUES CRUD GESTION DU STOCK (ADMIN)
# ==========================================

@login_required
@admin_required
def product_list_create(request):
    """
    Vue principale Admin : affiche tous les produits, calcule la valeur globale du stock,
    le bénéfice potentiel et permet d'ajouter un nouveau produit.
    """
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            # Si le champ pharmacie n'a pas été sélectionné, on assigne celle de l'admin s'il en a une
            if not product.pharmacy and request.user.pharmacy:
                product.pharmacy = request.user.pharmacy

            if not product.pharmacy:
                messages.error(request, "Veuillez sélectionner une pharmacie d'affectation pour ce produit.")
            else:
                product.save()
                messages.success(request, f"Le produit '{product.name}' a été ajouté au stock avec succès.")
                return redirect('inventory:product_list_create')
    else:
        form = ProductForm()

    # Récupération des produits selon le périmètre de l'admin
    user_pharmacy = _get_user_pharmacy(request.user)
    if request.user.is_superuser or not user_pharmacy:
        products = Product.objects.all().select_related('pharmacy')
    else:
        products = Product.objects.filter(pharmacy=user_pharmacy).select_related('pharmacy')

    # Calculs consolidés en temps réel
    total_stock_value = sum(p.total_stock_value for p in products)
    total_potential_profit = sum(p.potential_stock_profit for p in products)

    context = {
        'form': form,
        'products': products,
        'total_stock_value': total_stock_value,
        'total_potential_profit': total_potential_profit,
    }
    return render(request, 'inventory/product_management.html', context)


@login_required
@admin_required
def edit_product(request, pk):
    """Permet à l'Admin de modifier les informations d'un produit."""
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f"Mise à jour réussie pour le produit '{product.name}'.")
            return redirect('inventory:product_list_create')
        else:
            messages.error(request, "Erreur dans la saisie du formulaire. Vérifiez les prix et quantités.")
    return redirect('inventory:product_list_create')


@login_required
@admin_required
def delete_product(request, pk):
    """Permet à l'Admin de supprimer un produit du stock."""
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f"Le produit '{name}' a été supprimé du stock.")
    return redirect('inventory:product_list_create')


# ==========================================
# IMPRESSION FACTURE & ALERTES
# ==========================================

@login_required
def print_invoice_view(request, sale_id):
    """Génère et affiche la facture PDF."""
    user_pharmacy = _get_user_pharmacy(request.user)

    if request.user.is_superuser:
        sale = get_object_or_404(Sale, id=sale_id)
    else:
        sale = get_object_or_404(Sale, id=sale_id, pharmacy=user_pharmacy)

    pdf_buffer = generate_invoice_pdf(sale)

    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Facture_BeckyPharma_{sale.id}.pdf"'
    return response


@login_required
def alerts_center_view(request):
    """Centre de notifications et d'alertes du stock isolés par pharmacie."""
    today = timezone.now().date()
    expiring_threshold = today + timedelta(days=30)

    # Isolation par Pharmacie (Multi-tenancy)
    if request.user.is_superuser:
        products_qs = Product.objects.all()
    elif hasattr(request.user, 'pharmacy') and request.user.pharmacy:
        products_qs = Product.objects.filter(pharmacy=request.user.pharmacy)
    else:
        products_qs = Product.objects.none()

    # 1. Ruptures de Stock
    alerts_out_of_stock = products_qs.filter(stock_quantity=0)

    # 2. Stock faible (Stock > 0 et Stock <= Seuil d'alerte)
    alerts_low_stock = products_qs.filter(
        stock_quantity__gt=0,
        stock_quantity__lte=F('alert_threshold')
    )

    # 3. Péremption proche (<= 30 jours) ou déjà dépassée
    alerts_expiring = products_qs.filter(
        expiration_date__isnull=False,
        expiration_date__lte=expiring_threshold
    ).order_by('expiration_date')

    total_alerts_count = (
            alerts_out_of_stock.count() +
            alerts_low_stock.count() +
            alerts_expiring.count()
    )

    context = {
        'today': today,
        'alerts_out_of_stock': alerts_out_of_stock,
        'alerts_low_stock': alerts_low_stock,
        'alerts_expiring': alerts_expiring,
        'total_alerts_count': total_alerts_count,
    }
    return render(request, 'inventory/alerts_center.html', context)


# ==========================================
# EXPORT DU STOCK ET ALERTES
# ==========================================

@login_required
@admin_required
def export_stock_csv(request):
    """Exporte l'état complet du stock et des alertes au format CSV / Excel."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="inventaire_stock_beckypharma.csv"'
    response.write(u'\ufeff'.encode('utf8'))  # Encodage Excel UTF-8

    writer = csv.writer(response, delimiter=';')
    writer.writerow([
        'ID', 'Médicament', 'Pharmacie', 'Prix Achat ($)',
        'Prix Vente ($)', 'Stock Actuel', 'Seuil Alerte',
        'Date Péremption', 'Statut Alerte'
    ])

    user_pharmacy = _get_user_pharmacy(request.user)

    if request.user.is_superuser or not user_pharmacy:
        products = Product.objects.all().select_related('pharmacy')
    else:
        products = Product.objects.filter(pharmacy=user_pharmacy).select_related('pharmacy')

    for p in products.order_by('name'):
        threshold = _get_alert_threshold(p)

        statut = "OK"
        if p.stock_quantity == 0:
            statut = "RUPTURE"
        elif p.stock_quantity <= threshold:
            statut = "STOCK BAS"

        writer.writerow([
            p.id,
            p.name,
            p.pharmacy.name if p.pharmacy else 'Globale',
            p.purchase_price,
            p.selling_price,
            p.stock_quantity,
            threshold,
            p.expiration_date.strftime('%d/%m/%Y') if getattr(p, 'expiration_date', None) else 'N/A',
            statut
        ])

    return response


# ==========================================
# IMPORTATION DE CATALOGUE CSV
# ==========================================

@login_required
@admin_required
def import_products_csv(request):
    """Permet d'importer des médicaments à partir d'un fichier CSV."""
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']

        if not csv_file.name.endswith('.csv'):
            messages.error(request, "Format incorrect : le fichier doit impérativement être un fichier .csv")
            return render(request, 'inventory/import_csv.html')

        user_pharmacy = _get_user_pharmacy(request.user)
        if not user_pharmacy and not request.user.is_superuser:
            messages.error(request, "Aucune pharmacie associée à votre compte.")
            return redirect('inventory:alerts_center')

        try:
            data_set = csv_file.read().decode('utf-8-sig')
            io_string = io.StringIO(data_set)

            first_line = io_string.readline()
            io_string.seek(0)
            delimiter = ';' if ';' in first_line else ','

            reader = csv.reader(io_string, delimiter=delimiter)

            header = next(reader, None)
            is_exported_format = False
            if header and len(header) > 1 and ('id' in header[0].lower() or 'médicament' in header[1].lower()):
                is_exported_format = True

            count = 0
            with transaction.atomic():
                for row_num, row in enumerate(reader, start=2):
                    if not row or not any(field.strip() for field in row):
                        continue

                    offset = 1 if is_exported_format else 0

                    if len(row) >= (5 + offset):
                        name = row[0 + offset].strip()

                        raw_purchase = row[2 + offset] if is_exported_format else row[1]
                        raw_selling = row[3 + offset] if is_exported_format else row[2]
                        raw_stock = row[4 + offset] if is_exported_format else row[3]
                        raw_alert = row[5 + offset] if is_exported_format else row[4]

                        purchase_price = float(raw_purchase.replace(',', '.').strip())
                        selling_price = float(raw_selling.replace(',', '.').strip())
                        stock_quantity = int(raw_stock.strip())
                        alert_threshold = int(raw_alert.strip())

                        expiration_date = None
                        date_col_idx = 7 if is_exported_format else 5

                        if len(row) > date_col_idx and row[date_col_idx].strip() and row[date_col_idx].strip() != 'N/A':
                            raw_date = row[date_col_idx].strip().split(' ')[0]
                            for fmt in ('%d/%m/%Y', '%Y-%m-%d'):
                                try:
                                    expiration_date = datetime.strptime(raw_date, fmt).date()
                                    break
                                except ValueError:
                                    pass

                        product_sample = Product()
                        alert_field_name = 'alert_threshold' if hasattr(product_sample, 'alert_threshold') else (
                            'min_stock' if hasattr(product_sample, 'min_stock') else 'reorder_level'
                        )

                        defaults = {
                            'purchase_price': purchase_price,
                            'selling_price': selling_price,
                            'stock_quantity': stock_quantity,
                            alert_field_name: alert_threshold,
                        }
                        if expiration_date and hasattr(product_sample, 'expiration_date'):
                            defaults['expiration_date'] = expiration_date

                        Product.objects.update_or_create(
                            name=name,
                            pharmacy=user_pharmacy,
                            defaults=defaults
                        )
                        count += 1

            messages.success(request, f"Succès : {count} médicament(s) importé(s) ou mis à jour avec succès !")
            return redirect('inventory:alerts_center')

        except Exception as e:
            messages.error(request, f"Erreur lors du traitement du fichier CSV : {str(e)}")

    return render(request, 'inventory/import_csv.html')

