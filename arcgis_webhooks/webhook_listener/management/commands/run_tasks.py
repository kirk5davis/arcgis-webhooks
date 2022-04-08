from django.core.management.base import BaseCommand
from webhook_listener.models import Task

class Command(BaseCommand):
    help = "Run pending, active tasks"

    def handle(self, *args, **kwargs):
        for task in Task.objects.filter(active=True):
            task.run()