from .models import Notification, BloodGroup


def global_context(request):
    """
    Context processor injecting brand metadata and user notification state across all templates.
    """
    context = {
        'BRAND_NAME': 'LifeDrop',
        'BRAND_TAGLINE': 'Every Drop Counts. Every Second Matters.',
        'BLOOD_GROUPS': BloodGroup.choices,
        'unread_notifications_count': 0,
        'recent_notifications': [],
    }

    if request.user.is_authenticated:
        user_notifications = Notification.objects.filter(recipient=request.user)
        context['unread_notifications_count'] = user_notifications.filter(is_read=False).count()
        context['recent_notifications'] = user_notifications[:5]

    return context
