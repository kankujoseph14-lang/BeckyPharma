
from django.urls import path
from .views import activity_log_list

app_name = 'activity_logs'

urlpatterns = [
    path('', activity_log_list, name='log_list'),
]