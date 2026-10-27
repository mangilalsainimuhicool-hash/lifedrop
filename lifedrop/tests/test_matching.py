from datetime import date, timedelta
from django.test import TestCase
from django.utils import timezone
from lifedrop.models import (
    User,
    UserRole,
    DonorProfile,
    BloodRequest,
    BloodGroup,
    RequestPriority,
    RequestStatus,
)
from lifedrop.services.matching import find_matching_donors, get_compatibility_notice


class MatchingServiceTests(TestCase):
    def setUp(self):
        # Donor 1: Matching O+, in Mumbai, eligible
        user1 = User.objects.create_user(username="mumbai_o_pos", password="Pass123!", role=UserRole.DONOR)
        self.donor_match = DonorProfile.objects.create(
            user=user1,
            blood_group=BloodGroup.O_POS,
            city="Mumbai",
            state="Maharashtra",
            date_of_birth=date(1990, 5, 10),
            last_donation_date=date.today() - timedelta(days=120),
            is_available=True,
            consent_to_contact=True,
            weight_kg=65.0
        )

        # Donor 2: O+, but in Delhi (different city)
        user2 = User.objects.create_user(username="delhi_o_pos", password="Pass123!", role=UserRole.DONOR)
        self.donor_diff_city = DonorProfile.objects.create(
            user=user2,
            blood_group=BloodGroup.O_POS,
            city="New Delhi",
            state="Delhi",
            date_of_birth=date(1992, 4, 15),
            last_donation_date=date.today() - timedelta(days=120),
            is_available=True,
            consent_to_contact=True,
            weight_kg=70.0
        )

        # Donor 3: In Mumbai, but A+ (different blood group)
        user3 = User.objects.create_user(username="mumbai_a_pos", password="Pass123!", role=UserRole.DONOR)
        self.donor_diff_group = DonorProfile.objects.create(
            user=user3,
            blood_group=BloodGroup.A_POS,
            city="Mumbai",
            state="Maharashtra",
            date_of_birth=date(1993, 8, 20),
            last_donation_date=date.today() - timedelta(days=120),
            is_available=True,
            consent_to_contact=True,
            weight_kg=68.0
        )

        # Donor 4: In Mumbai, O+, but unavailable
        user4 = User.objects.create_user(username="mumbai_o_unavailable", password="Pass123!", role=UserRole.DONOR)
        self.donor_unavailable = DonorProfile.objects.create(
            user=user4,
            blood_group=BloodGroup.O_POS,
            city="Mumbai",
            state="Maharashtra",
            date_of_birth=date(1991, 2, 22),
            last_donation_date=date.today() - timedelta(days=120),
            is_available=False,
            consent_to_contact=True,
            weight_kg=65.0
        )

        # Blood Request: O+ in Mumbai
        self.request_o_mumbai = BloodRequest.objects.create(
            patient_name="Pooja Sharma",
            blood_group=BloodGroup.O_POS,
            units_needed=2,
            hospital_name="Apollo Hospital",
            hospital_city="Mumbai",
            hospital_address="Sector 12, Navi Mumbai",
            contact_name="Coordinator",
            contact_phone="+91 91234 56789",
            deadline=timezone.now() + timedelta(hours=8),
            priority=RequestPriority.URGENT,
            consent=True,
            status=RequestStatus.PENDING
        )

    def test_exact_group_and_proximity_matching(self):
        matches = find_matching_donors(self.request_o_mumbai, same_city_only=True)
        self.assertEqual(matches.count(), 1)
        self.assertEqual(matches.first(), self.donor_match)

    def test_matching_cross_city(self):
        matches_all_cities = find_matching_donors(self.request_o_mumbai, same_city_only=False)
        self.assertEqual(matches_all_cities.count(), 2)
        self.assertIn(self.donor_match, matches_all_cities)
        self.assertIn(self.donor_diff_city, matches_all_cities)

    def test_clinical_notice_present(self):
        notice = get_compatibility_notice()
        self.assertIn("NEVER a substitute for certified laboratory cross-matching", notice)
