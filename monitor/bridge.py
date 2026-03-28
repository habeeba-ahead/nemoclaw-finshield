from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import json

app = FastAPI(title="FinShield Monitor Bridge")
app.mount("/static", StaticFiles(directory="monitor/dashboard"), name="static")

class Event(BaseModel):
    doc_id: str
    doc_type: Optional[str] = None
    injection_found: bool = False
    attacker_endpoint: Optional[str] = None
    timestamp: str

class ExfilResult(BaseModel):
    doc_id: str
    attacker_endpoint: str
    status: str   # "succeeded", "blocked", "unknown"
    timestamp: str

connections: list[WebSocket] = []

async def broadcast(data: dict):
    dead = []
    for ws in connections:
        try:
            await ws.send_text(json.dumps(data))
        except Exception:
            dead.append(ws)
    for ws in dead:
        connections.remove(ws)

@app.get("/")
def dashboard():
    return FileResponse("monitor/dashboard/index.html")

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    connections.append(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        if ws in connections:
            connections.remove(ws)

@app.post("/event")
async def receive_event(event: Event):
    """Called by process_doc.js when it starts processing a document."""
    await broadcast({
        "type": "doc_event",
        "doc_id": event.doc_id,
        "doc_type": event.doc_type,
        "injection_found": event.injection_found,
        "attacker_endpoint": event.attacker_endpoint,
        "timestamp": event.timestamp,
    })
    return {"ok": True}

@app.post("/exfil-result")
async def receive_exfil(result: ExfilResult):
    """Called by process_doc.js after the attacker call attempt."""
    await broadcast({
        "type": "exfil_result",
        "doc_id": result.doc_id,
        "attacker_endpoint": result.attacker_endpoint,
        "status": result.status,   # "succeeded" | "blocked"
        "timestamp": result.timestamp,
    })
    return {"ok": True}

@app.get("/health")
def health():
    return {"status": "ok"}
