from typing import Literal

from pydantic import BaseModel, Field

SCENARIO_IDS = Literal[
    "account_blocked",
    "sap_sync_failure",
    "mysql_replication_lag",
    "gcp_service_down",
    "rundeck_job_failed",
]

SEVERITY = Literal["low", "medium", "high", "critical"]


class ClassifierLLMOutput(BaseModel):
    scenario_id: SCENARIO_IDS
    category: str
    severity: SEVERITY
    affected_services: list[str] = Field(min_length=1)
    symptom_summary: str
    reasoning: str


class PatchFileLLM(BaseModel):
    path: str
    action: str
    content: str = ""


class RCALLMOutput(BaseModel):
    root_cause: str
    summary: str
    confidence: float = Field(ge=0.0, le=1.0)
    eta_minutes: int = Field(ge=1, le=120)
    patch_id: str
    description: str
    files: list[PatchFileLLM] = Field(min_length=1)
    reasoning: str
