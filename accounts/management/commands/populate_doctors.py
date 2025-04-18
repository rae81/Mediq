from django.core.management.base import BaseCommand
from accounts.models import Doctor

class Command(BaseCommand):
    help = 'Populates the database with predefined doctors'

    def handle(self, *args, **kwargs):
        doctors = [
            {"name": "Dr. Salim (Cardiology)", "email": "salim@mediq.com", "password": "salim123", "phone": "+96171123456", "age": 45},
            {"name": "Dr. Haddad (Dermatology)", "email": "haddad@mediq.com", "password": "haddad123", "phone": "+96176123456", "age": 50},
            {"name": "Dr. Nassar (Pediatrics)", "email": "nassar@mediq.com", "password": "nassar123", "phone": "+96170123456", "age": 40},
            {"name": "Dr. Farah (Neurology)", "email": "farah@mediq.com", "password": "farah123", "phone": "+96178123456", "age": 48},
            {"name": "Dr. Kassem (Orthopedics)", "email": "kassem@mediq.com", "password": "kassem123", "phone": "+96179123456", "age": 52},
        ]

        for doc in doctors:
            Doctor.objects.create(**doc)

        self.stdout.write(self.style.SUCCESS('Doctors populated successfully.'))
