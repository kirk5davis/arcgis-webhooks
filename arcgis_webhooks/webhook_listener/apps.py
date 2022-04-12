from django.apps import AppConfig
from django.db.models import Q
import threading

class WebhookListenerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'webhook_listener'

    def ready(self):
        import webhook_listener.models

        def sched_jobs():
            from webhook_listener.models import Task
            import sched
            import time

            def exec_fn():
                for task in Task.objects.filter(Q(active=True) & (Q(failed=False) | Q(failed__isnull=True))):
                    task.run()

            s = sched.scheduler(time.time, time.sleep)
            while True:
                s.enter(30, 1, exec_fn)
                s.run(blocking=True)

        self.scheduling_thread = threading.Thread(target=sched_jobs, daemon=True)
        self.scheduling_thread.name = "scheduling_thread"
        self.scheduling_thread.start()