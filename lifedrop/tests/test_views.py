import json
from datetime import date, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from lifedrop.models import (
    User,
    UserRole,
    DonorProfile,
    BloodRequest,
    BloodBank,
    BloodGroup,
    RequestPriority,
)


class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Seed test donor user
        self.donor_user = User.objects.create_user(
            username="test_donor_view",
            password="Password123!",
            role=UserRole.DONOR,
            phone_number="+91 99999 11111"
        )
        self.profile = DonorProfile.objects.create(
            user=self.donor_user,
            blood_group=BloodGroup.O_POS,
            city="Pune",
            state="Maharashtra",
            date_of_birth=date(1995, 1, 1),
            is_available=True,
            consent_to_contact=True
        )

        # Seed sample blood bank
        self.bank = BloodBank.objects.create(
            name="Pune Red Cross Blood Bank",
            city="Pune",
            state="Maharashtra",
            address="Camp, Pune",
            latitude=18.5204,
            longitude=73.8567,
            contact_phone="+91 20 2612 0000",
            is_verified=True
        )

    def test_home_page_renders_successfully(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Every Drop Counts")
        self.assertIn('stats', response.context)

    def test_emergency_request_creation(self):
        post_data = {
            'patient_name': 'Sumanth K',
            'blood_group': BloodGroup.O_POS,
            'units_needed': 1,
            'priority': RequestPriority.URGENT,
            'hospital_name': 'Ruby Hall Clinic',
            'hospital_city': 'Pune',
            'hospital_address': 'Sassoon Road, Pune',
            'contact_name': 'Ramesh K',
            'contact_phone': '+91 98220 33445',
            'deadline': (timezone.now() + timedelta(hours=4)).strftime('%Y-%m-%dT%H:%M'),
            'consent': True,
        }
        response = self.client.post(reverse('request_create'), data=post_data)
        self.assertEqual(response.status_code, 302)
        created_req = BloodRequest.objects.filter(patient_name='Sumanth K').first()
        self.assertIsNotNone(created_req)
        self.assertTrue(created_req.reference_id.startswith('LD-'))

    def test_donor_availability_toggle_api(self):
        self.client.login(username="test_donor_view", password="Password123!")
        self.assertTrue(self.profile.is_available)

        response = self.client.post(reverse('toggle_availability_api'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertFalse(data['is_available'])

        self.profile.refresh_from_db()
        self.assertFalse(self.profile.is_available)

    def test_bloodbank_directory_view(self):
        response = self.client.get(reverse('bloodbank_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pune Red Cross Blood Bank")
        self.assertIn('map_markers_json', response.context)
