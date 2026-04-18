import json

from django.test import Client, TestCase

from core.models import MessageChannel, Task, TaskEntity, TaskMessage, TaskStatusHistory, TaskStep
from core.services.employee_assigner import assign_employee_team
from core.services.intent_extractor import extract_intent_and_entities
from core.services.risk_scorer import assess_risk


class IntentExtractorTests(TestCase):
    def test_send_money_heuristic(self):
        result = extract_intent_and_entities(
            "I need to send KES 15,000 to my mother in Kisumu urgently."
        )
        self.assertEqual(result.intent, "send_money")
        self.assertIn("amount", result.entities)
        self.assertTrue(result.fallback_used)

    def test_verify_document_heuristic(self):
        result = extract_intent_and_entities(
            "Please verify my land title deed for the plot in Karen."
        )
        self.assertEqual(result.intent, "verify_document")


class IntentExtractionApiTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_extract_intent_api_success(self):
        response = self.client.post(
            "/api/extract-intent/",
            data=json.dumps({"request_text": "Can someone clean my apartment in Westlands?"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["intent"], "hire_service")
        self.assertIn("entities", payload)
        self.assertIn("risk_score", payload)
        self.assertIn("risk_reasons", payload)
        self.assertIsInstance(payload["risk_reasons"], list)

    def test_extract_intent_api_validates_request_text(self):
        response = self.client.post(
            "/api/extract-intent/",
            data=json.dumps({"request_text": ""}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_create_task_api_persists_task(self):
        response = self.client.post(
            "/api/tasks/create/",
            data=json.dumps(
                {
                    "request_text": "I need to send KES 15000 to my mother in Kisumu urgently.",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertIn("task_code", payload)

        task = Task.objects.get(code=payload["task_code"])
        self.assertEqual(task.intent, "send_money")
        self.assertEqual(task.status, "PENDING")
        self.assertTrue(TaskEntity.objects.filter(task=task).exists())
        self.assertTrue(TaskStep.objects.filter(task=task).exists())
        self.assertTrue(TaskMessage.objects.filter(task=task).exists())
        self.assertTrue(TaskStatusHistory.objects.filter(task=task).exists())
        self.assertIn("steps", payload)
        self.assertIn("messages", payload)
        self.assertEqual(task.assigned_team, "FINANCE")
        self.assertIn("assignment_reason", payload)
        self.assertEqual(task.assignment_reason, payload["assignment_reason"])
        self.assertFalse(payload["llm_fulfillment_used"])
        self.assertFalse(payload["llm_assignment_used"])

    def test_create_task_api_generates_unique_codes(self):
        req_body = json.dumps({"request_text": "Please verify my land title deed for Karen."})
        first = self.client.post("/api/tasks/create/", data=req_body, content_type="application/json")
        second = self.client.post("/api/tasks/create/", data=req_body, content_type="application/json")
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertNotEqual(first.json()["task_code"], second.json()["task_code"])

    def test_list_tasks_api_returns_created_tasks(self):
        self.client.post(
            "/api/tasks/create/",
            data=json.dumps({"request_text": "Can someone clean my apartment in Westlands?"}),
            content_type="application/json",
        )
        response = self.client.get("/api/tasks/?limit=10")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("count", payload)
        self.assertIn("tasks", payload)
        self.assertGreaterEqual(payload["count"], 1)
        self.assertIn("task_code", payload["tasks"][0])
        self.assertIn("total", payload)
        self.assertIn("offset", payload)
        self.assertIn("has_more", payload)
        self.assertIn("risk_reasons", payload["tasks"][0])
        self.assertIsInstance(payload["tasks"][0]["risk_reasons"], list)

    def test_list_tasks_api_validates_limit(self):
        response = self.client.get("/api/tasks/?limit=bad")
        self.assertEqual(response.status_code, 400)

    def test_list_tasks_api_supports_offset(self):
        for i in range(3):
            self.client.post(
                "/api/tasks/create/",
                data=json.dumps(
                    {"request_text": f"Please verify land title deed number {i} for Karen."}
                ),
                content_type="application/json",
            )
        first = self.client.get("/api/tasks/?limit=2&offset=0")
        self.assertEqual(first.status_code, 200)
        second = self.client.get("/api/tasks/?limit=2&offset=2")
        self.assertEqual(second.status_code, 200)
        codes_a = {row["task_code"] for row in first.json()["tasks"]}
        codes_b = {row["task_code"] for row in second.json()["tasks"]}
        self.assertTrue(codes_a.isdisjoint(codes_b))

    def test_task_detail_api_returns_full_task(self):
        create = self.client.post(
            "/api/tasks/create/",
            data=json.dumps({"request_text": "Please verify my land title deed for Karen."}),
            content_type="application/json",
        )
        code = create.json()["task_code"]
        response = self.client.get(f"/api/tasks/{code}/")
        self.assertEqual(response.status_code, 200)
        detail = response.json()
        self.assertEqual(detail["task_code"], code)
        self.assertIn("customer_request_text", detail)
        self.assertIn("assignment_reason", detail)
        self.assertGreaterEqual(len(detail["steps"]), 1)
        self.assertEqual(len(detail["messages"]), 3)

    def test_task_detail_api_404_for_unknown_code(self):
        response = self.client.get("/api/tasks/VNH-NOT-REAL-CODE0/")
        self.assertEqual(response.status_code, 404)

    def test_update_task_status_persists_and_records_history(self):
        create = self.client.post(
            "/api/tasks/create/",
            data=json.dumps({"request_text": "Can someone clean my apartment in Westlands?"}),
            content_type="application/json",
        )
        self.assertEqual(create.status_code, 201)
        code = create.json()["task_code"]
        task = Task.objects.get(code=code)
        before_history = TaskStatusHistory.objects.filter(task=task).count()

        response = self.client.post(
            f"/api/tasks/{code}/status/",
            data=json.dumps({"status": "IN_PROGRESS"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["changed"])
        task.refresh_from_db()
        self.assertEqual(task.status, "IN_PROGRESS")
        self.assertGreater(TaskStatusHistory.objects.filter(task=task).count(), before_history)

    def test_update_task_status_rejects_invalid_value(self):
        create = self.client.post(
            "/api/tasks/create/",
            data=json.dumps({"request_text": "Please verify my land title deed for Karen."}),
            content_type="application/json",
        )
        code = create.json()["task_code"]
        response = self.client.post(
            f"/api/tasks/{code}/status/",
            data=json.dumps({"status": "INVALID"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_update_task_status_returns_404_for_unknown_code(self):
        response = self.client.post(
            "/api/tasks/VNH-UNKNOWN-CODE99/status/",
            data=json.dumps({"status": "COMPLETED"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)

    def test_create_task_api_persists_three_message_formats(self):
        response = self.client.post(
            "/api/tasks/create/",
            data=json.dumps({"request_text": "Please verify my land title deed for Karen."}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        task = Task.objects.get(code=response.json()["task_code"])

        channels = set(TaskMessage.objects.filter(task=task).values_list("channel", flat=True))
        self.assertEqual(
            channels,
            {MessageChannel.WHATSAPP, MessageChannel.EMAIL, MessageChannel.SMS},
        )

        sms_message = TaskMessage.objects.get(task=task, channel=MessageChannel.SMS)
        self.assertLessEqual(len(sms_message.content), 160)
        self.assertEqual(task.assigned_team, "LEGAL")


class RiskScorerTests(TestCase):
    def test_high_risk_money_transfer_scenario(self):
        result = assess_risk(
            "send_money",
            {
                "amount": "120000",
                "urgency": "high",
                "recipient_verified": False,
            },
        )
        self.assertGreaterEqual(result.score, 75)
        self.assertLessEqual(result.score, 100)

    def test_lower_risk_returning_customer_scenario(self):
        result = assess_risk(
            "check_status",
            {
                "returning_customer": True,
                "clean_history": True,
                "urgency": "normal",
            },
        )
        self.assertGreaterEqual(result.score, 0)
        self.assertLessEqual(result.score, 30)


class EmployeeAssignerTests(TestCase):
    def test_assign_send_money_to_finance(self):
        result = assign_employee_team("send_money", {"amount": "20000"})
        self.assertEqual(result.team, "FINANCE")

    def test_assign_verify_document_to_legal(self):
        result = assign_employee_team("verify_document", {"document_type": "land title"})
        self.assertEqual(result.team, "LEGAL")

    def test_assign_hire_service_to_operations(self):
        result = assign_employee_team("hire_service", {"service_type": "cleaning"})
        self.assertEqual(result.team, "OPERATIONS")
