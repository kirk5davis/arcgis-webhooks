from asyncio import events
import datetime as dt
import json
from secrets import compare_digest
import requests

from django.conf import settings
from django.db.transaction import atomic, non_atomic_requests
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.shortcuts import render, get_object_or_404



from webhook_listener.models import ArcGISWebhookMessage

from .utils import send_html_mail

from .libs.check_new_user_email import check_email

import logging

logger = logging.getLogger(__name__)

ARCGIS_PROCESS_DICT = {
    'signin': check_email,
}


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
def hx_test_webhook_send(request):
    test_webhook_data = """{"events": [{"id": "kirk.davis@ocio.wa.gov", "operation": "signin-test", "properties": {}, "source": "users", "userId":"e0d5b07c672c422baf83dd7a9f221bbc", "username": "kirk.davis@ocio.wa.gov", "when":
1645134525842}], "info": {"portalURL": "https://geoportal2.watech.wa.gov/portal/", "webhookId": "4edcf3c9ab0246f5a041d1225d0619f3", "webhookName": "all_webhooks", "when": 1645134525845},"properties": {}}"""
    new_request = HttpRequest()
    new_request.method = "POST"
    new_request.POST = test_webhook_data
    new_request.META["secret"] = settings.ARCGIS_WEBHOOK_TOKEN
    return arcgis_webhook(new_request)


@csrf_exempt
@require_POST
@non_atomic_requests
def arcgis_webhook(request):
    given_token_header = request.headers.get("secret", "")
    given_token_meta = request.META.get("secret", "")
    logger.debug(f"Given Tokens: {given_token_header}, {given_token_meta}, available headers: {request.headers}, available META: {request.META}")
    if not compare_digest(given_token_header, settings.ARCGIS_WEBHOOK_TOKEN) and not compare_digest(given_token_meta, settings.ARCGIS_WEBHOOK_TOKEN):
        return HttpResponseForbidden(
            "Incorrect token in ArcGIS-Webhook-Token.",
            content_type="text/plain",
        )

    # delete messages older than 7 days
    # ArcGISWebhookMessage.objects.filter(
    #     received_at__lte=timezone.now() - dt.timedelta(days=7)
    # ).delete()
    # print(f"Test Request Body: {request.body}")
    try:
        payload = json.loads(request.body)
    except (AttributeError, TypeError) as err:
        payload = json.loads(request.POST)
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
    process_webhook(event_name, payload)

    return HttpResponse("Message received.", content_type="text/plain")


@atomic
def process_webhook(event_name, payload):
    # create business logic
    try:
        logger.debug("Begin processing webhook:")
        logger.debug(event_name)
        logger.debug(payload)
        ARCGIS_PROCESS_DICT[event_name](payload)
        logger.debug("didn't throw exception")
    except KeyError:
        logger.debug(f"threw KeyError exception for event: {event_name}")
        pass