from datetime import date
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import (
    User,
    UserRole,
    DonorProfile,
    BloodRequest,
    BloodGroup,
    RequestPriority,
    RequestStatus,
    DonationRecord,
    RequestResponse,
    ResponseStatus,
)


class UserRegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, required=True, label="First Name")
    last_name = forms.CharField(max_length=50, required=True, label="Last Name")
    email = forms.EmailField(required=True, label="Email Address")
    phone_number = forms.CharField(
        max_length=20,
        required=True,
        label="Emergency Contact Number",
        help_text="Will only be shared with verified coordinators or requesters during emergencies."
    )
    role = forms.ChoiceField(
        choices=[
            (UserRole.DONOR, 'Blood Donor (I want to volunteer to donate)'),
            (UserRole.REQUESTER, 'Blood Requester (Patient or family member)'),
            (UserRole.HOSPITAL_STAFF, 'Hospital / Blood Bank Staff (Healthcare representative)'),
        ],
        required=True,
        label="I am joining as",
        initial=UserRole.DONOR
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone_number', 'role')

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email address already exists.")
        return email


class DonorProfileForm(forms.ModelForm):
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=True,
        label="Date of Birth",
        help_text="Donors must be at least 18 years old."
    )
    last_donation_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False,
        label="Date of Last Blood Donation (if any)",
        help_text="Whole blood donations require a minimum 90-day interval between donations."
    )

    class Meta:
        model = DonorProfile
        fields = [
            'blood_group',
            'date_of_birth',
            'weight_kg',
            'city',
            'state',
            'pincode',
            'address',
            'last_donation_date',
            'is_available',
            'consent_to_contact',
            'medical_notes',
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Street, Area, Landmark (Kept strictly private)'}),
            'medical_notes': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Optional: Any allergies, recent travel, or medical comments'}),
        }

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob:
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 18:
                raise ValidationError("You must be at least 18 years of age to register as a voluntary blood donor.")
            if age > 75:
                raise ValidationError("Standard donor eligibility age limit is 65-70 years. Please check with your doctor.")
        return dob

    def clean_weight_kg(self):
        weight = self.cleaned_data.get('weight_kg')
        if weight is not None and weight < 45:
            raise ValidationError("Minimum donor weight requirement is 45 kg for safe whole blood donation.")
        return weight

    def clean_last_donation_date(self):
        ldd = self.cleaned_data.get('last_donation_date')
        if ldd and ldd > date.today():
            raise ValidationError("Last donation date cannot be in the future.")
        return ldd

    def clean_consent_to_contact(self):
        consent = self.cleaned_data.get('consent_to_contact')
        if not consent:
            raise ValidationError("You must provide consent for coordinators to notify you regarding emergency blood requests.")
        return consent


class BloodRequestForm(forms.ModelForm):
    deadline = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        required=True,
        label="Required Before (Deadline)",
        help_text="Specify the time by which blood is critically needed at the hospital."
    )

    class Meta:
        model = BloodRequest
        fields = [
            'patient_name',
            'blood_group',
            'units_needed',
            'priority',
            'hospital_name',
            'hospital_city',
            'hospital_address',
            'contact_name',
            'contact_phone',
            'deadline',
            'notes',
            'consent',
        ]
        widgets = {
            'hospital_address': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Ward, Room Number, Street, Hospital Wing'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Attending Physician, Case No., or special patient instructions'}),
        }

    def clean_deadline(self):
        deadline = self.cleaned_data.get('deadline')
        if deadline and deadline <= timezone.now():
            raise ValidationError("Critical emergency deadline must be in the future.")
        return deadline

    def clean_units_needed(self):
        units = self.cleaned_data.get('units_needed')
        if not units or units < 1 or units > 25:
            raise ValidationError("Please specify a realistic emergency unit count between 1 and 25 units.")
        return units

    def clean_consent(self):
        consent = self.cleaned_data.get('consent')
        if not consent:
            raise ValidationError("You must consent to sharing patient medical blood requirements with potential donors.")
        return consent


class DonationRecordForm(forms.ModelForm):
    donation_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=True,
        label="Date of Donation",
        initial=date.today
    )

    class Meta:
        model = DonationRecord
        fields = ['donation_date', 'facility_name', 'units_donated', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Optional notes about the donation experience or donor card reference'}),
        }

    def clean_donation_date(self):
        d_date = self.cleaned_data.get('donation_date')
        if d_date and d_date > date.today():
            raise ValidationError("Donation date cannot be in the future.")
        return d_date


class RequestResponseForm(forms.ModelForm):
    class Meta:
        model = RequestResponse
        fields = ['response_status', 'message']
        widgets = {
            'message': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Provide your estimated arrival time, questions, or message to the requester...'
            }),
        }


class RequestStatusUpdateForm(forms.ModelForm):
    class Meta:
        model = BloodRequest
        fields = ['status', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
        }


class DonorSearchForm(forms.Form):
    blood_group = forms.ChoiceField(
        choices=[('', 'All Blood Groups')] + BloodGroup.choices,
        required=False,
        label="Blood Group"
    )
    city = forms.CharField(
        max_length=100,
        required=False,
        label="City / District",
        widget=forms.TextInput(attrs={'placeholder': 'e.g. Mumbai, New Delhi, Bengaluru...'})
    )
    only_available = forms.BooleanField(
        required=False,
        initial=True,
        label="Show available donors only"
    )


class BloodBankFilterForm(forms.Form):
    city = forms.CharField(
        max_length=100,
        required=False,
        label="Search by City",
        widget=forms.TextInput(attrs={'placeholder': 'e.g. Hyderabad, Chennai, Pune...'})
    )
    blood_group = forms.ChoiceField(
        choices=[('', 'All Groups in Stock')] + BloodGroup.choices,
        required=False,
        label="Stock Filter"
    )
