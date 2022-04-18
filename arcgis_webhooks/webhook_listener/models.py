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