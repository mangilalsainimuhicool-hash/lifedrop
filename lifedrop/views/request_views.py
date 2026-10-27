from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator

from lifedrop.models import (
    BloodRequest,
    RequestResponse,
    RequestStatus,
    ResponseStatus,
    BloodGroup,
    RequestPriority,
)
from lifedrop.forms import BloodRequestForm, RequestResponseForm, RequestStatusUpdateForm
from lifedrop.services.matching import find_matching_donors, get_compatibility_notice
from lifedrop.services.notifications import notify_matching_donors, send_notification
from lifedrop.services.audit import record_audit


def request_create(request):
    """
    Emergency Blood Request Submission:
    - Server-side validation
    - Auto-generated unique Reference ID
    - Donor notification dispatching
    - Audit tracking
    """
    if request.method == 'POST':
        form = BloodRequestForm(request.POST)
        if form.is_valid():
            blood_req = form.save(commit=False)
            if request.user.is_authenticated:
                blood_req.requester = request.user
            blood_req.save()

            # Record security audit
            record_audit(
                action="BLOOD_REQUEST_CREATED",
                actor=request.user if request.user.is_authenticated else None,
                details=(
                    f"Request {blood_req.reference_id} created for {blood_req.blood_group} "
                    f"({blood_req.units_needed} units) at {blood_req.hospital_name}, {blood_req.hospital_city}."
                ),
                request=request
            )

            # Dispatch in-app notifications to eligible registered donors
            notified_count = notify_matching_donors(blood_req)

            messages.success(
                request,
                f"Emergency Blood Request logged successfully! Reference ID: {blood_req.reference_id}. "
                f"{notified_count} matching voluntary donor(s) in {blood_req.hospital_city} have been notified."
            )
            return redirect('request_detail', reference_id=blood_req.reference_id)
        else:
            messages.error(request, "Please review and correct the errors below to submit the request.")
    else:
        initial_data = {}
        if request.user.is_authenticated:
            initial_data['contact_name'] = request.user.get_full_name() or request.user.username
            initial_data['contact_phone'] = getattr(request.user, 'phone_number', '')
        form = BloodRequestForm(initial=initial_data)

    return render(request, 'requests/request_create.html', {
        'form': form,
        'clinical_disclaimer': get_compatibility_notice()
    })


def request_detail(request, reference_id):
    """
    Detailed status and tracking page for a specific emergency blood request.
    Applies privacy mask on contact phone for anonymous users.
    """
    blood_req = get_object_or_404(BloodRequest, reference_id=reference_id)

    # Privacy mask: anonymous users see masked phone
    is_authorized = (
        request.user.is_authenticated and (
            request.user == blood_req.requester or
            request.user.is_hospital_staff or
            request.user.is_platform_admin or
            request.user.is_donor
        )
    )

    if not is_authorized and blood_req.contact_phone:
        raw = blood_req.contact_phone.strip()
        if len(raw) > 5:
            masked_phone = raw[:3] + ("*" * (len(raw) - 5)) + raw[-2:]
        else:
            masked_phone = "****"
    else:
        masked_phone = blood_req.contact_phone

    # Matching donors count (for display)
    matching_donors = find_matching_donors(blood_req)
    responses = blood_req.responses.select_related('donor__user').all()

    # Donor response eligibility
    can_respond = False
    existing_response = None
    if request.user.is_authenticated and hasattr(request.user, 'donor_profile'):
        can_respond = blood_req.status in [RequestStatus.PENDING, RequestStatus.CONTACTED]
        existing_response = responses.filter(donor=request.user.donor_profile).first()

    response_form = RequestResponseForm() if can_respond else None

    # Status update form for requester or hospital staff
    can_update_status = (
        request.user.is_authenticated and (
            request.user == blood_req.requester or
            request.user.is_hospital_staff or
            request.user.is_platform_admin
        )
    )
    status_form = RequestStatusUpdateForm(instance=blood_req) if can_update_status else None

    context = {
        'req': blood_req,
        'masked_phone': masked_phone,
        'is_authorized': is_authorized,
        'matching_donors_count': matching_donors.count(),
        'responses': responses,
        'can_respond': can_respond,
        'existing_response': existing_response,
        'response_form': response_form,
        'can_update_status': can_update_status,
        'status_form': status_form,
        'clinical_disclaimer': get_compatibility_notice(),
    }
    return render(request, 'requests/request_detail.html', context)


def request_track(request):
    """
    Search and track an emergency request by reference ID.
    """
    query = request.GET.get('ref', '').strip()
    if query:
        # Check case-insensitive
        req = BloodRequest.objects.filter(reference_id__iexact=query).first()
        if req:
            return redirect('request_detail', reference_id=req.reference_id)
        else:
            messages.warning(request, f"No emergency blood request found with reference ID '{query}'.")

    return render(request, 'requests/request_track.html')


def request_list(request):
    """
    Browse active blood requests with filter criteria and pagination.
    """
    queryset = BloodRequest.objects.all().order_by('-created_at')

    blood_group = request.GET.get('blood_group', '').strip()
    city = request.GET.get('city', '').strip()
    status = request.GET.get('status', '').strip()
    priority = request.GET.get('priority', '').strip()

    if blood_group:
        queryset = queryset.filter(blood_group=blood_group)
    if city:
        queryset = queryset.filter(hospital_city__icontains=city)
    if status:
        queryset = queryset.filter(status=status)
    else:
        # Default to active requests (PENDING, CONTACTED)
        queryset = queryset.filter(status__in=[RequestStatus.PENDING, RequestStatus.CONTACTED])
    if priority:
        queryset = queryset.filter(priority=priority)

    paginator = Paginator(queryset, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'blood_groups': BloodGroup.choices,
        'priorities': RequestPriority.choices,
        'statuses': RequestStatus.choices,
        'selected_blood_group': blood_group,
        'selected_city': city,
        'selected_status': status,
        'selected_priority': priority,
    }
    return render(request, 'requests/request_list.html', context)


@login_required
def request_update_status(request, reference_id):
    """Update status of a blood request by its requester, hospital staff, or admin."""
    blood_req = get_object_or_404(BloodRequest, reference_id=reference_id)

    can_update = (
        request.user == blood_req.requester or
        request.user.is_hospital_staff or
        request.user.is_platform_admin
    )
    if not can_update:
        messages.error(request, "You do not have permission to modify this emergency request.")
        return redirect('request_detail', reference_id=blood_req.reference_id)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        status_note = request.POST.get('notes', '').strip()

        if new_status in RequestStatus.values:
            old_status = blood_req.status
            blood_req.status = new_status
            if status_note:
                blood_req.notes = f"{blood_req.notes}\n[Status Update]: {status_note}".strip()
            blood_req.save()

            record_audit(
                action="BLOOD_REQUEST_STATUS_UPDATED",
                actor=request.user,
                details=f"Request {blood_req.reference_id} status changed from {old_status} to {new_status}.",
                request=request
            )

            # Notify requester if changed by staff
            if blood_req.requester and blood_req.requester != request.user:
                send_notification(
                    recipient=blood_req.requester,
                    title=f"Update on Blood Request {blood_req.reference_id}",
                    message=f"Your blood request status has been updated to: {blood_req.get_status_display()}.",
                    link=blood_req.get_absolute_url()
                )

            messages.success(request, f"Request status updated to {blood_req.get_status_display()}.")
        else:
            messages.error(request, "Invalid status choice selected.")

    return redirect('request_detail', reference_id=blood_req.reference_id)


@login_required
def request_respond(request, reference_id):
    """Allows an eligible donor to record their willingness to donate."""
    blood_req = get_object_or_404(BloodRequest, reference_id=reference_id)

    if not hasattr(request.user, 'donor_profile'):
        messages.error(request, "Only registered blood donors can submit donation responses.")
        return redirect('donor_register')

    donor_profile = request.user.donor_profile

    if request.method == 'POST':
        form = RequestResponseForm(request.POST)
        if form.is_valid():
            response_obj, created = RequestResponse.objects.update_or_create(
                request=blood_req,
                donor=donor_profile,
                defaults={
                    'response_status': form.cleaned_data['response_status'],
                    'message': form.cleaned_data['message'],
                }
            )

            # Auto-advance request status to CONTACTED if it was PENDING
            if blood_req.status == RequestStatus.PENDING:
                blood_req.status = RequestStatus.CONTACTED
                blood_req.save()

            record_audit(
                action="DONOR_RESPONDED_TO_REQUEST",
                actor=request.user,
                details=f"Donor {donor_profile} responded with status '{response_obj.response_status}' to request {blood_req.reference_id}.",
                request=request
            )

            # Notify the requester if available
            if blood_req.requester:
                send_notification(
                    recipient=blood_req.requester,
                    title=f"Donor Response Received for Request {blood_req.reference_id}",
                    message=f"Volunteer donor {request.user.first_name} has responded with: {response_obj.get_response_status_display()}.",
                    link=blood_req.get_absolute_url()
                )

            messages.success(
                request,
                f"Thank you for responding! The requester has been notified of your response ({response_obj.get_response_status_display()})."
            )
        else:
            messages.error(request, "Could not record response. Please check your inputs.")

    return redirect('request_detail', reference_id=blood_req.reference_id)
