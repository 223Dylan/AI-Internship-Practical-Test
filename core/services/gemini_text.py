from __future__ import annotations

import json
from urllib import error, request

from django.conf import settings


def gemini_text_available() -> bool:
    return settings.AI_PROVIDER == "gemini" and bool(settings.AI_API_KEY)


def generate_text(prompt: str, *, max_output_tokens: int = 1024) -> str:
    api_key = settings.AI_API_KEY
    if not api_key:
        raise RuntimeError("Gemini API key is not configured.")

    model = settings.GEMINI_MODEL
    endpoint = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        f"?key={api_key}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": max_output_tokens,
        },
    }
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        endpoint, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with request.urlopen(req, timeout=45) as resp:
            body = resp.read().decode("utf-8")
    except error.URLError as exc:
        raise RuntimeError(f"Gemini request failed: {exc}") from exc

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
