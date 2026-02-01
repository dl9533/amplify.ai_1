"""Chat schemas for the Discovery module."""
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class QuickAction(BaseModel):
    """Schema for a quick action button."""

    label: str = Field(
        ...,
        description="Display label for the action",
    )
    action: str = Field(
        ...,
        description="Action identifier",
    )

    model_config = {
        "from_attributes": True,
    }


class ChatMessage(BaseModel):
    """Schema for sending a chat message."""

    message: str = Field(
        ...,
        description="The message content to send",
    )

    model_config = {
        "from_attributes": True,
    }


class ChatResponse(BaseModel):
    """Schema for chat response from the orchestrator."""

    response: str = Field(
        ...,
        description="The response text from the assistant",
    )
    quick_actions: list[QuickAction] = Field(
        default_factory=list,
        description="List of quick action buttons to display",
    )

    model_config = {
        "from_attributes": True,
    }


class ChatHistoryItem(BaseModel):
    """Schema for a single chat history item."""

    role: Literal["user", "assistant"] = Field(
        ...,
        description="The role of the message sender (user or assistant)",
    )
    content: str = Field(
        ...,
        description="The message content",
    )
    timestamp: datetime = Field(
        ...,
        description="When the message was sent",
    )

    model_config = {
        "from_attributes": True,
    }


class QuickActionRequest(BaseModel):
    """Schema for executing a quick action."""

    action: str = Field(
        ...,
        description="The action identifier to execute",
    )
    params: dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters for the action",
    )

    model_config = {
        "from_attributes": True,
    }


class QuickActionResponse(BaseModel):
    """Schema for quick action execution response."""

    response: str = Field(
        ...,
        description="The response text after action execution",
    )
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional data returned by the action",
    )

    model_config = {
        "from_attributes": True,
    }
