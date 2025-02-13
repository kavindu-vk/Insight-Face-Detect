from django.core.management.base import BaseCommand
from django.utils.timezone import now
from app.models import ClassSchedule

class Command(BaseCommand):
    help = "Update class schedule status automatically"

    def handle(self, *args, **kwargs):
        current_time = now()

        # Set classes to 'Finished' if they have ended
        ClassSchedule.objects.filter(date__lt=current_time.date()).update(status='Finished')
        ClassSchedule.objects.filter(date=current_time.date(), end_time__lt=current_time.time()).update(status='Finished')

        self.stdout.write(self.style.SUCCESS("Successfully updated class statuses!"))