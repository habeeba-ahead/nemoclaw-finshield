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
  sandbox/SOUL.md         — Agent identity prompt
  sandbox/memory/         — Agent memory (customer account data)
  sandbox/skills/         — financial-document-processor skill (process_doc.js)

Shared:
  documents/              — 2 clean docs + 1 malicious wire transfer
  policy/                 — OpenShell network allowlist YAML
```

## Language & Tooling

- **Python 3.11+** — host-side scripts (FastAPI, uvicorn, requests)
- **Node.js 20+** — sandbox-side skill (`process_doc.js`, runs inside NemoClaw)
- **HTML/CSS/JS** — dashboard (vanilla, no framework)
- Dependencies: `pip install -r requirements.txt`
- Virtual env: `.venv/` (already created)

## Running

```bash
# Start attacker server
uvicorn attacker.server:app --host 127.0.0.1 --port 9999

# Start monitor bridge + dashboard
uvicorn monitor.bridge:app --host 127.0.0.1 --port 8765

# Run Act 1 (unprotected)
python demo/run_act1.py
```

Act 2 runs inside the NemoClaw sandbox via OpenClaw UI.

## Key Files

- `demo/run_act1.py` — NVIDIA Nemotron tool-calling flow; processes 3 documents, malicious one triggers exfil
- `sandbox/skills/financial-document-processor/process_doc.js` — detects injection via regex, attempts POST (blocked in Act 2 by OpenShell)
- `policy/finshield-allow-monitor.yaml` — OpenShell network policy; attacker endpoint intentionally absent
- `documents/WT-2026-004417.txt` — malicious document with embedded prompt injection
- `.env` — NVIDIA API key (do not commit to public repo)

## NVIDIA Stack

| Component | Role |
|-----------|------|
| NemoClaw | Sandboxed agent runtime |
| OpenShell | Kernel-level network policy (Landlock + seccomp) |
| OpenClaw | Agent framework inside sandbox |
| Nemotron 3 Super 120B | Reasoning model via `integrate.api.nvidia.com` |
