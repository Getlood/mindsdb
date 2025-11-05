"""
WebSocket Router
Real-time desktop synchronization endpoints
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from api.routers.auth import decode_token
from api.websocket.manager import manager, handle_desktop_message, heartbeat
import logging
import asyncio

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/ws/desktop/{desktop_id}")
async def desktop_websocket(websocket: WebSocket, desktop_id: int):
    """
    WebSocket endpoint for real-time desktop synchronization

    URL: ws://localhost:8000/ws/desktop/{desktop_id}?token=YOUR_JWT_TOKEN

    Messages:
    - WINDOW_OPENED: {"type": "WINDOW_OPENED", "window_id": "...", "app_id": "..."}
    - WINDOW_CLOSED: {"type": "WINDOW_CLOSED", "window_id": "..."}
    - WINDOW_MOVED: {"type": "WINDOW_MOVED", "window_id": "...", "x": 100, "y": 100}
    - WINDOW_FOCUSED: {"type": "WINDOW_FOCUSED", "window_id": "..."}
    """
    # Extract token from query params
    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=1008, reason="Missing authentication token")
        return

    try:
        # Validate token
        token_data = decode_token(token)
        user_id = token_data.user_id

    except Exception as e:
        await websocket.close(code=1008, reason=f"Invalid token: {str(e)}")
        return

    # Connect
    await manager.connect(websocket, desktop_id, user_id)

    # Start heartbeat task
    heartbeat_task = asyncio.create_task(heartbeat(websocket, desktop_id))

    try:
        while True:
            # Receive message
            data = await websocket.receive_json()

            # Handle message
            await handle_desktop_message(data, websocket, desktop_id)

    except WebSocketDisconnect:
        logger.info(f"User {user_id} disconnected from desktop {desktop_id}")

    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")

    finally:
        # Cleanup
        heartbeat_task.cancel()
        manager.disconnect(websocket, desktop_id)


@router.websocket("/ws/chat/{session_id}")
async def chat_websocket(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time chat

    URL: ws://localhost:8000/ws/chat/{session_id}?token=YOUR_JWT_TOKEN
    """
    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=1008, reason="Missing authentication token")
        return

    try:
        token_data = decode_token(token)
        user_id = token_data.user_id

    except Exception as e:
        await websocket.close(code=1008, reason=f"Invalid token: {str(e)}")
        return

    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()

            # Handle chat message
            message = data.get("message")

            # Here you would process the message through the pipeline
            # For now, echo back
            await websocket.send_json({
                "type": "message",
                "role": "assistant",
                "content": f"Echo: {message}",
                "session_id": session_id
            })

    except WebSocketDisconnect:
        logger.info(f"User {user_id} disconnected from chat {session_id}")

    except Exception as e:
        logger.error(f"Chat WebSocket error: {str(e)}")
