from lifedrop.models import Notification, DonorProfile


def send_notification(recipient, title, message, link=""):
    """
    Creates an in-app notification for a given user.
    """
    if not recipient or not recipient.is_authenticated:
        return None
    return Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        link=link
    )


def notify_matching_donors(blood_request):
    """
    Finds matching available donors for an emergency request and dispatches
    in-app notifications to each eligible registered donor.
    """
    from .matching import find_matching_donors

    matches = find_matching_donors(blood_request)
    notified_count = 0

    for donor in matches:
        title = f"EMERGENCY: {blood_request.blood_group} Blood Needed in {blood_request.hospital_city}"
        message = (
            f"Urgent request ({blood_request.reference_id}) at {blood_request.hospital_name}. "
            f"Units needed: {blood_request.units_needed}. Priority: {blood_request.get_priority_display()}."
        )
        link = blood_request.get_absolute_url()
        send_notification(recipient=donor.user, title=title, message=message, link=link)
        notified_count += 1

    return notified_count
