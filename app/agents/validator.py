import math
from app.core.config import Settings
from app.core.models import AgentRun, AgentStatus, ValidationIssue, ValidationResult, WorkflowState
from app.services.duplicate_store import DuplicateStore
from app.services.vendor_repository import VendorRepository


class ValidatorAgent:
    name = "Agent B - Validator"

    def __init__(
        self,
        settings: Settings,
        vendor_repository: VendorRepository,
        duplicate_store: DuplicateStore,
    ):
        self.settings = settings
        self.vendor_repository = vendor_repository
        self.duplicate_store = duplicate_store

    def run(self, state: WorkflowState) -> WorkflowState:
        invoice = state.extracted
        issues: list[ValidationIssue] = []
        verified_fields = {
            "vendor_source_grounded": False,
            "invoice_id_source_grounded": False,
            "total_source_grounded": False,
            "vendor_exists": False,
            "duplicate_invoice": False,
        }

        if invoice is None:
            issues.append(self._issue("NO_EXTRACTION", "critical", "No extraction payload to validate."))
            state.validation = ValidationResult(valid=False, issues=issues)
            return self._audit(state)

        vendor = self.vendor_repository.find_by_name(invoice.vendor)
        verified_fields["vendor_exists"] = bool(vendor and vendor.get("status") == "active")
        verified_fields["vendor_source_grounded"] = self._source_contains(state.source_text, invoice.vendor)
        verified_fields["invoice_id_source_grounded"] = self._source_contains(state.source_text, invoice.invoice_id)
        verified_fields["total_source_grounded"] = (
            invoice.total_amount is not None
            and str(int(invoice.total_amount)) in state.source_text.replace(",", "")
        )

        if not verified_fields["vendor_exists"]:
            issues.append(self._issue("VENDOR_NOT_APPROVED", "critical", "Vendor is missing, blocked, or unknown.", "vendor"))
        if not verified_fields["vendor_source_grounded"]:
            issues.append(self._issue("VENDOR_NOT_IN_SOURCE", "critical", "Vendor is not grounded in source text.", "vendor"))
        if not verified_fields["invoice_id_source_grounded"]:
            issues.append(self._issue("INVOICE_ID_NOT_IN_SOURCE", "critical", "Invoice ID is not grounded in source text.", "invoice_id"))
        if not verified_fields["total_source_grounded"]:
            issues.append(self._issue("TOTAL_NOT_IN_SOURCE", "major", "Total amount is not clearly grounded in source text.", "total_amount"))

        recalculated_total = round(sum(item.amount for item in invoice.line_items), 2)
        if invoice.total_amount is None or not math.isclose(recalculated_total, invoice.total_amount, abs_tol=0.01):
            issues.append(
                self._issue(
                    "TOTAL_MISMATCH",
                    "critical",
                    f"Invoice total {invoice.total_amount} does not match line item total {recalculated_total}.",
                    "total_amount",
                )
            )

        for item in invoice.line_items:
            expected = round(item.quantity * item.unit_price, 2)
            if not math.isclose(expected, item.amount, abs_tol=0.01):
                issues.append(
                    self._issue(
                        "LINE_ITEM_MISMATCH",
                        "major",
                        f"Line item '{item.description}' amount should be {expected}.",
                        "line_items",
                    )
                )

        if invoice.vendor and invoice.invoice_id and self.duplicate_store.exists(invoice.vendor, invoice.invoice_id):
            verified_fields["duplicate_invoice"] = True
            issues.append(self._issue("DUPLICATE_INVOICE", "critical", "Duplicate vendor and invoice ID detected.", "invoice_id"))

        if invoice.confidence < self.settings.min_extraction_confidence:
            issues.append(
                self._issue(
                    "LOW_CONFIDENCE",
                    "major",
                    f"Extraction confidence {invoice.confidence} is below threshold {self.settings.min_extraction_confidence}.",
                )
            )

        has_critical = any(issue.severity == "critical" for issue in issues)
        state.validation = ValidationResult(
            valid=not issues,
            issues=issues,
            verified_fields=verified_fields,
            recalculated_total=recalculated_total,
            confidence_adjustment=-0.1 if has_critical else 0,
        )
        return self._audit(state)

    def _source_contains(self, source: str, value: str | None) -> bool:
        return bool(value and value.casefold() in source.casefold())

    def _issue(self, code: str, severity: str, message: str, field: str | None = None) -> ValidationIssue:
        return ValidationIssue(code=code, severity=severity, message=message, field=field)

    def _audit(self, state: WorkflowState) -> WorkflowState:
        status = AgentStatus.success if state.validation and state.validation.status == AgentStatus.success else AgentStatus.failed
        state.audit.append(
            AgentRun(
                agent=self.name,
                status=status,
                message="Validated extraction against source text, totals, vendor registry, confidence, and duplicate policy.",
                data=state.validation.model_dump() if state.validation else {},
            )
        )
        return state

