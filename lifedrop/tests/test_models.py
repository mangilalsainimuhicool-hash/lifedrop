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
    AuditLog,
)


class ModelTests(TestCase):
    def setUp(self):
        self.donor_user = User.objects.create_user(
            username="test_donor",
            email="donor@example.com",
            password="TestPassword123!",
            role=UserRole.DONOR,
            phone_number="+91 98765 43210"
        )
        self.staff_user = User.objects.create_user(
            username="test_staff",
            email="staff@hospital.org",
            password="TestPassword123!",
            role=UserRole.HOSPITAL_STAFF,
            is_verified_staff=True
        )

    def test_user_roles(self):
        self.assertTrue(self.donor_user.is_donor)
        self.assertFalse(self.donor_user.is_hospital_staff)
        self.assertTrue(self.staff_user.is_hospital_staff)
        self.assertFalse(self.staff_user.is_requester)

    def test_donor_profile_eligibility(self):
        # Eligible donor (age >= 18, cooldown >= 90 days, weight >= 45)
        profile = DonorProfile.objects.create(
            user=self.donor_user,
            blood_group=BloodGroup.O_POS,
            city="Mumbai",
            state="Maharashtra",
            date_of_birth=date(1995, 1, 1),
            last_donation_date=date.today() - timedelta(days=100),
            weight_kg=70.0,
            is_available=True,
            consent_to_contact=True
        )
        self.assertTrue(profile.is_eligible)
        self.assertEqual(profile.eligibility_status_display, "Eligible to Donate")

        # Ineligible due to donation cooldown (< 90 days)
        profile.last_donation_date = date.today() - timedelta(days=30)
        profile.save()
        self.assertFalse(profile.is_eligible)
        self.assertIn("Cooldown", profile.eligibility_status_display)

        # Ineligible due to age (< 18)
        profile.last_donation_date = date.today() - timedelta(days=100)
        profile.date_of_birth = date.today() - timedelta(days=365 * 16)
        profile.save()
        self.assertFalse(profile.is_eligible)
        self.assertIn("Under 18", profile.eligibility_status_display)

    def test_blood_request_reference_id_generation(self):
        req = BloodRequest.objects.create(
            patient_name="Test Patient",
            blood_group=BloodGroup.A_POS,
            units_needed=2,
            hospital_name="City Hospital",
            hospital_city="Mumbai",
            hospital_address="123 Health Ave",
            contact_name="Family Member",
            contact_phone="+91 99999 88888",
            deadline=timezone.now() + timedelta(hours=6),
            priority=RequestPriority.URGENT,
            consent=True
        )
        self.assertTrue(req.reference_id.startswith("LD-"))
        self.assertFalse(req.is_expired)

    def test_audit_log_creation(self):
        log = AuditLog.objects.create(
            action="TEST_ACTION",
            actor=self.staff_user,
            details="Unit test audit entry",
            ip_address="127.0.0.1"
        )
        self.assertEqual(log.action, "TEST_ACTION")
        self.assertEqual(log.actor, self.staff_user)
