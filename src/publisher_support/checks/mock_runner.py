from publisher_support.adapters.scenarios import load_scenario
from publisher_support.checks.base import CheckContext, CheckResult


def run_checks(context: CheckContext) -> list[CheckResult]:
    scenario = load_scenario(context.scenario_id)
    checks_data = scenario.get("checks", {}).get(context.phase, [])
    return [
        CheckResult(
            check_id=c["id"],
            name=c["name"],
            passed=c.get("pass", True),
        )
        for c in checks_data
    ]
