from django.urls import path
from . import views
from .views import doctor_login_view, doctor_dashboard_view

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Existing URLs
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('virtual_check_in/', views.virtual_check_in_list, name='virtual_check_in_list'),
    path('virtual_check_in/<int:appointment_id>/', views.virtual_check_in_view, name='virtual_check_in'),
    path('appointment_reminder/', views.appointment_reminder_view, name='appointment_reminder'),
    path('billing_insurance/', views.billing_insurance_view, name='billing_insurance'),
    path('accessibility_mode/', views.accessibility_mode_view, name='accessibility_mode'),
    path('toggle_accessibility/', views.toggle_accessibility_view, name='toggle_accessibility'),
    path('trigger_reminder/', views.trigger_reminder_view, name='trigger_reminder'),
    path("scheduler/", views.smart_scheduler, name="smart_scheduler"),
    path('profile/', views.profile_view, name='profile'),
    path('profile/update/', views.profile_update, name='profile_update'),
    path('accessibility_settings/', views.accessibility_settings_view, name='accessibility_settings'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('contact-doctor/', views.contact_doctor_view, name='contact_doctor'),
    # Appointment Reminders
    path('save_reminder_preferences/', views.save_reminder_preferences, name='save_reminder_preferences'),
    path('send_reminder_now/', views.send_reminder_now, name='send_reminder_now'),
    path('edit_appointment/<int:appointment_id>/', views.edit_appointment, name='edit_appointment'),
    path('cancel_appointment/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),

    # Doctor Dashboard and Profile Editing
    path('doctor-login/', doctor_login_view, name='doctor_login'),
    path('doctor/modify/', views.modify_doctor_profile, name='modify_profile'),
    path('doctor-dashboard/', doctor_dashboard_view, name='doctor_dashboard'),
    path('doctor/availability/', views.doctor_availability_view, name='doctor_availability'),
    path('modify-profile/', views.modify_profile_view, name='modify_profile'),
    path('doctor/accessibility_settings/', views.doctor_accessibility_settings_view, name='doctor_accessibility_settings'),
    path('doctor/save_busy_time/', views.save_doctor_busy_time, name='save_doctor_busy_time'),
    path('doctor/save_appointment_notes/', views.save_appointment_notes, name='save_appointment_notes'),
    path('doctor/delete_busy_time/<int:busy_time_id>/', views.delete_doctor_busy_time, name='delete_doctor_busy_time'),
    path(
       'doctor/dashboard/',
       doctor_dashboard_view,
       name='doctor-dashboard'
   ),
    path('chats/',                views.patient_chat_list,   name='patient_chat_list'),
    path('chats/doctor/<int:doctor_id>/', views.patient_chat_detail, name='patient_chat_detail'),

    #–– Doctor chat UI
    path('doctor/chats/',            views.doctor_chat_list,   name='doctor_chat_list'),
    path('doctor/chats/patient/<int:patient_id>/',
         views.doctor_chat_detail,  name='doctor_chat_detail'),

    path('doctor-contact-patient/',views.doctor_contact_patient_view,name='doctor_contact_patient'),
    # Billing & Insurance
    path('add_insurance_policy/', views.add_insurance_policy, name='add_insurance_policy'),
    path('verify_insurance/', views.verify_insurance, name='verify_insurance'),
    path('billing_detail/<str:invoice_number>/', views.billing_detail_view, name='billing_detail'),
    path('make_payment/<str:invoice_number>/', views.make_payment, name='make_payment'),
    path('book_appointment/', views.book_appointment_direct, name='book_appointment_direct'),
    path('generate_billing_pdf/<str:invoice_number>/', views.generate_billing_pdf, name='generate_billing_pdf'),
    
    # Virtual Check-in
    path('perform_check_in/<int:appointment_id>/', views.perform_virtual_check_in, name='perform_virtual_check_in'),

    # New URL for doctor appointments feed
    path('doctor/appointments/feed/', views.doctor_appointments_feed, name='doctor_appointments_feed'),

    # Add to your urls.py
    path('available_slots/', views.available_slots, name='available_slots'),

    # Add to accounts/urls.py
    path('notification_settings/', views.notification_settings_view, name='notification_settings'),
]

# ✅ Serve media files (uploaded profile images)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
