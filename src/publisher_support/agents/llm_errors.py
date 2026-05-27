from publisher_support.agents.helpers import emit_audit, emit_client_message
from publisher_support.agents.messaging import client_message_escalated
from publisher_support.llm.errors import LLMConfigurationError, LLMInvocationError
from publisher_support.models.schemas import CaseState, CaseStatus


async def escalate_case(state: CaseState, reason: str, agent: str = "System") -> CaseState:
    state.status = CaseStatus.ESCALATED
    await emit_audit(state, agent, f"Error LLM: {reason}", error=reason)
    await emit_client_message(state, client_message_escalated())
    return state


async def handle_llm_error(state: CaseState, exc: Exception) -> CaseState:
    if isinstance(exc, LLMConfigurationError):
        return await escalate_case(state, str(exc))
    if isinstance(exc, LLMInvocationError):
        return await escalate_case(state, str(exc))
    return await escalate_case(state, f"Error inesperado: {exc}")
