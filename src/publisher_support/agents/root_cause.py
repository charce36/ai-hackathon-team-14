from publisher_support.adapters.scenarios import load_scenario
from publisher_support.agents.helpers import emit_audit
from publisher_support.models.schemas import (
    CaseState,
    CaseStatus,
    PatchProposal,
    RootCauseReport,
)


async def root_cause_node(state: CaseState) -> CaseState:
    state.status = CaseStatus.FIX_PROPOSED
    if not state.classified:
        return state

    scenario = load_scenario(state.classified.scenario_id)
    rc_data = scenario["root_cause"]
    patch_data = scenario["patch"]

    unhealthy = [
        svc for svc, snap in state.monitor_results.items() if not snap.healthy
    ]
    root_cause_text = rc_data["summary"]
    if unhealthy:
        root_cause_text += f" (servicios afectados: {', '.join(unhealthy)})"

    state.root_cause = RootCauseReport(
        root_cause=root_cause_text,
        confidence=0.92 if unhealthy else 0.75,
        eta_minutes=rc_data["eta_minutes"],
        summary=rc_data["summary"],
    )
    state.proposed_patch = PatchProposal(
        patch_id=patch_data["patch_id"],
        description=patch_data["description"],
        files=patch_data.get("files", []),
    )

    await emit_audit(
        state,
        "RCA",
        f"root_cause={state.root_cause.summary}, confidence={state.root_cause.confidence:.2f}",
    )
    await emit_audit(
        state,
        "Fix",
        f"patch_id={state.proposed_patch.patch_id}: {state.proposed_patch.description}",
        files=state.proposed_patch.files,
    )
    return state
