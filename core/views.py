import json

from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import Task, TaskStatus, TaskStatusHistory
from .services.intent_extractor import extract_intent_and_entities
from .services.risk_scorer import assess_risk
from .services.task_creator import create_task_from_request


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

    risk = assess_risk(result.intent, result.entities)
    return JsonResponse(
        {
            "intent": result.intent,
            "entities": result.entities,
            "provider": result.provider,
            "fallback_used": result.fallback_used,
            "risk_score": risk.score,
            "risk_reasons": risk.reasons,
        }
    )


@csrf_exempt
@require_http_methods(["POST"])
def create_task(request):
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
        creation = create_task_from_request(customer_text)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    except Exception:
        return JsonResponse({"error": "Task creation failed."}, status=502)

    task = creation.task
    steps = list(task.steps.values("step_order", "description"))
    messages = list(task.messages.values("channel", "content"))
    return JsonResponse(
        {
            "task_code": task.code,
            "status": task.status,
            "intent": task.intent,
            "entities": task.entities,
            "risk_score": task.risk_score,
            "risk_reasons": task.risk_reasons,
            "assigned_team": task.assigned_team,
            "assignment_reason": creation.assignment_reason,
            "created_at": task.created_at.isoformat(),
            "steps": steps,
            "messages": messages,
            "provider": creation.extraction_provider,
            "fallback_used": creation.fallback_used,
        },
        status=201,
    )


@require_http_methods(["GET"])
def list_tasks(request):
    limit_raw = request.GET.get("limit", "25")
    try:
        limit = max(1, min(int(limit_raw), 100))
    except (TypeError, ValueError):
        return JsonResponse({"error": "limit must be an integer."}, status=400)

    tasks = []
    queryset = (
        Task.objects.all()
        .values(
            "code",
            "intent",
            "status",
            "risk_score",
            "assigned_team",
            "created_at",
        )[:limit]
    )
    for row in queryset:
        tasks.append(
            {
                "task_code": row["code"],
                "intent": row["intent"],
                "status": row["status"],
                "risk_score": row["risk_score"],
                "assigned_team": row["assigned_team"],
                "created_at": row["created_at"].isoformat(),
            }
        )

    return JsonResponse({"count": len(tasks), "tasks": tasks})


ALLOWED_STATUS_VALUES = {
    TaskStatus.PENDING,
    TaskStatus.IN_PROGRESS,
    TaskStatus.COMPLETED,
}


@csrf_exempt
@require_http_methods(["POST"])
def update_task_status(request, task_code: str):
    payload = {}
    if request.content_type and "application/json" in request.content_type:
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON payload."}, status=400)
    else:
        payload = request.POST.dict()

    new_status = str(payload.get("status", "")).strip().upper()
    if new_status not in ALLOWED_STATUS_VALUES:
        return JsonResponse(
            {
                "error": "status must be one of: PENDING, IN_PROGRESS, COMPLETED.",
            },
            status=400,
        )

    task = get_object_or_404(Task, code=task_code)
    with transaction.atomic():
        task_locked = Task.objects.select_for_update().get(pk=task.pk)
        from_status = task_locked.status
        if from_status == new_status:
            return JsonResponse(
                {
                    "task_code": task_locked.code,
                    "status": task_locked.status,
                    "changed": False,
                    "updated_at": task_locked.updated_at.isoformat(),
                }
            )
        task_locked.status = new_status
        task_locked.save(update_fields=["status", "updated_at"])
        TaskStatusHistory.objects.create(
            task=task_locked,
            from_status=from_status,
            to_status=new_status,
        )

    task_locked.refresh_from_db()
    return JsonResponse(
        {
            "task_code": task_locked.code,
            "status": task_locked.status,
            "changed": True,
            "from_status": from_status,
            "updated_at": task_locked.updated_at.isoformat(),
        }
    )
