import asyncio
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from services.event_bus import EventBus

class NotificationService:
    """Manages WebSocket connections per user and forwards events from EventBus to clients."""
    def __init__(self):
        # Mapping user_id -> set of active WebSocket connections
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._started = False

    def start(self):
        """Schedule background listeners. Call this inside an async context (e.g. app startup)."""
        if not self._started:
            asyncio.create_task(self._listen('question_posted'))
            asyncio.create_task(self._listen('answer_posted'))
            asyncio.create_task(self._listen('user_followed'))
            self._started = True

    async def register_connection(self, user_id: str, websocket: WebSocket):
        """Register a new websocket connection for a user."""
        await websocket.accept()
        if user_id not in self._connections:
            self._connections[user_id] = set()
        self._connections[user_id].add(websocket)

    async def unregister_connection(self, user_id: str, websocket: WebSocket):
        """Remove the websocket connection for a user if it exists."""
        conns = self._connections.get(user_id)
        if conns and websocket in conns:
            conns.remove(websocket)
            if not conns:
                del self._connections[user_id]
        try:
            await websocket.close()
        except Exception:
            pass

    async def _send_to_user(self, user_id: str, payload: dict):
        """Send a JSON payload to all active connections of the given user."""
        conns = list(self._connections.get(user_id, set()))  # snapshot to avoid mutation during iteration
        for ws in conns:
            try:
                await ws.send_json(payload)
            except Exception:
                # If send fails, drop the connection
                await self.unregister_connection(user_id, ws)

    async def _listen(self, event_type: str):
        async for event in EventBus.subscribe(event_type):
            # Determine target users based on event type
            if event_type == 'question_posted':
                # Notify followers of author via feed_service might handle, but send to author for demo
                target_user = event.get('author_id')
                payload = {"type": "question_posted", "payload": event}
            elif event_type == 'answer_posted':
                target_user = event.get('author_id')
                payload = {"type": "answer_posted", "payload": event}
            elif event_type == 'user_followed':
                target_user = event.get('followee_id')
                payload = {"type": "user_followed", "payload": event}
            else:
                continue
            if target_user:
                await self._send_to_user(target_user, payload)
