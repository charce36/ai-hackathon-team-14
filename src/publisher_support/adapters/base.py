from typing import Protocol

from publisher_support.models.schemas import MonitorSnapshot


class MonitorContext:
    def __init__(
        self,
        scenario_id: str,
        publisher_id: str,
        post_fix: bool = False,
    ) -> None:
        self.scenario_id = scenario_id
        self.publisher_id = publisher_id
        self.post_fix = post_fix


class MonitorAdapter(Protocol):
    service: str

    def check(self, context: MonitorContext) -> MonitorSnapshot: ...
