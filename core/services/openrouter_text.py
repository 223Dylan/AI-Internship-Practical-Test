"""OpenRouter: OpenAI-compatible chat completions (e.g. Gemini via OpenRouter)."""

from __future__ import annotations

import json
from typing import Any

from django.conf import settings

from core.services.gemini_http import post_json_retryable


def openrouter_api_key() -> str:
    key = (settings.OPENROUTER_API_KEY or settings.AI_API_KEY or "").strip()
    return key


def openrouter_generate_text(
    prompt: str,
    *,
    max_output_tokens: int,
    temperature: float,
    timeout: float = 110.0,
) -> str:
    api_key = openrouter_api_key()
    if not api_key:
        raise RuntimeError(
            "OpenRouter API key is not configured. Set OPENROUTER_API_KEY or AI_API_KEY."
        )

    base = settings.OPENROUTER_BASE_URL.rstrip("/")
    url = f"{base}/chat/completions"
    model = settings.OPENROUTER_MODEL
    payload: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_output_tokens,
        "temperature": temperature,
    }

    headers: dict[str, str] = {
        "Authorization": f"Bearer {api_key}",
    }
    if settings.OPENROUTER_HTTP_REFERER:
        headers["HTTP-Referer"] = settings.OPENROUTER_HTTP_REFERER
    if settings.OPENROUTER_APP_TITLE:
        headers["X-Title"] = settings.OPENROUTER_APP_TITLE

    body = post_json_retryable(
        url,
        headers,
        payload,
        timeout=timeout,
        log_prefix="openrouter_http",
        abort_429_retry_if=None,
    )
    parsed = json.loads(body)
    choices = parsed.get("choices") or []
    if not choices:
        raise RuntimeError("OpenRouter returned no choices")

    message = choices[0].get("message") or {}
    content = message.get("content")
    if content is None:
        raise RuntimeError("OpenRouter returned empty message")

    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
            elif isinstance(block, str):
                parts.append(block)
        text = "\n".join(parts).strip()
    else:
        text = str(content).strip()

    if not text:
        raise RuntimeError("OpenRouter returned empty text")
    return text
