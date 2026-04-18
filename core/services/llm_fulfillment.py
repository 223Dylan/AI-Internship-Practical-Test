from __future__ import annotations

from typing import Any, Optional

from django.conf import settings

from core.services.gemini_text import gemini_text_available, generate_text
from core.services.intent_extractor import _parse_llm_json


def _llm_fulfillment_enabled() -> bool:
    if settings.AI_FULFILLMENT_LLM_DISABLED:
        return False
    return gemini_text_available()


def _truncate_sms(text: str, limit: int = 160) -> str:
    t = (text or "").strip()
    if len(t) <= limit:
        return t
    return t[: max(0, limit - 1)].rstrip() + "…"


def normalize_fulfillment_fields(
    raw: dict[str, Any],
) -> Optional[tuple[list[str], dict[str, str]]]:
    return _normalize_fulfillment(raw)


def _normalize_fulfillment(raw: dict[str, Any]) -> Optional[tuple[list[str], dict[str, str]]]:
    steps_raw = raw.get("steps")
    if not isinstance(steps_raw, list):
        return None
    steps: list[str] = []
    for item in steps_raw[:10]:
        if isinstance(item, str) and item.strip():
            steps.append(item.strip()[:500])
    if not (4 <= len(steps) <= 7):
        return None

    wa = raw.get("whatsapp")
    em = raw.get("email")
    sm = raw.get("sms")
    if not (isinstance(wa, str) and isinstance(em, str) and isinstance(sm, str)):
        return None
    wa = wa.strip()
    em = em.strip()
    sm = _truncate_sms(sm.strip(), 160)
    if not wa or not em or not sm:
        return None

    return steps, {"whatsapp": wa, "email": em, "sms": sm}


def try_llm_fulfillment(
    *,
    task_code: str,
    intent: str,
    assigned_team: str,
    risk_score: int,
    customer_text: str,
    allow_network: bool = True,
) -> Optional[tuple[list[str], dict[str, str]]]:
    if not allow_network or not _llm_fulfillment_enabled():
        return None

    prompt = f"""You are Vunoh's internal task fulfillment assistant.

Return ONLY valid JSON (no markdown) with this exact shape:
{{
  "steps": ["string", "..."],
  "whatsapp": "string",
  "email": "string",
  "sms": "string"
}}

Rules:
- steps: 4 to 7 concrete operational steps for the assigned team to execute this task.
- whatsapp: friendly, conversational, 2-5 short lines, include 1-2 tasteful emoji, mention task code {task_code}.
- email: professional, include greeting, task code {task_code}, next steps, and sign-off.
- sms: <= 160 characters, include task code {task_code}, one short actionable line.

Task code: {task_code}
Intent: {intent}
Assigned team: {assigned_team}
Risk score (0-100): {risk_score}
Customer request:
\"\"\"{customer_text}\"\"\"
"""

    try:
        text = generate_text(prompt, max_output_tokens=2048)
        parsed = _parse_llm_json(text)
        if not isinstance(parsed, dict):
            return None
        return normalize_fulfillment_fields(parsed)
    except Exception:
        return None
