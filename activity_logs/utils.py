from .models import ActivityLog

def log_activity(user, action_type, description):
    """
    Helper pour enregistrer une activité dans le journal d'activités.
    """
    pharmacy = getattr(user, 'pharmacy', None) if user and user.is_authenticated else None

    ActivityLog.objects.create(
        user=user if user and user.is_authenticated else None,
        pharmacy=pharmacy,
        action_type=action_type,
        description=description
    )