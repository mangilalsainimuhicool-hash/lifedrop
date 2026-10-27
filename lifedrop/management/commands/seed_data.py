from datetime import date, timedelta
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from lifedrop.models import (
    User,
    UserRole,
    DonorProfile,
    BloodBank,
    BloodInventory,
    BloodRequest,
    BloodGroup,
    RequestPriority,
    RequestStatus,
    DonationRecord,
)


class Command(BaseCommand):
    help = "Seeds initial realistic reference data, demo users, certified blood banks, and verified donors for LifeDrop."

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("Demo data can only be seeded when DEBUG is enabled.")

        self.stdout.write("Seeding LifeDrop database...")

        # 1. Superuser / Admin
        admin_user, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@lifedrop.org",
                "first_name": "LifeDrop",
                "last_name": "Admin",
                "role": UserRole.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            }
        )
        if created:
            admin_user.set_password("AdminPass123!")
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created demo superuser: admin"))

        # 2. Hospital Staff User
        staff_user, created = User.objects.get_or_create(
            username="staff_dr_sharma",
            defaults={
                "email": "dr.sharma@aims-hospital.org",
                "first_name": "Dr. Rajesh",
                "last_name": "Sharma",
                "role": UserRole.HOSPITAL_STAFF,
                "phone_number": "+91 98200 11223",
                "is_verified_staff": True,
            }
        )
        if created:
            staff_user.set_password("StaffPass123!")
            staff_user.save()
            self.stdout.write(self.style.SUCCESS("Created demo hospital staff: staff_dr_sharma"))

        # 3. Requester User
        requester_user, created = User.objects.get_or_create(
            username="requester_priya",
            defaults={
                "email": "priya.verma@example.com",
                "first_name": "Priya",
                "last_name": "Verma",
                "role": UserRole.REQUESTER,
                "phone_number": "+91 99887 66554",
            }
        )
        if created:
            requester_user.set_password("RequesterPass123!")
            requester_user.save()
            self.stdout.write(self.style.SUCCESS("Created demo requester: requester_priya"))

        # 4. Verified Voluntary Donors
        donors_data = [
            {
                "username": "donor_arjun",
                "first_name": "Arjun",
                "last_name": "Mehta",
                "email": "arjun.m@example.com",
                "blood_group": BloodGroup.O_POS,
                "city": "Mumbai",
                "state": "Maharashtra",
                "pincode": "400001",
                "dob": date(1994, 5, 14),
                "last_donation": date.today() - timedelta(days=120),
                "is_available": True,
                "is_verified": True,
                "weight_kg": 72.5,
            },
            {
                "username": "donor_sneha",
                "first_name": "Sneha",
                "last_name": "Patel",
                "email": "sneha.p@example.com",
                "blood_group": BloodGroup.A_POS,
                "city": "Mumbai",
                "state": "Maharashtra",
                "pincode": "400050",
                "dob": date(1998, 9, 21),
                "last_donation": date.today() - timedelta(days=95),
                "is_available": True,
                "is_verified": True,
                "weight_kg": 56.0,
            },
            {
                "username": "donor_vikram",
                "first_name": "Vikram",
                "last_name": "Rao",
                "email": "vikram.r@example.com",
                "blood_group": BloodGroup.B_POS,
                "city": "Bengaluru",
                "state": "Karnataka",
                "pincode": "560001",
                "dob": date(1991, 11, 3),
                "last_donation": date.today() - timedelta(days=150),
                "is_available": True,
                "is_verified": True,
                "weight_kg": 78.0,
            },
            {
                "username": "donor_ananya",
                "first_name": "Ananya",
                "last_name": "Iyer",
                "email": "ananya.i@example.com",
                "blood_group": BloodGroup.O_NEG,
                "city": "New Delhi",
                "state": "Delhi",
                "pincode": "110001",
                "dob": date(1996, 3, 18),
                "last_donation": date.today() - timedelta(days=110),
                "is_available": True,
                "is_verified": True,
                "weight_kg": 60.0,
            },
            {
                "username": "donor_karthik",
                "first_name": "Karthik",
                "last_name": "Reddy",
                "email": "karthik.reddy@example.com",
                "blood_group": BloodGroup.AB_POS,
                "city": "Hyderabad",
                "state": "Telangana",
                "pincode": "500001",
                "dob": date(1993, 7, 12),
                "last_donation": date.today() - timedelta(days=105),
                "is_available": True,
                "is_verified": True,
                "weight_kg": 68.0,
            },
        ]

        for d in donors_data:
            d_user, u_created = User.objects.get_or_create(
                username=d["username"],
                defaults={
                    "first_name": d["first_name"],
                    "last_name": d["last_name"],
                    "email": d["email"],
                    "role": UserRole.DONOR,
                    "phone_number": "+91 98000 12345",
                }
            )
            if u_created:
                d_user.set_password("DonorPass123!")
                d_user.save()

            profile, p_created = DonorProfile.objects.get_or_create(
                user=d_user,
                defaults={
                    "blood_group": d["blood_group"],
                    "city": d["city"],
                    "state": d["state"],
                    "pincode": d["pincode"],
                    "address": f"Flat 102, Green Avenue, {d['city']}",
                    "date_of_birth": d["dob"],
                    "last_donation_date": d["last_donation"],
                    "is_available": d["is_available"],
                    "is_verified": d["is_verified"],
                    "consent_to_contact": True,
                    "weight_kg": d["weight_kg"],
                }
            )

            # Record a verified previous donation record
            DonationRecord.objects.get_or_create(
                donor=profile,
                donation_date=d["last_donation"],
                defaults={
                    "facility_name": f"{d['city']} Civil Red Cross Center",
                    "units_donated": 1,
                    "is_verified": True,
                    "notes": "Routine voluntary donation, hemoglobin 14.2 g/dL."
                }
            )

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(donors_data)} voluntary donors with history."))

        # 5. Certified Blood Banks with Coordinates
        blood_banks_data = [
            {
                "name": "Rotary Blood Bank & Transfusion Center",
                "city": "New Delhi",
                "state": "Delhi",
                "address": "56-57, Tughlakabad Institutional Area, Near Batra Hospital",
                "latitude": 28.5135,
                "longitude": 77.2588,
                "phone": "+91 11 2605 1010",
                "email": "delhi@rotarybloodbank.org",
                "hours": "24/7 Round-the-clock Emergency Service",
                "website": "https://www.rotarybloodbank.org",
            },
            {
                "name": "KEM Hospital Blood Bank",
                "city": "Mumbai",
                "state": "Maharashtra",
                "address": "Acharya Donde Marg, Parel, Mumbai",
                "latitude": 19.0026,
                "longitude": 72.8427,
                "phone": "+91 22 2410 7000",
                "email": "bloodbank@kem.edu",
                "hours": "24/7 Emergency Blood Bank",
                "website": "https://kem.edu",
            },
            {
                "name": "Red Cross Blood Bank Bengaluru",
                "city": "Bengaluru",
                "state": "Karnataka",
                "address": "26, Red Cross Bhawan, 1st Main Road, Race Course",
                "latitude": 12.9815,
                "longitude": 77.5855,
                "phone": "+91 80 2226 4205",
                "email": "info@redcrosskarnataka.org",
                "hours": "24 Hours Emergency Transfusion Center",
                "website": "https://redcrosskarnataka.org",
            },
            {
                "name": "NIMS Hospital Transfusion Medicine Center",
                "city": "Hyderabad",
                "state": "Telangana",
                "address": "Nizams Institute of Medical Sciences, Punjagutta",
                "latitude": 17.4225,
                "longitude": 78.4526,
                "phone": "+91 40 2348 9000",
                "email": "transfusion@nims.edu.in",
                "hours": "24/7 Dedicated Trauma & Blood Center",
                "website": "https://nims.edu.in",
            },
            {
                "name": "Jivdaya Charitable Blood Bank",
                "city": "Pune",
                "state": "Maharashtra",
                "address": "Near Pune Station, Camp, Pune",
                "latitude": 18.5204,
                "longitude": 73.8567,
                "phone": "+91 20 2612 3456",
                "email": "contact@jivdayabloodbank.org",
                "hours": "24 Hours Emergency Assistance",
                "website": "https://jivdayabloodbank.org",
            },
        ]

        stock_matrix = {
            BloodGroup.O_POS: 12,
            BloodGroup.A_POS: 8,
            BloodGroup.B_POS: 15,
            BloodGroup.AB_POS: 5,
            BloodGroup.O_NEG: 3,
            BloodGroup.A_NEG: 2,
            BloodGroup.B_NEG: 4,
            BloodGroup.AB_NEG: 1,
        }

        for b_data in blood_banks_data:
            bank, b_created = BloodBank.objects.get_or_create(
                name=b_data["name"],
                city=b_data["city"],
                defaults={
                    "state": b_data["state"],
                    "address": b_data["address"],
                    "latitude": b_data["latitude"],
                    "longitude": b_data["longitude"],
                    "contact_phone": b_data["phone"],
                    "contact_email": b_data["email"],
                    "operating_hours": b_data["hours"],
                    "is_verified": True,
                    "website": b_data["website"],
                }
            )

            for bg, units in stock_matrix.items():
                BloodInventory.objects.get_or_create(
                    blood_bank=bank,
                    blood_group=bg,
                    defaults={"units_available": units}
                )

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(blood_banks_data)} certified Blood Banks with inventory."))

        # 6. Sample Active Emergency Requests
        requests_data = [
            {
                "patient_name": "Ramesh Chandra",
                "blood_group": BloodGroup.O_POS,
                "units_needed": 2,
                "priority": RequestPriority.URGENT,
                "hospital_name": "Lilavati Hospital & Research Centre",
                "hospital_city": "Mumbai",
                "hospital_address": "A-791, Bandra Reclamation, Bandra West, Mumbai",
                "contact_name": "Priya Verma",
                "contact_phone": "+91 99887 66554",
                "hours_deadline": 4,
                "notes": "Emergency bypass surgery scheduled. Immediate blood match requested.",
                "requester": requester_user,
            },
            {
                "patient_name": "Deepak Nair",
                "blood_group": BloodGroup.B_POS,
                "units_needed": 3,
                "priority": RequestPriority.HIGH,
                "hospital_name": "Manipal Hospital",
                "hospital_city": "Bengaluru",
                "hospital_address": "98, HAL Old Airport Rd, Kodihalli, Bengaluru",
                "contact_name": "Suresh Nair",
                "contact_phone": "+91 98450 99887",
                "hours_deadline": 14,
                "notes": "Severe anemia treatment. Platelets / whole blood support needed.",
                "requester": requester_user,
            },
            {
                "patient_name": "Meera Joshi",
                "blood_group": BloodGroup.O_NEG,
                "units_needed": 1,
                "priority": RequestPriority.URGENT,
                "hospital_name": "AIIMS New Delhi",
                "hospital_city": "New Delhi",
                "hospital_address": "Sri Aurobindo Marg, Ansari Nagar, New Delhi",
                "contact_name": "Alok Joshi",
                "contact_phone": "+91 98111 22334",
                "hours_deadline": 3,
                "notes": "Trauma ICU ward, rare O- group critical requirement.",
                "requester": None,
            },
        ]

        for req_data in requests_data:
            deadline = timezone.now() + timedelta(hours=req_data["hours_deadline"])
            req, r_created = BloodRequest.objects.get_or_create(
                patient_name=req_data["patient_name"],
                hospital_name=req_data["hospital_name"],
                defaults={
                    "blood_group": req_data["blood_group"],
                    "units_needed": req_data["units_needed"],
                    "priority": req_data["priority"],
                    "hospital_city": req_data["hospital_city"],
                    "hospital_address": req_data["hospital_address"],
                    "contact_name": req_data["contact_name"],
                    "contact_phone": req_data["contact_phone"],
                    "deadline": deadline,
                    "notes": req_data["notes"],
                    "consent": True,
                    "requester": req_data["requester"],
                    "status": RequestStatus.PENDING,
                }
            )

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(requests_data)} active emergency blood requests."))
        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))
