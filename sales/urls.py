from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    # Routes du Terminal POS (J3)
    path('pos/', views.pos_terminal, name='pos_terminal'),
    path('api/search/', views.search_products, name='search_products'),
    path('api/complete-sale/', views.complete_sale, name='complete_sale'),

    # Routes de l'Historique et des Reçus (J4)
    path('history/', views.sales_history, name='sales_history'),
    path('detail/<int:sale_id>/', views.sale_detail, name='sale_detail'),

    # Impression Facture PDF (J5)
    path('sale/<int:sale_id>/pdf/', views.print_invoice_view, name='print_invoice'),

    # Analytics & Tableau de bord (J7)
    path('analytics/', views.dashboard_analytics_view, name='analytics_dashboard'),

    # Exportation CSV / Excel des ventes (J12)
    path('export/csv/', views.export_sales_csv, name='export_sales_csv'),
]