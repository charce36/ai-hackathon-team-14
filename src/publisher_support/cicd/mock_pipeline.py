import asyncio
import uuid

from publisher_support.agents.helpers import emit_audit, demo_delay
from publisher_support.models.schemas import CaseState, CaseStatus, HumanApproval


async def mock_cicd_node(state: CaseState) -> CaseState:
    state.status = CaseStatus.DEPLOYING
    job_id = f"mock-{uuid.uuid4().hex[:8]}"
    await emit_audit(state, "CI/CD", f"Iniciando pipeline job #{job_id}")
    await demo_delay()
    await demo_delay()
    state.patch_applied = True
    if state.human_approval:
        state.human_approval.cicd_job_id = job_id
    await emit_audit(state, "CI/CD", f"Deploy completado — job #{job_id}")
    return state
