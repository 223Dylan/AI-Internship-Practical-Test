from __future__ import annotations

from django.db import models
from django.utils import timezone


class TaskStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    IN_PROGRESS = "IN_PROGRESS", "In Progress"
    COMPLETED = "COMPLETED", "Completed"


class TaskIntent(models.TextChoices):
    SEND_MONEY = "send_money", "send_money"
    GET_AIRPORT_TRANSFER = "get_airport_transfer", "get_airport_transfer"
    HIRE_SERVICE = "hire_service", "hire_service"
    VERIFY_DOCUMENT = "verify_document", "verify_document"
    CHECK_STATUS = "check_status", "check_status"


class EmployeeCategory(models.TextChoices):
    FINANCE = "FINANCE", "Finance"
    OPERATIONS = "OPERATIONS", "Operations"
    LEGAL = "LEGAL", "Legal"
    SUPPORT = "SUPPORT", "Support"


class MessageChannel(models.TextChoices):
    WHATSAPP = "WHATSAPP", "WhatsApp"
    EMAIL = "EMAIL", "Email"
    SMS = "SMS", "SMS"


class Task(models.Model):
    code = models.CharField(max_length=24, unique=True, db_index=True)

    customer_request_text = models.TextField()
    intent = models.CharField(max_length=32, choices=TaskIntent.choices, db_index=True)
    entities = models.JSONField(default=dict, blank=True)

    risk_score = models.PositiveSmallIntegerField()
    risk_reasons = models.JSONField(default=list, blank=True)

    status = models.CharField(
        max_length=16, choices=TaskStatus.choices, default=TaskStatus.PENDING, db_index=True
    )
    assigned_team = models.CharField(
        max_length=16, choices=EmployeeCategory.choices, db_index=True
    )
    assignment_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.code} ({self.intent})"


class TaskEntity(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="entity_items")
    key = models.CharField(max_length=64, db_index=True)
    value = models.TextField()

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["task", "key", "value"], name="uq_task_entity_kv")
        ]
        indexes = [models.Index(fields=["task", "key"])]

    def __str__(self) -> str:
        return f"{self.task.code}: {self.key}={self.value}"


class TaskStep(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="steps")
    step_order = models.PositiveSmallIntegerField()
    description = models.TextField()

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["task", "step_order"], name="uq_task_step_order"
            )
        ]
        indexes = [models.Index(fields=["task", "step_order"])]
        ordering = ["task", "step_order"]

    def __str__(self) -> str:
        return f"{self.task.code} step {self.step_order}"


class TaskMessage(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="messages")
    channel = models.CharField(max_length=16, choices=MessageChannel.choices)
    content = models.TextField()

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["task", "channel"], name="uq_task_message_channel")
        ]
        indexes = [models.Index(fields=["task", "channel"])]

    def __str__(self) -> str:
        return f"{self.task.code} {self.channel}"


class TaskStatusHistory(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="status_history")
    from_status = models.CharField(max_length=16, choices=TaskStatus.choices)
    to_status = models.CharField(max_length=16, choices=TaskStatus.choices)
    changed_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        indexes = [models.Index(fields=["task", "changed_at"])]
        ordering = ["-changed_at"]

    def __str__(self) -> str:
        return f"{self.task.code}: {self.from_status} -> {self.to_status}"
