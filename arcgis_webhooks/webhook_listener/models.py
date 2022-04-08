import uuid
from django.db import models


class ArcGISWebhookMessage(models.Model):

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
