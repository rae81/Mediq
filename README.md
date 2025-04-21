========================================================
                 MedIQ – Django 3.2 Platform
      Smart Medical Appointments • Messaging • Alerts
========================================================

Table of Contents
-----------------
1.  Overview
2.  Key Features
3.  Technology Stack & Dependencies
4.  Project Structure
5.  Quick Start (30‑second run)
6.  Full Installation Guide
7.  Scheduled Jobs & Notifications
8.  Static, Media & Service Workers
9.  Running Tests
10. Deployment Checklist
11. Troubleshooting FAQ
12. Security Best Practices
13. Contributing
14. License
15. Contact

================================================================
1.  Overview
================================================================
MedIQ is a full‑stack web application that streamlines interactions
between **patients** and **doctors**.  Built with Django 3.2,
it wraps appointment booking, real‑time messaging, push / e‑mail / SMS
reminders, profile management and secure document uploads inside a
modern, responsive UI (FullCalendar + Tailwind CSS).

The repository you are holding **already contains a functional virtual
environment and an offline wheel for Django 3.2.6** so you can bring
the project up even without Internet connectivity.

----------------------------------------------------------------
2.  Key Features
----------------------------------------------------------------
* Role‑based authentication for Patients & Doctors
* Responsive appointment calendar (FullCalendar v5)
* Doctor availability management & conflict detection
* Real‑time chat (user ↔ doctor or doctor ↔ doctor)
* E‑mail, Web‑Push (VAPID) and optional Twilio SMS reminders
* Profile pictures & file uploads stored in `/media`
* Background schedulers (APScheduler) for reminder dispatch
* GDPR‑friendly «Remember Me» & session hardening
* CSRF/Click‑jacking protections ready for production

----------------------------------------------------------------
3.  Technology Stack & Dependencies
----------------------------------------------------------------
| Category        | Package (minimum version)           |
| --------------- | ------------------------------------|
| Web framework   | Django == 3.2.* (wheel included)    |
| Scheduler       | APScheduler >= 3.10                 |
| Push            | django‑webpush >= 0.3.6             |
| Images          | Pillow >= 10                        |
| REST / HTTP     | requests >= 2.31                    |
| Dates           | python‑dateutil >= 2.9              |
| SMS (optional)  | twilio >= 9.0                       |

Install them with:

```
pip install -r requirements.txt
```

*(If you are offline, run `pip install Django-3.2.6-py3-none-any.whl` that
ships with the repo before the rest.)*

----------------------------------------------------------------
4.  Project Structure (truncated)
----------------------------------------------------------------
```
Mediq-main/
├── Django-3.2.6-py3-none-any.whl
├── mediq/                  # Django project root
│   ├── manage.py
│   ├── db.sqlite3
│   ├── mediq/              # Core settings, URLs, WSGI/ASGI
│   └── accounts/           # Main reusable app
│       ├── templates/
│       ├── static/
│       ├── models.py
│       ├── views.py
│       ├── forms.py
│       ├── reminder.py
│       └── scheduler.py
└── venv/                   # (optional) pre‑built virtual‑env
```

----------------------------------------------------------------
5.  Quick Start (development)
----------------------------------------------------------------
```bash
# 1. Create & activate virtualenv (skip if you use the supplied venv)
python -m venv venv
source venv/bin/activate               # Windows: venv\Scripts\activate

# 2. Install core requirements
pip install -r requirements.txt

# 3. Apply migrations & create an admin account
python manage.py migrate


# 4. Launch the development server
python manage.py runserver
```
Navigate to **http://127.0.0.1:8000/** 

----------------------------------------------------------------
6.  Full Installation Guide
----------------------------------------------------------------
### 6.1 Prerequisites
* Python 3.8 – 3.12
* pip / virtualenv
* SQLite (ships with Python) or PostgreSQL/MySQL for production
* NodeJS + npm/yarn **(only if you plan to rebuild front‑end assets)**

### 6.2 Clone & Environment
```bash
git clone <repo‑url> mediq
cd mediq
python -m venv venv && source venv/bin/activate
```

### 6.3 Configuration
Copy `.env.example` to `.env` (or export vars directly):

| Variable | Purpose |
| -------- | ------- |
| `SECRET_KEY` | Django crypto key *(generate your own!)* |
| `DEBUG` | `True` for local dev |
| `ALLOWED_HOSTS` | Domains / IPs comma‑separated |
| `EMAIL_HOST_USER` & `EMAIL_HOST_PASSWORD` | Gmail SMTP |
| `TWILIO_ACCOUNT_SID` / `TWILIO_AUTH_TOKEN` | SMS |
| `VAPID_PUBLIC_KEY` / `VAPID_PRIVATE_KEY` | Web‑Push |

> **Tip:** Generate VAPID keys with  
> `python manage.py webpush_generate_vapid_key --save`  

Update `mediq/settings.py` or rely on environment overrides.

### 6.4 Database Migrations
`python manage.py migrate`

### 6.5 Static & Media
```
python manage.py collectstatic      # production
```
Media uploads live in `media/`, served by Django in dev or your web
server of choice in production (NGINX/Apache).

### 6.6 Background Scheduler
Appointments reminders are dispatched by APScheduler.  
A default job store is configured; run:

```
python manage.py runapscheduler
```
*(Alternatively, daemonise through systemd or supervisor.)*

----------------------------------------------------------------
7.  Scheduled Jobs & Notifications
----------------------------------------------------------------
| Job                   | Frequency | Channel(s)      |
|-----------------------|-----------|-----------------|
| Appointment reminders | hourly    | E‑mail / Push / SMS |
| Clean old sessions    | daily     | ‑              |
| Health‑check ping     | 5 min     | Logging        |

Jobs are defined in `accounts/scheduler.py` – customise with cron‑style
expressions if required.

----------------------------------------------------------------
8.  Static, Media & Service Workers
----------------------------------------------------------------
* **Static:** `/static/` is collected via `collectstatic`.
* **Media:** User uploads (profile pictures, documents) go to `/media/`.
* **Service Worker:** `accounts/static/serviceWorker.js` enables Web‑Push.

When deploying, configure your web server to serve both directories
directly for performance.

----------------------------------------------------------------
9.  Running Tests
----------------------------------------------------------------
```bash
python manage.py test
```
Custom fixtures live in `accounts/tests/fixtures/`.  
Add your own with the Django `TestCase` framework.

----------------------------------------------------------------
10. Deployment Checklist
----------------------------------------------------------------
1. `DEBUG = False`
2. Unique `SECRET_KEY`
3. Set `ALLOWED_HOSTS`
4. Configure HTTPS & `SECURE_*` settings
5. Run `collectstatic`
6. Point Gunicorn/Uvicorn + NGINX to `mediq.wsgi` or `mediq.asgi`
7. Move scheduler to a managed process

*A sample `docker-compose.yml` is provided in `/deploy/` (coming soon).*

----------------------------------------------------------------
11. Contributing
----------------------------------------------------------------
1. Fork ➜ feature branch (`feat/<topic>`) ➜ Pull Request
2. Run `black` & `flake8` before committing
3. Add unit tests for **any** new behaviour
4. Follow the **Conventional Commits** specification

----------------------------------------------------------------
14. License
----------------------------------------------------------------
© MediQ& Contributors – All rights reserved  


----------------------------------------------------------------
