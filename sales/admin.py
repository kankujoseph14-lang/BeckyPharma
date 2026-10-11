from django.contrib import admin
from .models import Sale, SaleItem, Credit


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'unit_price', 'unit_purchase_price', 'total_price')

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'pharmacy', 'agent', 'total_amount', 'total_profit', 'is_credit', 'created_at')
    list_filter = ('pharmacy', 'is_credit', 'created_at')
    search_fields = ('agent__username', 'id')
    inlines = [SaleItemInline]
    readonly_fields = ('created_at',)

    # ==========================================
    # SÉCURITÉ MULTI-TENANCY (J9)
    # ==========================================

    def get_queryset(self, request):
        """Le Superadmin voit toutes les ventes, un gérant ne voit que celles de sa pharmacie."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs

        user_pharmacy = getattr(request.user, 'pharmacy', None)
        if user_pharmacy:
            return qs.filter(pharmacy=user_pharmacy)

        return qs.none()

    def has_add_permission(self, request):
        """Les ventes doivent passer par le POS, pas par l'Admin."""
        return request.user.is_superuser


@admin.register(Credit)
class CreditAdmin(admin.ModelAdmin):
    list_display = ('client_name', 'get_pharmacy', 'get_amount', 'is_paid', 'paid_at')
    list_filter = ('is_paid', 'sale__pharmacy')
    search_fields = ('client_name', 'reason')

    # ==========================================
    # SÉCURITÉ MULTI-TENANCY (J9)
    # ==========================================

    def get_queryset(self, request):
        """Filtrage des crédits par la pharmacie de la vente associée."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs

        user_pharmacy = getattr(request.user, 'pharmacy', None)
        if user_pharmacy:
            return qs.filter(sale__pharmacy=user_pharmacy)

        return qs.none()

    # ==========================================
    # AFFICHAGE PERSONNALISÉ
    # ==========================================

    @admin.display(description='Pharmacie')
    def get_pharmacy(self, obj):
        return obj.sale.pharmacy.name if obj.sale and obj.sale.pharmacy else "-"

    @admin.display(description='Montant Crédit')
    def get_amount(self, obj):
        return f"{obj.sale.total_amount} FCFA/CDF" if obj.sale else "0 FCFA/CDF"