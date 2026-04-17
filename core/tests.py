import json

from django.test import Client, TestCase

from core.models import Task, TaskEntity, TaskStatusHistory
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
        self.assertTrue(TaskStatusHistory.objects.filter(task=task).exists())

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

    def test_list_tasks_api_validates_limit(self):
        response = self.client.get("/api/tasks/?limit=bad")
        self.assertEqual(response.status_code, 400)


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
