from django.core.management.base import BaseCommand
from apps.writers.services import process_assignment_deadlines

class Command(BaseCommand):
    help = 'Process writer SLAs and script submission deadlines'

    def handle(self, *args, **options):
        self.stdout.write('Checking writer deadlines...')
        process_assignment_deadlines()
        self.stdout.write(self.style.SUCCESS('Finished checking deadlines.'))
