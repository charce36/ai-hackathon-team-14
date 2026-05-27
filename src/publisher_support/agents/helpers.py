import asyncio
from typing import Callable, Awaitable

from publisher_support.config import settings
from publisher_support.events.broadcaster import broadcaster
from publisher_support.models.events import AuditEvent, ClientMessage
from publisher_support.models.schemas import CaseState


async def demo_delay() -> None:
    if settings.demo_step_delay_ms > 0:
        await asyncio.sleep(settings.demo_step_delay_ms / 1000)


async def emit_audit(
    state: CaseState,
    agent: str,
    message: str,
    **metadata,
) -> AuditEvent:
    event = AuditEvent(agent=agent, message=message, metadata=metadata)
    state.timeline.append(event)
    await broadcaster.emit_audit(state.case_id, event)
    await demo_delay()
    return event


async def emit_client_message(state: CaseState, message: ClientMessage) -> None:
    state.client_messages.append(message)
    await broadcaster.emit_client_message(state.case_id, message)


StepFn = Callable[[CaseState], Awaitable[CaseState]]
