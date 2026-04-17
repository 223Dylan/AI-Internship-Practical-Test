import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .services.intent_extractor import extract_intent_and_entities


def home(request):
    return render(request, "core/home.html")


@csrf_exempt
@require_http_methods(["POST"])
def extract_intent(request):
    payload = {}
    if request.content_type and "application/json" in request.content_type:
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON payload."}, status=400)
    else:
        payload = request.POST.dict()

    customer_text = str(payload.get("request_text", "")).strip()
    if not customer_text:
        return JsonResponse({"error": "request_text is required."}, status=400)

    try:
        result = extract_intent_and_entities(customer_text)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    except Exception:
        return JsonResponse({"error": "Intent extraction failed."}, status=502)

    return JsonResponse(
        {
            "intent": result.intent,
            "entities": result.entities,
            "provider": result.provider,
            "fallback_used": result.fallback_used,
        }
    )
