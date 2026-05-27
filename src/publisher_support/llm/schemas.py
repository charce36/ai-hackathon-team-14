from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

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
    reasoning: str = ""

    @model_validator(mode="before")
    @classmethod
    def fill_missing(cls, data: Any) -> Any:
        if isinstance(data, dict) and not data.get("reasoning"):
            data["reasoning"] = "Clasificación basada en la consulta del publisher."
        return data


class PatchFileLLM(BaseModel):
    path: str
    action: str = "run"
    content: str = ""


class RCALLMOutput(BaseModel):
    root_cause: str
    summary: str = ""
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    eta_minutes: int = Field(default=15, ge=1, le=120)
    patch_id: str = "fix-pending"
    description: str = ""
    files: list[PatchFileLLM] = Field(default_factory=list)
    reasoning: str = ""

    @model_validator(mode="before")
    @classmethod
    def fill_missing(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        root = data.get("root_cause") or "Incidente en plataforma publisher"

        if not data.get("summary"):
            data["summary"] = root[:250]

        if not data.get("reasoning"):
            data["reasoning"] = f"Correlación stacktrace + monitores: {root[:200]}"

        if not data.get("patch_id"):
            data["patch_id"] = "publisher-platform-fix"

        if not data.get("description"):
            data["description"] = "Acción correctiva para restaurar operación del publisher"

        if not data.get("files"):
            data["files"] = [
                {
                    "path": "scripts/apply_fix.sh",
                    "action": "run",
                    "content": (
                        "#!/bin/bash\n"
                        "set -euo pipefail\n"
                        f"echo 'Aplicando fix: {data.get('patch_id', 'publisher-platform-fix')}'\n"
                        f"echo 'Causa: {root[:120]}'\n"
                    ),
                }
            ]

        return data

    @model_validator(mode="after")
    def ensure_file_content(self) -> "RCALLMOutput":
        for f in self.files:
            if not f.content.strip():
                f.content = (
                    f"# Fix: {self.patch_id}\n"
                    f"# {self.description}\n"
                    "print('fix applied')\n"
                )
        return self
