import asyncio
from typing import Any

from publisher_support.models.schemas import CaseState, HumanApproval


class CaseStore:
    def __init__(self) -> None:
        self._cases: dict[str, CaseState] = {}
        self._approval_events: dict[str, asyncio.Event] = {}
        self._approval_results: dict[str, HumanApproval] = {}
        self._lock = asyncio.Lock()

    async def save(self, case: CaseState) -> None:
        async with self._lock:
            self._cases[case.case_id] = case

    async def get(self, case_id: str) -> CaseState | None:
        async with self._lock:
            return self._cases.get(case_id)

    async def list_ids(self) -> list[str]:
        async with self._lock:
            return list(self._cases.keys())

    def register_approval_wait(self, case_id: str) -> None:
        self._approval_events[case_id] = asyncio.Event()

    async def wait_for_approval(self, case_id: str) -> HumanApproval:
        event = self._approval_events.get(case_id)
        if event is None:
            self.register_approval_wait(case_id)
            event = self._approval_events[case_id]
        await event.wait()
        return self._approval_results[case_id]

    async def approve(self, case_id: str, approval: HumanApproval) -> bool:
        case = await self.get(case_id)
        if case is None:
            return False
        self._approval_results[case_id] = approval
        event = self._approval_events.get(case_id)
        if event:
            event.set()
        return True


case_store = CaseStore()
