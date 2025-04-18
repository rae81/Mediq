import smtplib
from datetime import datetime, timedelta
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from accounts.models import Appointment, SentReminder, ReminderPreference

# --- Email Configuration ---
EMAIL_ENABLED = True

# --- SMS Configuration (Using Twilio) ---
SMS_ENABLED = False  # Set to True when your Twilio account is set up

# For real SMS, install the Twilio Python SDK:
# pip install twilio
try:
    from twilio.rest import Client
    TWILIO_ACCOUNT_SID = "MG62f3992b5f85ff0fdf063a1123a8d98b"  # Replace with your Twilio SID
    TWILIO_AUTH_TOKEN = "26a38a4f07149f21b0c96f6d3d3f5608"    # Replace with your Twilio auth token
    TWILIO_PHONE_NUMBER = "+12347035468 "            # Replace with your Twilio phone number
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
except ImportError:
    SMS_ENABLED = True
    print("Twilio not installed. SMS reminders disabled.")

def send_email_reminder(appointment):
    """Send an email reminder to the patient about an upcoming appointment"""
    if not EMAIL_ENABLED:
        print("Email reminders are disabled.")
        return False
        
    try:
        user = appointment.user
        subject = "Appointment Reminder - MedIQ"
        
        # Create context for the email template
        context = {
            'user': user,
            'appointment': appointment,
            'clinic_name': 'MedIQ Health Center',
            'directions_url': 'https://maps.google.com/?q=MedIQ+Health+Center',
        }
        
        # Render email template with context
        html_message = render_to_string('accounts/email/appointment_reminder.html', context)
        plain_message = f"Dear {user.username},\n\nThis is a reminder of your appointment with {appointment.doctor} on {appointment.date} at {appointment.time}.\n\nSincerely,\nMedIQ Team"
        
        # Send email using Django's email system
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        # Record that this reminder was sent
        SentReminder.objects.create(
            appointment=appointment,
            reminder_type='email'
        )
        
        print(f"Email reminder sent to {user.email} for appointment on {appointment.date} at {appointment.time}")
        return True
    except Exception as e:
        print(f"Error sending email reminder: {e}")
        return False

def send_sms_reminder(appointment):
    """Send an SMS reminder to the patient about an upcoming appointment"""
    if not SMS_ENABLED:
        print("SMS reminders are disabled")
        return False
    
    try:
        user = appointment.user
        if not hasattr(user, 'profile') or not user.profile.phone:
            print(f"No phone number available for user {user.username}")
            return False
        
        # Build the SMS message
        message = f"MedIQ Reminder: You have an appointment with {appointment.doctor} on {appointment.date} at {appointment.time}. Reply Y to confirm."
        
        # Send using Twilio
        try:
            message = twilio_client.messages.create(
                body=message,
                from_=TWILIO_PHONE_NUMBER,
                to=user.profile.phone
            )
            
            # Record that this reminder was sent
            SentReminder.objects.create(
                appointment=appointment,
                reminder_type='sms'
            )
            
            print(f"SMS reminder sent to {user.profile.phone} for appointment on {appointment.date} at {appointment.time}")
            return True
        except Exception as e:
            print(f"Twilio SMS error: {e}")
            return False
            
    except Exception as e:
        print(f"Error sending SMS reminder: {e}")
        return False

def get_appointments_needing_reminders():
    """Get appointments that need reminders based on user preferences"""
    now = timezone.now()
    
    # Get all future appointments that haven't been reminded yet
    appointments = []
    
    for preference in ReminderPreference.objects.select_related('user'):
        user = preference.user
        days_before = preference.days_before
        hours_before = preference.hours_before
        
        # Calculate the time window for sending reminders
        reminder_window_start = now
        reminder_window_end = now + timedelta(hours=1)  # Look ahead 1 hour
        
        # Find appointment date/times that fall within the reminder window
        target_time = now + timedelta(days=days_before)
        
        # Find appointments for this user that need reminders
        user_appointments = Appointment.objects.filter(
            user=user,
            date__gte=now.date(),
            # More complex filtering could be added here
        )
        
        for appointment in user_appointments:
            # Convert appointment date/time to datetime for comparison
            appt_datetime = datetime.combine(
                appointment.date, 
                appointment.time,
                tzinfo=timezone.get_current_timezone()
            )
            
            # Check if we should send a reminder now based on user preferences
            time_diff = appt_datetime - now
            hours_diff = time_diff.total_seconds() / 3600
            
            if days_before == 1 and hours_diff <= 24 and hours_diff > 23:
                # It's about 24 hours before the appointment
                if preference.email_reminders:
                    if not SentReminder.objects.filter(appointment=appointment, reminder_type='email').exists():
                        appointments.append((appointment, 'email'))
                
                if preference.sms_reminders:
                    if not SentReminder.objects.filter(appointment=appointment, reminder_type='sms').exists():
                        appointments.append((appointment, 'sms'))
    
    return appointments

def remind_patients():
    """Main function to send reminders based on preferences"""
    print(f"Starting reminder process at {timezone.now()}")
    
    appointments = get_appointments_needing_reminders()
    
    if not appointments:
        print("No appointments need reminders at this time.")
        return
    
    for appointment, reminder_type in appointments:
        print(f"Sending {reminder_type} reminder for appointment {appointment.id}")
        
        if reminder_type == 'email':
            success = send_email_reminder(appointment)
        elif reminder_type == 'sms':
            success = send_sms_reminder(appointment)
        else:
            success = False
            
        if success:
            print(f"Successfully sent {reminder_type} reminder for appointment {appointment.id}")
        else:
            print(f"Failed to send {reminder_type} reminder for appointment {appointment.id}")
    
    print(f"Reminder process completed at {timezone.now()}")