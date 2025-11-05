"""
WebSocket Manager
Real-time bidirectional communication for desktop state sync
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import asyncio
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections per desktop"""

    def __init__(self):
        # desktop_id -> Set of WebSocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # websocket -> user_id mapping
        self.user_mapping: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, desktop_id: int, user_id: str):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()

        if desktop_id not in self.active_connections:
            self.active_connections[desktop_id] = set()

        self.active_connections[desktop_id].add(websocket)
        self.user_mapping[websocket] = user_id

        logger.info(f"User {user_id} connected to desktop {desktop_id}")

        # Send initial state
        await self.send_personal_message({
            "type": "connected",
            "desktop_id": desktop_id,
            "user_id": user_id
        }, websocket)

    def disconnect(self, websocket: WebSocket, desktop_id: int):
        """Remove WebSocket connection"""
        if desktop_id in self.active_connections:
            self.active_connections[desktop_id].discard(websocket)

            # Clean up empty desktop groups
            if not self.active_connections[desktop_id]:
                del self.active_connections[desktop_id]

        user_id = self.user_mapping.pop(websocket, None)
        logger.info(f"User {user_id} disconnected from desktop {desktop_id}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific connection"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")

    async def broadcast_to_desktop(self, message: dict, desktop_id: int, exclude: WebSocket = None):
        """Broadcast message to all connections on a desktop"""
        if desktop_id not in self.active_connections:
            return

        disconnected = set()

        for connection in self.active_connections[desktop_id]:
            if connection == exclude:
                continue

            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast: {e}")
                disconnected.add(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn, desktop_id)

    async def broadcast_to_user(self, message: dict, user_id: str):
        """Broadcast message to all connections of a specific user"""
        for websocket, uid in self.user_mapping.items():
            if uid == user_id:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send to user {user_id}: {e}")


# Global connection manager instance
manager = ConnectionManager()


async def handle_desktop_message(data: dict, websocket: WebSocket, desktop_id: int):
    """
    Handle incoming desktop messages

    Message types:
    - WINDOW_OPENED: New window created
    - WINDOW_CLOSED: Window closed
    - WINDOW_MOVED: Window position changed
    - WINDOW_RESIZED: Window size changed
    - WINDOW_FOCUSED: Window focus changed
    - DESKTOP_SWITCHED: Desktop changed
    """
    message_type = data.get("type")

    # Broadcast to other clients on the same desktop
    await manager.broadcast_to_desktop(data, desktop_id, exclude=websocket)

    # Handle specific message types
    if message_type == "WINDOW_MOVED":
        # Could save to database here
        logger.debug(f"Window moved: {data.get('window_id')} to ({data.get('x')}, {data.get('y')})")

    elif message_type == "WINDOW_OPENED":
        logger.info(f"Window opened: {data.get('app_id')}")

    elif message_type == "WINDOW_CLOSED":
        logger.info(f"Window closed: {data.get('window_id')}")


async def heartbeat(websocket: WebSocket, desktop_id: int):
    """Send periodic heartbeat to keep connection alive"""
    try:
        while True:
            await asyncio.sleep(30)  # Every 30 seconds
            await manager.send_personal_message({
                "type": "heartbeat",
                "timestamp": asyncio.get_event_loop().time()
            }, websocket)
    except Exception:
        pass  # Connection closed
