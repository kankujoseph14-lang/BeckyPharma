from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    # Redirige la racine (/) vers la page de connexion accounts/login/
    path('', lambda request: redirect('accounts:login')),

    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('pharmacies/', include('pharmacies.urls')),
    path('inventory/', include('inventory.urls')),
    path('sales/', include('sales.urls')),
    path('logs/', include('activity_logs.urls')),  # <-- Ligne ajoutée pour le journal d'activités
]