import asyncio

import pytest


@pytest.fixture
async def client_no_key(monkeypatch):
    from httpx import ASGITransport, AsyncClient

    from publisher_support.config import settings
    from publisher_support.llm.errors import LLMConfigurationError
    from publisher_support.main import app

    monkeypatch.setattr(settings, "anthropic_api_key", "")

    async def fail_invoke(**kwargs):
        raise LLMConfigurationError(
            "ANTHROPIC_API_KEY no configurada. Agregala en el archivo .env"
        )

    monkeypatch.setattr("publisher_support.agents.classifier.invoke_structured", fail_invoke)
    monkeypatch.setattr("publisher_support.agents.root_cause.invoke_structured", fail_invoke)
    monkeypatch.setattr("publisher_support.llm.client.invoke_structured", fail_invoke)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.no_llm_mock
@pytest.mark.asyncio
async def test_missing_api_key_escalates(client_no_key):
    res = await client_no_key.post(
        "/cases",
        json={
            "query": "No puedo publicar",
            "publisher_id": "pub-demo-001",
            "scenario_id": "account_blocked",
            "video_demo": True,
        },
    )
    case_id = res.json()["case_id"]

    case = None
    for _ in range(40):
        await asyncio.sleep(0.1)
        case = (await client_no_key.get(f"/cases/{case_id}")).json()
        if case["status"] == "escalated":
            break

    assert case is not None
    assert case["status"] == "escalated"
    system_events = [e for e in case["timeline"] if e["agent"] == "System"]
    assert len(system_events) >= 1
    assert "ANTHROPIC_API_KEY" in system_events[0]["message"]


@pytest.mark.asyncio
async def test_rca_patch_has_code_content(client):
    res = await client.post(
        "/cases",
        json={
            "query": "No puedo publicar",
            "scenario_id": "account_blocked",
            "video_demo": True,
        },
    )
    case_id = res.json()["case_id"]

    case = None
    for _ in range(80):
        await asyncio.sleep(0.15)
        case = (await client.get(f"/cases/{case_id}")).json()
        if case.get("proposed_patch"):
            break

    assert case is not None
    assert case.get("proposed_patch") is not None
    assert case["proposed_patch"]["files"][0]["content"] != ""
