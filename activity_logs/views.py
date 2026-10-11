from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from accounts.decorators import admin_required  # 👈 Import J11
from .models import ActivityLog


@login_required
@admin_required  # 👈 Protection J11 : Réservé aux Administrateurs
def activity_log_list(request):
    """Affiche le journal d'activités filtré par pharmacie (Accès Admin uniquement)."""
    user_pharmacy = getattr(request.user, 'pharmacy', None)

    # Superadmin voit tout, l'admin local voit sa pharmacie
    if request.user.is_superuser or not user_pharmacy:
        logs = ActivityLog.objects.all()
    else:
        logs = ActivityLog.objects.filter(pharmacy=user_pharmacy)

    # Filtre optionnel par type d'action
    action_filter = request.GET.get('action')
    if action_filter:
        logs = logs.filter(action_type=action_filter)

    context = {
        'logs': logs[:100],  # Limite aux 100 dernières actions
        'selected_action': action_filter or '',
        'action_choices': ActivityLog.ActionType.choices
    }
    return render(request, 'activity_logs/log_list.html', context)