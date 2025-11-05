"""
Chat Router
Handles chat completions and conversations using the AI pipeline
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, AsyncIterator
from datetime import datetime
import json

from api.routers.auth import get_current_user, User
from core.pipeline.pipeline_executor import (
    PipelineExecutor,
    ExecutionContext,
    PipelineResult
)

router = APIRouter()


# Models
class ChatMessage(BaseModel):
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: Optional[datetime] = None


class ChatCompletionRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    stream: bool = False
    conversation_history: List[ChatMessage] = []
    workspace_state: Dict[str, Any] = {}
    user_preferences: Dict[str, Any] = {}


class ChatCompletionResponse(BaseModel):
    id: str
    message: str
    intent: Optional[Dict[str, Any]] = None
    routing: Optional[Dict[str, Any]] = None
    agent_used: Optional[str] = None
    actions: List[Dict[str, Any]] = []
    quick_replies: List[str] = []
    metadata: Dict[str, Any] = {}
    execution_time_ms: float


class ConversationSummary(BaseModel):
    session_id: str
    message_count: int
    last_message_at: datetime
    title: str


# Helper functions
async def execute_pipeline(
    request: ChatCompletionRequest,
    user: User,
    pipeline_executor: PipelineExecutor
) -> PipelineResult:
    """Execute AI pipeline for chat completion"""

    # Build execution context
    context = ExecutionContext(
        user_id=user.id,
        session_id=request.session_id or f"session_{user.id}_{int(datetime.now().timestamp())}",
        project=f"user_{user.id}",
        conversation_history=[msg.dict() for msg in request.conversation_history],
        user_preferences=request.user_preferences,
        workspace_state=request.workspace_state
    )

    # Execute pipeline
    result = await pipeline_executor.execute(
        user_message=request.message,
        context=context
    )

    return result


async def stream_pipeline_response(
    request: ChatCompletionRequest,
    user: User,
    pipeline_executor: PipelineExecutor
) -> AsyncIterator[str]:
    """Stream pipeline response as Server-Sent Events"""

    # Send initial message
    yield f"data: {json.dumps({'type': 'start', 'timestamp': datetime.now().isoformat()})}\n\n"

    # Build context
    context = ExecutionContext(
        user_id=user.id,
        session_id=request.session_id or f"session_{user.id}_{int(datetime.now().timestamp())}",
        project=f"user_{user.id}",
        conversation_history=[msg.dict() for msg in request.conversation_history],
        user_preferences=request.user_preferences,
        workspace_state=request.workspace_state
    )

    # Execute pipeline stages and stream progress
    yield f"data: {json.dumps({'type': 'stage', 'stage': 'intent_detection', 'status': 'running'})}\n\n"

    result = await pipeline_executor.execute(
        user_message=request.message,
        context=context
    )

    # Stream intent
    if result.intent:
        yield f"data: {json.dumps({'type': 'intent', 'data': result.intent.intent_type.value})}\n\n"

    # Stream routing
    if result.routing:
        yield f"data: {json.dumps({'type': 'routing', 'data': result.routing.mode.value})}\n\n"

    # Stream agent selection
    if result.selected_agent:
        yield f"data: {json.dumps({'type': 'agent', 'data': result.selected_agent.agent_name})}\n\n"

    # Stream response chunks
    if result.enhanced_response:
        words = result.enhanced_response.split()
        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            yield f"data: {json.dumps({'type': 'chunk', 'data': chunk})}\n\n"

    # Stream actions
    if result.enhancement and result.enhancement.neural_ui.action_buttons:
        yield f"data: {json.dumps({'type': 'actions', 'data': result.enhancement.neural_ui.action_buttons})}\n\n"

    # Stream quick replies
    if result.enhancement and result.enhancement.neural_ui.quick_replies:
        yield f"data: {json.dumps({'type': 'quick_replies', 'data': result.enhancement.neural_ui.quick_replies})}\n\n"

    # Send completion
    yield f"data: {json.dumps({'type': 'done', 'execution_time_ms': result.execution_time_ms})}\n\n"


# Routes
@router.post("/completions", response_model=ChatCompletionResponse)
async def chat_completion(
    request: ChatCompletionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create a chat completion

    Executes the 5-stage AI pipeline and returns enhanced response
    """
    from api.main import get_app_state

    app_state = get_app_state()

    if 'pipeline_executor' not in app_state:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Pipeline executor not available"
        )

    pipeline_executor: PipelineExecutor = app_state['pipeline_executor']

    # Handle streaming
    if request.stream:
        return StreamingResponse(
            stream_pipeline_response(request, current_user, pipeline_executor),
            media_type="text/event-stream"
        )

    # Non-streaming execution
    result = await execute_pipeline(request, current_user, pipeline_executor)

    # Build response
    response = ChatCompletionResponse(
        id=result.id,
        message=result.enhanced_response,
        intent={
            "type": result.intent.intent_type.value,
            "confidence": result.intent.confidence
        } if result.intent else None,
        routing={
            "mode": result.routing.mode.value,
            "reasoning_method": result.routing.reasoning_method.value if result.routing.reasoning_method else None
        } if result.routing else None,
        agent_used=result.selected_agent.agent_name if result.selected_agent else None,
        actions=result.enhancement.neural_ui.action_buttons if result.enhancement else [],
        quick_replies=result.enhancement.neural_ui.quick_replies if result.enhancement else [],
        metadata={
            "tokens_used": result.tokens_used,
            "cost_usd": result.cost_usd
        },
        execution_time_ms=result.execution_time_ms
    )

    return response


@router.get("/conversations", response_model=List[ConversationSummary])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0
):
    """
    List user's conversation sessions

    Returns summary of recent conversations
    """
    # In production, fetch from database
    # For now, return mock data

    conversations = [
        ConversationSummary(
            session_id=f"session_{current_user.id}_001",
            message_count=15,
            last_message_at=datetime.now(),
            title="Dashboard creation discussion"
        ),
        ConversationSummary(
            session_id=f"session_{current_user.id}_002",
            message_count=8,
            last_message_at=datetime.now(),
            title="Data analysis workflow"
        )
    ]

    return conversations[offset:offset + limit]


@router.get("/conversations/{session_id}/messages", response_model=List[ChatMessage])
async def get_conversation_messages(
    session_id: str,
    current_user: User = Depends(get_current_user),
    limit: int = 50
):
    """
    Get messages from a conversation

    Returns message history for a specific session
    """
    # In production, fetch from database
    # For now, return mock data

    messages = [
        ChatMessage(
            role="user",
            content="Hello, can you help me create a dashboard?",
            timestamp=datetime.now()
        ),
        ChatMessage(
            role="assistant",
            content="Of course! I can help you create a dashboard. What kind of data do you want to visualize?",
            timestamp=datetime.now()
        )
    ]

    return messages[:limit]


@router.delete("/conversations/{session_id}")
async def delete_conversation(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a conversation

    Removes all messages from a conversation session
    """
    # In production, delete from database

    return {"message": f"Conversation {session_id} deleted successfully"}


@router.post("/conversations/{session_id}/clear")
async def clear_conversation(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Clear conversation history

    Removes all messages but keeps the session
    """
    # In production, clear messages from database

    return {"message": f"Conversation {session_id} cleared successfully"}
