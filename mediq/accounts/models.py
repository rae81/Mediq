from django.db import models
from django.contrib.auth.models import User
import uuid
from django.utils import timezone
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


# ======================= User Profile =======================

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    age = models.PositiveIntegerField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)

    def __str__(self):
        return f"Profile of {self.user.username}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


# ======================= Doctor =======================

class Doctor(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)
    profile_image = models.ImageField(upload_to='doctor_profiles/', null=True, blank=True)
    specialty = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    age = models.PositiveIntegerField()

    def __str__(self):
        return self.name


# ======================= Messaging =======================

class Message(models.Model):
    sender_user     = models.ForeignKey(
                        User,
                        null=True, blank=True,
                        related_name="sent_messages",
                        on_delete=models.CASCADE
                      )
    receiver_doctor = models.ForeignKey(
                        Doctor,
                        null=True, blank=True,
                        related_name="received_messages_doctor",
                        on_delete=models.CASCADE
                      )
    sender_doctor   = models.ForeignKey(
                        Doctor,
                        null=True, blank=True,
                        related_name="sent_messages_doctor",
                        on_delete=models.CASCADE
                      )
    receiver_user   = models.ForeignKey(
                        User,
                        null=True, blank=True,
                        related_name="received_messages",
                        on_delete=models.CASCADE
                      )
    content   = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        who = self.sender_user or self.sender_doctor
        whom = self.receiver_user or self.receiver_doctor
        return f"{who} → {whom}: {self.content[:20]}"

# ======================= Appointment & Check-In =======================

class Appointment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.CharField(max_length=100)
    specialty = models.CharField(max_length=100)
    date = models.DateField()
    time = models.TimeField()
    reason = models.TextField(blank=True, null=True)
    contact = models.CharField(max_length=100)
    insurance = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('doctor', 'date', 'time')

    def __str__(self):
        return f"Appointment with {self.doctor} on {self.date} at {self.time} for {self.user}"


class CheckIn(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    check_in_time = models.DateTimeField(auto_now_add=True)
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name='check_ins')

    def __str__(self):
        if self.appointment:
            return f"{self.user.username} checked in for Appt #{self.appointment.id} at {self.check_in_time}"
        else:
            return f"{self.user.username} checked in at {self.check_in_time}"


# ======================= Reminder =======================

class ReminderPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='reminder_preference')
    email_reminders = models.BooleanField(default=True)
    sms_reminders = models.BooleanField(default=False)
    days_before = models.IntegerField(default=1, choices=[(1, '1 day'), (2, '2 days'), (3, '3 days'), (7, '1 week')])
    hours_before = models.IntegerField(default=24, choices=[(2, '2 hours'), (6, '6 hours'), (12, '12 hours'), (24, '24 hours')])

    def __str__(self):
        return f"Reminder preferences for {self.user.username}"


class SentReminder(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='sent_reminders')
    reminder_type = models.CharField(max_length=10, choices=[('email', 'Email'), ('sms', 'SMS')])
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('appointment', 'reminder_type')

    def __str__(self):
        return f"{self.reminder_type} reminder for appointment #{self.appointment.id}"


# ======================= Billing =======================

class InsuranceProvider(models.Model):
    name = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=20)
    website = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class InsurancePolicy(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='insurance_policy')
    provider = models.ForeignKey(InsuranceProvider, on_delete=models.SET_NULL, null=True, related_name='policies')
    policy_number = models.CharField(max_length=100)
    group_number = models.CharField(max_length=100, blank=True, null=True)
    member_id = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    primary_holder_name = models.CharField(max_length=100)
    primary_holder_relationship = models.CharField(max_length=20, choices=[
        ('self', 'Self'),
        ('spouse', 'Spouse'),
        ('parent', 'Parent'),
        ('other', 'Other')
    ], default='self')
    coverage_verified = models.BooleanField(default=False)
    last_verified_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.provider.name} - {self.policy_number}"


class ServiceType(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    description = models.TextField(blank=True, null=True)
    base_cost = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.code})"


class BillingRecord(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('insurance_pending', 'Insurance Pending'),
        ('partially_paid', 'Partially Paid'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    ]

    invoice_number = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='billing_records')
    appointment = models.OneToOneField(Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name='billing')
    service_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    services = models.ManyToManyField(ServiceType, through='BillingService')
    sub_total = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    insurance_policy = models.ForeignKey(InsurancePolicy, on_delete=models.SET_NULL, null=True, blank=True)
    insurance_claim_number = models.CharField(max_length=100, blank=True, null=True)
    insurance_coverage_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    patient_responsibility = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    payment_due_date = models.DateField()
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-service_date']

    def __str__(self):
        return f"Invoice #{self.invoice_number} - {self.user.username}"

    def is_overdue(self):
        return timezone.now().date() > self.payment_due_date and self.payment_status in ['unpaid', 'partially_paid']

    def save(self, *args, **kwargs):
        self.patient_responsibility = self.total_amount - self.insurance_coverage_amount
        super().save(*args, **kwargs)


class BillingService(models.Model):
    billing_record = models.ForeignKey(BillingRecord, on_delete=models.CASCADE, related_name='billing_services')
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.service_type.name} for {self.billing_record.invoice_number}"

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('bank_transfer', 'Bank Transfer'),
        ('insurance', 'Insurance'),
        ('other', 'Other'),
    ]

    billing_record = models.ForeignKey(BillingRecord, on_delete=models.CASCADE, related_name='payments')
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    is_insurance_payment = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-payment_date']

    def __str__(self):
        return f"Payment of ${self.amount} on {self.payment_date} for {self.billing_record.invoice_number}"


# ======================= Availability =======================

class DoctorBusyTime(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='busy_times')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    reason = models.CharField(max_length=200)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.doctor.name} busy on {self.date} from {self.start_time} to {self.end_time}"


# ======================= Notifications =======================

class NotificationPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    appointments_enabled = models.BooleanField(default=True)
    messages_enabled = models.BooleanField(default=True)
    browser_push_enabled = models.BooleanField(default=False)
    email_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=True)

    def __str__(self):
        return f"Notification preferences for {self.user.username}"
