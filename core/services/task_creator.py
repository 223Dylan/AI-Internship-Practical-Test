from __future__ import annotations

import random
import string
from dataclasses import dataclass
from typing import Any

from django.db import transaction

from core.models import Task, TaskEntity, TaskStatus, TaskStatusHistory
from core.services.intent_extractor import extract_intent_and_entities
from core.services.risk_scorer import assess_risk


INTENT_TEAM_MAP = {
    "send_money": "FINANCE",
    "get_airport_transfer": "OPERATIONS",
    "hire_service": "OPERATIONS",
    "verify_document": "LEGAL",
    "check_status": "SUPPORT",
}


@dataclass(frozen=True)
class TaskCreationResult:
    task: Task
    extraction_provider: str
    fallback_used: bool


def create_task_from_request(customer_text: str) -> TaskCreationResult:
    extraction = extract_intent_and_entities(customer_text)
    risk = assess_risk(extraction.intent, extraction.entities)

    with transaction.atomic():
        task = Task.objects.create(
            code=_generate_task_code(),
            customer_request_text=customer_text.strip(),
            intent=extraction.intent,
            entities=extraction.entities,
            risk_score=risk.score,
            risk_reasons=risk.reasons,
            assigned_team=INTENT_TEAM_MAP.get(extraction.intent, "SUPPORT"),
            status=TaskStatus.PENDING,
        )

        _persist_entity_items(task, extraction.entities)
        TaskStatusHistory.objects.create(
            task=task,
            from_status=TaskStatus.PENDING,
            to_status=TaskStatus.PENDING,
        )

    return TaskCreationResult(
        task=task,
        extraction_provider=extraction.provider,
        fallback_used=extraction.fallback_used,
    )


def _persist_entity_items(task: Task, entities: dict[str, Any]) -> None:
    for key, value in entities.items():
        value_string = _normalize_value(value)
        TaskEntity.objects.create(task=task, key=str(key), value=value_string)


def _normalize_value(value: Any) -> str:
    if isinstance(value, (list, dict)):
        return str(value)
    return "" if value is None else str(value)


def _generate_task_code() -> str:
    # Example code: VNH-20260416-AB12CD
    from django.utils import timezone

    date_part = timezone.now().strftime("%Y%m%d")
    for _ in range(20):
        suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        candidate = f"VNH-{date_part}-{suffix}"
        if not Task.objects.filter(code=candidate).exists():
            return candidate
    raise RuntimeError("Unable to generate unique task code.")

