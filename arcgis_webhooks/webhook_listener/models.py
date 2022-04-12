from datetime import datetime
from doctest import DocTestFinder
import uuid
import types
import logging
from xml.etree.ElementInclude import default_loader
from django.db import models
from django.utils.timezone import make_aware
from django.utils.module_loading import import_string



class ArcGISWebhookMessage(models.Model):
    
    id = models.AutoField(primary_key=True)
    received_at = models.DateTimeField(help_text="When this event was received.")
    payload = models.JSONField(default=None, null=True)
    event_name = models.TextField(verbose_name="Event Name")

    def __str__(self):
        return f"ArcGIS Webhook @ {self.received_at}"

    class Meta:
        indexes = [
            models.Index(fields=["received_at"]),
        ]
        verbose_name = "ArcGIS Webhook"
        verbose_name_plural = "ArcGIS Webhooks"


class TaskKind(models.Model):
    id = models.AutoField(primary_key=True)
    dotted_path = models.TextField(null=False, blank=False, unique=True)
    description = models.TextField(null=False, blank=False)
    created = models.DateTimeField(auto_now_add=True, null=False, blank=False)
    last_modified = models.DateTimeField(auto_now_add=True, null=False, blank=False)

    def __str__(self):
        return self.dotted_path
    
    @staticmethod
    def from_func(func):
        if isinstance(func, types.FunctionType):
            dotted_path = f"{func.__module__}.{func.__name__}"
            description = f"{func.__doc__}"
            ret, _ = TaskKind.objects.get_or_create(dotted_path=dotted_path, description=description)
            return ret
        else:
            raise TypeError

    def run(self, Task):
        try:
            func = import_string(self.dotted_path)
            return func(Task)
        except ImportError:
            logging.error(f"Could not resolve Task dotted_path: {self.dotted_path}")
            raise ImportError


class Task(models.Model):
    id = models.AutoField(primary_key=True)
    kind = models.ForeignKey(TaskKind, null=True, on_delete=models.SET_NULL)
    created = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True, null=False, blank=False)
    periodic = models.BooleanField(default=False, null=False, blank=False)
    failed = models.BooleanField(default=None, null=True, blank=True)
    last_run = models.DateTimeField(default=None, null=True, blank=True)
    logs = models.TextField(null=True, blank=True)
    data = models.JSONField(null=True, blank=True)
    source = models.ForeignKey(ArcGISWebhookMessage, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.kind} {self.data}"
    
    def run(self):
        if not self.kind_id:
            return
        self.last_run = make_aware(datetime.now())
        try:
            res = self.kind.run(self)
            if res and not self.periodic:
                self.active = False
            if isinstance(res, str):
                if self.logs is None:
                    self.logs = ""
                self.logs += res
            self.failed = False
            self.save(update_fields=["last_run", "failed", "active", "logs"])
        except Exception as exc:
            if self.logs is None:
                self.logs = ""
            self.logs += str(exc)
            self.failed = True
            self.save(update_fields=["last_run", "failed", "logs"])
        return