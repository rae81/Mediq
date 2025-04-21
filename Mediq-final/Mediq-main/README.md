MedIQ Healthcare Appointment System
A full‑featured Django-based web application for managing patient registrations, doctor scheduling, messaging, billing, and automated reminders.
________________


Table of Contents
1. Features

2. Requirements

3. Installation & Setup

4. Database Migrations & Seeding

5. Running the Application

6. Automated Reminders Scheduler

7. Project Structure

8. Environment Variables

9. Contributing

10. License

________________


Features
   * User Authentication: Patient signup/login, profile management.

   * Doctor Management: Pre‑populated doctors with specialties, busy times, and profile images.

   * Appointment Booking: Patients select doctor, date/time, reason, contact info.

   * Messaging: Two‑way chat between patients and doctors.

   * Reminder System: Email/SMS reminders based on user preferences.

   * Billing Module: Invoice generation, insurance policies, payment tracking.

   * Accessibility Modes: High‑contrast and larger‑font views.

   * Web Push Notifications: Browser push via VAPID keys.

   * Weather Alerts (Demo): Rescheduling suggestions on severe weather.

________________


Requirements
      * Python 3.8+

      * Django 3.2.x

      * PostgreSQL or SQLite (default)

      * Redis (for production caching and Celery, optional)

      * Twilio SDK (optional, for SMS)

      * APScheduler (for scheduler)

Python packages:

Django>=3.2
djangorestframework
django‑webpush
apscheduler
twilio  # if using SMS
python-dateutil
         * ________________


Installation & Setup
Clone the repository

 git clone https://github.com/yourorg/mediq.git
cd mediq
         1. Create a virtual environment & install dependencies

 python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
         2.          3. Configure settings

            * Copy mediq/mediq/settings.py and adjust:

               * SECRET_KEY

               * DEBUG

               * ALLOWED_HOSTS

               * Email SMTP credentials (EMAIL_HOST_USER, EMAIL_HOST_PASSWORD) ​

               * VAPID keys under WEBPUSH_SETTINGS ​

Collect static files

 python manage.py collectstatic
                  4. ________________


Database Migrations & Seeding
Run migrations

 python manage.py makemigrations
python manage.py migrate
                  1. Create superuser

 python manage.py createsuperuser
                  2. Populate initial doctors
 This command seeds the database with predefined doctors. ​

python manage.py populate_doctors
                  3. ________________


Running the Application
Start the development server:
python manage.py runserver


                  * Patient portal: http://localhost:8000/

                  * Admin panel: http://localhost:8000/admin/

Login routes are defined in mediq/mediq/urls.py ​.
________________


Automated Reminders Scheduler
To send daily appointment reminders, run the scheduler command:
python manage.py send_reminders


This uses APScheduler to invoke accounts.reminder.remind_patients() every day at midnight. ​
________________


Project Structure
bash
mediq/
├── accounts/
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── views.py
│   ├── reminder.py
│   ├── scheduler.py
│   ├── management/
│   │   └── commands/
│   │       ├── populate_doctors.py
│   │       └── send_reminders.py
│   ├── migrations/
│   ├── templates/accounts/    # HTML templates
│   └── static/accounts/       # CSS, JS, service worker
├── mediq/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── manage.py
└── requirements.txt


________________


Environment Variables
Recommended to use a .env file or CI/CD secrets for sensitive data:
SECRET_KEY=your-secret-key
EMAIL_HOST_USER=you@example.com
EMAIL_HOST_PASSWORD=app-password
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your-token
WEBPUSH_VAPID_PRIVATE_KEY=...
WEBPUSH_VAPID_PUBLIC_KEY=...


________________


Contributing
                     1. Fork the repo & create a feature branch

                     2. Write tests for new functionality

                     3. Ensure code style compliance (PEP8)

                     4. Submit a pull request with a clear description

________________


License
This project is licensed under the MIT License.
© 2025 Mediq Healthcare.
