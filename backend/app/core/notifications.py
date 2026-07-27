import json
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from app.core.security import decode_token


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_to_user(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            dead = []
            for ws in self.active_connections[user_id]:
                try:
                    await ws.send_json(message)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self.active_connections[user_id].discard(ws)

    async def broadcast(self, message: dict, exclude_user: str = None):
        for uid, connections in list(self.active_connections.items()):
            if uid == exclude_user:
                continue
            dead = []
            for ws in connections:
                try:
                    await ws.send_json(message)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                connections.discard(ws)


manager = ConnectionManager()


async def notify_user(user_id: str, notification: dict):
    await manager.send_to_user(user_id, notification)
