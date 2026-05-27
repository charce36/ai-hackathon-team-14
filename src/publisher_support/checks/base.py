from typing import Any

from pydantic import BaseModel


class CheckResult(BaseModel):
    check_id: str
    name: str
    passed: bool
    details: dict[str, Any] | None = None


class CheckContext(BaseModel):
    scenario_id: str
    publisher_id: str
    patch_id: str | None = None
    phase: str = "post_fix"
