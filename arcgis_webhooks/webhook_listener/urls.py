from django.urls import path

import webhook_listener.views as views

urlpatterns = [
    path('', views.index, name="index"),
    path('webhooks/', views.webhooks, name="webhooks"),
    path('webhooks/wh-<int:webhook_id>/', views.webhook_detail, name="webhook_detail"),
    path('hx_webhooks/', views.hx_webhooks, name="hx_webhooks"),
    path('hx_tasks/', views.hx_tasks, name="hx_tasks"),
    path('tasks/', views.tasks, name="tasks"),
    path("webhooks/arcgis/mPnBRC1qxapOAxQpWmjy4NofbgxCmXSj/", views.arcgis_webhook),
    path('hx_test_webhook_send/', views.hx_test_webhook_send, name="hx_test_webhook_send")
]