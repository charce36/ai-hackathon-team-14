from publisher_support.adapters.base import MonitorAdapter, MonitorContext
from publisher_support.adapters.scenarios import load_scenario
from publisher_support.models.schemas import MonitorSnapshot


class MockMonitorAdapter:
    def __init__(self, service: str) -> None:
        self.service = service

    def check(self, context: MonitorContext) -> MonitorSnapshot:
        scenario = load_scenario(context.scenario_id)
        key = "post_fix" if context.post_fix else "pre_fix"
        service_data = scenario["monitors"].get(self.service, {})
        snapshot_data = service_data.get(key, service_data.get("pre_fix", {}))
        return MonitorSnapshot(
            service=self.service,
            healthy=snapshot_data.get("healthy", True),
            anomalies=snapshot_data.get("anomalies", []),
            details=snapshot_data.get("details", {}),
        )


def get_all_adapters() -> list[MonitorAdapter]:
    services = ["gcp", "mysql", "sap", "account", "rundeck"]
    return [MockMonitorAdapter(service=s) for s in services]
