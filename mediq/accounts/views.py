from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .forms import SignUpForm, LoginForm
from django.views.decorators.csrf import csrf_exempt
from .reminder import remind_patients
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta, time
from django.db.models import Sum
from .reminder import send_email_reminder, send_sms_reminder
from .scheduler import MediqChatbot, DOCTORS, AZURE_TTS_KEY_1
from .models import Appointment
from django.contrib import messages
import json
from django.conf import settings
from .models import NotificationPreference

from .models import (
    Appointment, ReminderPreference, SentReminder, 
    InsuranceProvider, InsurancePolicy, BillingRecord, 
    Payment, ServiceType, BillingService, DoctorBusyTime
)
# ------------------------------
# Existing Views (Signup, Login, etc.)
# ------------------------------

import random, string
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import SignUpForm

def _make_code(length=5):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def signup_view(request):
    # on GET: generate+store a fresh code
    if request.method == 'GET':
        request.session['signup_code'] = _make_code()
        form = SignUpForm()
        return render(request, 'accounts/signup.html', {
            'form': form,
            'captcha_code': request.session['signup_code'],
        })

    # on POST: bind form & validate captcha
    form = SignUpForm(request.POST, request.FILES)
    expected = request.session.get('signup_code', '')
    entered  = request.POST.get('captcha_input', '').strip().upper()

    if entered != expected:
        form.add_error('captcha_input', "That code doesn't match.")

    if form.is_valid():
        # … your existing user‑creation logic …
        username = form.cleaned_data['username']
        email    = form.cleaned_data['email']
        password = form.cleaned_data['password']
        user = User.objects.create_user(username=username, email=email, password=password)
        profile = user.profile
        profile.age   = form.cleaned_data.get('age')
        profile.phone = form.cleaned_data.get('phone')
        if request.FILES.get('profile_picture'):
            profile.profile_picture = request.FILES['profile_picture']
        profile.save()
        login(request, user)
        return redirect('dashboard')

    # if we reach here, either form error or bad code → regenerate code
    request.session['signup_code'] = _make_code()
    return render(request, 'accounts/signup.html', {
        'form': form,
        'captcha_code': request.session['signup_code'],
    })


def profile_view(request):
    """User profile settings view"""
    return render(request, 'accounts/profile.html')

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                form.add_error(None, "Invalid credentials")
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard_view(request):
    return render(request, 'accounts/dashboard.html')

def smart_scheduling_view(request):
    # This could be used if you want a separate smart scheduling page.
    # Currently, the chatbot view is used for smart scheduling.
    return render(request, 'accounts/smart_scheduling.html')
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import SignUpForm, LoginForm, PatientMessageForm, DoctorMessageForm
from .models import Message

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Doctor, Message
from .forms import SignUpForm, LoginForm, PatientMessageForm, DoctorMessageForm

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import SignUpForm, LoginForm, PatientMessageForm, DoctorMessageForm
from .models import Doctor

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.templatetags.static import static

from .forms import SignUpForm, LoginForm, PatientMessageForm, DoctorMessageForm
from .models import Doctor

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.templatetags.static import static

from .forms import SignUpForm, LoginForm, PatientMessageForm, DoctorMessageForm
from .models import Doctor

# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.templatetags.static import static

from .forms import SignUpForm, LoginForm, PatientMessageForm, DoctorMessageForm
from .models import Doctor

# accounts/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.templatetags.static import static

from .forms import PatientMessageForm
from .models import Doctor, Message
# accounts/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages

from .models import Doctor, Message
from .forms import PatientMessageForm, DoctorMessageForm

@login_required
def patient_chat_list(request):
    """
    Show a list of doctors the current user has chatted with.
    """
    # Doctors where user has either sent or received a message
    doctor_ids = Message.objects.filter(
        Q(sender_user=request.user) | Q(receiver_user=request.user)
    ).values_list('receiver_doctor', 'sender_doctor')
    # flatten and remove None, then unique
    flat = set(d for pair in doctor_ids for d in pair if d)
    doctors = Doctor.objects.filter(id__in=flat)

    return render(request, 'accounts/patient_chat_list.html', {
        'doctors': doctors
    })


@login_required
def patient_chat_detail(request, doctor_id):
    """
    Show the two‑way chat between request.user and Doctor(pk=doctor_id).
    """
    doctor = get_object_or_404(Doctor, pk=doctor_id)

    # Build the chat history
    chat_history = Message.objects.filter(
        Q(sender_user=request.user,   receiver_doctor=doctor) |
        Q(sender_doctor=doctor,       receiver_user=request.user)
    ).order_by('timestamp')

    form = PatientMessageForm(request.POST or None)
    form.fields['receiver_doctor'].queryset = Doctor.objects.filter(pk=doctor_id)

    if request.method == 'POST' and form.is_valid():
        msg = form.save(commit=False)
        msg.sender_user = request.user
        msg.receiver_doctor = doctor
        msg.save()
        return redirect('patient_chat_detail', doctor_id=doctor_id)

    return render(request, 'accounts/patient_chat_detail.html', {
        'doctor': doctor,
        'chat_history': chat_history,
        'form': form
    })


@login_required
def doctor_chat_list(request):
    """
    Show a list of patients that have messaged this doctor.
    """
    # must have set request.session['doctor_id'] on login
    doctor = get_object_or_404(Doctor, pk=request.session.get('doctor_id'))

    # Users who have either sent to or received from this doctor
    user_ids = Message.objects.filter(
        Q(sender_doctor=doctor) | Q(receiver_doctor=doctor)
    ).values_list('receiver_user', 'sender_user')
    flat = set(u for pair in user_ids for u in pair if u)
    from django.contrib.auth.models import User
    patients = User.objects.filter(id__in=flat)

    return render(request, 'accounts/doctor_chat_list.html', {
        'doctor': doctor,
        'patients': patients
    })


@login_required
def doctor_chat_detail(request, patient_id):
    """
    Two‑way chat between Doctor and a selected patient.
    """
    doctor = get_object_or_404(Doctor, pk=request.session.get('doctor_id'))
    from django.contrib.auth.models import User
    patient = get_object_or_404(User, pk=patient_id)

    chat_history = Message.objects.filter(
        Q(sender_doctor=doctor,    receiver_user=patient) |
        Q(sender_user=patient,     receiver_doctor=doctor)
    ).order_by('timestamp')

    form = DoctorMessageForm(request.POST or None)
    form.fields['receiver_user'].queryset = [patient]

    if request.method == 'POST' and form.is_valid():
        msg = form.save(commit=False)
        msg.sender_doctor = doctor
        msg.receiver_user = patient
        msg.save()
        return redirect('doctor_chat_detail', patient_id=patient_id)

    return render(request, 'accounts/doctor_chat_detail.html', {
        'doctor': doctor,
        'patient': patient,
        'chat_history': chat_history,
        'form': form
    })

@login_required
def contact_doctor_view(request):
    # 1) pull in every doctor from the database
    doctors = Doctor.objects.all()

    # 2) Always assign the static default avatar URL to each doctor
    for doc in doctors:
        filename = f"Dr.{doc.name.lower()}.jpg"
        doc.img_url = static(f"accounts/images/{filename}")

    if request.method == 'POST':
        # instantiate the form with POST data
        form = PatientMessageForm(request.POST)
        # restrict the doctor choices to your actual doctors queryset
        form.fields['receiver_doctor'].queryset = doctors

        if form.is_valid():
            msg = form.save(commit=False)
            # set the user→doctor direction properly
            msg.sender_user = request.user
            msg.save()
            messages.success(request, "Your message has been sent!")
            return redirect('dashboard')
    else:
        form = PatientMessageForm()
        form.fields['receiver_doctor'].queryset = doctors

    return render(request, 'accounts/contact_doctor.html', {
        'form': form,
        'doctors': doctors,
    })


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from .models import Doctor, Message
from .forms import SignUpForm, LoginForm, PatientMessageForm, DoctorMessageForm

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Doctor, Message
from .forms import SignUpForm, LoginForm, PatientMessageForm, DoctorMessageForm

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User

from .models import Doctor, Message
from .forms import DoctorMessageForm

# accounts/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.templatetags.static import static
from django.db.models import Q

from .models import Doctor, Message
from .forms import PatientMessageForm

# accounts/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.templatetags.static import static
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse

from .models import Doctor, Message
from .forms import PatientMessageForm

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Doctor, Message
from .forms import PatientMessageForm
from django.db.models import Q
from django.urls import reverse

from django.shortcuts  import render, redirect, get_object_or_404
from django.urls      import reverse
from django.contrib   import messages
from django.contrib.auth.models import User
from django.db.models import Q

from .models   import Doctor, Message

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from django.urls import reverse

from .models import Doctor, Message

# accounts/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from django.urls import reverse

from .models import Doctor, Message

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from django.urls import reverse

from .models import Doctor, Message

# in accounts/views.py

from django.shortcuts   import render, redirect, get_object_or_404
from django.contrib    import messages
from django.contrib.auth.models import User
from django.db.models  import Q
from django.urls       import reverse

from .models  import Doctor, Message

def doctor_contact_patient_view(request):
    # 1) Identify the logged‑in Doctor
    doctor_id = request.session.get('doctor_id')
    if not doctor_id:
        return redirect('doctor_login')
    doctor = get_object_or_404(Doctor, id=doctor_id)

    # 2) All patients who've ever exchanged messages with this doctor
    patients = User.objects.filter(
        Q(sent_messages__receiver_doctor=doctor) |
        Q(received_messages__sender_doctor=doctor)
    ).distinct().order_by('username')

    # 3) Which patient is selected?
    sel_id = request.GET.get('patient')
    selected_patient = None
    chat_history = []

    if sel_id:
        selected_patient = get_object_or_404(User, id=sel_id)

        # 4) If POST, send the doctor's reply
        if request.method == 'POST':
            content = request.POST.get('content', '').strip()
            if content:
                Message.objects.create(
                    sender_doctor=doctor,
                    receiver_user=selected_patient,
                    content=content
                )
                # reload with same patient in URL
                return redirect(f"{reverse('doctor_contact_patient')}?patient={sel_id}")

        # 5) Pull the two‑way chat history
        chat_history = Message.objects.filter(
            Q(sender_doctor=doctor,      receiver_user=selected_patient) |
            Q(sender_user=selected_patient, receiver_doctor=doctor)
        ).order_by('timestamp')

    return render(request, 'accounts/doctor_contact_patient.html', {
        'doctor':           doctor,
        'patients':         patients,
        'selected_patient': selected_patient,
        'chat_history':     chat_history,
    })



from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.db.models import Q
from .models import Doctor, Message
from .forms import PatientMessageForm
from django.templatetags.static import static

def contact_doctor_view(request):
    # 1) load all doctors (attach avatar URL)
    doctors = list(Doctor.objects.all())
    for doc in doctors:
        fn = f"Dr.{doc.name.lower()}.jpg"
        doc.img_url = static(f"accounts/images/{fn}")

    # 2) figure out which doctor is selected
    sel_id = request.GET.get('doctor') or request.POST.get('receiver_doctor')
    try:
        selected = next(d for d in doctors if str(d.id) == str(sel_id))
    except StopIteration:
        selected = doctors[0] if doctors else None

    # 3) pull full two‑way history
    chat_history = []
    if selected:
        chat_history = Message.objects.filter(
            Q(sender_user=request.user,    receiver_doctor=selected) |
            Q(sender_doctor=selected,      receiver_user=request.user)
        ).order_by('timestamp')

    # 4) form setup + send
    form = PatientMessageForm(request.POST or None)
    form.fields['receiver_doctor'].queryset = Doctor.objects.filter(id=selected.id) if selected else Doctor.objects.none()

    if request.method == 'POST' and form.is_valid():
        msg = form.save(commit=False)
        msg.sender_user     = request.user
        msg.receiver_doctor = selected
        msg.save()
        messages.success(request, "Message sent!")
        return redirect(f"{reverse('contact_doctor')}?doctor={selected.id}")

    return render(request, 'accounts/contact_doctor.html', {
        'doctors':      doctors,
        'selected':     selected,
        'chat_history': chat_history,
        'form':         form,
    })


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import SignUpForm, LoginForm, PatientMessageForm, DoctorMessageForm
from .models import Message, Doctor

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Doctor, Message
from django.contrib.auth.models import User

from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Doctor, Message

class MultiMessageForm(forms.Form):
    receiver = forms.ModelMultipleChoiceField(
        label="Select patient(s)",
        queryset=User.objects.none(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
    )
    content = forms.CharField(
        label="Your message",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4})
    )

from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Doctor, Message

# accounts/views.py

from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth.models import User

from .models import Doctor, Message
from .forms import DoctorMessageForm


from django.db.models import Q

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from django.urls import reverse

from .models import Doctor, Message
from .forms import PatientMessageForm

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q

from .models import Doctor, Message

from django.shortcuts      import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models    import User
from django.db.models      import Q
from django.urls           import reverse
from .models               import Doctor, Message
from functools import wraps
from django.shortcuts import redirect

def doctor_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.session.get('doctor_id'):
            return redirect('doctor_login')
        return view_func(request, *args, **kwargs)
    return _wrapped


def doctor_contact_patient_view(request):
    # 1) Identify the logged‑in Doctor
    doctor_id = request.session.get('doctor_id')
    if not doctor_id:
        return redirect('doctor_login')
    doctor = get_object_or_404(Doctor, id=doctor_id)

    # 2) Get all Users who've ever messaged this doctor (either direction)
    patients = User.objects.filter(
        Q(sent_messages__receiver_doctor=doctor) |
        Q(received_messages__sender_doctor=doctor)
    ).distinct().order_by('username')

    # 3) Which patient is selected?
    sel_id = request.GET.get('patient')
    selected_patient = None
    chat_history = []

    if sel_id:
        selected_patient = get_object_or_404(User, pk=sel_id)

        # 4) Handle doctor's reply
        if request.method == 'POST':
            content = request.POST.get('content', '').strip()
            if content:
                Message.objects.create(
                    sender_doctor=doctor,
                    receiver_user=selected_patient,
                    content=content
                )
                return redirect(f"{reverse('doctor_contact_patient')}?patient={sel_id}")

        # 5) Pull the two‑way chat history
        chat_history = Message.objects.filter(
            Q(sender_doctor=doctor,      receiver_user=selected_patient) |
            Q(sender_user=selected_patient, receiver_doctor=doctor)
        ).order_by('timestamp')

    return render(request, 'accounts/doctor_contact_patient.html', {
        'doctor':           doctor,
        'patients':         patients,
        'selected_patient': selected_patient,
        'chat_history':     chat_history,
    })



@login_required
def appointment_reminder_view(request):
    """View reverted to show upcoming appointments list"""
    
    # Get reminder preferences if needed for display/other logic
    try:
        preference = request.user.reminder_preference
    except (AttributeError, ReminderPreference.DoesNotExist):
        preference = ReminderPreference.objects.create(user=request.user)
        
    now = timezone.now()
    today = now.date()
    
    # Filter for TODAY's and FUTURE appointments ONLY
    appointments = Appointment.objects.filter(
        user=request.user,
        date__gte=today 
    ).order_by('date', 'time') # Order by soonest first

    for appointment in appointments:
        # Add simple flags if needed by template
        appointment.is_today = (appointment.date == today)
        
        # Check if already checked-in (assuming migrations worked)
        try:
            appointment.has_checked_in = CheckIn.objects.filter(user=request.user, appointment=appointment).exists()
        except Exception as e: 
             print(f"DB Error checking check-in (reminder view) for appt {appointment.id}: {e}")
             appointment.has_checked_in = False # Fallback

    context = {
        'preference': preference, 
        'appointments': appointments,
        'message': request.session.pop('message', None) 
    }
    
    # Render the list template
    return render(request, 'accounts/appointment_reminder.html', context) 

def billing_insurance_view(request):
    return render(request, 'accounts/billing_insurance.html')

def accessibility_mode_view(request):
    return render(request, 'accounts/accessibility_mode.html')

def toggle_accessibility_view(request):
    if request.session.get('accessibility_mode'):
        request.session['accessibility_mode'] = False
    else:
        request.session['accessibility_mode'] = True
    # Temporary print statement to debug accessibility mode state:
    print("Accessibility mode is now:", request.session.get('accessibility_mode'))
    return redirect('dashboard')

from django.contrib.auth.decorators import login_required
from .models import CheckIn

@login_required
def virtual_check_in_view(request, appointment_id):
    """Displays status and timer for a specific appointment check-in."""
    appointment = get_object_or_404(Appointment, id=appointment_id, user=request.user)
    
    now = timezone.now()
    today = now.date()
    
    # Combine date/time, ensure aware
    naive_datetime = datetime.combine(appointment.date, appointment.time)
    if timezone.is_naive(naive_datetime):
         appointment_start_dt = timezone.make_aware(naive_datetime, timezone.get_current_timezone())
    else:
         appointment_start_dt = timezone.localtime(appointment.time) if timezone.is_aware(appointment.time) else timezone.make_aware(naive_datetime, timezone.get_current_timezone())

    # Check-in window calculation
    check_in_window_duration = timedelta(hours=1)
    check_in_start_time = appointment_start_dt - check_in_window_duration

    # Calculate status and time remaining
    can_check_in = False
    is_expired = False
    seconds_until_appointment = -1
    seconds_to_checkin_window = -1
    has_checked_in = False

    # Check if already checked in (requires successful migration)
    try:
        has_checked_in = CheckIn.objects.filter(user=request.user, appointment=appointment).exists()
    except Exception as e:
        print(f"DB Error checking check-in (status view) for appt {appointment.id}: {e}")
        has_checked_in = False # Fallback

    if not has_checked_in: # Only calculate if not already checked in
        if now >= appointment_start_dt:
            is_expired = True
        elif now >= check_in_start_time:
            can_check_in = True
            time_until_appt = appointment_start_dt - now
            seconds_until_appointment = int(time_until_appt.total_seconds())
        elif appointment_start_dt > now:
            time_until_window = check_in_start_time - now
            seconds_to_checkin_window = int(time_until_window.total_seconds())
            time_until_appt = appointment_start_dt - now
            seconds_until_appointment = int(time_until_appt.total_seconds())
            
    context = {
        'appointment': appointment,
        'can_check_in': can_check_in,
        'is_expired': is_expired,
        'has_checked_in': has_checked_in,
        'seconds_to_checkin_window': seconds_to_checkin_window, 
        'seconds_until_appointment': seconds_until_appointment, 
        'appointment_datetime_iso': appointment_start_dt.isoformat(), 
    }
    
    # Render the template (which should be renamed to virtual_check_in.html)
    return render(request, 'accounts/virtual_check_in.html', context)

@csrf_exempt  # For testing purposes; consider removing in production.
def trigger_reminder_view(request):
    message = ""
    if request.method == 'POST':
        remind_patients()
        message = "Reminders have been sent."
    return render(request, 'accounts/appointment_reminder.html', {'message': message})

# ------------------------------
# New Smart Scheduler Views (Integrated as a Feature)
# ------------------------------

import uuid
import requests

# Configuration for Dialogflow via Google Cloud.
PROJECT_ID = "f430-qncx"  # Your Dialogflow Project ID
API_KEY = "sk-be3748ba0fdb4eba8f5dcda980153b4e"  # Your provided API key
LANGUAGE_CODE = "en"

# accounts/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import datetime
# Remove MediqChatbot, DOCTORS, AZURE_TTS_KEY_1 imports if they are no longer used elsewhere after this removal
# from .scheduler import MediqChatbot, DOCTORS, AZURE_TTS_KEY_1 

# Comment out or delete the entire smart_scheduler function
# @login_required
# def smart_scheduler(request):
#     chatbot = MediqChatbot(request.user)
#     response_message = ""
#     # ... (rest of the function code) ...
#     return render(request, "accounts/smart_scheduler.html", context)


from datetime import datetime
from django.contrib import messages

from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import Appointment, DoctorBusyTime, Doctor

from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import Appointment, DoctorBusyTime, Doctor

from datetime import datetime
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib import messages

# … your other imports …

from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.db.models import Q

from .models import Appointment, DoctorBusyTime, Doctor

@login_required
def book_appointment_direct(request):
    doctors = {
        "Dr. Salim": "Cardiology",
        "Dr. Haddad": "Dermatology",
        "Dr. Nassar": "Pediatrics",
        "Dr. Farah": "Neurology",
        "Dr. Kassem": "Orthopedics",
    }
    time_slots = ['09:00','10:00','11:00','12:00','13:00','14:00','15:00','16:00','17:00']

    selected_doctor = selected_date = selected_time = None
    available_slots = list(time_slots)

    if request.method == 'POST':
        selected_doctor = request.POST.get('doctor')
        selected_date   = request.POST.get('date')
        selected_time   = request.POST.get('time')
        reason          = request.POST.get('reason', '')
        contact         = request.POST.get('contact') or request.user.email
        insurance       = request.POST.get('insurance', '')

        # <— initialize here so it always exists below
        doc_obj = None

        # parse date/time
        try:
            date_obj = datetime.strptime(selected_date, '%Y-%m-%d').date()
            time_obj = datetime.strptime(selected_time, '%H:%M').time()
        except (ValueError, TypeError):
            messages.error(request, "Invalid date or time.")
        else:
            # 1) double‑book check
            if Appointment.objects.filter(
                doctor=selected_doctor, date=date_obj, time=time_obj
            ).exists():
                messages.error(request,
                    f"{selected_time} on {selected_date} is already booked.")
            else:
                # 2) busy‑time lookup
                name_key = selected_doctor.replace("Dr. ", "").strip()
                doc_obj  = Doctor.objects.filter(name__iexact=name_key).first()
                busy_conflict = False

                if doc_obj:
                    for b in DoctorBusyTime.objects.filter(doctor=doc_obj, date=date_obj):
                        if b.start_time <= time_obj < b.end_time:
                            busy_conflict = True
                            messages.error(request,
                                f"Dr. {doc_obj.name} is busy at {selected_time} on {selected_date}.")
                            break

                # 3) create appointment if clear
                if not busy_conflict and not messages.get_messages(request):
                    Appointment.objects.create(
                        user=request.user,
                        doctor=selected_doctor,
                        specialty=doctors[selected_doctor],
                        date=date_obj,
                        time=time_obj,
                        reason=reason,
                        contact=contact,
                        insurance=insurance
                    )
                    messages.success(request, "Appointment booked successfully!")
                    return redirect('appointment_reminder')

            # recompute available_slots after any errors
            booked_times = Appointment.objects.filter(
                doctor=selected_doctor, date=date_obj
            ).values_list('time', flat=True)
            booked_str = [t.strftime('%H:%M') for t in booked_times]

            busy_str = []
            if doc_obj:
                for b in DoctorBusyTime.objects.filter(doctor=doc_obj, date=date_obj):
                    for slot in time_slots:
                        slot_t = datetime.strptime(slot, '%H:%M').time()
                        if b.start_time <= slot_t < b.end_time:
                            busy_str.append(slot)

            unavailable = set(booked_str) | set(busy_str)
            available_slots = [s for s in time_slots if s not in unavailable]

    context = {
        'doctors':            doctors,
        'today':              datetime.now().date().strftime('%Y-%m-%d'),
        'time_slots':         time_slots,
        'available_slots':    available_slots,
        'selected_doctor':    selected_doctor,
        'selected_specialty': doctors.get(selected_doctor, '') if selected_doctor else '',
        'selected_date':      selected_date,
        'selected_time':      selected_time,
    }
    return render(request, 'accounts/book_appointment.html', context)




@login_required
def profile_view(request):
    """User profile settings view"""
    return render(request, 'accounts/profile.html')

@login_required
def profile_update(request):
    """Handle profile updates from different forms"""
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        
        if form_type == 'account_info':
            # Update account information
            user = request.user
            user.username = request.POST.get('username')
            user.email = request.POST.get('email')
            user.first_name = request.POST.get('first_name')
            user.last_name = request.POST.get('last_name')
            user.save()
            
            # Update profile information
            profile = user.profile
            profile.age = request.POST.get('age') or None
            profile.phone = request.POST.get('phone') or None
            profile.save()
            
            messages.success(request, "Account information updated successfully!")
            
        elif form_type == 'change_password':
            # Change password
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            user = request.user
            if user.check_password(current_password):
                if new_password == confirm_password:
                    user.set_password(new_password)
                    user.save()
                    # Update session to prevent logout
                    from django.contrib.auth import update_session_auth_hash
                    update_session_auth_hash(request, user)
                    messages.success(request, "Password changed successfully!")
                else:
                    messages.error(request, "New passwords don't match!")
            else:
                messages.error(request, "Current password is incorrect!")
                
        elif form_type == 'profile_picture':
            # Update profile picture
            profile_picture = request.FILES.get('profile_picture')
            if profile_picture:
                profile = request.user.profile
                profile.profile_picture = profile_picture
                profile.save()
                messages.success(request, "Profile picture updated successfully!")
            else:
                messages.error(request, "No file selected!")
    
    return redirect('profile')
# ------------------------------
# New Accessibility Settings View
# ------------------------------

@login_required
def accessibility_settings_view(request):
    """
    Allows users to toggle individual accessibility features:
      - dark_mode: Enable dark background.
      - large_text: Increase font size (predefined).
      - alternative_font: Use an alternative font.
      - high_contrast: Enable high contrast mode.
      - font_size: Custom font size via a slider.
    High contrast mode is mutually exclusive with dark mode.
    Settings are stored in the session.
    """
    if request.method == 'POST':
        dark_mode = (request.POST.get('dark_mode') == 'on')
        large_text = (request.POST.get('large_text') == 'on')
        alternative_font = (request.POST.get('alternative_font') == 'on')
        high_contrast = (request.POST.get('high_contrast') == 'on')
        # Enforce mutual exclusivity: if high contrast is enabled, disable dark mode.
        if high_contrast:
            dark_mode = False
        # Save custom font size (using a slider)
        font_size = request.POST.get('font_size')
        try:
            font_size = int(font_size) if font_size else 22
        except ValueError:
            font_size = 22
        
        request.session['dark_mode'] = dark_mode
        request.session['large_text'] = large_text
        request.session['alternative_font'] = alternative_font
        request.session['high_contrast'] = high_contrast
        request.session['font_size'] = font_size
        
        return redirect('dashboard')
    
    # Set a default custom font size if not already set
    if 'font_size' not in request.session:
        request.session['font_size'] = 22
        
    return render(request, 'accounts/accessibility_settings.html')

@login_required
def dashboard_view(request):
    """Enhanced dashboard view with upcoming appointments and notifications"""
    
    # Get user's upcoming appointment
    today = timezone.now().date()
    upcoming_appointment = Appointment.objects.filter(
        user=request.user,
        date__gte=today
    ).order_by('date', 'time').first()
    
    # Count unpaid bills
    try:
        unpaid_bills = BillingRecord.objects.filter(
            user=request.user,
            payment_status__in=['unpaid', 'partially_paid']
        ).count()
    except:
        unpaid_bills = 0  # In case BillingRecord isn't fully set up yet
    
    # Check if insurance needs verification
    insurance_needs_verification = False
    try:
        insurance_policy = request.user.insurance_policy
        if insurance_policy and not insurance_policy.coverage_verified:
            insurance_needs_verification = True
    except:
        pass  # No insurance policy or not set up yet
    
    # Count appointments needing reminders
    pending_reminders = 0
    try:
        # Get upcoming appointments without sent reminders
        upcoming_appointments = Appointment.objects.filter(
            user=request.user,
            date__gte=today
        ).exclude(
            id__in=SentReminder.objects.values_list('appointment_id', flat=True)
        ).count()
        
        if upcoming_appointments > 0:
            pending_reminders = upcoming_appointments
    except:
        pass  # SentReminder might not be set up yet
    
    context = {
        'upcoming_appointment': upcoming_appointment,
        'unpaid_bills': unpaid_bills,
        'insurance_needs_verification': insurance_needs_verification,
        'pending_reminders': pending_reminders
    }
    
    return render(request, 'accounts/dashboard.html', context)

@login_required
def save_reminder_preferences(request):
    """Save user's reminder preferences"""
    if request.method == 'POST':
        # Get existing preferences or create new
        try:
            preference = request.user.reminder_preference
        except (AttributeError, ReminderPreference.DoesNotExist):
            preference = ReminderPreference(user=request.user)
        
        # Update preference settings
        preference.email_reminders = 'email_reminders' in request.POST
        preference.sms_reminders = 'sms_reminders' in request.POST
        
        # Get and validate days_before
        days_before = request.POST.get('days_before')
        if days_before in ['1', '2', '3', '7']:
            preference.days_before = int(days_before)
        
        # Get and validate hours_before
        hours_before = request.POST.get('hours_before')
        if hours_before in ['0', '2', '6', '12', '24']:
            preference.hours_before = int(hours_before)
        
        preference.save()
        
        request.session['message'] = "Reminder preferences saved successfully."
    
    return redirect('appointment_reminder')

@login_required
def send_reminder_now(request):
    """Manually send a reminder for a specific appointment"""
    if request.method == 'POST':
        appointment_id = request.POST.get('appointment_id')
        if not appointment_id:
            return JsonResponse({'success': False, 'message': 'No appointment specified.'})
        
        try:
            appointment = Appointment.objects.get(id=appointment_id, user=request.user)
            
            # Simple email
            user = appointment.user
            subject = "MedIQ Appointment Reminder"
            message = f"Hello {user.username},\n\nThis is a reminder for your appointment with {appointment.doctor} on {appointment.date} at {appointment.time}.\n\nBest regards,\nMedIQ Team"
            
            # Use Django's send_mail function
            from django.core.mail import send_mail
            send_mail(
                subject=subject,
                message=message,
                from_email='noreply@mediq.com',
                recipient_list=[user.email],
                fail_silently=False,
            )
            
            # Record this reminder
            from .models import SentReminder
            SentReminder.objects.get_or_create(
                appointment=appointment,
                reminder_type='email'
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Reminder sent successfully!'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})

from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Appointment, DoctorBusyTime, Doctor
from .models import SentReminder  # for clearing reminders
# … your other imports …

@login_required
def edit_appointment(request, appointment_id):
    """Edit an existing appointment, but disallow busy/unavailable slots."""
    appointment = get_object_or_404(Appointment, id=appointment_id, user=request.user)

    # ----- POST handling (unchanged) -----
    if request.method == 'POST':
        appointment.doctor    = request.POST.get('doctor', appointment.doctor)
        appointment.specialty = request.POST.get('specialty', appointment.specialty)

        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        if date_str:
            try:
                appointment.date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        if time_str:
            try:
                appointment.time = datetime.strptime(time_str, '%H:%M').time()
            except ValueError:
                pass

        appointment.reason    = request.POST.get('reason', appointment.reason)
        appointment.contact   = request.POST.get('contact', appointment.contact)
        appointment.insurance = request.POST.get('insurance', appointment.insurance)

        appointment.save()
        # clear any sent reminders
        SentReminder.objects.filter(appointment=appointment).delete()
        messages.success(request, "Appointment updated successfully.")
        return redirect('appointment_reminder')

    # ----- GET: compute available slots just like in your booking view -----
    time_slots   = ['09:00','10:00','11:00','12:00','13:00','14:00','15:00','16:00','17:00']
    selected_doc = appointment.doctor
    date_obj     = appointment.date

    # find the Doctor instance
    key     = selected_doc.replace("Dr. ", "").strip()
    doc_obj = Doctor.objects.filter(name__iexact=key).first()

    # slots already booked _excluding_ this appointment
    booked_qs  = Appointment.objects.filter(
        doctor=selected_doc,
        date=date_obj
    ).exclude(id=appointment.id).values_list('time', flat=True)
    booked_str = {t.strftime('%H:%M') for t in booked_qs}

    busy_str = set()
    if doc_obj:
        for b in DoctorBusyTime.objects.filter(doctor=doc_obj, date=date_obj):
            for slot in time_slots:
                t = datetime.strptime(slot, '%H:%M').time()
                if b.start_time <= t < b.end_time:
                    busy_str.add(slot)

    unavailable    = booked_str | busy_str
    available_slots = [s for s in time_slots if s not in unavailable]

    context = {
        'appointment':     appointment,
        'doctors':         [ "Dr. Salim", "Dr. Haddad", "Dr. Nassar", "Dr. Farah", "Dr. Kassem" ],
        'specialties':     [ "Cardiology", "Dermatology", "Pediatrics", "Neurology", "Orthopedics", "General Medicine" ],
        'time_slots':      time_slots,
        'available_slots': available_slots,
    }
    return render(request, 'accounts/edit_appointment.html', context)

def doctor_accessibility_settings_view(request):
    doctor_id = request.session.get('doctor_id')
    if not doctor_id:
        return redirect('doctor_login')

    if request.method == 'POST':
        dark_mode = (request.POST.get('dark_mode') == 'on')
        large_text = (request.POST.get('large_text') == 'on')
        alternative_font = (request.POST.get('alternative_font') == 'on')
        high_contrast = (request.POST.get('high_contrast') == 'on')

        if high_contrast:
            dark_mode = False

        font_size = request.POST.get('font_size')
        try:
            font_size = int(font_size) if font_size else 22
        except ValueError:
            font_size = 22

        request.session['dark_mode'] = dark_mode
        request.session['large_text'] = large_text
        request.session['alternative_font'] = alternative_font
        request.session['high_contrast'] = high_contrast
        request.session['font_size'] = font_size

        return redirect('doctor_dashboard')

    if 'font_size' not in request.session:
        request.session['font_size'] = 22

    return render(request, 'accounts/doctor_accessibility_settings.html')

@login_required
def cancel_appointment(request, appointment_id):
    """Cancel an existing appointment"""
    appointment = get_object_or_404(Appointment, id=appointment_id, user=request.user)
    
    if request.method == 'POST':
        # In a real system, you might want to keep a record of cancelled appointments
        # For this demo, we'll just delete it
        appointment.delete()
        
        request.session['message'] = "Appointment cancelled successfully."
        return redirect('appointment_reminder')
    
    # If not POST, render a confirmation page
    context = {
        'appointment': appointment,
    }
    
    return render(request, 'accounts/cancel_appointment.html', context)

@login_required
def billing_insurance_view(request):
    """Main billing and insurance dashboard"""
    
    # Get user's insurance policy
    try:
        insurance_policy = request.user.insurance_policy
        has_insurance = True
    except (AttributeError, InsurancePolicy.DoesNotExist):
        insurance_policy = None
        has_insurance = False
    
    # Get insurance providers for the dropdown
    insurance_providers = InsuranceProvider.objects.filter(is_active=True)
    
    # Get user's billing records
    billing_records = BillingRecord.objects.filter(user=request.user).order_by('-service_date')
    
    # Calculate total due amount
    total_due = billing_records.filter(
        payment_status__in=['unpaid', 'partially_paid']
    ).aggregate(Sum('patient_responsibility'))['patient_responsibility__sum'] or 0
    
    # Get recent payments
    recent_payments = Payment.objects.filter(
        billing_record__user=request.user
    ).order_by('-payment_date')[:5]
    
    # Get overdue bills
    today = timezone.now().date()
    overdue_bills = billing_records.filter(
        payment_due_date__lt=today,
        payment_status__in=['unpaid', 'partially_paid']
    )
    
    context = {
        'insurance_policy': insurance_policy,
        'has_insurance': has_insurance,
        'insurance_providers': insurance_providers,
        'billing_records': billing_records,
        'total_due': total_due,
        'recent_payments': recent_payments,
        'overdue_bills': overdue_bills,
    }
    
    return render(request, 'accounts/billing_insurance.html', context)

@login_required
@login_required
def add_insurance_policy(request):
    """Add or update insurance policy information"""
    if request.method == 'POST':
        provider_id = request.POST.get('provider')
        policy_number = request.POST.get('policy_number')
        group_number = request.POST.get('group_number')
        member_id = request.POST.get('member_id')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date') or None
        primary_holder_name = request.POST.get('primary_holder_name')
        primary_holder_relationship = request.POST.get('primary_holder_relationship')
        
        # Validate required fields
        if not all([provider_id, policy_number, member_id, start_date, primary_holder_name]):
            try:
                from django.contrib import messages
                messages.error(request, 'Please fill in all required fields.')
            except:
                pass
            return redirect('billing_insurance')
        
        try:
            provider = InsuranceProvider.objects.get(id=provider_id)
            
            # Check if user already has a policy and update it, otherwise create new
            try:
                policy = request.user.insurance_policy
                policy.provider = provider
                policy.policy_number = policy_number
                policy.group_number = group_number
                policy.member_id = member_id
                policy.start_date = start_date
                policy.end_date = end_date
                policy.primary_holder_name = primary_holder_name
                policy.primary_holder_relationship = primary_holder_relationship
                policy.coverage_verified = False  # Reset verification status
                policy.save()
                message = "Insurance policy updated successfully."
            except (AttributeError, InsurancePolicy.DoesNotExist):
                policy = InsurancePolicy.objects.create(
                    user=request.user,
                    provider=provider,
                    policy_number=policy_number,
                    group_number=group_number,
                    member_id=member_id,
                    start_date=start_date,
                    end_date=end_date,
                    primary_holder_name=primary_holder_name,
                    primary_holder_relationship=primary_holder_relationship
                )
                message = "Insurance policy added successfully."
            
            # Add success message
            try:
                from django.contrib import messages
                messages.success(request, message)
            except:
                pass
                
            # Redirect back to billing_insurance page
            return redirect('billing_insurance')
            
        except InsuranceProvider.DoesNotExist:
            try:
                from django.contrib import messages
                messages.error(request, 'Selected insurance provider does not exist.')
            except:
                pass
            return redirect('billing_insurance')
    
    # If not POST method
    return redirect('billing_insurance')

@login_required
def verify_insurance(request):
    """Simulates insurance verification process"""
    if request.method == 'POST':
        try:
            policy = request.user.insurance_policy
            
            # In a real system, this would make an API call to verify coverage
            # For demo purposes, we'll simulate the verification
            import random
            verification_success = random.choice([True, True, True, False])  # 75% success rate
            
            if verification_success:
                policy.coverage_verified = True
                policy.last_verified_date = timezone.now().date()
                policy.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Insurance coverage verified successfully.',
                    'verified_date': policy.last_verified_date.strftime('%B %d, %Y')
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Unable to verify insurance coverage. Please contact your provider.'
                })
                
        except (AttributeError, InsurancePolicy.DoesNotExist):
            return JsonResponse({
                'success': False,
                'message': 'No insurance policy found.'
            })
    
    return redirect('billing_insurance')

@login_required
def billing_detail_view(request, invoice_number):
    """View details of a specific billing record"""
    billing_record = get_object_or_404(
        BillingRecord, 
        invoice_number=invoice_number,
        user=request.user
    )
    
    # Get services associated with this billing
    services = billing_record.billing_services.all()
    
    # Get payments made for this billing
    payments = billing_record.payments.all()
    
    # Calculate amount paid
    amount_paid = payments.aggregate(Sum('amount'))['amount__sum'] or 0
    remaining_balance = billing_record.patient_responsibility - amount_paid
    
    context = {
        'billing': billing_record,
        'services': services,
        'payments': payments,
        'amount_paid': amount_paid,
        'remaining_balance': remaining_balance,
    }
    
    return render(request, 'accounts/billing_detail.html', context)

@login_required
def make_payment(request, invoice_number):
    """Process a payment for a billing record"""
    if request.method == 'POST':
        billing_record = get_object_or_404(
            BillingRecord, 
            invoice_number=invoice_number,
            user=request.user
        )
        
        payment_method = request.POST.get('payment_method')
        amount = request.POST.get('amount')
        
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError("Amount must be positive")
                
            # In a real system, this would integrate with a payment processor
            # For demo purposes, we'll create a payment record directly
            
            # Generate a fake transaction ID
            import uuid
            transaction_id = str(uuid.uuid4())
            
            payment = Payment.objects.create(
                billing_record=billing_record,
                payment_date=timezone.now().date(),
                amount=amount,
                payment_method=payment_method,
                transaction_id=transaction_id,
                is_insurance_payment=False
            )
            
            # Update billing record status
            total_paid = Payment.objects.filter(billing_record=billing_record).aggregate(
                Sum('amount')
            )['amount__sum'] or 0
            
            if total_paid >= billing_record.patient_responsibility:
                billing_record.payment_status = 'paid'
            elif total_paid > 0:
                billing_record.payment_status = 'partially_paid'
            
            billing_record.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Payment of ${amount:.2f} processed successfully.',
                'new_status': billing_record.get_payment_status_display(),
                'transaction_id': transaction_id
            })
            
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return redirect('billing_detail', invoice_number=invoice_number)

@login_required
def generate_billing_pdf(request, invoice_number):
    """Generate a PDF of the billing record for download"""
    # In a real system, this would generate an actual PDF
    # For demo purposes, we'll just redirect back with a message
    
    return redirect('billing_detail', invoice_number=invoice_number)

@login_required
def smart_scheduler(request):
    """View for the combined Calendar and Chatbot interface"""
    chatbot = MediqChatbot(request.user)
    response_message = ""
    conversation_history = chatbot.conversation_history # Get initial history

    # Handle Chatbot POST requests ONLY
    if request.method == "POST":
        # Optional: Check form_type if other POSTs could reach here
        # form_type = request.POST.get('form_type') 
        # if form_type == 'chat_form': 
        user_input = request.POST.get("user_input", "")
        if user_input:
            chatbot.add_to_conversation("user", user_input) # Add user input first

            # Handle weather alerts (if active)
            if chatbot.weather_alert_active and chatbot.current_weather_alert:
                 # ... (weather alert handling logic, add bot responses to history) ...
                 if "same day" in user_input.lower() or "1" in user_input.lower():
                     reschedule_result = chatbot.calendar_system.reschedule_appointment(0, "same_day")
                     chatbot.weather_alert_active = False
                     response_message = reschedule_result.get("message", "Appointment rescheduled for later today.")
                     chatbot.add_to_conversation("assistant", response_message)
                 elif "next day" in user_input.lower() or "2" in user_input.lower():
                      reschedule_result = chatbot.calendar_system.reschedule_appointment(0, "next_day")
                      chatbot.weather_alert_active = False
                      response_message = reschedule_result.get("message", "Appointment rescheduled for tomorrow.")
                      chatbot.add_to_conversation("assistant", response_message)
                 elif "keep" in user_input.lower() or "3" in user_input.lower():
                      chatbot.weather_alert_active = False
                      response_message = "Okay, keeping original appointment."
                      chatbot.add_to_conversation("assistant", response_message)
                 else:
                      response_message = "Invalid weather alert option. Please choose 1, 2, or 3."
                      chatbot.add_to_conversation("assistant", response_message)

            # Handle confirmation or regular chat
            elif "confirm" in user_input.lower() and chatbot.confirmation_needed:
                response_message = chatbot.book_appointment()
                chatbot.add_to_conversation("assistant", response_message)
                if "✅ Appointment Confirmed!" in response_message:
                    messages.success(request, "Appointment booked successfully via chatbot!")
                    # Redirect SELF to refresh state after booking via chat
                    return redirect('smart_scheduler') 
            else:
                response_message = chatbot.get_ai_response(user_input)
                chatbot.add_to_conversation("assistant", response_message)

            # Update conversation history after processing
            conversation_history = chatbot.conversation_history

    # --- GET request logic or rendering after POST ---

    # Calendar Generation
    selected_doctor = request.GET.get("doctor")
    doctor_list_keys = list(DOCTORS.keys())
    if selected_doctor is None or selected_doctor not in doctor_list_keys:
        selected_doctor = doctor_list_keys[0] if doctor_list_keys else None

    date_str = request.GET.get("date", datetime.now().strftime("%Y-%m-%d"))

    calendar_html = ""
    if selected_doctor:
        try:
            calendar_html = chatbot.calendar_system.generate_calendar_html(selected_doctor, date_str)
        except Exception as e:
            calendar_html = f"<p class='text-danger'>Error generating calendar: {str(e)}</p>"
    else:
        calendar_html = "<p class='text-warning'>No doctors configured.</p>"

    context = {
        "conversation_history": conversation_history,
        "calendar_html": calendar_html,
        "azure_tts_key": AZURE_TTS_KEY_1,
        "response_message": response_message, # Pass chat response if any
        "doctor_list": doctor_list_keys,
        "selected_doctor": selected_doctor,
        "date_str": date_str,
    }
    
    return render(request, "accounts/smart_scheduler.html", context)
from django.shortcuts import render
from .models import Appointment, DoctorBusyTime

# accounts/views.py
import json
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Appointment, DoctorBusyTime, Doctor

# accounts/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Appointment, DoctorBusyTime

# accounts/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Appointment, DoctorBusyTime

# accounts/views.py

from datetime import datetime, timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Appointment, DoctorBusyTime

# accounts/views.py
from datetime import datetime, timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


from datetime import datetime, timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

import json
from .models import Appointment, DoctorBusyTime

from datetime import datetime, timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import json
from .models import Appointment, DoctorBusyTime

from datetime import datetime, timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import json
from .models import Appointment, DoctorBusyTime

@login_required
def calendar_view(request):
    user = request.user
    appts = Appointment.objects.filter(user=user)

    # build your events list
    events = []
    for a in appts:
        start = f"{a.date.isoformat()}T{a.time.strftime('%H:%M:%S')}"
        end_time = (datetime.combine(a.date, a.time) + timedelta(hours=1)).time()
        end   = f"{a.date.isoformat()}T{end_time.strftime('%H:%M:%S')}"
        events.append({
            'title': f"{a.doctor}: appointment at {a.time.strftime('%H:%M')}",
            'start': start,
            'end':   end,
            'color': '#007bff',  # Changed to blue for user's own appointments
            'allDay': False,
            'extendedProps': {
                'type': 'my-appointment'  # Add a type flag to identify user's appointments
            }
        })

    # now add busy slots
    # (you can adjust filter logic here to only include the doctors you care about)
    busy_all = DoctorBusyTime.objects.select_related('doctor').all()
    for b in busy_all:
        start = f"{b.date.isoformat()}T{b.start_time.strftime('%H:%M:%S')}"
        end   = f"{b.date.isoformat()}T{b.end_time.strftime('%H:%M:%S')}"
        events.append({
            'title': f"{b.doctor.name}: busy ({b.reason})",
            'start': start,
            'end':   end,
            'color': '#dc3545',
            'allDay': False,
            'extendedProps': {
                'type': 'busy'  # Add a type flag for busy times
            }
        })

    # ---- DEDUPE PASS ----
    seen = set()
    unique_events = []
    for ev in events:
        key = (ev['title'], ev['start'], ev['end'])
        if key not in seen:
            seen.add(key)
            unique_events.append(ev)

    # render with only the unique ones
    return render(request, 'accounts/calendar.html', {
        'events_json': json.dumps(unique_events)
    })




from .models import Doctor
from .forms import DoctorLoginForm

def doctor_login_view(request):
    if request.method == 'POST':
        form = DoctorLoginForm(request.POST)
        if form.is_valid():
            doctor = form.cleaned_data['doctor']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            if doctor.email == email and doctor.password == password:
                request.session['doctor_id'] = doctor.id
                return redirect('doctor_dashboard')
            else:
                messages.error(request, "Invalid credentials")
    else:
        form = DoctorLoginForm()
    return render(request, 'accounts/doctor_login.html', {'form': form})

def doctor_availability_view(request):
    doctor_id = request.session.get('doctor_id')
    if not doctor_id:
        return render(request, 'accounts/error.html', {'message': 'Unauthorized'})

    doctor = get_object_or_404(Doctor, id=doctor_id)
    
    # Debug print to see doctor's name
    print(f"Loading calendar for doctor: {doctor.name} (ID: {doctor.id})")
    
    # Get appointments for this doctor
    # IMPORTANT: Check how the doctor name is stored in appointments
    appointments_list = Appointment.objects.filter(
        doctor__icontains=doctor.name.replace("Dr. ", "")  # Try more flexible matching
    ).order_by('date', 'time')
    
    # Debug print
    print(f"Found {appointments_list.count()} appointments")
    for appt in appointments_list:
        print(f"  - Date: {appt.date}, Time: {appt.time}, Patient: {appt.user.username}")
    
    # Format appointments for JSON with correct format 
    appointments_data = []
    for appointment in appointments_list:
        # Make sure time format is consistent
        start_time = appointment.time.strftime('%H:%M')
        # Calculate end time (1 hour later)
        end_time_dt = (datetime.combine(appointment.date, appointment.time) + timedelta(hours=1))
        end_time = end_time_dt.time().strftime('%H:%M')
        
        appointments_data.append({
            'id': appointment.id,
            'date': appointment.date.isoformat(),
            'start': start_time,
            'end': end_time,
            'patient_name': f"{appointment.user.first_name} {appointment.user.last_name}",
            'reason': appointment.reason or 'Appointment',
            'notes': appointment.notes or '',
            'type': 'booked'  # Key for correct rendering
        })

    # Load busy times for this doctor
    busy_times_list = DoctorBusyTime.objects.filter(doctor=doctor).order_by('date', 'start_time')
    
    # Format busy times for JSON
    busy_times_data = []
    for busy_time in busy_times_list:
        busy_times_data.append({
            'id': busy_time.id,
            'date': busy_time.date.isoformat(),
            'start_time': busy_time.start_time.strftime('%H:%M'),
            'end_time': busy_time.end_time.strftime('%H:%M'),
            'reason': busy_time.reason,
            'notes': busy_time.notes or ''
        })
    
    return render(request, 'accounts/doctor_availability.html', {
        'appointments_json': json.dumps(appointments_data),
        'busy_times_json': json.dumps(busy_times_data),
        'doctor': doctor
    })


def modify_doctor_profile(request):
    # dummy response for now
    return HttpResponse("Modify profile page")

from django.shortcuts import get_object_or_404, render, redirect
from .models import Doctor
# views.py
from django.shortcuts import render, redirect
from .models import Doctor
from .forms import DoctorProfileForm

from django.shortcuts import render, redirect, get_object_or_404
from .models import Doctor
from .forms import DoctorProfileForm
from django.contrib import messages

def modify_profile_view(request):
    doctor_id = request.session.get('doctor_id')
    if not doctor_id:
        return redirect('doctor_login')

    doctor = get_object_or_404(Doctor, id=doctor_id)

    if request.method == 'POST':
        form = DoctorProfileForm(request.POST, request.FILES, instance=doctor)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('doctor_dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = DoctorProfileForm(instance=doctor)

    return render(request, 'accounts/modify_profile.html', {'form': form, 'doctor': doctor})


def doctor_dashboard_view(request):
    doctor_id = request.session.get('doctor_id')
    if not doctor_id:
        return redirect('doctor_login')

    doctor = get_object_or_404(Doctor, id=doctor_id)

    # Check for uploaded image
    if doctor.profile_image:
        image_path = doctor.profile_image.url  # Uploaded media file
    else:
        # Use static fallback image based on doctor name
        name_key = doctor.name.lower().replace("dr. ", "").replace(" ", "")
        image_filename = f"Dr.{name_key.title()}.jpg"
        static_path = f"accounts/images/{image_filename}"
        available_static = [
            "Dr.Nassar.jpg", "Dr.Farah.jpg", "Dr.Kassem.jpg",
            "Dr.Salim.jpg", "Dr.Haddad.jpg"
        ]
        if image_filename in available_static:
            image_path = static_path  # static fallback
        else:
            image_path = "accounts/images/default.jpg"  # default

    return render(request, 'accounts/doctor_dashboard.html', {
        'doctor': doctor,
        'image_path': image_path,
    })


@login_required
def perform_virtual_check_in(request, appointment_id):
    """Performs the check-in action for a specific appointment."""
    appointment_instance = None
    if appointment_id:
        appointment_instance = get_object_or_404(Appointment, id=appointment_id, user=request.user)
        
        # Optional: Server-side check for timing window robustness
        now = timezone.now()
        naive_datetime = datetime.combine(appointment_instance.date, appointment_instance.time)
        if timezone.is_naive(naive_datetime):
             appointment_start_dt = timezone.make_aware(naive_datetime, timezone.get_current_timezone())
        else:
             appointment_start_dt = timezone.localtime(appointment_instance.time) if timezone.is_aware(appointment_instance.time) else timezone.make_aware(naive_datetime, timezone.get_current_timezone())
        check_in_start_time = appointment_start_dt - timedelta(hours=1)

        if not (check_in_start_time <= now < appointment_start_dt):
             messages.error(request, "Check-in is not currently available for this appointment.")
             # Redirect back to the status page
             return redirect('virtual_check_in', appointment_id=appointment_id) 

        # Check if already checked in
        if CheckIn.objects.filter(user=request.user, appointment=appointment_instance).exists():
             messages.warning(request, "You have already checked in for this appointment.")
              # Redirect back to the status page
             return redirect('virtual_check_in', appointment_id=appointment_id) 

    # Create the check-in record
    try:
        checkin = CheckIn.objects.create(user=request.user, appointment=appointment_instance)
        messages.success(request, "You have successfully checked in!")
    except Exception as e:
         # Catch potential DB errors here too
         print(f"DB Error performing check-in for appt {appointment_id}: {e}")
         messages.error(request, "An error occurred during check-in. Please try again.")
         # Redirect back to the status page on error
         return redirect('virtual_check_in', appointment_id=appointment_id) 

    # Redirect back to the status page after successful check-in
    return redirect('virtual_check_in', appointment_id=appointment_id) 
    
    # Note: The confirmation HTML template is likely no longer needed if we just redirect back

def save_doctor_busy_time(request):
    """Save busy time for doctor's calendar"""
    if request.method == 'POST':
        doctor_id = request.session.get('doctor_id')
        if not doctor_id:
            return JsonResponse({'success': False, 'message': 'Unauthorized'})
        
        try:
            from .models import Doctor, DoctorBusyTime
            doctor = get_object_or_404(Doctor, id=doctor_id)
            date_str = request.POST.get('date')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            reason = request.POST.get('reason')
            notes = request.POST.get('notes', '')
            
            # Validate required fields
            if not all([date_str, start_time, end_time, reason]):
                return JsonResponse({'success': False, 'message': 'Missing required fields'})
            
            # Parse date
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Create the busy time record
            busy_time = DoctorBusyTime.objects.create(
                doctor=doctor,
                date=date_obj,
                start_time=start_time,
                end_time=end_time,
                reason=reason,
                notes=notes
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Busy time saved successfully',
                'id': busy_time.id
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def save_appointment_notes(request):
    """Save notes for an appointment"""
    if request.method == 'POST':
        try:
            # Try to parse JSON data
            data = json.loads(request.body)
            appointment_id = data.get('appointment_id')
            notes = data.get('notes', '')
            
            print(f"Saving notes for appointment {appointment_id}: {notes}")  # Add logging
            
            # Get the appointment
            appointment = get_object_or_404(Appointment, id=appointment_id)
            
            # Update notes
            appointment.notes = notes
            appointment.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Notes saved successfully'
            })
            
        except Exception as e:
            print(f"Error saving notes: {str(e)}")  # Add logging
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

def delete_doctor_busy_time(request, busy_time_id):
    """Delete busy time from doctor's calendar"""
    if request.method == 'POST':
        doctor_id = request.session.get('doctor_id')
        if not doctor_id:
            return JsonResponse({'success': False, 'message': 'Unauthorized'})
        
        try:
            doctor = get_object_or_404(Doctor, id=doctor_id)
            busy_time = get_object_or_404(DoctorBusyTime, id=busy_time_id, doctor=doctor)
            
            # Actually delete the busy time
            busy_time.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Busy time deleted successfully'
            })
            
        except Exception as e:
            print(f"Error deleting busy time: {str(e)}")  # Add logging
            return JsonResponse({
                'success': False, 
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

def doctor_appointments_feed(request):
    """API endpoint to provide appointments data for FullCalendar"""
    doctor_id = request.session.get('doctor_id')
    if not doctor_id:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    doctor = get_object_or_404(Doctor, id=doctor_id)
    
    # Get start and end parameters from request (if provided by FullCalendar)
    start = request.GET.get('start')
    end = request.GET.get('end')
    
    # Filter appointments by date range if provided
    appointments_list = Appointment.objects.filter(doctor=doctor.name).order_by('date', 'time')
    if start:
        start_date = datetime.fromisoformat(start.split('T')[0])
        appointments_list = appointments_list.filter(date__gte=start_date)
    if end:
        end_date = datetime.fromisoformat(end.split('T')[0])
        appointments_list = appointments_list.filter(date__lte=end_date)
    
    # Get busy times as well
    busy_times_list = DoctorBusyTime.objects.filter(doctor=doctor).order_by('date', 'start_time')
    if start:
        busy_times_list = busy_times_list.filter(date__gte=start_date)
    if end:
        busy_times_list = busy_times_list.filter(date__lte=end_date)
    
    # Format for FullCalendar
    events = []
    
    # Add appointments
    for appointment in appointments_list:
        start_datetime = datetime.combine(appointment.date, appointment.time)
        end_datetime = start_datetime + timedelta(hours=1)  # Assuming 1-hour appointments
        
        events.append({
            'id': f'appt_{appointment.id}',
            'title': f'Patient: {appointment.user.first_name} {appointment.user.last_name}',
            'start': start_datetime.isoformat(),
            'end': end_datetime.isoformat(),
            'color': '#ffc107',  # Yellow for appointments
            'extendedProps': {
                'type': 'appointment',
                'appointment_id': appointment.id,
                'patient_name': f"{appointment.user.first_name} {appointment.user.last_name}",
                'reason': appointment.reason or 'Appointment',
                'notes': appointment.notes or '',
            }
        })
    
    # Add busy times
    for busy_time in busy_times_list:
        start_datetime = datetime.combine(busy_time.date, busy_time.start_time)
        end_datetime = datetime.combine(busy_time.date, busy_time.end_time)
        
        events.append({
            'id': f'busy_{busy_time.id}',
            'title': busy_time.reason,
            'start': start_datetime.isoformat(),
            'end': end_datetime.isoformat(),
            'color': '#dc3545',  # Red for busy times
            'extendedProps': {
                'type': 'busy',
                'busy_id': busy_time.id,
                'reason': busy_time.reason,
                'notes': busy_time.notes or '',
            }
        })
    
    return JsonResponse(events, safe=False)

def available_slots(request):
    """API to check available time slots for a doctor on a specific date"""
    doctor = request.GET.get('doctor')
    date_str = request.GET.get('date')
    
    # Add logging to help debug
    print(f"Checking available slots for doctor: {doctor}, date: {date_str}")
    
    if not doctor or not date_str:
        return JsonResponse({'error': 'Missing doctor or date parameter'}, status=400)
    
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Define standard time slots (9 AM to 5 PM)
        all_slots = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00']
        
        # Find booked appointments
        booked_appointments = Appointment.objects.filter(
            doctor=doctor,
            date=date_obj
        ).values_list('time', flat=True)
        
        # Convert times to strings for comparison
        booked_times = [t.strftime('%H:%M') for t in booked_appointments]
        print(f"Booked times: {booked_times}")
        
        # Check doctor busy times
        busy_times = []
        try:
            doctor_obj = Doctor.objects.filter(name__iexact=doctor).first()
            if doctor_obj:
                busy_time_records = DoctorBusyTime.objects.filter(
                    doctor=doctor_obj,
                    date=date_obj
                )
                
                for busy in busy_time_records:
                    start_time = busy.start_time.strftime('%H:%M')
                    end_time = busy.end_time.strftime('%H:%M')
                    
                    # Mark all slots that overlap with busy time as unavailable
                    for slot in all_slots:
                        if start_time <= slot < end_time:
                            busy_times.append(slot)
                print(f"Busy times: {busy_times}")
            else:
                print(f"Doctor not found in Doctor model: {doctor}")
        except Exception as e:
            print(f"Error checking busy times: {str(e)}")
            # Continue even if there's an error with busy times
        
        # Combine booked and busy times
        unavailable_slots = set(booked_times) | set(busy_times)
        
        # Filter available slots
        available_slots = [slot for slot in all_slots if slot not in unavailable_slots]
        print(f"Available slots: {available_slots}")
        
        return JsonResponse({
            'available_slots': available_slots,
            'date': date_str,
            'doctor': doctor
        })
    
    except Exception as e:
        print(f"Error in available_slots: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def virtual_check_in_list(request):
    """Displays a list of appointments eligible for check-in"""
    now = timezone.now()
    today = now.date()
    
    # Get upcoming appointments
    appointments = Appointment.objects.filter(
        user=request.user,
        date__gte=today
    ).order_by('date', 'time')
    
    for appointment in appointments:
        # Calculate check-in eligibility for each appointment
        naive_datetime = datetime.combine(appointment.date, appointment.time)
        if timezone.is_naive(naive_datetime):
            appointment_start_dt = timezone.make_aware(naive_datetime, timezone.get_current_timezone())
        else:
            appointment_start_dt = naive_datetime
        
        # Check-in window calculation
        check_in_window_duration = timedelta(hours=1)
        check_in_start_time = appointment_start_dt - check_in_window_duration
        
        # Add status flags to each appointment
        appointment.can_check_in = now >= check_in_start_time and now < appointment_start_dt
        appointment.is_expired = now >= appointment_start_dt
        
        # Check if already checked in
        try:
            appointment.has_checked_in = CheckIn.objects.filter(
                user=request.user, 
                appointment=appointment
            ).exists()
        except Exception as e:
            appointment.has_checked_in = False
    
    context = {
        'appointments': appointments,
        'today': today
    }
    
    return render(request, 'accounts/virtual_check_in_list.html', context)

@login_required
def notification_settings_view(request):
    # Use session-based preferences instead of database
    if request.method == 'POST':
        # Store preferences in session
        request.session['notifications_appointments_enabled'] = request.POST.get('appointments_enabled') == 'on'
        request.session['notifications_messages_enabled'] = request.POST.get('messages_enabled') == 'on'
        request.session['notifications_browser_push_enabled'] = request.POST.get('browser_push_enabled') == 'on'
        
        # Add a success message
        from django.contrib import messages
        messages.success(request, "Notification settings saved successfully!")
        
    # Get VAPID public key for browser push
    vapid_public_key = getattr(settings, 'WEBPUSH_SETTINGS', {}).get('VAPID_PUBLIC_KEY', '')
    
    # Get preferences from session or use defaults
    preferences = {
        'appointments_enabled': request.session.get('notifications_appointments_enabled', True),
        'messages_enabled': request.session.get('notifications_messages_enabled', True),
        'browser_push_enabled': request.session.get('notifications_browser_push_enabled', False),
    }
    
    context = {
        'preferences': preferences,
        'vapid_public_key': vapid_public_key
    }
    
    return render(request, 'accounts/notification_settings.html', context)

def send_notification(user, title, message, url=None):
    """Send notification to user via web push"""
    # Check user preferences before sending
    try:
        preferences = user.notification_preferences
        if not preferences.enable_web_push:
            return False
    except NotificationPreference.DoesNotExist:
        # Default to sending if no preferences set
        pass
    
    payload = {
        "head": title,
        "body": message
    }
    
    if url:
        payload["url"] = url
    
    try:
        from webpush import send_user_notification
        send_user_notification(user=user, payload=payload, ttl=86400)
        return True
    except Exception as e:
        print(f"Error sending notification: {e}")
        return False

# This should go in your views.py or equivalent file where you handle the smart_scheduler view

from django.shortcuts import render
from django.http import JsonResponse
import json
import requests
from datetime import datetime, timedelta

# Add this import for handling the Groq API
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

@login_required
def smart_scheduler(request):
    """View for the combined Calendar and Chatbot interface"""
    user = request.user
    
    # Initialize or get conversation history from session
    if 'conversation_history' not in request.session:
        request.session['conversation_history'] = []
    conversation_history = request.session['conversation_history']
    
    # Get current doctor list from your database or settings
    doctor_list_keys = ["Dr. Salim", "Dr. Haddad", "Dr. Nassar", "Dr. Farah", "Dr. Kassem"]
    
    # Handle selected doctor and date
    selected_doctor = request.GET.get('doctor', doctor_list_keys[0] if doctor_list_keys else None)
    date_str = request.GET.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    # Generate empty calendar as default
    calendar_html = "<p>Select a doctor to view their calendar.</p>"
    response_message = None
    
    # Handle form submissions
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        
        # Handle chat form submission
        if form_type == 'chat_form':
            user_input = request.POST.get('user_input')
            doctor_info = request.POST.get('doctor_info', '[]')
            groq_api_key = request.POST.get('groq_api_key', '')
            
            # Add user message to conversation history
            if user_input:
                conversation_history.append({"role": "user", "content": user_input})
                
                # Process with Groq API
                response = process_with_groq(user_input, conversation_history, json.loads(doctor_info), groq_api_key)
                
                # Add bot response to history
                conversation_history.append({"role": "assistant", "content": response})
                
                # Save updated conversation
                request.session['conversation_history'] = conversation_history
                response_message = response
                
            # Handle AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'message': response_message,
                    'calendar_html': calendar_html if selected_doctor else ""
                })
        
        # Handle clear chat form submission
        elif form_type == 'clear_chat':
            # Reset conversation history
            request.session['conversation_history'] = []
            conversation_history = []
            
            # Handle AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
    
    # Generate calendar HTML for the selected doctor and date
    if selected_doctor:
        try:
            calendar_html = generate_calendar_html(selected_doctor, date_str)
        except Exception as e:
            calendar_html = f"<p class='text-danger'>Error generating calendar: {str(e)}</p>"
    
    context = {
        "conversation_history": conversation_history,
        "calendar_html": calendar_html,
        "response_message": response_message,
        "doctor_list": doctor_list_keys,
        "selected_doctor": selected_doctor,
        "date_str": date_str,
    }
    
    return render(request, "accounts/smart_scheduler.html", context)


def process_with_groq(user_input, conversation_history, doctor_info, api_key):
    """Process user input with Groq LLM API"""
    try:
        # Prepare doctor information
        doctor_info_text = "\n".join([
            f"{doc['name']} - {doc['specialty']} - Gender: {doc['gender']} "
            f"- Languages: {', '.join(doc['languages'])} - Virtual: {'Yes' if doc['virtual'] else 'No'} "
            f"- Handles: {', '.join(doc['symptoms'])}"
            for doc in doctor_info
        ])
        
        # Create system message with clear limitations
        system_message = {
            "role": "system",
            "content": f"""You are MediqBot, an informational medical assistant chatbot.

IMPORTANT LIMITATIONS: 
- You can ONLY provide information - you cannot book appointments, send emails, or perform any actions.
- When users ask to book appointments, explain that they need to use the booking system or contact the clinic directly.
- Do not say phrases like "I'll book that for you" or "I'll send an email" or make any promises about actions.
- Always clarify that you are providing information only.

Available doctors:
{doctor_info_text}

Your role is to:
1. Answer questions about doctors' specialties and availability
2. Suggest appropriate doctors based on symptoms
3. Provide general medical information
4. Explain how the booking process works

For appointment requests, always say: "To book an appointment, please use the calendar interface on the left or contact our clinic directly."
"""
        }
        
        # Prepare messages for API
        messages = [system_message]
        # Add the last 10 messages from conversation history
        messages.extend(conversation_history[-10:])
        
        # Make API request
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama3-8b-8192",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 512
            }
        )
        
        # Check if request was successful
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            # Log the error
            print(f"Groq API error: {response.status_code} - {response.text}")
            return f"I'm having trouble connecting to my knowledge base right now. Please try again later."
    
    except Exception as e:
        # Log the exception
        print(f"Error processing with Groq API: {str(e)}")
        return "Sorry, I encountered an error processing your request. The team has been notified."


def generate_calendar_html(doctor_name, date_str):
    """Generate HTML calendar for a doctor on a specific date"""
    # Mock implementation - replace with your actual calendar generation logic
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        day_name = date_obj.strftime('%A')
        
        # Generate table for the calendar
        html = f"""
        <h3>Calendar for {doctor_name} on {date_obj.strftime('%B %d, %Y')} ({day_name})</h3>
        <table class="table table-bordered">
            <thead class="thead-light">
                <tr>
                    <th>Time</th>
                    <th>Status</th>
                    <th>Weather</th>
                </tr>
            </thead>
            <tbody>
        """
        
        # Generate rows for each hour (9 AM to 5 PM)
        for hour in range(9, 18):
            time_str = f"{hour}:00"
            # Randomly make some slots booked (for demo)
            is_booked = hour % 2 == 0
            status = "Booked" if is_booked else "Available"
            row_class = "table-danger" if is_booked else "table-success"
            
            # Mock weather data
            weather = "Normal lightrain" if hour < 14 else "Clear"
            temp = 20 + (hour % 5)
            
            html += f"""
            <tr class="{row_class}">
                <td>{time_str}</td>
                <td>{status}</td>
                <td>{weather} {temp}°C</td>
            </tr>
            """
        
        html += """
            </tbody>
        </table>
        """
        
        return html
    
    except Exception as e:
        return f"<p class='text-danger'>Error generating calendar: {str(e)}</p>"