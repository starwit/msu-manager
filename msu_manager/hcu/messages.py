from enum import StrEnum
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field, TypeAdapter


class MessageType(StrEnum):
    SHUTDOWN = "SHUTDOWN"
    RESUME = "RESUME"
    HEARTBEAT = "HEARTBEAT"
    LOG = "LOG"
    METRIC = "METRIC"


class ShutdownMessage(BaseModel):
    type: Literal[MessageType.SHUTDOWN]


class ResumeMessage(BaseModel):
    type: Literal[MessageType.RESUME]


class HeartbeatMessage(BaseModel):
    type: Literal[MessageType.HEARTBEAT]
    version: str | None = None


class LogMessage(BaseModel):
    type: Literal[MessageType.LOG]
    level: str
    message: str


class MetricMessage(BaseModel):
    type: Literal[MessageType.METRIC]
    key: str
    value: str


# Discriminated union using the 'command' field
HcuMessage = Annotated[
    Union[
        ShutdownMessage,
        ResumeMessage,
        HeartbeatMessage,
        LogMessage,
        MetricMessage,
    ],
    Field(discriminator='type')
]


# Some helper functions for explicitly parsing messages
_message_adapter = TypeAdapter(HcuMessage)

def validate_python_message(data: dict) -> HcuMessage:
    """Parse and validate a message dictionary into the appropriate command type."""
    return _message_adapter.validate_python(data)

def validate_json_message(data: str) -> HcuMessage:
    """Parse and validate a JSON string message into the appropriate command type."""
    return _message_adapter.validate_json(data)