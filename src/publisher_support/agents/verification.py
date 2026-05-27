from publisher_support.adapters.base import MonitorContext
from publisher_support.adapters.mock import get_all_adapters
from publisher_support.agents.helpers import emit_audit
from publisher_support.models.schemas import CaseState, CaseStatus, VerificationResult


async def verification_node(state: CaseState) -> CaseState:
    state.status = CaseStatus.VERIFYING
    if not state.classified or not state.patch_applied:
        return state

    context = MonitorContext(
        scenario_id=state.classified.scenario_id,
        publisher_id=state.publisher_id,
        post_fix=True,
    )

    post_results = {}
    all_healthy = True
    for adapter in get_all_adapters():
        snapshot = adapter.check(context)
        post_results[snapshot.service] = snapshot
        if not snapshot.healthy:
            all_healthy = False

    state.monitor_results = post_results
    tests_pass = state.patch_applied and all_healthy
    resolved = tests_pass and all_healthy

    state.verification = VerificationResult(
        resolved=resolved,
        tests_pass=tests_pass,
        monitors_healthy=all_healthy,
        evidence=f"Re-monitoreo post-fix: {len(post_results)} servicios verificados",
    )

    await emit_audit(
        state,
        "Verify",
        f"tests={'OK' if tests_pass else 'FAIL'}, monitors={'healthy' if all_healthy else 'unhealthy'}",
    )
    return state
