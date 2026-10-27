from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User,
    DonorProfile,
    BloodRequest,
    BloodBank,
    BloodInventory,
    DonationRecord,
    RequestResponse,
    Notification,
    AuditLog,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_verified_staff', 'is_staff')
    list_filter = ('role', 'is_verified_staff', 'is_staff', 'is_active')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('LifeDrop Access Details', {'fields': ('role', 'phone_number', 'is_verified_staff')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('LifeDrop Access Details', {'fields': ('role', 'phone_number', 'is_verified_staff')}),
    )


class BloodInventoryInline(admin.TabularInline):
    model = BloodInventory
    extra = 1


@admin.register(DonorProfile)
class DonorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'blood_group', 'city', 'state', 'is_available', 'is_verified', 'last_donation_date')
    list_filter = ('blood_group', 'is_available', 'is_verified', 'state')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'city', 'pincode')
    actions = ['verify_donors']

    @admin.action(description="Mark selected donors as verified")
    def verify_donors(self, request, queryset):
        queryset.update(is_verified=True)


@admin.register(BloodRequest)
class BloodRequestAdmin(admin.ModelAdmin):
    list_display = (
        'reference_id',
        'blood_group',
        'units_needed',
        'priority',
        'status',
        'hospital_name',
        'hospital_city',
        'deadline',
        'created_at'
    )
    list_filter = ('status', 'priority', 'blood_group', 'hospital_city')
    search_fields = ('reference_id', 'patient_name', 'hospital_name', 'contact_name', 'contact_phone')
    readonly_fields = ('reference_id', 'created_at', 'updated_at')


@admin.register(BloodBank)
class BloodBankAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'state', 'contact_phone', 'is_verified')
    list_filter = ('city', 'state', 'is_verified')
    search_fields = ('name', 'city', 'address', 'contact_phone')
    inlines = [BloodInventoryInline]


@admin.register(DonationRecord)
class DonationRecordAdmin(admin.ModelAdmin):
    list_display = ('donor', 'facility_name', 'donation_date', 'units_donated', 'is_verified')
    list_filter = ('is_verified', 'donation_date')
    search_fields = ('donor__user__username', 'facility_name')


@admin.register(RequestResponse)
class RequestResponseAdmin(admin.ModelAdmin):
    list_display = ('request', 'donor', 'response_status', 'responded_at')
    list_filter = ('response_status', 'responded_at')
    search_fields = ('request__reference_id', 'donor__user__username')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'title', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('recipient__username', 'title', 'message')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'action', 'actor', 'ip_address')
    list_filter = ('action', 'timestamp')
    search_fields = ('action', 'actor__username', 'details', 'ip_address')
    readonly_fields = ('action', 'actor', 'timestamp', 'details', 'ip_address')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
