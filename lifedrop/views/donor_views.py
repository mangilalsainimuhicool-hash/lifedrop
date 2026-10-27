import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from lifedrop.models import DonorProfile, BloodGroup
from lifedrop.forms import DonorProfileForm, DonorSearchForm
from lifedrop.services.audit import record_audit
from lifedrop.services.notifications import send_notification


@login_required
def donor_register(request):
    """Register or update voluntary donor profile."""
    # Check if donor profile already exists for this user
    profile, created = DonorProfile.objects.get_or_create(
        user=request.user,
        defaults={
            'city': 'Unknown',
            'state': 'Unknown',
            'blood_group': BloodGroup.O_POS,
        }
    )

    if request.method == 'POST':
        form = DonorProfileForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save()
            record_audit(
                action="DONOR_PROFILE_SAVED",
                actor=request.user,
                details=f"Donor profile updated for {request.user.username} (Group: {profile.blood_group}, City: {profile.city}).",
                request=request
            )
            messages.success(request, "Your voluntary donor profile has been updated and active matching is enabled!")
            return redirect('donor_dashboard')
        else:
            messages.error(request, "Please resolve the errors in the profile form.")
    else:
        form = DonorProfileForm(instance=profile)

    return render(request, 'donors/donor_register.html', {
        'form': form,
        'profile': profile,
        'created': created
    })


def donor_search(request):
    """
    Search voluntary donors with filters for blood group, city, and availability.
    Strict privacy controls: Anonymous visitors cannot access direct phone numbers or private addresses.
    """
    form = DonorSearchForm(request.GET)
    queryset = DonorProfile.objects.select_related('user').filter(consent_to_contact=True).order_by('-is_available', '-is_verified', 'city')

    blood_group = request.GET.get('blood_group', '').strip()
    city = request.GET.get('city', '').strip()
    only_available = request.GET.get('only_available')

    if blood_group:
        queryset = queryset.filter(blood_group=blood_group)
    if city:
        queryset = queryset.filter(city__icontains=city)
    if only_available or 'only_available' not in request.GET:
        queryset = queryset.filter(is_available=True)

    paginator = Paginator(queryset, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'form': form,
        'page_obj': page_obj,
        'selected_blood_group': blood_group,
        'selected_city': city,
        'is_anonymous_viewer': not request.user.is_authenticated,
    }
    return render(request, 'donors/donor_search.html', context)


def donor_detail(request, pk):
    """
    Public/Authorized profile view for a specific donor.
    Protects private contact information if visitor is unauthenticated.
    """
    donor = get_object_or_404(DonorProfile.objects.select_related('user'), pk=pk)

    is_authorized = (
        request.user.is_authenticated and (
            request.user == donor.user or
            request.user.is_hospital_staff or
            request.user.is_platform_admin or
            request.user.is_requester
        )
    )

    donations_count = donor.donations.filter(is_verified=True).count()

    context = {
        'donor': donor,
        'is_authorized': is_authorized,
        'donations_count': donations_count,
    }
    return render(request, 'donors/donor_detail.html', context)


@login_required
@require_POST
def toggle_availability_api(request):
    """
    Interactive API for donor to toggle their availability status in real-time.
    """
    if not hasattr(request.user, 'donor_profile'):
        return JsonResponse({'success': False, 'error': 'Donor profile not found'}, status=404)

    donor = request.user.donor_profile
    donor.is_available = not donor.is_available
    donor.save()

    record_audit(
        action="DONOR_AVAILABILITY_TOGGLED",
        actor=request.user,
        details=f"Donor {donor} toggled availability to {donor.is_available}.",
        request=request
    )

    return JsonResponse({
        'success': True,
        'is_available': donor.is_available,
        'status_text': "Available for Donation" if donor.is_available else "Temporarily Unavailable"
    })
