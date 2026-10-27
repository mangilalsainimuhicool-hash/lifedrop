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

---

## 🛠️ Quickstart Installation & Execution

### 1. Requirements
Ensure Python 3.10+ is installed:
```powershell
pip install -r requirements.txt
```

### 2. Apply Migrations & Seed Local Demo Data
```powershell
python manage.py migrate
python manage.py seed_data
```
The seed command creates fictional demo users and records for local testing only. It refuses to run when `DEBUG` is disabled.

### 3. Run Automated Tests
```powershell
python manage.py test lifedrop.tests
```

### 4. Start Development Server
```powershell
python manage.py runserver 127.0.0.1:8000
```
Open your web browser at `http://127.0.0.1:8000/`.

## Deploy on Render

GitHub stores the source code; it does not run this Django application. The included `render.yaml` configures a Render web service. Before deploying, create a PostgreSQL database with your hosting provider and supply its connection URL as `DATABASE_URL` when Render requests it. Review the provider's current pricing and data-retention terms before creating a database.

1. Push the `main` branch to GitHub.
2. In Render, choose **New > Blueprint**, connect this repository, and follow the prompts.
3. Provide the PostgreSQL connection URL for `DATABASE_URL`. Render generates `SECRET_KEY` and configures HTTPS settings from the blueprint.
4. Open the Render service URL after the first deployment completes.

Do not run `seed_data` in a deployed environment. It creates fictional demo accounts and is blocked when `DEBUG` is disabled. Do not enter real patient or donor information into a demo deployment; use an appropriately secured and reviewed production environment for sensitive data.

---

## ⚕️ Clinical Safety Statement

LifeDrop coordinates communication between voluntary donors, requesters, and healthcare facilities. **LifeDrop is NOT a clinical blood bank and does not perform medical cross-matching.** Attending physicians, hospital transfusion services, and certified laboratories must always perform mandatory pre-transfusion laboratory cross-matching, blood typing confirmation, and infectious marker screening before administering blood products.
