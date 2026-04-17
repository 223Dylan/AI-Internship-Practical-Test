import json

from django.test import Client, TestCase

from core.services.intent_extractor import extract_intent_and_entities


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

    def test_extract_intent_api_validates_request_text(self):
        response = self.client.post(
            "/api/extract-intent/",
            data=json.dumps({"request_text": ""}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
