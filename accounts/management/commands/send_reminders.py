from django.core.management.base import BaseCommand
from apscheduler.schedulers.blocking import BlockingScheduler
from accounts.reminder import remind_patients  # Make sure your reminder module is set up in accounts/reminder.py

class Command(BaseCommand):
    help = "Starts the scheduler to send appointment reminders."

    def handle(self, *args, **kwargs):
        scheduler = BlockingScheduler()

        # Schedule 'remind_patients' to run every day at midnight.
        scheduler.add_job(remind_patients, 'cron', hour=0, minute=0)
        
        self.stdout.write("Scheduler started. Waiting for the next scheduled reminder...")
        
        try:
            scheduler.start()
        except KeyboardInterrupt:
            scheduler.shutdown()
            self.stdout.write("Scheduler stopped.")
