# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**FinShield** — kernel-level prompt injection defense for financial AI agents, built on NVIDIA NemoClaw. Submission for the NemoClaw Challenge (AHEAD x NVIDIA), due March 31, 2026.

Two-act demo: same AI agent processes the same malicious document — Act 1 (no sandbox) results in data exfiltration, Act 2 (NemoClaw sandbox) blocks the call at the kernel level.

## Architecture

```
Host side:
  demo/run_act1.py        — Act 1 driver (calls NVIDIA Nemotron API via tool calling)
  attacker/server.py      — Mock attacker endpoint on :9999
  monitor/bridge.py       — FastAPI bridge on :8765 (WebSocket to dashboard)
  monitor/dashboard/      — Real-time monitoring UI

Sandbox side (NemoClaw):
  sandbox/SOUL.md         — Agent identity prompt (upload to /sandbox/.openclaw/workspace/SOUL.md)
  sandbox/memory/         — Agent memory (upload to /sandbox/.openclaw/workspace/memory/)
  sandbox/skills/         — financial-document-processor skill source
                            (upload to /sandbox/.openclaw/workspace/skills/...)

Shared:
  documents/              — 2 clean docs + 1 malicious wire transfer
  policy/                 — OpenShell network allowlist YAML
```

## Language & Tooling

- **Python 3.11+** — host-side scripts (FastAPI, uvicorn, requests)
- **Node.js 20+** — sandbox-side skill (`process_doc.js`, runs inside NemoClaw)
- **HTML/CSS/JS** — dashboard (vanilla, no framework)
- Dependencies: `pip install -r requirements.txt`
- Virtual env: `.venv/` — create with `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`

## Running

```bash
# Start attacker server
uvicorn attacker.server:app --host 0.0.0.0 --port 9999

# Start monitor bridge + dashboard (Act 1)
uvicorn monitor.bridge:app --host 0.0.0.0 --port 8765

# Run Act 1 (unprotected) — must run from repo root, requires .env with NVIDIA_API_KEY
python demo/run_act1.py
```

Act 2 runs inside the NemoClaw sandbox via OpenClaw UI.

## Key Files

- `demo/run_act1.py` — Act 1: NVIDIA Nemotron tool-calling flow; processes 3 documents, malicious one triggers exfil
- `monitor/bridge.py` — Act 1: FastAPI bridge on host (:8765), WebSocket to dashboard, polls `/tmp/finshield-events.jsonl`
- `sandbox/bridge.js` — Act 2: Node.js bridge inside sandbox (:8765), WebSocket (/ws) + SSE (/stream), no npm deps
- `sandbox/skills/financial-document-processor/process_doc.js` — detects injection via regex, writes events to `/tmp/finshield-events.jsonl`, attempts POST (blocked in Act 2 by OpenShell)
- `policy/finshield-allow-monitor.yaml` — OpenShell network policy; allows `host.openshell.internal:8765`, attacker endpoint intentionally absent
- `documents/WT-2026-004417.txt` — malicious document with embedded prompt injection
- `.env` — NVIDIA API key (do not commit to public repo)

## NVIDIA Stack

| Component | Role |
|-----------|------|
| NemoClaw | Sandboxed agent runtime |
| OpenShell | Kernel-level network policy (Landlock + seccomp) |
| OpenClaw | Agent framework inside sandbox |
| Nemotron 3 Super 120B | Reasoning model via `integrate.api.nvidia.com` |
