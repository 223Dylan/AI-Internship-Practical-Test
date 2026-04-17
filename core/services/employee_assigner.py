from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AssignmentResult:
    team: str
    reason: str


def assign_employee_team(intent: str, entities: dict[str, Any]) -> AssignmentResult:
    normalized_intent = (intent or "").strip().lower()
    doc_hint = str(entities.get("document_type") or entities.get("document") or "").lower()

    if normalized_intent == "send_money":
        return AssignmentResult(
            team="FINANCE",
            reason="Money transfer workflows are handled by Finance for fraud and settlement checks.",
        )
    if normalized_intent == "verify_document":
        if any(token in doc_hint for token in ("title", "land")):
            return AssignmentResult(
                team="LEGAL",
                reason="Land/title documents require Legal verification and compliance review.",
            )
        return AssignmentResult(
            team="LEGAL",
            reason="Document verification requests are routed to Legal for validation.",
        )
    if normalized_intent in {"hire_service", "get_airport_transfer"}:
        return AssignmentResult(
            team="OPERATIONS",
            reason="Service fulfillment and field logistics are coordinated by Operations.",
        )
    if normalized_intent == "check_status":
        return AssignmentResult(
            team="SUPPORT",
            reason="Status follow-ups are handled by Support for customer communication.",
        )

    return AssignmentResult(
        team="SUPPORT",
        reason="Default routing to Support when intent is unclear.",
    )

