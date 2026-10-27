from django.shortcuts import render, redirect
from django.contrib import messages
from lifedrop.models import BloodRequest, BloodBank, DonorProfile, RequestStatus
from lifedrop.services.audit import record_audit


def home(request):
    """
    LifeDrop Landing Page:
    - Hero section with urgent CTAs
    - Real-time urgent blood request ticker
    - Platform impact metrics (strictly derived from database counts)
    - How it works workflow
    - Quick eligibility checklist
    - Coordination & safety disclaimer
    """
    urgent_requests = BloodRequest.objects.filter(
        status__in=[RequestStatus.PENDING, RequestStatus.CONTACTED]
    ).order_by('-created_at')[:6]

    # Authentic system counters
    stats = {
        'total_requests': BloodRequest.objects.count(),
        'fulfilled_requests': BloodRequest.objects.filter(status=RequestStatus.FULFILLED).count(),
        'registered_donors': DonorProfile.objects.filter(is_available=True).count(),
        'blood_banks_count': BloodBank.objects.filter(is_verified=True).count(),
    }

    context = {
        'urgent_requests': urgent_requests,
        'stats': stats,
    }
    return render(request, 'home.html', context)


def about(request):
    """Platform mission, coordination principles, and donor advocacy."""
    return render(request, 'about.html')


def contact(request):
    """Contact & support desk page."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()

        if name and email and message:
            record_audit(
                action="SUPPORT_INQUIRY_SUBMITTED",
                actor=request.user if request.user.is_authenticated else None,
                details=f"Inquiry from {name} ({email}) - Subject: {subject}",
                request=request
            )
            messages.success(
                request,
                "Thank you for contacting LifeDrop Support. Our coordination team will review your query shortly."
            )
            return redirect('contact')
        else:
            messages.error(request, "Please fill in all required fields.")

    return render(request, 'contact.html')


def eligibility_guide(request):
    """Detailed donor eligibility and deferral criteria."""
    return render(request, 'eligibility.html')


def privacy_policy(request):
    """Privacy and health information handling principles."""
    return render(request, 'privacy.html')


def terms_of_service(request):
    """Platform terms, volunteer conditions, and clinical disclaimers."""
    return render(request, 'terms.html')
