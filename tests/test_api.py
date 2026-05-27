import pytest


@pytest.mark.asyncio
async def test_health(client):
    res = await client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_list_scenarios(client):
    res = await client.get("/scenarios")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 5
    ids = {s["id"] for s in data}
    assert "account_blocked" in ids


@pytest.mark.asyncio
async def test_happy_path_resolves(client):
    import asyncio

    res = await client.post(
        "/cases",
        json={
            "query": "No puedo publicar mis avisos",
            "publisher_id": "pub-demo-001",
            "scenario_id": "account_blocked",
            "video_demo": True,
        },
    )
    assert res.status_code == 200
    case_id = res.json()["case_id"]

    for _ in range(80):
        await asyncio.sleep(0.15)
        case_res = await client.get(f"/cases/{case_id}")
        case = case_res.json()
        if case["status"] == "resolved":
            break

    assert case["status"] == "resolved"
    assert case["verification"]["resolved"] is True

    msg_types = [m["type"] for m in case["client_messages"]]
    assert "user" in msg_types
    assert "checking" in msg_types
    assert "identified" in msg_types
    assert "resolved" in msg_types


@pytest.mark.asyncio
async def test_messaging_sequence_order(client):
    import asyncio

    res = await client.post(
        "/cases",
        json={
            "query": "Facturación desactualizada SAP",
            "publisher_id": "pub-demo-002",
            "scenario_id": "sap_sync_failure",
            "video_demo": True,
        },
    )
    case_id = res.json()["case_id"]

    for _ in range(80):
        await asyncio.sleep(0.15)
        case = (await client.get(f"/cases/{case_id}")).json()
        if case["status"] == "resolved":
            break

    bot_msgs = [m for m in case["client_messages"] if m["type"] != "user"]
    types = [m["type"] for m in bot_msgs]
    assert types.index("checking") < types.index("identified")
    assert types.index("identified") < types.index("resolved")


@pytest.mark.asyncio
async def test_timeline_has_agents(client):
    import asyncio

    res = await client.post(
        "/cases",
        json={
            "query": "Error 503 API",
            "scenario_id": "gcp_service_down",
            "video_demo": True,
        },
    )
    case_id = res.json()["case_id"]

    for _ in range(80):
        await asyncio.sleep(0.15)
        case = (await client.get(f"/cases/{case_id}")).json()
        if case["status"] == "resolved":
            break

    agents = {e["agent"] for e in case["timeline"]}
    assert "Supervisor" in agents
    assert "Classifier" in agents
    assert "RCA" in agents
    assert "Verify" in agents
