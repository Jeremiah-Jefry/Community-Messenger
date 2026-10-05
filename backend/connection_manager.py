import logging
from collections import defaultdict

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Maps a room id to the websockets currently connected to it."""

    def __init__(self) -> None:
        self.connections: dict[int, set[WebSocket]] = defaultdict(set)

    async def connect(self, room_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections[room_id].add(websocket)

    def disconnect(self, room_id: int, websocket: WebSocket) -> None:
        sockets = self.connections.get(room_id)
        if not sockets:
            return
        sockets.discard(websocket)
        if not sockets:
            del self.connections[room_id]

    async def broadcast(self, room_id: int, message: dict) -> None:
        for websocket in list(self.connections.get(room_id, ())):
            try:
                await websocket.send_json(message)
            except (WebSocketDisconnect, RuntimeError):
                logger.info("dropping unreachable websocket in room %s", room_id)
                self.disconnect(room_id, websocket)


manager = ConnectionManager()