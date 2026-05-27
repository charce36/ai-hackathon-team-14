from publisher_support.agents.helpers import emit_audit, emit_client_message
from publisher_support.llm.errors import LLMConfigurationError, LLMInvocationError
from publisher_support.models.events import ClientMessage, ClientMessageType
from publisher_support.models.schemas import CaseState, CaseStatus


async def escalate_case(state: CaseState, reason: str, agent: str = "System") -> CaseState:
    state.status = CaseStatus.ESCALATED
    await emit_audit(state, agent, f"Error LLM: {reason}", error=reason)
    await emit_client_message(
        state,
        ClientMessage(
            type=ClientMessageType.IDENTIFIED,
            text=(
                "Detectamos un problema al analizar tu consulta. "
                "Un operador humano revisará tu caso a la brevedad."
            ),
        ),
    )
    return state


async def handle_llm_error(state: CaseState, exc: Exception) -> CaseState:
    if isinstance(exc, LLMConfigurationError):
        return await escalate_case(state, str(exc))
    if isinstance(exc, LLMInvocationError):
        return await escalate_case(state, str(exc))
    return await escalate_case(state, f"Error inesperado: {exc}")
