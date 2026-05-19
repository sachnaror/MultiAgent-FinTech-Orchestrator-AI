from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    pending = "PENDING"
    success = "SUCCESS"
    failed = "FAILED"
    stopped = "STOPPED"


class Decision(str, Enum):
    auto_approve = "AUTO_APPROVE"
    human_review = "HUMAN_REVIEW"
    reject = "REJECT"
    stopped = "STOPPED"


class LineItem(BaseModel):
    description: str
    quantity: float = Field(default=1, ge=0)
    unit_price: float = Field(default=0, ge=0)
    amount: float = Field(ge=0)
    source_ref: str | None = None


class ExtractedInvoice(BaseModel):
    vendor: str | None = None
    invoice_id: str | None = None
    total_amount: float | None = Field(default=None, ge=0)
    line_items: list[LineItem] = Field(default_factory=list)
    confidence: float = Field(default=0, ge=0, le=1)
    source_refs: dict[str, str] = Field(default_factory=dict)


class ValidationIssue(BaseModel):
    code: str
    severity: str
    message: str
    field: str | None = None


class ValidationResult(BaseModel):
    valid: bool
    status: AgentStatus = AgentStatus.success
    issues: list[ValidationIssue] = Field(default_factory=list)
    verified_fields: dict[str, bool] = Field(default_factory=dict)
    recalculated_total: float | None = None
    confidence_adjustment: float = 0


class AgentRun(BaseModel):
    agent: str
    status: AgentStatus
    message: str
    data: dict[str, Any] = Field(default_factory=dict)


class WorkflowState(BaseModel):
    workflow_id: str
    source_text: str
    extracted: ExtractedInvoice | None = None
    validation: ValidationResult | None = None
    decision: Decision | None = None
    decision_reason: str | None = None
    status: AgentStatus = AgentStatus.pending
    audit: list[AgentRun] = Field(default_factory=list)


class TextInvoiceRequest(BaseModel):
    text: str = Field(min_length=1)


class ProcessResponse(BaseModel):
    workflow_id: str
    status: AgentStatus
    decision: Decision | None
    decision_reason: str | None
    extracted: ExtractedInvoice | None
    validation: ValidationResult | None
    audit: list[AgentRun]

