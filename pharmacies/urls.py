# pharmacies/urls.py
from django.urls import path
from . import views

app_name = 'pharmacies'

urlpatterns = [
    path('manage/', views.pharmacy_list_create, name='pharmacy_list_create'),
    path('<int:pk>/edit/', views.edit_pharmacy, name='edit_pharmacy'),
    path('<int:pk>/delete/', views.delete_pharmacy, name='delete_pharmacy'),

    path('agents/create/', views.create_agent, name='create_agent'),
    path('agents/<int:pk>/edit/', views.edit_agent, name='edit_agent'),
    path('agents/<int:pk>/delete/', views.delete_agent, name='delete_agent'),

    path('cash/open/', views.open_cash_register, name='open_cash_register'),
    path('cash/close/', views.close_cash_register, name='close_cash_register'),
]

