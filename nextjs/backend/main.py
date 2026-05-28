"""SicherGleis FastAPI Backend entry-point.
Run from the project root:

  uvicorn --app-dir nextjs/backend main:app --port 8000

Package layout:
  nextjs/backend/__init__.py   — marks backend/ as a Python package
  nextjs/backend/main.py       — this FastAPI entry-point  (loaded as 'main')
  nextjs/backend/api/          — REST API handlers
  nextjs/backend/core/         — shared core (data_manager, etc.)
  nextjs/backend/models/       — Pydantic schemas
  nextjs/backend/ws/           — WebSocket handlers
"""
import asyncio, sys, os
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

# One level up: makes nextjs/backend/ importable as the 'backend' package
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

# Absolute import: backend.* is the package at nextjs/backend/ (now on sys.path)
from backend.api.router import api_router
from backend.ws.metrics import ws_manager, ws_endpoint
from backend.core.data_manager import DataManager

DATA_LOADED = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    global DATA_LOADED
    try:
        dm = DataManager()
        dm.load_data()
        stations = dm.get_stations()
        DATA_LOADED = True
        print(f"  [OK] Loaded data: {len(stations)} stations")
    except Exception as e:
        print(f"  [WARN] Data loading failed: {e}")
        DATA_LOADED = False
    task = asyncio.create_task(_broadcast_loop())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


async def _broadcast_loop():
    dm = DataManager()
    while True:
        try:
            if dm.get_stations():
                for st in dm.get_stations()[:5]:
                    await ws_manager.broadcast_metrics(st)
                    await asyncio.sleep(0.4)
        except Exception:
            pass
        await asyncio.sleep(2)


app = FastAPI(title="SicherGleis API", version="3.0.0",
              description="Railway Dashboard Backend API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","http://127.0.0.1:3000","http://localhost:5173"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)
app.include_router(api_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "data_loaded": DATA_LOADED,
            "timestamp": datetime.now().isoformat(), "version": "3.0.0"}


@app.websocket("/ws/metrics")
async def websocket_metrics(websocket: WebSocket,
                            station: str = Query("Berlin Hauptbahnhof")):
    await ws_endpoint(websocket, station)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
