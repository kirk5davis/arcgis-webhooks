import datetime as dt
import json
from secrets import compare_digest

from django.conf import settings
from django.db.transaction import atomic, non_atomic_requests
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.shortcuts import render, get_object_or_404
from django.utils.html import format_html

from webhook_listener.models import ArcGISWebhookMessage

# Create your views here.
def index(request):
    webhook_count = ArcGISWebhookMessage.objects.count()
    last_webhook_update = ArcGISWebhookMessage.objects.latest('-received_at')
    task_count = 0
    context = {"webhook_count": webhook_count, "last_webhook_update": last_webhook_update.received_at, "task_count":task_count}
    return render(request, "index.html", context)


def webhooks(request):
    webhook_objs = ArcGISWebhookMessage.objects.all().order_by('-received_at')
    context = {"webhook_objs": webhook_objs}
    return render(request, "webhooks.html", context)


def tasks(request):
    task_count = 0
    context = {"task_count":task_count}
    return render(request, "tasks.html", context)

def webhook_detail(request, webhook_id):
    webhook_obj = get_object_or_404(ArcGISWebhookMessage, pk=webhook_id)
    context = {"webhook_obj": webhook_obj}
    return render(request, "webhook_detail.html", context)


def hx_webhooks(request):
    webhook_objs = ArcGISWebhookMessage.objects.all().order_by('-received_at')
    context = {"webhook_objs": webhook_objs}
    return render(request, "webhook_refresh_fragment.html", context)


@csrf_exempt
@require_POST
@non_atomic_requests
def arcgis_webhook(request):
    given_token = request.headers.get("secret", "")
    if not compare_digest(given_token, settings.ARCGIS_WEBHOOK_TOKEN):
        print(given_token)
        return HttpResponseForbidden(
            "Incorrect token in ArcGIS-Webhook-Token.",
            content_type="text/plain",
        )

    # delete messages older than 7 days
    # ArcGISWebhookMessage.objects.filter(
    #     received_at__lte=timezone.now() - dt.timedelta(days=7)
    # ).delete()
    # print(f"Test Request Body: {request.body}")

    payload = json.loads(request.body)
    event_name = "other"
    try:
        if "events" in payload:
            event_name = " ".join([i['operation'] for i in payload['events']])
    except:
        pass
    ArcGISWebhookMessage.objects.create(
        received_at=timezone.now(),
        payload=payload,
        event_name = event_name,
    )

    # custome function to process the webhook payload
    process_webhook(payload)

    return HttpResponse("Message received.", content_type="text/plain")


@atomic
def process_webhook(payload):
    # TODO: business logic
    print(payload)
    pass