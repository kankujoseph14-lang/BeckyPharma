from django.urls import path
from .views import CustomLoginView, CustomLogoutView, AdminSetupView

app_name = 'accounts'

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('setup/', AdminSetupView.as_view(), name='setup'),
]