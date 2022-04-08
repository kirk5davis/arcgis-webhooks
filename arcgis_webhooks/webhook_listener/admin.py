from django.contrib import admin
from webhook_listener.models import ArcGISWebhookMessage

# Register your models here.
admin.site.register(ArcGISWebhookMessage)