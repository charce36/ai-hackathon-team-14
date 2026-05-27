import asyncio
import json
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from sse_starlette.sse import EventSourceResponse

from publisher_support.adapters.scenarios import list_scenarios
from publisher_support.cases.store import case_store
from publisher_support.config import ROOT_DIR, settings
from publisher_support.events.broadcaster import broadcaster
from publisher_support.graph.workflow import run_case
from publisher_support.models.events import ClientMessage, ClientMessageType
from publisher_support.models.schemas import (
    ApproveRequest,
    CaseState,
    CreateCaseRequest,
    HumanApproval,
)

app = FastAPI(title="Publisher Support Agent", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DEMO_UI_DIST = ROOT_DIR / "demo-ui" / "dist"


async def _execute_case(case: CaseState, video_demo: bool | None) -> None:
    case_store.register_approval_wait(case.case_id)
    try:
        updated = await run_case(case, video_demo=video_demo)
        await case_store.save(updated)
    except Exception as exc:
        from publisher_support.models.events import AuditEvent

        await broadcaster.emit_audit(
            case.case_id,
            AuditEvent(agent="System", message=f"Error en workflow: {exc}"),
        )


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "video_demo": settings.video_demo,
        "claude_model": settings.claude_model,
        "llm_configured": bool(settings.anthropic_api_key),
    }


@app.get("/scenarios")
async def get_scenarios():
    return list_scenarios()


@app.post("/cases")
async def create_case(body: CreateCaseRequest, background_tasks: BackgroundTasks):
    case = CaseState(
        publisher_id=body.publisher_id,
        raw_query=body.query,
        scenario_id=body.scenario_id,
    )
    user_msg = ClientMessage(
        type=ClientMessageType.USER,
        text=body.query,
    )
    case.client_messages.append(user_msg)
    await case_store.save(case)
    await broadcaster.emit_client_message(case.case_id, user_msg)

    video_demo = body.video_demo if body.video_demo is not None else settings.video_demo
    background_tasks.add_task(_execute_case, case, video_demo)
    return {"case_id": case.case_id, "status": case.status}


@app.get("/cases/{case_id}")
async def get_case(case_id: str):
    case = await case_store.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@app.post("/cases/{case_id}/approve")
async def approve_case(case_id: str, body: ApproveRequest):
    case = await case_store.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    approval = HumanApproval(
        approved=body.approved,
        reviewer=body.reviewer,
        notes=body.notes,
    )
    ok = await case_store.approve(case_id, approval)
    if not ok:
        raise HTTPException(status_code=404, detail="Case not found")
    return {"case_id": case_id, "approved": body.approved}


@app.get("/cases/{case_id}/events")
async def case_events(case_id: str):
    case = await case_store.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    async def event_generator():
        for msg in case.client_messages:
            yield {
                "event": "client_message",
                "data": json.dumps(msg.model_dump(mode="json")),
            }
        for event in case.timeline:
            yield {
                "event": "audit",
                "data": json.dumps(event.model_dump(mode="json")),
            }

        async for payload in broadcaster.subscribe(case_id):
            yield {
                "event": payload.get("event", "message"),
                "data": json.dumps(payload.get("data", payload)),
            }

    return EventSourceResponse(event_generator())


@app.get("/demo")
async def demo_page():
    index = DEMO_UI_DIST / "index.html"
    if index.exists():
        return FileResponse(index)
    return {
        "message": "Demo UI not built. Run: cd demo-ui && npm install && npm run build",
        "api": "/docs",
    }


@app.get("/demo/assets/{asset_path:path}")
async def demo_assets(asset_path: str):
    asset = (DEMO_UI_DIST / "assets" / asset_path).resolve()
    assets_root = (DEMO_UI_DIST / "assets").resolve()
    if not str(asset).startswith(str(assets_root)) or not asset.is_file():
        raise HTTPException(status_code=404, detail="Asset not found")
    return FileResponse(asset)


def main():
    import uvicorn

    uvicorn.run("publisher_support.main:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
