from django.contrib import admin
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'pharmacy', 'stock_quantity', 'purchase_price',
        'selling_price', 'get_unit_profit', 'expiration_date', 'get_status'
    )
    list_filter = ('pharmacy', 'expiration_date')
    search_fields = ('name', 'pharmacy__name')
    ordering = ('name',)

    # ==========================================
    # SÉCURITÉ MULTI-TENANCY (J9)
    # ==========================================

    def get_queryset(self, request):
        """Filtre les produits : le Superadmin voit tout, le gérant ne voit que sa pharmacie."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs

        user_pharmacy = getattr(request.user, 'pharmacy', None)
        if user_pharmacy:
            return qs.filter(pharmacy=user_pharmacy)

        return qs.none()

    def save_model(self, request, obj, form, change):
        """Associe automatiquement le produit à la pharmacie de l'utilisateur s'il n'est pas Superadmin."""
        if not request.user.is_superuser:
            user_pharmacy = getattr(request.user, 'pharmacy', None)
            if user_pharmacy:
                obj.pharmacy = user_pharmacy
        super().save_model(request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        """Masque ou désactive le champ 'pharmacy' pour un gérant ordinaire."""
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser and 'pharmacy' in form.base_fields:
            # Masque le champ pour éviter qu'il change la pharmacie manuellement
            form.base_fields['pharmacy'].required = False
            form.base_fields['pharmacy'].widget = admin.widgets.AdminTextareaWidget(attrs={'hidden': True})
        return form

    # ==========================================
    # AFFICHAGE PERSONNALISÉ
    # ==========================================

    @admin.display(description='Bénéfice Unitaire')
    def get_unit_profit(self, obj):
        return f"{obj.unit_profit} FCFA/CDF"

    @admin.display(description='État Stock')
    def get_status(self, obj):
        if obj.is_out_of_stock:
            return "❌ Rupture"
        elif obj.is_low_stock:
            return "⚠️ Stock Faible"
        elif obj.is_near_expiration:
            return "⌛ Péremption Imminente"
        return "✅ Bon"