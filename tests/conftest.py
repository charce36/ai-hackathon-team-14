import pytest

from publisher_support.config import settings
from publisher_support.llm.schemas import ClassifierLLMOutput, PatchFileLLM, RCALLMOutput


MOCK_CLASSIFIER_OUTPUTS = {
    "account_blocked": ClassifierLLMOutput(
        scenario_id="account_blocked",
        category="account",
        severity="high",
        affected_services=["account"],
        symptom_summary="No puede publicar avisos",
        reasoning="Consulta indica bloqueo al publicar; coincide con account_blocked.",
    ),
    "sap_sync_failure": ClassifierLLMOutput(
        scenario_id="sap_sync_failure",
        category="billing",
        severity="medium",
        affected_services=["sap"],
        symptom_summary="Facturación desactualizada",
        reasoning="Menciona facturación SAP desactualizada.",
    ),
    "gcp_service_down": ClassifierLLMOutput(
        scenario_id="gcp_service_down",
        category="infrastructure",
        severity="critical",
        affected_services=["gcp"],
        symptom_summary="Error 503 en API",
        reasoning="Error 503 apunta a servicio Cloud Run caído.",
    ),
}


def _mock_rca_output(scenario_id: str) -> RCALLMOutput:
    patches = {
        "account_blocked": (
            "unblock-account",
            "Desbloquear cuenta tras regularizar deuda SAP",
            '#!/usr/bin/env python3\nprint("Unblocking publisher account...")\n',
        ),
        "sap_sync_failure": (
            "trigger-sap-sync",
            "Re-ejecutar sincronización SAP",
            "#!/bin/bash\nrundeck run --job sap-sync-job\n",
        ),
        "gcp_service_down": (
            "rollback-gcp-service",
            "Rollback Cloud Run a revisión estable",
            "apiVersion: serving.knative.dev/v1\nkind: Service\n",
        ),
    }
    patch_id, desc, content = patches.get(
        scenario_id,
        ("generic-fix", "Fix genérico", "# fix\n"),
    )
    return RCALLMOutput(
        root_cause=f"Causa raíz mock para {scenario_id}",
        summary=f"Problema identificado en {scenario_id}",
        confidence=0.91,
        eta_minutes=15,
        patch_id=patch_id,
        description=desc,
        files=[PatchFileLLM(path="scripts/fix.py", action="run", content=content)],
        reasoning=f"RCA mock basado en stacktrace de {scenario_id}",
    )


@pytest.fixture(autouse=True)
def fast_demo(monkeypatch):
    monkeypatch.setattr(settings, "demo_step_delay_ms", 50)
    monkeypatch.setattr(settings, "auto_approve_delay_sec", 0.1)
    monkeypatch.setattr(settings, "video_demo", True)
    monkeypatch.setattr(settings, "anthropic_api_key", "test-key-mock")


@pytest.fixture(autouse=True)
def mock_claude(request, monkeypatch):
    if request.node.get_closest_marker("no_llm_mock") or request.node.name == "test_missing_api_key_escalates":
        return

    async def fake_invoke_structured(*, system, user, output_model, tool_name, **kwargs):
        if output_model.__name__ == "ClassifierLLMOutput":
            for sid, output in MOCK_CLASSIFIER_OUTPUTS.items():
                if sid in user or sid.replace("_", " ") in user.lower():
                    return output
            if "scenario_id sugerido = account_blocked" in user:
                return MOCK_CLASSIFIER_OUTPUTS["account_blocked"]
            if "scenario_id sugerido = sap_sync_failure" in user:
                return MOCK_CLASSIFIER_OUTPUTS["sap_sync_failure"]
            if "scenario_id sugerido = gcp_service_down" in user:
                return MOCK_CLASSIFIER_OUTPUTS["gcp_service_down"]
            return MOCK_CLASSIFIER_OUTPUTS["account_blocked"]

        if output_model.__name__ == "RCALLMOutput":
            for sid in MOCK_CLASSIFIER_OUTPUTS:
                if sid in user:
                    return _mock_rca_output(sid)
            return _mock_rca_output("account_blocked")

        raise ValueError(f"Unexpected output_model: {output_model}")

    monkeypatch.setattr(
        "publisher_support.llm.client.invoke_structured",
        fake_invoke_structured,
    )
    monkeypatch.setattr(
        "publisher_support.agents.classifier.invoke_structured",
        fake_invoke_structured,
    )
    monkeypatch.setattr(
        "publisher_support.agents.root_cause.invoke_structured",
        fake_invoke_structured,
    )


@pytest.fixture
async def client():
    from httpx import ASGITransport, AsyncClient

    from publisher_support.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
