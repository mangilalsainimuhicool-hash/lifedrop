from datetime import date, timedelta
from django.test import TestCase
from django.utils import timezone
from lifedrop.forms import BloodRequestForm, DonorProfileForm
from lifedrop.models import BloodGroup, RequestPriority


class FormValidationTests(TestCase):
    def test_valid_blood_request_form(self):
        form_data = {
            'patient_name': 'Kavita Roy',
            'blood_group': BloodGroup.AB_POS,
            'units_needed': 2,
            'priority': RequestPriority.URGENT,
            'hospital_name': 'Max Healthcare',
            'hospital_city': 'New Delhi',
            'hospital_address': 'Saket, New Delhi',
            'contact_name': 'Rohan Roy',
            'contact_phone': '+91 98111 22233',
            'deadline': (timezone.now() + timedelta(hours=10)).strftime('%Y-%m-%dT%H:%M'),
            'consent': True,
        }
        form = BloodRequestForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_past_deadline_rejected(self):
        past_time = (timezone.now() - timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M')
        form_data = {
            'patient_name': 'Kavita Roy',
            'blood_group': BloodGroup.AB_POS,
            'units_needed': 2,
            'priority': RequestPriority.URGENT,
            'hospital_name': 'Max Healthcare',
            'hospital_city': 'New Delhi',
            'hospital_address': 'Saket',
            'contact_name': 'Rohan',
            'contact_phone': '+91 98111 22233',
            'deadline': past_time,
            'consent': True,
        }
        form = BloodRequestForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('deadline', form.errors)

    def test_donor_under_18_rejected(self):
        underage_dob = date.today() - timedelta(days=365 * 17)
        form_data = {
            'blood_group': BloodGroup.O_POS,
            'date_of_birth': underage_dob,
            'city': 'Mumbai',
            'state': 'Maharashtra',
            'consent_to_contact': True,
        }
        form = DonorProfileForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('date_of_birth', form.errors)

    def test_donor_underweight_rejected(self):
        valid_dob = date.today() - timedelta(days=365 * 25)
        form_data = {
            'blood_group': BloodGroup.O_POS,
            'date_of_birth': valid_dob,
            'weight_kg': 40.0,  # Below 45 kg threshold
            'city': 'Mumbai',
            'state': 'Maharashtra',
            'consent_to_contact': True,
        }
        form = DonorProfileForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('weight_kg', form.errors)
