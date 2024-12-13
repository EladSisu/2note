from typing import Dict, Optional, Set

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, document_id: str):
        await websocket.accept()
        if document_id not in self.active_connections:
            self.active_connections[document_id] = set()
        self.active_connections[document_id].add(websocket)

    async def disconnect(self, websocket: WebSocket, document_id: str):
        if document_id in self.active_connections:
            self.active_connections[document_id].discard(websocket)
            if not self.active_connections[document_id]:
                del self.active_connections[document_id]

    async def broadcast(self, message: dict, document_id: str, exclude: Optional[WebSocket] = None):
        if document_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[document_id]:
                if connection != exclude:
                    try:
                        await connection.send_json(message)
                    except RuntimeError:
                        disconnected.add(connection)
            
            # Clean up disconnected clients
            for conn in disconnected:
                await self.disconnect(conn, document_id)