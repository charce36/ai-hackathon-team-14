import json
from pathlib import Path

from publisher_support.config import SCENARIOS_DIR
from publisher_support.models.schemas import ScenarioInfo


def load_scenario(scenario_id: str) -> dict:
    path = SCENARIOS_DIR / f"{scenario_id}.json"
    if not path.exists():
        path = SCENARIOS_DIR / "account_blocked.json"
    return json.loads(path.read_text(encoding="utf-8"))


def list_scenarios() -> list[ScenarioInfo]:
    scenarios: list[ScenarioInfo] = []
    for path in sorted(SCENARIOS_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        scenarios.append(
            ScenarioInfo(
                id=data["id"],
                label=data["label"],
                query=data["query"],
                publisher_id=data.get("publisher_id", "pub-demo-001"),
            )
        )
    return scenarios


SCENARIO_KEYWORDS: dict[str, list[str]] = {
    "account_blocked": ["no puedo publicar", "bloqueada", "bloqueado", "publicar"],
    "sap_sync_failure": ["facturación", "facturacion", "sap", "desactualizada"],
    "mysql_replication_lag": ["datos viejos", "panel", "replicación", "replicacion", "lag"],
    "gcp_service_down": ["503", "error api", "servicio caído", "servicio caido", "cloud run"],
    "rundeck_job_failed": ["proceso no corrió", "proceso no corrio", "rundeck", "job falló", "job fallo"],
}


def detect_scenario(query: str, scenario_id: str | None = None) -> str:
    if scenario_id:
        return scenario_id
    normalized = query.lower()
    for sid, keywords in SCENARIO_KEYWORDS.items():
        if any(kw in normalized for kw in keywords):
            return sid
    return "account_blocked"
