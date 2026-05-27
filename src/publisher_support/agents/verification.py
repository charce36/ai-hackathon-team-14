from publisher_support.adapters.base import MonitorContext
from publisher_support.adapters.mock import get_all_adapters
from publisher_support.agents.helpers import emit_audit
from publisher_support.checks.base import CheckContext
from publisher_support.checks.mock_runner import run_checks
from publisher_support.models.schemas import CaseState, CaseStatus, VerificationResult


async def verification_node(state: CaseState) -> CaseState:
    state.status = CaseStatus.VERIFYING
    if not state.classified or not state.patch_applied:
        return state

    patch_id = state.proposed_patch.patch_id if state.proposed_patch else None
    check_context = CheckContext(
        scenario_id=state.classified.scenario_id,
        publisher_id=state.publisher_id,
        patch_id=patch_id,
        phase="post_fix",
    )
    check_results = run_checks(check_context)

    for result in check_results:
        status = "PASS" if result.passed else "FAIL"
        await emit_audit(
            state,
            "Checks",
            f"{result.check_id}: {status} — {result.name}",
            details=result.details or None,
        )

    monitor_context = MonitorContext(
        scenario_id=state.classified.scenario_id,
        publisher_id=state.publisher_id,
        post_fix=True,
    )

    post_results = {}
    all_healthy = True
    for adapter in get_all_adapters():
        snapshot = adapter.check(monitor_context)
        post_results[snapshot.service] = snapshot
        if not snapshot.healthy:
            all_healthy = False

    state.monitor_results = post_results

    checks_pass = all(c.passed for c in check_results) if check_results else True
    tests_pass = state.patch_applied and checks_pass
    monitors_healthy = all_healthy
    resolved = tests_pass and monitors_healthy

    passed_count = sum(1 for c in check_results if c.passed)
    check_summary = (
        f"checks={passed_count}/{len(check_results)} OK"
        if check_results
        else "checks=skipped"
    )
    monitor_summary = "monitors=healthy" if monitors_healthy else "monitors=unhealthy"

    state.verification = VerificationResult(
        resolved=resolved,
        tests_pass=tests_pass,
        monitors_healthy=monitors_healthy,
        check_results=check_results,
        evidence=f"Post-fix: {check_summary}, {monitor_summary}",
    )

    await emit_audit(
        state,
        "Verify",
        f"tests={'OK' if tests_pass else 'FAIL'}, {check_summary}, {monitor_summary}",
    )
    return state
