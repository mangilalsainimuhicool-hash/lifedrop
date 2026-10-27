from lifedrop.models import AuditLog


def get_client_ip(request):
    """Safely extracts client IP address from standard and proxy headers."""
    if not request:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def record_audit(action, actor=None, details="", request=None, ip_address=None):
    """
    Records security-critical and operational actions into the audit log.
    """
    if request and not ip_address:
        ip_address = get_client_ip(request)
        if not actor and request.user.is_authenticated:
            actor = request.user

    return AuditLog.objects.create(
        action=action,
        actor=actor,
        details=details,
        ip_address=ip_address
    )
