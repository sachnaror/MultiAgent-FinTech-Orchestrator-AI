from app.core.config import Settings
from app.core.models import AgentRun, AgentStatus, Decision, WorkflowState


class DecisionAgent:
    name = "Agent C - Decision"

    def __init__(self, settings: Settings):
        self.settings = settings

    def run(self, state: WorkflowState) -> WorkflowState:
        invoice = state.extracted
        validation = state.validation

        if not invoice or not validation:
            return self._decide(state, Decision.stopped, "Required upstream state is missing.")

        critical = [issue for issue in validation.issues if issue.severity == "critical"]
        major = [issue for issue in validation.issues if issue.severity == "major"]

        if critical:
            return self._decide(state, Decision.reject, f"Rejected due to critical issue: {critical[0].code}.")

        if major:
            return self._decide(state, Decision.human_review, f"Human review required due to {major[0].code}.")

        if invoice.total_amount is None:
            return self._decide(state, Decision.stopped, "Total amount is missing.")

        if invoice.total_amount > self.settings.auto_approve_max_amount:
            return self._decide(state, Decision.human_review, "Amount exceeds auto-approval threshold.")

        return self._decide(state, Decision.auto_approve, "Invoice passed all validation gates.")

    def _decide(self, state: WorkflowState, decision: Decision, reason: str) -> WorkflowState:
        state.decision = decision
        state.decision_reason = reason
        state.status = AgentStatus.success if decision != Decision.stopped else AgentStatus.stopped
        state.audit.append(
            AgentRun(
                agent=self.name,
                status=state.status,
                message=reason,
                data={"decision": decision},
            )
        )
        return state

