from django.contrib import admin
from .models import Pharmacy, CashRegister

@admin.register(Pharmacy)
class PharmacyAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'address', 'created_at')
    search_fields = ('name', 'phone')


@admin.register(CashRegister)
class CashRegisterAdmin(admin.ModelAdmin):
    list_display = (
        'pharmacy', 'agent', 'status', 'opening_amount',
        'get_theoretical', 'closing_amount_real', 'get_gap', 'opened_at', 'closed_at'
    )
    list_filter = ('status', 'pharmacy', 'opened_at')
    search_fields = ('agent__username', 'pharmacy__name')
    readonly_fields = ('opened_at',)

    @admin.display(description='Théorique')
    def get_theoretical(self, obj):
        return f"{obj.theoretical_amount} FCFA/CDF"

    @admin.display(description='Écart')
    def get_gap(self, obj):
        gap = obj.gap_amount
        return f"{gap} FCFA/CDF" if gap != 0 else "0"

