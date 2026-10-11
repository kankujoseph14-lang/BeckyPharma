# inventory/urls.py
from django.urls import path
from . import views

app_name = 'inventory'  # Namespace de l'application

urlpatterns = [
    # Routes J1 - Gestion CRUD des Stocks (Admin)
    path('', views.product_list_create, name='product_list_create'),
    path('product/<int:pk>/edit/', views.edit_product, name='edit_product'),
    path('product/<int:pk>/delete/', views.delete_product, name='delete_product'),

    # Route J9 - Impression de facture PDF
    path('invoice/<int:sale_id>/pdf/', views.print_invoice_view, name='print_invoice'),

    # Route Centre d'alertes
    path('alerts/', views.alerts_center_view, name='alerts_center'),

    # Routes J12 (Export & Import CSV)
    path('export/csv/', views.export_stock_csv, name='export_stock_csv'),
    path('import/csv/', views.import_products_csv, name='import_products_csv'),
]

