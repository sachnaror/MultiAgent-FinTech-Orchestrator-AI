from uuid import uuid4
from app.agents.decision import DecisionAgent
from app.agents.extractor import ExtractorAgent
from app.agents.validator import ValidatorAgent
from app.core.config import Settings
from app.core.errors import WorkflowStop
from app.core.models import AgentRun, AgentStatus, Decision, WorkflowState
from app.core.state_gate import require_extraction_complete, require_validation_complete
from app.services.duplicate_store import duplicate_store
from app.services.vendor_repository import VendorRepository


class InvoiceWorkflow:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.extractor = ExtractorAgent()
        self.validator = ValidatorAgent(settings, VendorRepository(), duplicate_store)
        self.decision_agent = DecisionAgent(settings)

    def process(self, source_text: str) -> WorkflowState:
        state = WorkflowState(workflow_id=str(uuid4()), source_text=source_text)
        try:
            state = self.extractor.run(state)
            require_extraction_complete(state)

            state = self.validator.run(state)
            require_validation_complete(state)

            state = self.decision_agent.run(state)

            if state.decision == Decision.auto_approve and state.extracted:
                duplicate_store.mark_seen(state.extracted.vendor or "", state.extracted.invoice_id or "")

        except WorkflowStop as exc:
            state.status = AgentStatus.stopped
            state.decision = Decision.stopped
            state.decision_reason = exc.message
            state.audit.append(
                AgentRun(
                    agent="Workflow Guard",
                    status=AgentStatus.stopped,
                    message=exc.message,
                )
            )
        except Exception as exc:
            state.status = AgentStatus.failed
            state.decision = Decision.stopped
            state.decision_reason = "Unexpected workflow failure."
            state.audit.append(
                AgentRun(
                    agent="Workflow Guard",
                    status=AgentStatus.failed,
                    message=str(exc),
                )
            )
        return state

