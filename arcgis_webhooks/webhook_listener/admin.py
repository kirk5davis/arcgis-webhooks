from django.contrib import admin
from webhook_listener.models import ArcGISWebhookMessage, Task, TaskKind


# register the Run tasks management action
@admin.action(description="Run tasks")
def run_tasks(modeladmin, request, queryset):
    for task in queryset.all():
        task.run()


# register Tasks model with admin
class TaskAdmin(admin.ModelAdmin):
    def success(self, obj):
        if obj.last_run is None:
            return None
        return not obj.failed
    
    readonly_fields = (
        "json_pprint",
    )

    @admin.display(description="JSON pretty print")
    def json_pprint(self, instance):
        import json
        return admin.mark_safe(
            f"""<pre>{json.dumps(instance.data, sort_keys=True, indent=4)}</pre>"""
        )

    success.boolean = True
    ordering = ["-created", "-last_run"]
    actions = [run_tasks]
    list_display = ["__str__", "created", "active", "periodic", "success", "last_run"]
    list_filter = [
        "kind",
        "active",
        "failed",
    ]


class TaskKindAdmin(admin.ModelAdmin):
    def resolves(self, obj):
        from django.utils.module_loading import import_string

        try:
            _ = import_string(obj.dotted_path)
            return True
        except ImportError:
            return False

    resolves.boolean = True
    ordering = ["-created", "-last_modified"]
    list_display = ["__str__", "created", "last_modified", "resolves"]

# register model objects
admin.site.register(ArcGISWebhookMessage)
admin.site.register(Task, TaskAdmin)
admin.site.register(TaskKind, TaskKindAdmin)