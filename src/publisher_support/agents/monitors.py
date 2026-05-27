from publisher_support.adapters.base import MonitorContext
from publisher_support.adapters.mock import get_all_adapters
from publisher_support.agents.helpers import emit_audit
from publisher_support.models.schemas import CaseState, CaseStatus


async def monitors_node(state: CaseState) -> CaseState:
    state.status = CaseStatus.INVESTIGATING
    if not state.classified:
        return state

    context = MonitorContext(
        scenario_id=state.classified.scenario_id,
        publisher_id=state.publisher_id,
        post_fix=False,
    )

    for adapter in get_all_adapters():
        snapshot = adapter.check(context)
        state.monitor_results[snapshot.service] = snapshot
        status = "OK" if snapshot.healthy else "ANOMALY"
        anomalies = ", ".join(snapshot.anomalies) if snapshot.anomalies else "ninguna"
        await emit_audit(
            state,
            adapter.service.upper(),
            f"health={status}, anomalies=[{anomalies}]",
            details=snapshot.details,
        )

    return state
