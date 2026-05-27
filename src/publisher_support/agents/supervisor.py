from publisher_support.agents.helpers import emit_audit, emit_client_message
from publisher_support.models.events import ClientMessage, ClientMessageType
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
        ClientMessage(
            type=ClientMessageType.IDENTIFIED,
            text=(
                f"Identificamos el problema: {state.root_cause.summary}. "
                f"Lo resolveremos en aproximadamente {state.root_cause.eta_minutes} minutos."
            ),
        ),
    )
    await emit_audit(state, "Notify", "Mensaje de progreso enviado al publisher")
    return state


async def notify_resolved_node(state: CaseState) -> CaseState:
    summary = state.root_cause.summary if state.root_cause else "tu consulta"
    await emit_client_message(
        state,
        ClientMessage(
            type=ClientMessageType.RESOLVED,
            text=f"Tu consulta quedó resuelta: {summary}. Ya podés operar con normalidad.",
        ),
    )
    state.status = CaseStatus.RESOLVED
    await emit_audit(state, "Notify", "Caso cerrado — publisher notificado")
    return state
