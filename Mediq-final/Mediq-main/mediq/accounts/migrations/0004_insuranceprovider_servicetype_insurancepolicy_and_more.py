# Generated by Django 5.2 on 2025-04-09 20:14

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_appointment'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='InsuranceProvider',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('contact_number', models.CharField(max_length=20)),
                ('website', models.URLField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='ServiceType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('code', models.CharField(max_length=20)),
                ('description', models.TextField(blank=True, null=True)),
                ('base_cost', models.DecimalField(decimal_places=2, max_digits=10)),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='InsurancePolicy',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('policy_number', models.CharField(max_length=100)),
                ('group_number', models.CharField(blank=True, max_length=100, null=True)),
                ('member_id', models.CharField(max_length=100)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField(blank=True, null=True)),
                ('primary_holder_name', models.CharField(max_length=100)),
                ('primary_holder_relationship', models.CharField(choices=[('self', 'Self'), ('spouse', 'Spouse'), ('parent', 'Parent'), ('other', 'Other')], default='self', max_length=20)),
                ('coverage_verified', models.BooleanField(default=False)),
                ('last_verified_date', models.DateField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='insurance_policy', to=settings.AUTH_USER_MODEL)),
                ('provider', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='policies', to='accounts.insuranceprovider')),
            ],
        ),
        migrations.CreateModel(
            name='BillingRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('invoice_number', models.CharField(default=uuid.uuid4, max_length=50, unique=True)),
                ('service_date', models.DateField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('sub_total', models.DecimalField(decimal_places=2, max_digits=10)),
                ('tax', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('discount', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('insurance_claim_number', models.CharField(blank=True, max_length=100, null=True)),
                ('insurance_coverage_amount', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('patient_responsibility', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('payment_status', models.CharField(choices=[('unpaid', 'Unpaid'), ('insurance_pending', 'Insurance Pending'), ('partially_paid', 'Partially Paid'), ('paid', 'Paid'), ('refunded', 'Refunded'), ('cancelled', 'Cancelled')], default='unpaid', max_length=20)),
                ('payment_due_date', models.DateField()),
                ('notes', models.TextField(blank=True, null=True)),
                ('appointment', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='billing', to='accounts.appointment')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='billing_records', to=settings.AUTH_USER_MODEL)),
                ('insurance_policy', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.insurancepolicy')),
            ],
            options={
                'ordering': ['-service_date'],
            },
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payment_date', models.DateField()),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('payment_method', models.CharField(choices=[('credit_card', 'Credit Card'), ('debit_card', 'Debit Card'), ('cash', 'Cash'), ('check', 'Check'), ('bank_transfer', 'Bank Transfer'), ('insurance', 'Insurance'), ('other', 'Other')], max_length=20)),
                ('transaction_id', models.CharField(blank=True, max_length=100, null=True)),
                ('is_insurance_payment', models.BooleanField(default=False)),
                ('notes', models.TextField(blank=True, null=True)),
                ('billing_record', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='accounts.billingrecord')),
            ],
            options={
                'ordering': ['-payment_date'],
            },
        ),
        migrations.CreateModel(
            name='ReminderPreference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email_reminders', models.BooleanField(default=True)),
                ('sms_reminders', models.BooleanField(default=False)),
                ('days_before', models.IntegerField(choices=[(1, '1 day'), (2, '2 days'), (3, '3 days'), (7, '1 week')], default=1)),
                ('hours_before', models.IntegerField(choices=[(2, '2 hours'), (6, '6 hours'), (12, '12 hours'), (24, '24 hours')], default=24)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='reminder_preference', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='BillingService',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('total_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('billing_record', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='billing_services', to='accounts.billingrecord')),
                ('service_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.servicetype')),
            ],
        ),
        migrations.AddField(
            model_name='billingrecord',
            name='services',
            field=models.ManyToManyField(through='accounts.BillingService', to='accounts.servicetype'),
        ),
        migrations.CreateModel(
            name='SentReminder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reminder_type', models.CharField(choices=[('email', 'Email'), ('sms', 'SMS')], max_length=10)),
                ('sent_at', models.DateTimeField(auto_now_add=True)),
                ('appointment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_reminders', to='accounts.appointment')),
            ],
            options={
                'unique_together': {('appointment', 'reminder_type')},
            },
        ),
    ]
