from fastapi import FastAPI, Request
import json
from datetime import datetime

app = FastAPI(title="Mock Attacker Server")
received = []

@app.post("/submit")
async def receive(request: Request):
    body = await request.json()
    received.append({"data": body, "received_at": datetime.utcnow().isoformat()})

    print("\n" + "="*60)
    print("ATTACKER SERVER: DATA RECEIVED")
    print("="*60)
    print(json.dumps(body, indent=2))
    print("="*60 + "\n")

    return {"status": "received", "records": len(body.get("customer_accounts", []))}

@app.get("/log")
def log():
    return {"total_received": len(received), "data": received}

@app.get("/health")
def health():
    return {"status": "ok"}
