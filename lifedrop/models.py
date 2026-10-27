import uuid
from datetime import date
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.urls import reverse


class UserRole(models.TextChoices):
    DONOR = 'DONOR', 'Blood Donor'
    REQUESTER = 'REQUESTER', 'Patient / Blood Requester'
    HOSPITAL_STAFF = 'HOSPITAL_STAFF', 'Hospital / Blood Bank Staff'
    ADMIN = 'ADMIN', 'System Administrator'


class BloodGroup(models.TextChoices):
    A_POS = 'A+', 'A Positive (A+)'
    A_NEG = 'A-', 'A Negative (A-)'
    B_POS = 'B+', 'B Positive (B+)'
    B_NEG = 'B-', 'B Negative (B-)'
    AB_POS = 'AB+', 'AB Positive (AB+)'
    AB_NEG = 'AB-', 'AB Negative (AB-)'
    O_POS = 'O+', 'O Positive (O+)'
    O_NEG = 'O-', 'O Negative (O-)'


class RequestPriority(models.TextChoices):
    URGENT = 'URGENT', 'Immediate / Critical (Within 2-4 Hours)'
    HIGH = 'HIGH', 'High Priority (Within 12-24 Hours)'
    NORMAL = 'NORMAL', 'Standard / Scheduled (24-48+ Hours)'


class RequestStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending Matching'
    CONTACTED = 'CONTACTED', 'Donors Contacted'
    FULFILLED = 'FULFILLED', 'Fulfilled'
    CANCELLED = 'CANCELLED', 'Cancelled'
    EXPIRED = 'EXPIRED', 'Expired'


class ResponseStatus(models.TextChoices):
    INTERESTED = 'INTERESTED', 'Willing to Donate'
    CONTACTED = 'CONTACTED', 'Direct Contact Initiated'
    DONATED = 'DONATED', 'Donation Completed'
    DECLINED = 'DECLINED', 'Unable to Donate'


class User(AbstractUser):
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.REQUESTER,
        help_text="Role determining access permissions and dashboard interface."
    )
    phone_number = models.CharField(max_length=20, blank=True, help_text="Contact telephone number.")
    is_verified_staff = models.BooleanField(
        default=False,
        help_text="Designates whether this user has been verified as authorized healthcare staff."
    )

    @property
    def is_donor(self):
        return self.role == UserRole.DONOR or hasattr(self, 'donor_profile')

    @property
    def is_requester(self):
        return self.role == UserRole.REQUESTER

    @property
    def is_hospital_staff(self):
        return self.role == UserRole.HOSPITAL_STAFF or self.is_superuser

    @property
    def is_platform_admin(self):
        return self.role == UserRole.ADMIN or self.is_superuser or self.is_staff

    def __str__(self):
        full_name = self.get_full_name()
        display_name = full_name if full_name else self.username
        return f"{display_name} ({self.get_role_display()})"


class DonorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='donor_profile')
    blood_group = models.CharField(max_length=5, choices=BloodGroup.choices, db_index=True)
    date_of_birth = models.DateField(null=True, blank=True, help_text="Must be 18+ to donate.")
    city = models.CharField(max_length=100, db_index=True)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True, help_text="Private address; never displayed to anonymous visitors.")
    last_donation_date = models.DateField(null=True, blank=True, help_text="Date of most recent donation.")
    is_available = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether donor is currently willing and available for emergency donation."
    )
    is_verified = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Verification of blood group and donor identity."
    )
    consent_to_contact = models.BooleanField(
        default=True,
        help_text="Donor explicitly consents to receive urgent blood request notifications."
    )
    medical_notes = models.TextField(blank=True, help_text="Confidential medical disclosures or deferrals.")
    weight_kg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Donor weight in kg (minimum 45-50 kg recommended)."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['blood_group', 'city', 'is_available']),
            models.Index(fields=['is_available', 'is_verified']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} [{self.blood_group}] - {self.city}"

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    @property
    def days_since_last_donation(self):
        if not self.last_donation_date:
            return None
        today = date.today()
        return (today - self.last_donation_date).days

    @property
    def is_eligible_by_date(self):
        """Clinical guideline: minimum 90-day interval between whole blood donations."""
        if not self.last_donation_date:
            return True
        return self.days_since_last_donation >= 90

    @property
    def is_eligible(self):
        """Combined basic eligibility check: Age >= 18, 90-day cooldown, weight >= 45."""
        if self.age is not None and self.age < 18:
            return False
        if not self.is_eligible_by_date:
            return False
        if self.weight_kg is not None and self.weight_kg < 45:
            return False
        return True

    @property
    def eligibility_status_display(self):
        if self.age is not None and self.age < 18:
            return "Ineligible (Under 18)"
        if not self.is_eligible_by_date:
            days_left = 90 - self.days_since_last_donation
            return f"Cooldown period ({days_left} days remaining)"
        if self.weight_kg is not None and self.weight_kg < 45:
            return "Ineligible (Weight under 45 kg)"
        return "Eligible to Donate"


class BloodRequest(models.Model):
    reference_id = models.CharField(max_length=30, unique=True, db_index=True)
    requester = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='blood_requests'
    )
    patient_name = models.CharField(max_length=150)
    blood_group = models.CharField(max_length=5, choices=BloodGroup.choices, db_index=True)
    units_needed = models.PositiveIntegerField(default=1)
    hospital_name = models.CharField(max_length=200)
    hospital_city = models.CharField(max_length=100, db_index=True)
    hospital_address = models.TextField()
    contact_name = models.CharField(max_length=150)
    contact_phone = models.CharField(max_length=25)
    deadline = models.DateTimeField(help_text="Critical deadline before which blood is needed.")
    priority = models.CharField(
        max_length=15,
        choices=RequestPriority.choices,
        default=RequestPriority.URGENT
    )
    status = models.CharField(
        max_length=20,
        choices=RequestStatus.choices,
        default=RequestStatus.PENDING,
        db_index=True
    )
    notes = models.TextField(blank=True, help_text="Doctor name, case description, or special instructions.")
    consent = models.BooleanField(
        default=True,
        help_text="Consent to publish emergency request details for donor matching."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['blood_group', 'hospital_city', 'status']),
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.reference_id}] {self.blood_group} for {self.patient_name} ({self.hospital_city})"

    def save(self, *args, **kwargs):
        if not self.reference_id:
            date_prefix = timezone.now().strftime('%Y%m%d')
            unique_part = uuid.uuid4().hex[:6].upper()
            self.reference_id = f"LD-{date_prefix}-{unique_part}"
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        if self.status in [RequestStatus.FULFILLED, RequestStatus.CANCELLED]:
            return False
        return timezone.now() > self.deadline

    def get_absolute_url(self):
        return reverse('request_detail', kwargs={'reference_id': self.reference_id})


class BloodBank(models.Model):
    name = models.CharField(max_length=250)
    city = models.CharField(max_length=100, db_index=True)
    state = models.CharField(max_length=100)
    address = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    contact_phone = models.CharField(max_length=50)
    contact_email = models.EmailField(blank=True)
    operating_hours = models.CharField(max_length=150, default="24/7 Emergency Blood Bank")
    is_verified = models.BooleanField(default=True, db_index=True)
    website = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['city', 'is_verified']),
        ]
        ordering = ['city', 'name']

    def __str__(self):
        return f"{self.name} - {self.city}"


class BloodInventory(models.Model):
    blood_bank = models.ForeignKey(BloodBank, on_delete=models.CASCADE, related_name='inventories')
    blood_group = models.CharField(max_length=5, choices=BloodGroup.choices)
    units_available = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('blood_bank', 'blood_group')
        indexes = [
            models.Index(fields=['blood_group', 'units_available']),
        ]

    def __str__(self):
        return f"{self.blood_bank.name} : {self.blood_group} ({self.units_available} units)"


class DonationRecord(models.Model):
    donor = models.ForeignKey(DonorProfile, on_delete=models.CASCADE, related_name='donations')
    donation_date = models.DateField(default=date.today)
    facility_name = models.CharField(max_length=200, help_text="Hospital or Blood Bank where donation occurred.")
    units_donated = models.PositiveIntegerField(default=1)
    is_verified = models.BooleanField(default=False, help_text="Verified by healthcare facility staff.")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-donation_date']

    def __str__(self):
        return f"{self.donor.user.username} - {self.donation_date} ({self.facility_name})"


class RequestResponse(models.Model):
    request = models.ForeignKey(BloodRequest, on_delete=models.CASCADE, related_name='responses')
    donor = models.ForeignKey(DonorProfile, on_delete=models.CASCADE, related_name='responses')
    response_status = models.CharField(
        max_length=20,
        choices=ResponseStatus.choices,
        default=ResponseStatus.INTERESTED
    )
    message = models.TextField(blank=True, help_text="Volunteer response note or ETA.")
    responded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('request', 'donor')
        ordering = ['-responded_at']

    def __str__(self):
        return f"{self.donor} -> {self.request.reference_id} [{self.response_status}]"


class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False, db_index=True)
    link = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.title}"


class AuditLog(models.Model):
    action = models.CharField(max_length=100, db_index=True)
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    details = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        actor_name = self.actor.username if self.actor else "System / Anonymous"
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {self.action} by {actor_name}"
