"""
Shared JSON POST with retries for LLM HTTP APIs (Gemini generateContent, OpenRouter chat, etc.).
"""

from __future__ import annotations

import json
import logging
import random
import time
from collections.abc import Callable
from typing import Any
from urllib import error, request

from django.conf import settings

LOGGER = logging.getLogger(__name__)

_RETRYABLE_STATUS = frozenset({429, 502, 503})


def _quota_exhausted_gemini(body: str) -> bool:
    """429 with billing/quota exhaustion on Google Gemini — retrying often won't help."""
    b = body.lower()
    if "exceeded your current quota" in b:
        return True
    if "prepayment credits" in b and "depleted" in b:
        return True
    if "resource has been exhausted" in b or "resource_exhausted" in b:
        return True
    if "billing" in b and "quota" in b:
        return True
    return False


def _retry_delay_seconds(http_exc: error.HTTPError, attempt: int) -> float:
    raw = http_exc.headers.get("Retry-After") if http_exc.headers else None
    if raw:
        try:
            return min(float(raw), float(settings.GEMINI_HTTP_MAX_BACKOFF))
        except ValueError:
            pass
    base = float(settings.GEMINI_HTTP_BASE_DELAY)
    cap = float(settings.GEMINI_HTTP_MAX_BACKOFF)
    exp = min(base * (2**attempt), cap)
    jitter = random.uniform(0, min(1.5, cap * 0.1))
    return min(exp + jitter, cap)


def post_json_retryable(
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    *,
    timeout: float,
    log_prefix: str = "llm_http",
    abort_429_retry_if: Callable[[str], bool] | None = None,
) -> str:
    """
    POST JSON; return UTF-8 response body. Retries 429 / 502 / 503 with backoff.
    If abort_429_retry_if(body) is True, do not retry that 429 (Gemini quota).
    """
    data = json.dumps(payload).encode("utf-8")
    max_retries = max(1, int(settings.GEMINI_HTTP_MAX_RETRIES))
    max_total_sleep = float(settings.GEMINI_HTTP_MAX_TOTAL_SLEEP)
    total_sleep = 0.0

    for attempt in range(max_retries):
        merged = dict(headers)
        merged.setdefault("Content-Type", "application/json")
        req = request.Request(url, data=data, headers=merged, method="POST")
        try:
            with request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8")
        except error.HTTPError as exc:
            err_body = ""
            try:
                err_body = exc.read().decode("utf-8", errors="replace")
            except Exception:
                pass

            abort_429 = (
                exc.code == 429
                and abort_429_retry_if is not None
                and abort_429_retry_if(err_body)
            )
            if (
                exc.code in _RETRYABLE_STATUS
                and attempt < max_retries - 1
                and not abort_429
            ):
                wait = _retry_delay_seconds(exc, attempt)
                room = max_total_sleep - total_sleep
                if room <= 0:
                    raise RuntimeError(
                        f"{log_prefix} HTTP {exc.code} (retry budget exhausted): "
                        f"{err_body[:800] or exc.reason}"
                    ) from exc
                wait = min(wait, room)
                total_sleep += wait
                LOGGER.warning(
                    "%s.retry status=%s attempt=%s/%s wait=%.2fs err=%s",
                    log_prefix,
                    exc.code,
                    attempt + 1,
                    max_retries,
                    wait,
                    err_body[:240].replace("\n", " "),
                )
                time.sleep(wait)
                continue

            raise RuntimeError(
                f"{log_prefix} HTTP {exc.code}: {err_body[:800] or exc.reason}"
            ) from exc
        except error.URLError as exc:
            if attempt < max_retries - 1:
                wait = min(
                    float(settings.GEMINI_HTTP_BASE_DELAY) * (2**attempt)
                    + random.uniform(0, 0.5),
                    float(settings.GEMINI_HTTP_MAX_BACKOFF),
                )
                room = max_total_sleep - total_sleep
                if room <= 0:
                    raise RuntimeError(f"{log_prefix} request failed: {exc}") from exc
                wait = min(wait, room)
                total_sleep += wait
                LOGGER.warning(
                    "%s.retry url_error attempt=%s/%s wait=%.2fs err=%s",
                    log_prefix,
                    attempt + 1,
                    max_retries,
                    wait,
                    exc,
                )
                time.sleep(wait)
                continue
            raise RuntimeError(f"{log_prefix} request failed: {exc}") from exc

    raise RuntimeError(f"{log_prefix}: exhausted retries")


def post_generate_content(
    endpoint: str,
    payload: dict[str, Any],
    *,
    timeout: float,
) -> str:
    """POST to Gemini generateContent (API key in query string)."""
    return post_json_retryable(
        endpoint,
        {"Content-Type": "application/json"},
        payload,
        timeout=timeout,
        log_prefix="gemini_http",
        abort_429_retry_if=_quota_exhausted_gemini,
    )
