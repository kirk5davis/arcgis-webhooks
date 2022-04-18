from django.contrib import admin
from webhook_listener.models import ArcGISWebhookMessage

# register model objects
admin.site.register(ArcGISWebhookMessage)