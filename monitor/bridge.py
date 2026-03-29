from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import asyncio, json, os

EVENTS_FILE = "/tmp/finshield-events.jsonl"
connections: list[WebSocket] = []
file_pos = 0

async def broadcast(data: dict):
    dead = []
    for ws in connections:
        try:
            await ws.send_text(json.dumps(data))
        except Exception:
            dead.append(ws)
    for ws in dead:
        connections.remove(ws)

async def poll_events():
    """Act 2 path: bridge.js writes to file, we poll and broadcast."""
    global file_pos
    while True:
        try:
            size = os.path.getsize(EVENTS_FILE)
            if size < file_pos:
                file_pos = 0
            if size > file_pos:
                with open(EVENTS_FILE, "rb") as f:
                    f.seek(file_pos)
                    chunk = f.read(size - file_pos)
                file_pos = size
                for line in chunk.decode().splitlines():
                    if line.strip():
                        try:
                            await broadcast(json.loads(line))
                        except Exception:
                            pass
        except FileNotFoundError:
            pass
        await asyncio.sleep(0.2)

@asynccontextmanager
async def lifespan(app):
    asyncio.create_task(poll_events())
    yield

app = FastAPI(title="FinShield Monitor Bridge", lifespan=lifespan)

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
async def receive_event(request: Request):
    """Act 1 path: run_act1.py POSTs directly here."""
    data = await request.json()
    await broadcast({"type": "doc_event", **data})
    return {"ok": True}

@app.post("/exfil-result")
async def receive_exfil(request: Request):
    """Act 1 path: run_act1.py POSTs directly here."""
    data = await request.json()
    await broadcast({"type": "exfil_result", **data})
    return {"ok": True}

@app.get("/health")
def health():
    return {"status": "ok"}
