from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

from lifedrop.models import (
    UserRole,
    DonorProfile,
    BloodRequest,
    RequestResponse,
    DonationRecord,
    Notification,
    AuditLog,
    RequestStatus,
)
from lifedrop.forms import DonationRecordForm
from lifedrop.services.audit import record_audit


@login_required
def dashboard_dispatcher(request):
    """Directs authenticated users to their specific functional dashboard."""
    user = request.user
    if user.is_hospital_staff or user.is_platform_admin:
        return redirect('staff_dashboard')
    elif user.is_donor:
        return redirect('donor_dashboard')
    else:
        return redirect('requester_dashboard')


@login_required
def donor_dashboard(request):
    """
    Donor Dashboard:
    - Availability switcher
    - Eligibility countdown tracker
    - Nearby urgent emergency requests matching donor's blood group
    - Responses given to requests
    - Donation history log
    """
    profile, _ = DonorProfile.objects.get_or_create(
        user=request.user,
        defaults={'city': 'Default', 'state': 'Default', 'blood_group': 'O+'}
    )

    # Emergency requests matching this donor's blood group and city
    matching_requests = BloodRequest.objects.filter(
        blood_group=profile.blood_group,
        hospital_city__iexact=profile.city.strip(),
        status__in=[RequestStatus.PENDING, RequestStatus.CONTACTED]
    ).order_by('-priority', '-created_at')[:8]

    # All active responses submitted by this donor
    my_responses = RequestResponse.objects.filter(
        donor=profile
    ).select_related('request').order_by('-responded_at')

    # Verified donation history
    donation_history = profile.donations.all().order_by('-donation_date')
    donation_form = DonationRecordForm()

    context = {
        'profile': profile,
        'matching_requests': matching_requests,
        'my_responses': my_responses,
        'donation_history': donation_history,
        'donation_form': donation_form,
    }
    return render(request, 'dashboards/donor_dashboard.html', context)


@login_required
def requester_dashboard(request):
    """
    Requester Dashboard:
    - Active blood requests posted by user
    - Live donor responses
    - Status management actions
    """
    my_requests = BloodRequest.objects.filter(
        requester=request.user
    ).prefetch_related('responses__donor__user').order_by('-created_at')

    active_count = my_requests.filter(status__in=[RequestStatus.PENDING, RequestStatus.CONTACTED]).count()
    fulfilled_count = my_requests.filter(status=RequestStatus.FULFILLED).count()

    context = {
        'my_requests': my_requests,
        'active_count': active_count,
        'fulfilled_count': fulfilled_count,
    }
    return render(request, 'dashboards/requester_dashboard.html', context)


@login_required
def staff_dashboard(request):
    """
    Healthcare Staff & Administrator Dashboard:
    - Donor verification queue
    - Platform-wide emergency requests overview
    - Comprehensive audit trail
    """
    if not (request.user.is_hospital_staff or request.user.is_platform_admin):
        messages.error(request, "Access restricted to certified healthcare staff and administrators.")
        return redirect('dashboard')

    pending_donors = DonorProfile.objects.filter(is_verified=False).select_related('user')[:15]
    active_requests = BloodRequest.objects.filter(
        status__in=[RequestStatus.PENDING, RequestStatus.CONTACTED]
    ).order_by('-priority', '-created_at')[:15]

    recent_audit_logs = AuditLog.objects.select_related('actor').order_by('-timestamp')[:35]

    context = {
        'pending_donors': pending_donors,
        'active_requests': active_requests,
        'recent_audit_logs': recent_audit_logs,
    }
    return render(request, 'dashboards/staff_dashboard.html', context)


@login_required
@require_POST
def add_donation_record(request):
    """Records a new donation entry and automatically updates the donor's last donation date."""
    if not hasattr(request.user, 'donor_profile'):
        messages.error(request, "Only registered blood donors can log donation history.")
        return redirect('dashboard')

    profile = request.user.donor_profile
    form = DonationRecordForm(request.POST)
    if form.is_valid():
        donation = form.save(commit=False)
        donation.donor = profile
        donation.save()

        # Update donor's last donation date if this record is more recent
        if not profile.last_donation_date or donation.donation_date > profile.last_donation_date:
            profile.last_donation_date = donation.donation_date
            profile.save()

        record_audit(
            action="DONATION_RECORD_LOGGED",
            actor=request.user,
            details=f"Donation logged by {request.user.username} at {donation.facility_name} on {donation.donation_date}.",
            request=request
        )

        messages.success(request, f"Donation at {donation.facility_name} recorded! Your eligibility calendar has been updated.")
    else:
        messages.error(request, "Could not save donation record. Please ensure the date is valid and not in the future.")

    return redirect('donor_dashboard')


@login_required
@require_POST
def verify_donor_staff_action(request, donor_id):
    """Allows staff or administrators to verify a donor profile."""
    if not (request.user.is_hospital_staff or request.user.is_platform_admin):
        messages.error(request, "Permission denied.")
        return redirect('dashboard')

    donor = get_object_or_404(DonorProfile, id=donor_id)
    donor.is_verified = True
    donor.save()

    record_audit(
        action="DONOR_VERIFIED_BY_STAFF",
        actor=request.user,
        details=f"Donor {donor.user.username} verified by staff member {request.user.username}.",
        request=request
    )

    messages.success(request, f"Donor {donor.user.get_full_name() or donor.user.username} has been verified.")
    return redirect('staff_dashboard')


@login_required
def mark_notification_read(request, notification_id):
    """Marks a single notification as read and redirects to its target link."""
    notif = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notif.is_read = True
    notif.save()
    if notif.link:
        return redirect(notif.link)
    return redirect('dashboard')
