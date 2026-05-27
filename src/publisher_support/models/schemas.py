from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from publisher_support.checks.base import CheckResult
from publisher_support.models.events import AuditEvent, ClientMessage


class CaseStatus(str, Enum):
    RECEIVED = "received"
    CLASSIFYING = "classifying"
    INVESTIGATING = "investigating"
    FIX_PROPOSED = "fix_proposed"
    AWAITING_HUMAN = "awaiting_human"
    DEPLOYING = "deploying"
    VERIFYING = "verifying"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


class ClassifiedQuery(BaseModel):
    publisher_id: str
    portal: str = "ZP"
    symptom: str
    category: str
    severity: str = "medium"
    affected_services: list[str] = Field(default_factory=list)
    scenario_id: str


class MonitorSnapshot(BaseModel):
    service: str
    healthy: bool
    anomalies: list[str] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)


class PatchProposal(BaseModel):
    patch_id: str
    description: str
    files: list[dict[str, str]] = Field(default_factory=list)


class RootCauseReport(BaseModel):
    root_cause: str
    confidence: float
    eta_minutes: int
    summary: str


class HumanApproval(BaseModel):
    approved: bool
    reviewer: str = "demo-reviewer"
    notes: str = ""
    cicd_job_id: str | None = None


class VerificationResult(BaseModel):
    resolved: bool
    tests_pass: bool
    monitors_healthy: bool
    check_results: list[CheckResult] = Field(default_factory=list)
    evidence: str


class CaseState(BaseModel):
    case_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    publisher_id: str
    raw_query: str
    scenario_id: str | None = None
    status: CaseStatus = CaseStatus.RECEIVED
    classified: ClassifiedQuery | None = None
    monitor_results: dict[str, MonitorSnapshot] = Field(default_factory=dict)
    root_cause: RootCauseReport | None = None
    proposed_patch: PatchProposal | None = None
    human_approval: HumanApproval | None = None
    verification: VerificationResult | None = None
    patch_applied: bool = False
    client_messages: list[ClientMessage] = Field(default_factory=list)
    timeline: list[AuditEvent] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CreateCaseRequest(BaseModel):
    query: str
    publisher_id: str = "pub-demo-001"
    scenario_id: str | None = None
    video_demo: bool | None = None


class ApproveRequest(BaseModel):
    approved: bool = True
    reviewer: str = "ops-reviewer"
    notes: str = ""


class ScenarioInfo(BaseModel):
    id: str
    label: str
    query: str
    publisher_id: str = "pub-demo-001"
