from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Optional

from django.conf import settings

from core.services.gemini_text import generate_text, llm_text_available
from core.services.intent_extractor import _parse_llm_json

ASSIGNABLE_TEAMS = frozenset({"FINANCE", "OPERATIONS", "LEGAL", "SUPPORT"})
_VALID_TEAMS = ASSIGNABLE_TEAMS


@dataclass(frozen=True)
class AssignmentResult:
    team: str
    reason: str


def _llm_assignment_enabled() -> bool:
    if settings.AI_ASSIGNMENT_LLM_DISABLED:
        return False
    return llm_text_available()


def try_llm_assign(
    intent: str, entities: dict[str, Any], customer_text: str
) -> Optional[AssignmentResult]:
    snippet = (customer_text or "").strip()
    if len(snippet) > 4000:
        snippet = snippet[:4000] + "…"
    prompt = f"""You route customer tasks to one employee team at Vunoh.

Return ONLY valid JSON (no markdown) with this exact shape:
{{"team":"FINANCE"|"OPERATIONS"|"LEGAL"|"SUPPORT","reason":"one concise sentence citing the request"}}

Intent label: {intent}
Structured entities: {json.dumps(entities, ensure_ascii=False)}
Customer message:
\"\"\"{snippet}\"\"\"

Choose FINANCE for payments/transfers/wallets/refunds. LEGAL for documents/titles/contracts/compliance.
OPERATIONS for bookings, cleaning, drivers, airport runs, field services. SUPPORT for status checks
or when intent is unclear."""

    try:
        text = generate_text(prompt, max_output_tokens=256)
        parsed = _parse_llm_json(text)
        if not isinstance(parsed, dict):
            return None
        team = str(parsed.get("team", "")).strip().upper()
        reason = str(parsed.get("reason", "")).strip()
        if team not in _VALID_TEAMS or not reason:
            return None
        return AssignmentResult(team=team, reason=reason)
    except Exception:
        return None


def assign_employee_team_with_llm_optional(
    intent: str,
    entities: dict[str, Any],
    customer_text: str,
    *,
    allow_llm: bool = True,
) -> tuple[AssignmentResult, bool]:
    if allow_llm and _llm_assignment_enabled():
        assigned = try_llm_assign(intent, entities, customer_text)
        if assigned is not None:
            return assigned, True
    return assign_employee_team(intent, entities), False


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

