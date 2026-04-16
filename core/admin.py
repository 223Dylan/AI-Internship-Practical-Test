from django.contrib import admin

from .models import Task, TaskEntity, TaskMessage, TaskStatusHistory, TaskStep


class TaskEntityInline(admin.TabularInline):
    model = TaskEntity
    extra = 0


class TaskStepInline(admin.TabularInline):
    model = TaskStep
    extra = 0


class TaskMessageInline(admin.TabularInline):
    model = TaskMessage
    extra = 0


class TaskStatusHistoryInline(admin.TabularInline):
    model = TaskStatusHistory
    extra = 0
    readonly_fields = ("from_status", "to_status", "changed_at")
    can_delete = False


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("code", "intent", "status", "risk_score", "assigned_team", "created_at")
    list_filter = ("intent", "status", "assigned_team")
    search_fields = ("code", "customer_request_text")
    readonly_fields = ("created_at", "updated_at")
    inlines = (TaskEntityInline, TaskStepInline, TaskMessageInline, TaskStatusHistoryInline)


admin.site.register(TaskEntity)
admin.site.register(TaskStep)
admin.site.register(TaskMessage)
admin.site.register(TaskStatusHistory)
