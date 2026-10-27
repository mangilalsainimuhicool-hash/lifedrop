# LifeDrop — Emergency Blood Service

> **"Every Drop Counts. Every Second Matters."**

LifeDrop is a production-ready Django web application designed to bridge critical gaps between patients in immediate need of blood transfusions, voluntary registered donors, and certified regional blood banks.

---

## 🌟 Technology Stack

- **Backend:** Python 3.14 with Django 6.0 (Server-Side Rendering)
- **Database:** SQLite (default for development), PostgreSQL-ready with environment flags
- **Frontend:** HTML5, CSS3, JavaScript, Bootstrap 5.3, Bootstrap Icons
- **Interactive Maps:** OpenStreetMap integrated via Leaflet.js (custom markers, popups, and live inventory indicators)
- **Authentication:** Django custom user model (`AUTH_USER_MODEL = 'lifedrop.User'`) with role-based access control (`DONOR`, `REQUESTER`, `HOSPITAL_STAFF`, `ADMIN`)
- **Forms & Validation:** Django Forms and ModelForms with medical constraint validation (minimum 18 years age, 90-day cooldown between whole blood donations, 45 kg minimum weight)
- **Security & Privacy:** CSRF protection, secure cookie flags, phone number and address masking for anonymous visitors, and audit logging.

---

## 🚀 Key Features & Core Workflows

1. **Emergency Blood Request Flow:**
   - Validated submission form (patient name, blood group, units, hospital details, deadline, priority).
   - Auto-generated human-readable tracking ID (e.g. `LD-20261027-3849`).
   - Automated in-app notification dispatch to matching registered donors in the same city.
   - Public live status tracking progression bar (`Posted` &rarr; `Matching` &rarr; `Fulfilled`).
   - Clinical disclaimer on coordination vs. laboratory cross-matching.

2. **Privacy-Preserving Donor Directory:**
   - Filter voluntary donors by exact blood group, city/district, and active availability.
   - **Zero-Leakage Privacy Safeguard:** Anonymous users and automated web crawlers cannot view private telephone numbers or home addresses.
   - Interactive availability toggle: donors can pause or resume emergency notifications with one click.

3. **Blood Bank Directory with OpenStreetMap (Leaflet.js):**
   - Certified facility directory with hours, verified badges, and emergency contact numbers.
   - Interactive Leaflet map plotting verified facilities with popups.
   - Real-time stock matrices for component inventories.

4. **Role-Based User Dashboards:**
   - **Donor Dashboard:** Availability switch, medical eligibility countdown (90-day interval tracker), matching emergency requests in donor's city, donation history logger.
   - **Requester Dashboard:** Overview of logged requests, donor responses, 1-click status updater (Mark as Fulfilled or Cancel).
   - **Healthcare Staff / Admin Console:** Pending donor verification queue, active requests overview, security audit forensics log.

5. **Security & Audit Forensics:**
   - Dedicated `AuditLog` model recording operational and security actions (`USER_LOGIN`, `BLOOD_REQUEST_CREATED`, `DONOR_AVAILABILITY_TOGGLED`, `DONOR_VERIFIED_BY_STAFF`).
   - Immutable audit logs protected in Django admin.

---

## 🔑 Pre-seeded Demo Credentials

To test the application immediately, the database is pre-seeded with sample users:

| Role | Username | Password | Notes |
|---|---|---|---|
| **Admin** | `admin` | `AdminPass123!` | Full superuser access to Django admin & staff console |
| **Hospital Staff** | `staff_dr_sharma` | `StaffPass123!` | Verified healthcare staff console & donor verifications |
| **Requester** | `requester_priya` | `RequesterPass123!` | Patient requester with active emergency requests |
| **Donor (O+)** | `donor_arjun` | `DonorPass123!` | Verified donor in Mumbai with donation history |
| **Donor (A+)** | `donor_sneha` | `DonorPass123!` | Verified donor in Mumbai |
| **Donor (B+)** | `donor_vikram` | `DonorPass123!` | Verified donor in Bengaluru |
| **Donor (O-)** | `donor_ananya` | `DonorPass123!` | Verified rare donor in New Delhi |
| **Donor (AB+)**| `donor_karthik` | `DonorPass123!` | Verified donor in Hyderabad |

---

## 🛠️ Quickstart Installation & Execution

### 1. Requirements
Ensure Python 3.10+ is installed:
```powershell
pip install -r requirements.txt
```

### 2. Apply Migrations & Seed Data
```powershell
python manage.py migrate
python manage.py seed_data
```

### 3. Run Automated Tests
```powershell
python manage.py test lifedrop.tests
```

### 4. Start Development Server
```powershell
python manage.py runserver 127.0.0.1:8000
```
Open your web browser at `http://127.0.0.1:8000/`.

---

## ⚕️ Clinical Safety Statement

LifeDrop coordinates communication between voluntary donors, requesters, and healthcare facilities. **LifeDrop is NOT a clinical blood bank and does not perform medical cross-matching.** Attending physicians, hospital transfusion services, and certified laboratories must always perform mandatory pre-transfusion laboratory cross-matching, blood typing confirmation, and infectious marker screening before administering blood products.
