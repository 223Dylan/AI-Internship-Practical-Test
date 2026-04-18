from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any

from django.conf import settings

from core.services.gemini_text import generate_text, llm_text_available

LOGGER = logging.getLogger(__name__)

ALLOWED_INTENTS = {
    "send_money",
    "get_airport_transfer",
    "hire_service",
    "verify_document",
    "check_status",
}

INTENT_ALIASES = {
    "get airport transfer": "get_airport_transfer",
    "airport_transfer": "get_airport_transfer",
    "airport transfer": "get_airport_transfer",
}


@dataclass(frozen=True)
class IntentExtractionResult:
    intent: str
    entities: dict[str, Any]
    provider: str
    fallback_used: bool
    raw_response: str


def extract_intent_and_entities(
    customer_text: str, *, prefer_local: bool = False
) -> IntentExtractionResult:
    clean_text = customer_text.strip()
    if not clean_text:
        raise ValueError("customer_text is required")

    provider = settings.AI_PROVIDER

    LOGGER.info("intent_extraction.start provider=%s text_length=%d", provider, len(clean_text))
    if not prefer_local and llm_text_available():
        try:
            raw_output = generate_text(
                _build_prompt(clean_text),
                max_output_tokens=350,
                temperature=0.1,
            )
            payload = _parse_llm_json(raw_output)
            normalized_intent = _normalize_intent(payload.get("intent", ""))
            entities = _normalize_entities(payload.get("entities"))
            return IntentExtractionResult(
                intent=normalized_intent,
                entities=entities,
                provider=provider,
                fallback_used=False,
                raw_response=raw_output,
            )
        except Exception as exc:
            LOGGER.warning("intent_extraction.llm_failed error=%s", exc)

    fallback = _heuristic_fallback(clean_text)
    return IntentExtractionResult(
        intent=fallback["intent"],
        entities=fallback["entities"],
        provider="mock",
        fallback_used=True,
        raw_response=json.dumps(fallback),
    )


def _build_prompt(customer_text: str) -> str:
    return (
        "You are an intent extraction engine for a diaspora support platform.\n"
        "Return ONLY valid JSON with this exact shape:\n"
        '{ "intent": "<one allowed intent>", "entities": { ... } }\n'
        "Allowed intents: send_money, get_airport_transfer, hire_service, verify_document, check_status.\n"
        "Rules:\n"
        "- Do not include markdown or code fences.\n"
        "- entities must be a flat JSON object.\n"
        "- Use null for unknown values.\n"
        f'Customer request: "{customer_text}"'
    )


def _parse_llm_json(raw_output: str) -> dict[str, Any]:
    candidate = raw_output.strip()
    if candidate.startswith("```"):
        candidate = candidate.strip("`")
        candidate = candidate.replace("json", "", 1).strip()

    try:
        parsed = json.loads(candidate)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    embedded = _extract_embedded_json(candidate)
    return json.loads(embedded)


def _extract_embedded_json(text: str) -> str:
    start = text.find("{")
    if start == -1:
        raise ValueError("No JSON object found in LLM output")

    depth = 0
    for idx, char in enumerate(text[start:], start=start):
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : idx + 1]
    raise ValueError("Malformed JSON object in LLM output")


def _normalize_intent(raw_intent: str) -> str:
    value = raw_intent.strip().lower().replace("-", "_")
    value = re.sub(r"\s+", "_", value)
    value = INTENT_ALIASES.get(value, value)
    if value not in ALLOWED_INTENTS:
        raise ValueError(f"Unsupported intent: {raw_intent}")
    return value


def _normalize_entities(raw_entities: Any) -> dict[str, Any]:
    if isinstance(raw_entities, dict):
        return raw_entities
    if raw_entities is None:
        return {}
    raise ValueError("entities must be a JSON object")


def _heuristic_fallback(customer_text: str) -> dict[str, Any]:
    text = customer_text.lower()
    entities: dict[str, Any] = {
        "urgency": "high" if "urgent" in text or "asap" in text else "normal"
    }

    amount_match = re.search(r"(kes|ksh)?\s*([\d,]+)", text)
    if amount_match:
        entities["amount"] = amount_match.group(2).replace(",", "")
        entities["currency"] = "KES"

    if "verify" in text or "title deed" in text or "document" in text:
        return {"intent": "verify_document", "entities": entities}
    if "clean" in text or "lawyer" in text or "service" in text or "hire" in text:
        return {"intent": "hire_service", "entities": entities}
    if "airport" in text or "pickup" in text or "pick up" in text or "transfer" in text:
        return {"intent": "get_airport_transfer", "entities": entities}
    if "status" in text or "follow up" in text or "track" in text:
        return {"intent": "check_status", "entities": entities}
    return {"intent": "send_money", "entities": entities}
