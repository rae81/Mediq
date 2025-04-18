# Generated by Django 3.2.25 on 2025-04-17 14:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_checkin_appointment'),
    ]

    operations = [
        migrations.CreateModel(
            name='Doctor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('password', models.CharField(max_length=100)),
                ('specialty', models.CharField(max_length=100)),
                ('phone', models.CharField(max_length=20)),
                ('age', models.PositiveIntegerField()),
            ],
        ),
    ]
