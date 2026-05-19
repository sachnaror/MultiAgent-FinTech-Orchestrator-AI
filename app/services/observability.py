from collections import deque
from threading import Lock
from app.core.models import ObservabilityResponse, ObservabilityRun, WorkflowState


class ObservabilityStore:
    def __init__(self, max_runs: int = 100):
        self._runs: deque[ObservabilityRun] = deque(maxlen=max_runs)
        self._lock = Lock()

    def record(self, state: WorkflowState) -> ObservabilityRun:
        extracted = state.extracted
        validation = state.validation
        run = ObservabilityRun(
            workflow_id=state.workflow_id,
            status=state.status,
            decision=state.decision,
            decision_reason=state.decision_reason,
            vendor=extracted.vendor if extracted else None,
            invoice_id=extracted.invoice_id if extracted else None,
            total_amount=extracted.total_amount if extracted else None,
            validation_issues=validation.issues if validation else [],
            stateful_checkpoints=state.audit,
        )
        with self._lock:
            self._runs.appendleft(run)
        return run

    def list_runs(self) -> ObservabilityResponse:
        with self._lock:
            runs = list(self._runs)
        return ObservabilityResponse(total_runs=len(runs), runs=runs)

    def get_run(self, workflow_id: str) -> ObservabilityRun | None:
        with self._lock:
            for run in self._runs:
                if run.workflow_id == workflow_id:
                    return run
        return None

    def clear(self) -> None:
        with self._lock:
            self._runs.clear()


observability_store = ObservabilityStore()
