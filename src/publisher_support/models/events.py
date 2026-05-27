from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class ClientMessageType(str, Enum):
    CHECKING = "checking"
    IDENTIFIED = "identified"
    RESOLVED = "resolved"
    USER = "user"


class ClientMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: ClientMessageType
    text: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AuditEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    agent: str
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_sse(self) -> dict[str, Any]:
        return {
            "event": "audit",
            "data": self.model_dump(mode="json"),
        }


class SSEClientMessage(BaseModel):
    event: str = "client_message"
    data: ClientMessage

    def to_sse(self) -> dict[str, Any]:
        return {
            "event": "client_message",
            "data": self.data.model_dump(mode="json"),
        }
