import unittest
from app.core.config import Settings
from app.core.models import Decision, AgentStatus
from app.orchestrator import InvoiceWorkflow
from app.services.duplicate_store import duplicate_store


VALID_INVOICE = """Vendor: ABC Ltd
Invoice Number: INV777
Item: Cloud hosting | Qty: 2 | Unit Price: 1500 | Amount: 3000
Item: Support retainer | Qty: 1 | Unit Price: 2000 | Amount: 2000
Total Amount: 5000"""


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        duplicate_store.seen.clear()
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


if __name__ == "__main__":
    unittest.main()

