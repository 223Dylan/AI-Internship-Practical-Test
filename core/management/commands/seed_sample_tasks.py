from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Task, TaskStatus, TaskStatusHistory
from core.services.task_creator import create_task_from_request


SAMPLE_REQUESTS = [
    "I need to send KES 15,000 to my mother in Kisumu urgently.",
    "Please verify my land title deed for the plot in Karen.",
    "Can someone clean my apartment in Westlands on Friday?",
    "I need an airport pickup in Nairobi on Tuesday morning.",
    "What is the status of my last request? Task follow up please.",
]


def _apply_status(task: Task, new_status: str) -> None:
    with transaction.atomic():
        locked = Task.objects.select_for_update().get(pk=task.pk)
        if locked.status == new_status:
            return
        old = locked.status
        locked.status = new_status
        locked.save(update_fields=["status", "updated_at"])
        TaskStatusHistory.objects.create(
            task=locked, from_status=old, to_status=new_status
        )


class Command(BaseCommand):
    help = (
        "Create at least five fully populated sample tasks (entities, steps, messages, "
        "risk, assignment, status history). Use --clear to remove existing tasks first."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all tasks (cascades to related rows) before seeding.",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            deleted, _ = Task.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Deleted {deleted} task-related rows."))

        created_codes = []
        for text in SAMPLE_REQUESTS:
            result = create_task_from_request(text)
            created_codes.append(result.task.code)
            self.stdout.write(f"Created task {result.task.code} ({result.task.intent})")

        tasks = list(Task.objects.filter(code__in=created_codes).order_by("created_at"))
        if len(tasks) < 5:
            self.stdout.write(self.style.ERROR("Expected 5 tasks; check SAMPLE_REQUESTS."))
            return

        _apply_status(tasks[1], TaskStatus.IN_PROGRESS)
        _apply_status(tasks[2], TaskStatus.IN_PROGRESS)
        _apply_status(tasks[2], TaskStatus.COMPLETED)
        _apply_status(tasks[3], TaskStatus.IN_PROGRESS)

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(tasks)} sample tasks with mixed statuses."))
