"""
LifeDrop Donor Matching Service

Implements strict exact-group matching and geographic proximity filtering.
Enforces that coordination NEVER assumes clinical cross-matching compatibility.
"""

from lifedrop.models import DonorProfile, BloodRequest, RequestStatus

CLINICAL_DISCLAIMER = (
    "LifeDrop acts purely as a volunteer coordination bridge. "
    "Exact blood group matching is filtered here for donor notification. "
    "Platform coordination is NEVER a substitute for certified laboratory cross-matching, "
    "infectious marker screening, and clinical pre-transfusion verification."
)


def find_matching_donors(blood_request, same_city_only=True):
    """
    Finds verified/active voluntary donors matching the exact blood group of the request.
    Applies city-based proximity filter and clinical donation cooldown rules.
    """
    if blood_request.status not in [RequestStatus.PENDING, RequestStatus.CONTACTED]:
        return DonorProfile.objects.none()

    # Exact blood group filter + availability + consent
    queryset = DonorProfile.objects.filter(
        blood_group=blood_request.blood_group,
        is_available=True,
        consent_to_contact=True,
    ).select_related('user')

    if same_city_only and blood_request.hospital_city:
        queryset = queryset.filter(city__iexact=blood_request.hospital_city.strip())

    # Filter out donors who are in 90-day cooldown or under 18
    eligible_donor_ids = [
        donor.id for donor in queryset if donor.is_eligible
    ]

    return DonorProfile.objects.filter(id__in=eligible_donor_ids).select_related('user')


def get_compatibility_notice():
    return CLINICAL_DISCLAIMER
