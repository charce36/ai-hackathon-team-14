from publisher_support.agents.helpers import emit_audit, emit_client_message
from publisher_support.agents.messaging import (
    client_message_identified,
    client_message_resolved,
)
from publisher_support.models.schemas import CaseState, CaseStatus


async def supervisor_node(state: CaseState) -> CaseState:
    state.status = CaseStatus.RECEIVED
    await emit_audit(
        state,
        "Supervisor",
        f"Caso #{state.case_id} recibido de publisher {state.publisher_id}",
        query=state.raw_query[:80],
    )
    return state


async def notify_identified_node(state: CaseState) -> CaseState:
    if not state.root_cause:
        return state
    await emit_client_message(
        state,
        client_message_identified(
            state.root_cause.summary,
            state.root_cause.eta_minutes,
        ),
    )
    await emit_audit(state, "Notify", "Mensaje de progreso enviado al publisher")
    return state


async def notify_resolved_node(state: CaseState) -> CaseState:
    summary = (
        state.root_cause.summary
        if state.root_cause
        else "Tu consulta fue atendida correctamente."
    )
    await emit_client_message(state, client_message_resolved(summary))
    state.status = CaseStatus.RESOLVED
    await emit_audit(state, "Notify", "Caso cerrado — publisher notificado")
    return state
