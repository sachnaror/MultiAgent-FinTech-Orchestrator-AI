from app.core.errors import WorkflowStop
from app.core.models import AgentStatus, WorkflowState


def require_extraction_complete(state: WorkflowState) -> None:
    extracted = state.extracted
    if not extracted:
        raise WorkflowStop("Extractor did not produce an invoice payload.")

    missing = []
    if not extracted.vendor:
        missing.append("vendor")
    if not extracted.invoice_id:
        missing.append("invoice_id")
    if extracted.total_amount is None:
        missing.append("total_amount")
    if not extracted.line_items:
        missing.append("line_items")

    if missing:
        raise WorkflowStop(f"Extraction incomplete: {', '.join(missing)}.")


def require_validation_complete(state: WorkflowState) -> None:
    if not state.validation:
        raise WorkflowStop("Validator did not produce a validation payload.")
    if state.validation.status != AgentStatus.success:
        raise WorkflowStop("Validator status is not SUCCESS.")
    if state.validation.recalculated_total is None:
        raise WorkflowStop("Validator did not independently recalculate total.")

