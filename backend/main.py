"""
Intelligence Fusion Dashboard — FastAPI Backend
Main application entry point with WebSocket support for real-time updates.
"""

import asyncio
import json
import random
import sys
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Set

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import init_db, get_db
from backend.routes.auth_routes import router as auth_router
from backend.routes.data_routes import router as data_router
from backend.routes.ai_routes import router as ai_router
from backend.routes.intelligence_routes import router as intel_router
from backend.routes.alert_routes import router as alert_router


# ─── WebSocket Connection Manager ──────────────────────
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        disconnected = set()
        for ws in self.active_connections:
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.add(ws)
        self.active_connections -= disconnected


manager = ConnectionManager()


# ─── Real-time alert broadcaster ───────────────────────
async def broadcast_live_alerts():
    """Continuously broadcast new alerts to all connected WebSocket clients."""
    known_alert_ids: Set[int] = set()
    while True:
        try:
            await asyncio.sleep(5)
            if not manager.active_connections:
                continue
            db = await get_db()
            try:
                cursor = await db.execute(
                    "SELECT id, type, severity, title, description, latitude, longitude, risk_score, created_at "
                    "FROM alerts ORDER BY created_at DESC LIMIT 20"
                )
                rows = await cursor.fetchall()
                new_alerts = []
                for r in rows:
                    if r[0] not in known_alert_ids:
                        known_alert_ids.add(r[0])
                        new_alerts.append({
                            "id": r[0], "type": r[1], "severity": r[2],
                            "title": r[3], "description": r[4],
                            "latitude": r[5], "longitude": r[6],
                            "risk_score": r[7], "created_at": r[8],
                        })

                if new_alerts:
                    await manager.broadcast({
                        "event": "new_alerts",
                        "data": new_alerts,
                        "timestamp": datetime.utcnow().isoformat(),
                    })

                # Also broadcast live stats
                total = (await (await db.execute("SELECT COUNT(*) FROM intelligence_data")).fetchone())[0]
                unack = (await (await db.execute("SELECT COUNT(*) FROM alerts WHERE acknowledged=0")).fetchone())[0]
                await manager.broadcast({
                    "event": "stats_update",
                    "data": {"total_intelligence": total, "unacknowledged_alerts": unack,
                             "timestamp": datetime.utcnow().isoformat()},
                })
            finally:
                await db.close()
        except Exception:
            pass


# ─── Lifespan ──────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    task = asyncio.create_task(broadcast_live_alerts())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


# ─── App Setup ─────────────────────────────────────────
app = FastAPI(
    title="Intelligence Fusion Dashboard API",
    description="Multi-Source AI-Powered Intelligence Analysis Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ───────────────────────────────────────────
app.include_router(auth_router)
app.include_router(data_router)
app.include_router(ai_router)
app.include_router(intel_router)
app.include_router(alert_router)


# ─── WebSocket Endpoint ────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        await websocket.send_json({
            "event": "connected",
            "message": "Intelligence Fusion Dashboard — Live Feed Active",
            "timestamp": datetime.utcnow().isoformat(),
        })
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("type") == "ping":
                await websocket.send_json({"event": "pong", "timestamp": datetime.utcnow().isoformat()})
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ─── Health Check ─────────────────────────────────────
@app.get("/health")
async def health_check():
    return {
        "status": "operational",
        "service": "Intelligence Fusion Dashboard",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "active_connections": len(manager.active_connections),
    }


if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
