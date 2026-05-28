"""WebSocket handler for real-time metrics push."""
from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import random


class ConnectionManager:
    def __init__(self):
        self._connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self._connections.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self._connections:
            self._connections.remove(ws)

    async def broadcast_metrics(self, station: str):
        payload = {
            "type":    "metrics",
            "station": station,
            "temp":    round(20 + random.random() * 15, 2),
            "vib":     round(random.random() * 2, 3),
            "pax":     random.randint(50, 300),
            "sync":    random.randint(60, 100),
        }
        for ws in list(self._connections):
            try:
                await ws.send_json(payload)
            except Exception:
                self.disconnect(ws)

    async def broadcast_incident(self, event: dict):
        for ws in list(self._connections):
            try:
                await ws.send_json({"type": "incident", **event})
            except Exception:
                self.disconnect(ws)


ws_manager = ConnectionManager()


async def ws_endpoint(websocket: WebSocket, station: str = "Berlin Hauptbahnhof"):
    await ws_manager.connect(websocket)
    try:
        await websocket.send_json({"type":"connected","station":station})
        while True:
            data = await websocket.receive_text()
            station = data or station
            await ws_manager.broadcast_metrics(station)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
