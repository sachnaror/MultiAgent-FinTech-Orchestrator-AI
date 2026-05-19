import unittest
from fastapi.testclient import TestClient
from app.core.config import Settings
from app.core.models import Decision, AgentStatus
from app.main import app
from app.orchestrator import InvoiceWorkflow
from app.services.duplicate_store import duplicate_store
from app.services.observability import observability_store


VALID_INVOICE = """Vendor: ABC Ltd
Invoice Number: INV777
Item: Cloud hosting | Qty: 2 | Unit Price: 1500 | Amount: 3000
Item: Support retainer | Qty: 1 | Unit Price: 2000 | Amount: 2000
Total Amount: 5000"""


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        duplicate_store.seen.clear()
        observability_store.clear()
        self.settings = Settings(
            auto_approve_max_amount=10000,
            min_extraction_confidence=0.8,
            strict_fail_fast=True,
        )

    def test_auto_approves_valid_invoice(self):
        state = InvoiceWorkflow(self.settings).process(VALID_INVOICE)

        self.assertEqual(state.status, AgentStatus.success)
        self.assertEqual(state.decision, Decision.auto_approve)
        self.assertTrue(state.validation.valid)

    def test_rejects_total_mismatch(self):
        invoice = VALID_INVOICE.replace("Total Amount: 5000", "Total Amount: 4500")
        state = InvoiceWorkflow(self.settings).process(invoice)

        self.assertEqual(state.decision, Decision.reject)
        self.assertIn("TOTAL_MISMATCH", {issue.code for issue in state.validation.issues})

    def test_stops_on_incomplete_extraction_before_validator_decision(self):
        invoice = "Vendor: ABC Ltd\nInvoice Number: INV778\nTotal Amount: 5000"
        state = InvoiceWorkflow(self.settings).process(invoice)

        self.assertEqual(state.status, AgentStatus.stopped)
        self.assertEqual(state.decision, Decision.stopped)
        self.assertIn("line_items", state.decision_reason)
        self.assertFalse(any(event.agent == "Agent C - Decision" for event in state.audit))

    def test_rejects_duplicate_invoice(self):
        first = InvoiceWorkflow(self.settings).process(VALID_INVOICE)
        second = InvoiceWorkflow(self.settings).process(VALID_INVOICE)

        self.assertEqual(first.decision, Decision.auto_approve)
        self.assertEqual(second.decision, Decision.reject)
        self.assertIn("DUPLICATE_INVOICE", {issue.code for issue in second.validation.issues})

    def test_api_records_audit_trail_for_observability(self):
        client = TestClient(app)
        response = client.post("/api/process-text", json={"text": VALID_INVOICE.replace("INV777", "INV900")})
        self.assertEqual(response.status_code, 200)

        runs = client.get("/api/observability/runs").json()

        self.assertEqual(runs["total_runs"], 1)
        self.assertEqual(runs["runs"][0]["decision"], "AUTO_APPROVE")
        self.assertGreaterEqual(len(runs["runs"][0]["stateful_checkpoints"]), 3)
        self.assertEqual(runs["runs"][0]["validation_issues"], [])

    def test_api_records_validation_issues_for_observability(self):
        client = TestClient(app)
        invalid = VALID_INVOICE.replace("INV777", "INV901").replace("Total Amount: 5000", "Total Amount: 4500")
        response = client.post("/api/process-text", json={"text": invalid})
        self.assertEqual(response.status_code, 200)

        runs = client.get("/api/observability/runs").json()

        issue_codes = {issue["code"] for issue in runs["runs"][0]["validation_issues"]}
        self.assertIn("TOTAL_MISMATCH", issue_codes)
        self.assertGreaterEqual(len(runs["runs"][0]["stateful_checkpoints"]), 3)


if __name__ == "__main__":
    unittest.main()
