from __future__ import annotations

import random
import string
from dataclasses import dataclass
from typing import Any

from django.conf import settings
from django.db import transaction

from core.models import (
    MessageChannel,
    Task,
    TaskEntity,
    TaskMessage,
    TaskStatus,
    TaskStatusHistory,
    TaskStep,
)
from core.services.employee_assigner import assign_employee_team_with_llm_optional
from core.services.intent_extractor import extract_intent_and_entities
from core.services.llm_combined_task import combined_task_llm_enabled, try_combined_task_llm
from core.services.llm_fulfillment import try_llm_fulfillment
from core.services.risk_scorer import assess_risk


@dataclass(frozen=True)
class TaskCreationResult:
    task: Task
    extraction_provider: str
    fallback_used: bool
    assignment_reason: str
    llm_fulfillment_used: bool
    llm_assignment_used: bool


def create_task_from_request(customer_text: str) -> TaskCreationResult:
    text = customer_text.strip()
    combined_attempted = False

    if combined_task_llm_enabled():
        combined_attempted = True
        code = _generate_task_code()
        combined = try_combined_task_llm(text, task_code=code)
        if combined:
            risk = assess_risk(combined.intent, combined.entities)
            with transaction.atomic():
                task = Task.objects.create(
                    code=code,
                    customer_request_text=text,
                    intent=combined.intent,
                    entities=combined.entities,
                    risk_score=risk.score,
                    risk_reasons=risk.reasons,
                    assigned_team=combined.assigned_team,
                    assignment_reason=combined.assignment_reason,
                    status=TaskStatus.PENDING,
                )
                _persist_entity_items(task, combined.entities)
                _persist_steps_from_list(task, combined.steps)
                _persist_messages_from_channel_strings(
                    task, combined.messages_by_channel
                )
                TaskStatusHistory.objects.create(
                    task=task,
                    from_status=TaskStatus.PENDING,
                    to_status=TaskStatus.PENDING,
                )
            return TaskCreationResult(
                task=task,
                extraction_provider=settings.AI_PROVIDER,
                fallback_used=False,
                assignment_reason=combined.assignment_reason,
                llm_fulfillment_used=True,
                llm_assignment_used=True,
            )

    extraction = extract_intent_and_entities(text, prefer_local=combined_attempted)
    risk = assess_risk(extraction.intent, extraction.entities)
    assignment, llm_assignment_used = assign_employee_team_with_llm_optional(
        extraction.intent,
        extraction.entities,
        text,
        allow_llm=not combined_attempted,
    )

    code = _generate_task_code()
    fulfil = try_llm_fulfillment(
        task_code=code,
        intent=extraction.intent,
        assigned_team=assignment.team,
        risk_score=risk.score,
        customer_text=text,
        allow_network=not combined_attempted,
    )
    llm_fulfillment_used = fulfil is not None

    with transaction.atomic():
        task = Task.objects.create(
            code=code,
            customer_request_text=text,
            intent=extraction.intent,
            entities=extraction.entities,
            risk_score=risk.score,
            risk_reasons=risk.reasons,
            assigned_team=assignment.team,
            assignment_reason=assignment.reason,
            status=TaskStatus.PENDING,
        )

        _persist_entity_items(task, extraction.entities)
        if fulfil:
            steps, messages_by_channel = fulfil
            _persist_steps_from_list(task, steps)
            _persist_messages_from_channel_strings(task, messages_by_channel)
        else:
            _persist_steps(task, extraction.intent, extraction.entities)
            _persist_messages(task)
        TaskStatusHistory.objects.create(
            task=task,
            from_status=TaskStatus.PENDING,
            to_status=TaskStatus.PENDING,
        )

    return TaskCreationResult(
        task=task,
        extraction_provider=extraction.provider,
        fallback_used=extraction.fallback_used,
        assignment_reason=assignment.reason,
        llm_fulfillment_used=llm_fulfillment_used,
        llm_assignment_used=llm_assignment_used,
    )


def _persist_steps_from_list(task: Task, steps: list[str]) -> None:
    for index, description in enumerate(steps, start=1):
        TaskStep.objects.create(task=task, step_order=index, description=description)


def _persist_messages_from_channel_strings(task: Task, messages: dict[str, str]) -> None:
    mapping = {
        "whatsapp": MessageChannel.WHATSAPP,
        "email": MessageChannel.EMAIL,
        "sms": MessageChannel.SMS,
    }
    for key, channel in mapping.items():
        content = messages.get(key, "").strip()
        TaskMessage.objects.create(task=task, channel=channel, content=content)


def _persist_entity_items(task: Task, entities: dict[str, Any]) -> None:
    for key, value in entities.items():
        value_string = _normalize_value(value)
        TaskEntity.objects.create(task=task, key=str(key), value=value_string)


def _normalize_value(value: Any) -> str:
    if isinstance(value, (list, dict)):
        return str(value)
    return "" if value is None else str(value)


def _persist_steps(task: Task, intent: str, entities: dict[str, Any]) -> None:
    steps = _generate_steps(intent, entities)
    for index, description in enumerate(steps, start=1):
        TaskStep.objects.create(task=task, step_order=index, description=description)


def _persist_messages(task: Task) -> None:
    messages = _generate_messages(task)
    for channel, content in messages.items():
        TaskMessage.objects.create(task=task, channel=channel, content=content)


def _generate_steps(intent: str, entities: dict[str, Any]) -> list[str]:
    location = str(entities.get("location") or entities.get("destination") or "Nairobi")
    service = str(entities.get("service_type") or "requested service")
    document = str(entities.get("document_type") or entities.get("document") or "document")
    recipient = str(entities.get("recipient") or "recipient")

    if intent == "send_money":
        return [
            "Confirm sender identity and transaction authorization.",
            f"Verify recipient details for {recipient}.",
            "Run fraud checks and compliance screening.",
            "Initiate transfer and capture confirmation reference.",
            "Notify customer after transfer confirmation.",
        ]
    if intent == "verify_document":
        return [
            f"Collect and validate submitted {document} details.",
            "Run records verification with relevant authorities.",
            "Escalate suspicious mismatches to Legal review.",
            "Prepare verification result and supporting notes.",
            "Share verification outcome with customer.",
        ]
    if intent == "hire_service":
        return [
            f"Confirm service scope for {service}.",
            f"Match and shortlist providers near {location}.",
            "Confirm schedule and service fee with customer.",
            "Dispatch provider and monitor completion evidence.",
            "Close task after customer sign-off.",
        ]
    if intent == "get_airport_transfer":
        return [
            "Collect arrival details and passenger contacts.",
            f"Assign verified driver and vehicle for {location}.",
            "Share pickup instructions with customer.",
            "Track arrival and pickup completion status.",
            "Confirm successful drop-off and close task.",
        ]
    return [
        "Retrieve task details by code and current workflow status.",
        "Confirm latest update from assigned operations team.",
        "Prepare concise progress summary for customer.",
        "Share next expected action and timeline.",
    ]


def _generate_messages(task: Task) -> dict[str, str]:
    whatsapp = (
        f"Hi! Your request is received and now in {task.status.replace('_', ' ').title()}.\n"
        f"Task code: {task.code}\n"
        f"Team: {task.assigned_team.title()}\n"
        "We'll keep you updated at each milestone."
    )
    email = (
        "Subject: Vunoh Task Confirmation\n\n"
        f"Dear Customer,\n\nYour request has been logged successfully.\n"
        f"Task Code: {task.code}\n"
        f"Intent: {task.intent}\n"
        f"Current Status: {task.status.replace('_', ' ').title()}\n"
        f"Assigned Team: {task.assigned_team.title()}\n"
        f"Risk Score: {task.risk_score}\n\n"
        "We will notify you as your task progresses.\n\nRegards,\nVunoh Global"
    )
    sms = _truncate_sms(
        f"Vunoh: Task {task.code} is {task.status.replace('_', ' ').title()}."
        f" Team {task.assigned_team.title()}. Reply with code for updates."
    )

    return {
        MessageChannel.WHATSAPP: whatsapp,
        MessageChannel.EMAIL: email,
        MessageChannel.SMS: sms,
    }


def _truncate_sms(message: str) -> str:
    return message if len(message) <= 160 else message[:157] + "..."


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

