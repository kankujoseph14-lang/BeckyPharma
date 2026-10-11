from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'role', 'pharmacy', 'is_staff', 'is_active')
    list_filter = ('role', 'pharmacy', 'is_staff')

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informations BeckyPharma', {'fields': ('role', 'pharmacy')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Informations BeckyPharma', {'fields': ('role', 'pharmacy')}),
    )

    def save_model(self, request, obj, form, change):
        # Si c'est un agent, on s'assure qu'il n'a pas d'accès staff au Django Admin
        if obj.role == User.Role.AGENT:
            obj.is_staff = False
        elif obj.role == User.Role.ADMIN:
            obj.is_staff = True
        super().save_model(request, obj, form, change)

