from datetime import date, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from lifedrop.models import (
    User,
    UserRole,
    DonorProfile,
    BloodRequest,
    BloodGroup,
    RequestPriority,
)


class PrivacyAndSecurityTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Create donor
        self.donor_user = User.objects.create_user(
            username="secure_donor",
            first_name="Rajesh",
            last_name="Khanna",
            password="SecurePass123!",
            role=UserRole.DONOR,
            phone_number="+91 98765 00000"
        )
        self.donor_profile = DonorProfile.objects.create(
            user=self.donor_user,
            blood_group=BloodGroup.B_POS,
            city="Bengaluru",
            state="Karnataka",
            address="Confidential Residential Flat 4B",
            date_of_birth=date(1990, 1, 1),
            is_available=True,
            consent_to_contact=True
        )

        # Create emergency request
        self.request_obj = BloodRequest.objects.create(
            patient_name="Anita Deshmukh",
            blood_group=BloodGroup.B_POS,
            units_needed=1,
            hospital_name="Fortis Hospital",
            hospital_city="Bengaluru",
            hospital_address="Bannerghatta Road",
            contact_name="Sanjay Deshmukh",
            contact_phone="+91 99887 76655",
            deadline=timezone.now() + timedelta(hours=5),
            priority=RequestPriority.URGENT,
            consent=True
        )

    def test_anonymous_donor_search_privacy(self):
        """Anonymous users must NEVER see private phone number or street address."""
        response = self.client.get(reverse('donor_search'))
        self.assertEqual(response.status_code, 200)

        # Phone number and residential address must NOT be in the rendered HTML
        self.assertNotContains(response, "+91 98765 00000")
        self.assertNotContains(response, "Confidential Residential Flat 4B")
        self.assertContains(response, "Log In to Contact")

    def test_anonymous_request_detail_masked_phone(self):
        """Anonymous visitor to request detail should see masked telephone."""
        response = self.client.get(reverse('request_detail', kwargs={'reference_id': self.request_obj.reference_id}))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "+91 99887 76655")
        self.assertContains(response, "Protected for privacy")

    def test_authenticated_donor_can_view_request_contact(self):
        """Logged-in donor can view emergency contact coordinates."""
        self.client.login(username="secure_donor", password="SecurePass123!")
        response = self.client.get(reverse('request_detail', kwargs={'reference_id': self.request_obj.reference_id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "+91 99887 76655")
        self.assertContains(response, "Call Now")

    def test_staff_dashboard_access_control(self):
        """Regular donors cannot access healthcare staff dashboard."""
        self.client.login(username="secure_donor", password="SecurePass123!")
        response = self.client.get(reverse('staff_dashboard'))
        # Should redirect to standard dashboard or home
        self.assertEqual(response.status_code, 302)
