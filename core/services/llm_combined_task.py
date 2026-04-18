from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from django.conf import settings

from core.services.employee_assigner import ASSIGNABLE_TEAMS
from core.services.gemini_text import gemini_text_available, generate_text
from core.services.intent_extractor import (
    _normalize_entities,
    _normalize_intent,
    _parse_llm_json,
)
from core.services.llm_fulfillment import normalize_fulfillment_fields


@dataclass(frozen=True)
class CombinedTaskLLMResult:
    intent: str
    entities: dict[str, Any]
    assigned_team: str
    assignment_reason: str
    steps: list[str]
    messages_by_channel: dict[str, str]


def combined_task_llm_enabled() -> bool:
    if settings.AI_COMBINED_LLM_DISABLED:
        return False
    return gemini_text_available()


def try_combined_task_llm(
    customer_text: str, *, task_code: str
) -> Optional[CombinedTaskLLMResult]:
    if not combined_task_llm_enabled():
        return None

    snippet = customer_text.strip()
    if len(snippet) > 6000:
        snippet = snippet[:6000] + "…"

    prompt = f"""You are Vunoh's task intake pipeline. Produce one JSON object only (no markdown).

Shape:
{{
  "intent": "<one of: send_money, get_airport_transfer, hire_service, verify_document, check_status>",
  "entities": {{ }},
  "assigned_team": "FINANCE"|"OPERATIONS"|"LEGAL"|"SUPPORT",
  "assignment_reason": "one concise sentence",
  "steps": ["4 to 7 short operational steps for the assigned team"],
  "whatsapp": "friendly multi-line message with 1-2 emoji, mention task code {task_code}",
  "email": "professional email body with greeting, task code {task_code}, next steps, sign-off",
  "sms": "<= 160 chars, include task code {task_code}"
}}

Rules:
- entities: flat JSON only; use null for unknowns.
- FINANCE: payments/transfers. LEGAL: documents/titles. OPERATIONS: services, drivers, airport, field work. SUPPORT: status/unclear.
- steps must be 4-7 non-empty strings.
- sms must be <= 160 characters.

Task code (use exactly in messages): {task_code}
Customer request:
\"\"\"{snippet}\"\"\"
"""

    try:
        raw = generate_text(prompt, max_output_tokens=3072)
        parsed = _parse_llm_json(raw)
        if not isinstance(parsed, dict):
            return None

        intent = _normalize_intent(str(parsed.get("intent", "")))
        entities = _normalize_entities(parsed.get("entities"))

        team = str(parsed.get("assigned_team", "")).strip().upper()
        reason = str(parsed.get("assignment_reason", "")).strip()
        if team not in ASSIGNABLE_TEAMS or not reason:
            return None

        fulfil = normalize_fulfillment_fields(parsed)
        if fulfil is None:
            return None
        steps, messages_by_channel = fulfil

        return CombinedTaskLLMResult(
            intent=intent,
            entities=entities,
            assigned_team=team,
            assignment_reason=reason,
            steps=steps,
            messages_by_channel=messages_by_channel,
        )
    except Exception:
        return None
