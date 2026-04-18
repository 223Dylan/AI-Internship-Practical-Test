from __future__ import annotations

import json

from django.conf import settings

from core.services.gemini_http import post_generate_content
from core.services.openrouter_text import openrouter_api_key, openrouter_generate_text


def llm_text_available() -> bool:
    p = settings.AI_PROVIDER
    if p == "gemini":
        return bool(settings.AI_API_KEY)
    if p == "openrouter":
        return bool(openrouter_api_key())
    return False


def gemini_text_available() -> bool:
    """Backward-compatible alias: true when Gemini or OpenRouter LLM is configured."""
    return llm_text_available()


def generate_text(
    prompt: str,
    *,
    max_output_tokens: int = 1024,
    temperature: float = 0.2,
) -> str:
    provider = settings.AI_PROVIDER
    if provider == "openrouter":
        return openrouter_generate_text(
            prompt,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
            timeout=110.0,
        )

    if provider != "gemini":
        raise RuntimeError(
            f"AI_PROVIDER must be 'gemini' or 'openrouter' for generate_text (got {provider!r})."
        )

    api_key = settings.AI_API_KEY
    if not api_key:
        raise RuntimeError("Gemini API key is not configured (AI_API_KEY).")

    model = settings.GEMINI_MODEL
    endpoint = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        f"?key={api_key}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_output_tokens,
        },
    }
    body = post_generate_content(endpoint, payload, timeout=110.0)

    parsed = json.loads(body)
    candidates = parsed.get("candidates", [])
    if not candidates:
        raise RuntimeError("Gemini returned no candidates")

    parts = candidates[0].get("content", {}).get("parts", [])
    chunks = [p.get("text", "") for p in parts if isinstance(p, dict)]
    text = "\n".join(chunks).strip()
    if not text:
        raise RuntimeError("Gemini returned empty text")
    return text
