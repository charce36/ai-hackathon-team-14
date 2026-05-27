import asyncio

from publisher_support.agents.helpers import emit_audit
from publisher_support.cases.store import case_store
from publisher_support.config import settings
from publisher_support.models.schemas import CaseState, CaseStatus, HumanApproval


async def human_gate_node(state: CaseState, video_demo: bool | None = None) -> CaseState:
    state.status = CaseStatus.AWAITING_HUMAN
    patch_desc = state.proposed_patch.description if state.proposed_patch else "N/A"
    await emit_audit(
        state,
        "Human",
        f"Esperando aprobación para patch: {patch_desc}",
        patch_id=state.proposed_patch.patch_id if state.proposed_patch else None,
    )

    use_video_demo = video_demo if video_demo is not None else settings.video_demo

    if use_video_demo:
        await asyncio.sleep(settings.auto_approve_delay_sec)
        approval = HumanApproval(
            approved=True,
            reviewer="auto-demo-reviewer",
            notes="Auto-aprobado en modo VIDEO_DEMO",
        )
    else:
        await emit_audit(state, "Human", "Pausa — aguardando POST /cases/{id}/approve")
        approval = await case_store.wait_for_approval(state.case_id)

    state.human_approval = approval
    if not approval.approved:
        state.status = CaseStatus.ESCALATED
        await emit_audit(state, "Human", "Patch rechazado — caso escalado")
        return state

    await emit_audit(
        state,
        "Human",
        f"Aprobado por {approval.reviewer}",
        notes=approval.notes,
    )
    return state
