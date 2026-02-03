"""Chat router for the Discovery module."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.schemas.chat import (
    ChatHistoryItem,
    ChatMessage,
    ChatResponse,
    QuickAction,
    QuickActionRequest,
    QuickActionResponse,
)
from app.services.chat_service import (
    ChatService,
    get_chat_service,
)
from collections.abc import AsyncGenerator


router = APIRouter(
    prefix="/discovery",
    tags=["discovery-chat"],
)


def _dict_to_quick_action(data: dict) -> QuickAction:
    """Convert a dictionary to QuickAction.

    Args:
        data: Dictionary containing quick action data.

    Returns:
        QuickAction instance.
    """
    return QuickAction(
        label=data["label"],
        action=data["action"],
    )


def _dict_to_chat_history_item(data: dict) -> ChatHistoryItem:
    """Convert a dictionary to ChatHistoryItem.

    Args:
        data: Dictionary containing chat history item data.

    Returns:
        ChatHistoryItem instance.
    """
    return ChatHistoryItem(
        role=data["role"],
        content=data["content"],
        timestamp=data["timestamp"],
    )


@router.post(
    "/sessions/{session_id}/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send chat message",
    description="Sends a message to the orchestrator and receives a response with optional quick actions.",
)
async def send_message(
    session_id: UUID,
    body: ChatMessage,
    service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    """Send a chat message to the orchestrator."""
    result = await service.send_message(
        session_id=session_id,
        message=body.message,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID {session_id} not found",
        )

    return ChatResponse(
        response=result["response"],
        quick_actions=[
            _dict_to_quick_action(action)
            for action in result.get("quick_actions", [])
        ],
    )


@router.get(
    "/sessions/{session_id}/chat",
    response_model=list[ChatHistoryItem],
    status_code=status.HTTP_200_OK,
    summary="Get chat history",
    description="Retrieves the chat history for a session.",
)
async def get_history(
    session_id: UUID,
    service: ChatService = Depends(get_chat_service),
) -> list[ChatHistoryItem]:
    """Get chat history for a session."""
    result = await service.get_history(session_id=session_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID {session_id} not found",
        )

    return [_dict_to_chat_history_item(item) for item in result]


@router.get(
    "/sessions/{session_id}/chat/stream",
    status_code=status.HTTP_200_OK,
    summary="Stream chat responses",
    description="Server-Sent Events endpoint for streaming chat responses.",
)
async def stream_chat(
    session_id: UUID,
    service: ChatService = Depends(get_chat_service),
) -> StreamingResponse:
    """Stream chat responses via SSE."""
    result = await service.stream_response(session_id=session_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID {session_id} not found",
        )

    return StreamingResponse(
        result,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post(
    "/sessions/{session_id}/chat/action",
    response_model=QuickActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute quick action",
    description="Executes a quick action and returns the result.",
)
async def execute_action(
    session_id: UUID,
    body: QuickActionRequest,
    service: ChatService = Depends(get_chat_service),
) -> QuickActionResponse:
    """Execute a quick action."""
    result = await service.execute_action(
        session_id=session_id,
        action=body.action,
        params=body.params,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID {session_id} not found",
        )

    return QuickActionResponse(
        response=result["response"],
        data=result.get("data", {}),
    )
