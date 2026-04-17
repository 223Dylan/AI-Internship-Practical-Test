from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass
from typing import Any
from urllib import error, request

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


def extract_intent_and_entities(customer_text: str) -> IntentExtractionResult:
    clean_text = customer_text.strip()
    if not clean_text:
        raise ValueError("customer_text is required")

    provider = os.environ.get("AI_PROVIDER", "mock").strip().lower() or "mock"
    api_key = os.environ.get("AI_API_KEY", "").strip()

    LOGGER.info("intent_extraction.start provider=%s text_length=%d", provider, len(clean_text))
    if provider == "gemini" and api_key:
        try:
            raw_output = _call_gemini(clean_text, api_key)
            payload = _parse_llm_json(raw_output)
            normalized_intent = _normalize_intent(payload.get("intent", ""))
            entities = _normalize_entities(payload.get("entities"))
            return IntentExtractionResult(
                intent=normalized_intent,
                entities=entities,
                provider="gemini",
                fallback_used=False,
                raw_response=raw_output,
            )
        except Exception as exc:
            LOGGER.warning("intent_extraction.gemini_failed error=%s", exc)

    fallback = _heuristic_fallback(clean_text)
    return IntentExtractionResult(
        intent=fallback["intent"],
        entities=fallback["entities"],
        provider="mock",
        fallback_used=True,
        raw_response=json.dumps(fallback),
    )


def _call_gemini(customer_text: str, api_key: str) -> str:
    model = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
    prompt = _build_prompt(customer_text)
    endpoint = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        f"?key={api_key}"
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 350},
    }
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        endpoint, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )

    try:
        with request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8")
    except error.URLError as exc:
        raise RuntimeError(f"Gemini request failed: {exc}") from exc

    parsed = json.loads(body)
    candidates = parsed.get("candidates", [])
    if not candidates:
        raise RuntimeError("Gemini returned no candidates")

    parts = candidates[0].get("content", {}).get("parts", [])
    text_chunks = [item.get("text", "") for item in parts if isinstance(item, dict)]
    joined_text = "\n".join(text_chunks).strip()
    if not joined_text:
        raise RuntimeError("Gemini returned empty text")
    return joined_text


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

