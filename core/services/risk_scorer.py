from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any


@dataclass(frozen=True)
class RiskAssessmentResult:
    score: int
    reasons: list[str]


def assess_risk(intent: str, entities: dict[str, Any]) -> RiskAssessmentResult:
    score = 20
    reasons: list[str] = ["Base operational risk."]

    score += _intent_risk(intent, reasons)
    score += _amount_risk(entities, reasons)
    score += _urgency_risk(entities, reasons)
    score += _recipient_risk(entities, reasons)
    score += _document_risk(entities, reasons)
    score += _history_adjustment(entities, reasons)

    bounded = max(0, min(100, score))
    return RiskAssessmentResult(score=bounded, reasons=reasons)


def _intent_risk(intent: str, reasons: list[str]) -> int:
    if intent == "verify_document":
        reasons.append("Document verification carries elevated fraud/legal exposure.")
        return 22
    if intent == "send_money":
        reasons.append("Money transfer requests require stronger fraud checks.")
        return 16
    if intent == "get_airport_transfer":
        reasons.append("Airport transfer has moderate coordination and trust risk.")
        return 10
    if intent == "hire_service":
        reasons.append("Service hire has moderate fulfillment and quality risk.")
        return 8
    if intent == "check_status":
        reasons.append("Status checks carry low execution risk.")
        return 2
    reasons.append("Unknown intent type; conservative risk uplift applied.")
    return 12


def _amount_risk(entities: dict[str, Any], reasons: list[str]) -> int:
    amount = _extract_amount(entities)
    if amount is None:
        return 0
    if amount >= Decimal("100000"):
        reasons.append("Large transfer amount (>=100,000 KES) increases risk.")
        return 30
    if amount >= Decimal("50000"):
        reasons.append("Higher transfer amount (>=50,000 KES) increases risk.")
        return 20
    if amount >= Decimal("15000"):
        reasons.append("Moderate transfer amount (>=15,000 KES) increases risk.")
        return 10
    return 0


def _urgency_risk(entities: dict[str, Any], reasons: list[str]) -> int:
    urgency = str(entities.get("urgency", "")).strip().lower()
    if urgency in {"high", "urgent", "asap", "immediate"}:
        reasons.append("High urgency requests have higher error and fraud pressure.")
        return 14
    return 0


def _recipient_risk(entities: dict[str, Any], reasons: list[str]) -> int:
    if "recipient_verified" not in entities:
        return 0

    verified = _to_bool(entities.get("recipient_verified"))
    if verified is False:
        reasons.append("Recipient is unverified, increasing transfer risk.")
        return 15
    if verified is None:
        reasons.append("Recipient verification status unknown.")
        return 8
    return 0


def _document_risk(entities: dict[str, Any], reasons: list[str]) -> int:
    doc_type = str(
        entities.get("document_type")
        or entities.get("document")
        or entities.get("service_type")
        or ""
    ).strip().lower()
    if any(token in doc_type for token in ("land title", "title deed", "title")):
        reasons.append("Land/title documentation requests are legally sensitive.")
        return 15
    return 0


def _history_adjustment(entities: dict[str, Any], reasons: list[str]) -> int:
    returning = _to_bool(entities.get("returning_customer"))
    clean_history = _to_bool(entities.get("clean_history"))
    if returning and clean_history:
        reasons.append("Returning customer with clean history lowers risk.")
        return -14
    return 0


def _extract_amount(entities: dict[str, Any]) -> Decimal | None:
    candidates = [
        entities.get("amount"),
        entities.get("transfer_amount"),
        entities.get("amount_kes"),
    ]
    for value in candidates:
        if value is None:
            continue
        cleaned = str(value).replace(",", "").replace("KES", "").replace("ksh", "")
        cleaned = cleaned.strip().lower().replace("kes", "").strip()
        if not cleaned:
            continue
        try:
            amount = Decimal(cleaned)
            if amount >= 0:
                return amount
        except (InvalidOperation, ValueError):
            continue
    return None


def _to_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None:
        return None

    lowered = str(value).strip().lower()
    if lowered in {"true", "yes", "y", "1", "verified"}:
        return True
    if lowered in {"false", "no", "n", "0", "unverified", "unknown"}:
        return False
    return None

