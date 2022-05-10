from asyncio import events
import datetime as dt
import json
from secrets import compare_digest

from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.transaction import atomic, non_atomic_requests
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.shortcuts import render, get_object_or_404

from webhook_listener.models import ArcGISWebhookMessage
from django_celery_results.models import TaskResult

from .tasks import new_user_email_check
from .tasks import send_test_webhook_email
from .tasks import share_item_with_org_check

import logging

logger = logging.getLogger(__name__)


WEBHOOK_PROCESS_DICT = {
    'add_user_to_org': new_user_email_check,
    'add_item_to_org': share_item_with_org_check,
    'test_webhook': send_test_webhook_email,
}


# Create your views here.
def index(request):
    webhook_count = ArcGISWebhookMessage.objects.count()
    last_webhook_update = ArcGISWebhookMessage.objects.latest('-received_at')
    task_count = TaskResult.objects.count()
    last_task_update = TaskResult.objects.latest('-date_done')
    context = {"webhook_count": webhook_count, "last_webhook_update": last_webhook_update.received_at, "task_count":task_count, "last_task_update":last_task_update.date_done}
    return render(request, "index.html", context)


def webhooks(request):
    webhook_objs = ArcGISWebhookMessage.objects.all().order_by('-received_at')
    page_num = request.GET.get('page', 1)
    paginator = Paginator(webhook_objs, 20)

    try:
        page_obj = paginator.page(page_num)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    context = {"webhook_objs": page_obj}
    return render(request, "webhooks.html", context)


def tasks(request):
    task_objs = TaskResult.objects.all().order_by('-date_done')
    context = {"task_objs":task_objs}
    return render(request, "tasks.html", context)


def webhook_detail(request, webhook_id):
    webhook_obj = get_object_or_404(ArcGISWebhookMessage, pk=webhook_id)
    context = {"webhook_obj": webhook_obj}
    return render(request, "webhook_detail.html", context)


def hx_webhooks(request):
    webhook_objs = ArcGISWebhookMessage.objects.all().order_by('-received_at')
    context = {"webhook_objs": webhook_objs}
    return render(request, "webhook_refresh_fragment.html", context)


def hx_tasks(request):
    task_objs = TaskResult.objects.all().order_by('-date_done')
    context = {"task_objs": task_objs}
    return render(request, "task_refresh_fragment.html", context)

@csrf_exempt
def hx_test_webhook_send(request):
    test_webhook_data = """{"events": [{"id": "kirk.davis@ocio.wa.gov", "operation": "signin-test", "properties": {}, "source": "users", "userId":"e0d5b07c672c422baf83dd7a9f221bbc", "username": "kirk.davis@ocio.wa.gov", "when":
1645134525842}], "info": {"portalURL": "https://geoportal2.watech.wa.gov/portal/", "webhookId": "4edcf3c9ab0246f5a041d1225d0619f3", "webhookName": "test_webhook", "when": 1645134525845},"properties": {}}"""
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
    webhook_obj = ArcGISWebhookMessage.objects.create(
        received_at=timezone.now(),
        payload=payload,
        event_name = event_name,
    )

    # custome function to process the webhook payload
    process_webhook(webhook_obj)

    return HttpResponse("Message received.", content_type="text/plain")


@atomic
def process_webhook(webhook_obj):
    # assign webhook to a task
    try:
        webhook_name = webhook_obj.payload["info"]["webhookName"]
        WEBHOOK_PROCESS_DICT[webhook_name].delay(webhook_obj.payload)
    except KeyError:
        pass