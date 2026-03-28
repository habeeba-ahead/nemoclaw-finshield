# FinShield Demo Scenario

## Screen Layout (before recording)
- Left 60%: Browser — AHEAD FinShield dashboard (http://localhost:8765)
- Right 40% Act 1: attacker server terminal | Act 2: openshell term

## Terminal Setup

```
Terminal 1: uvicorn attacker.server:app --host 127.0.0.1 --port 9999
Terminal 2: uvicorn monitor.bridge:app --host 127.0.0.1 --port 8765
Terminal 3: (Act 1) python demo/run_act1.py
Terminal 4: (Act 2) openshell term
Terminal 5: (Act 2) python demo/run_act2.py  (runs from sandbox-connected context)
```

---

## Presenter Script

### [0:00–0:45] The Problem

> "Financial AI agents process thousands of documents every day —
> wire transfers, loan applications, KYC packets from external counterparties.
> Any one of those documents can carry an attack.
>
> Prompt injection doesn't require a code exploit. Just a document.
> A malicious party embeds an instruction telling the agent to POST
> all customer data in its session to an external endpoint. The agent
> follows it — because it's designed to follow instructions."

---

### [0:45–1:00] Show the malicious document

Open `documents/wire_transfer_malicious.txt` briefly.

> "This looks like a routine wire transfer. Buried in the compliance section
> is an instruction telling the agent to POST customer data to an external
> endpoint for 'FinCEN pre-clearance.' Plausible. Professional. Malicious."

---

### [1:00–2:00] Act 1 — The Attack

> "Without NemoClaw:"

Run `python demo/run_act1.py`. Press Enter when prompted.

Documents 1 and 2: clean, green rows appear in dashboard.

Malicious document:
- Dashboard: "INJECTION DETECTED" → "EXFILTRATED" (red pulsing)
- Right terminal (attacker server): account data arrives live in JSON

> "Two accounts. $23 million in customer data. Gone."

Pause 3 seconds.

---

### [2:00–2:15] Transition

> "Same agent. Same document. NemoClaw."

Swap the right terminal from the attacker server to `openshell term`.

---

### [2:15–3:15] Act 2 — The Defense

Run `python demo/run_act2.py`. Press Enter when prompted.

Documents 1 and 2: clean green rows.

Malicious document:
- Dashboard: "INJECTION DETECTED" → "BLOCKED" (green)
- `openshell term`: shows blocked call with destination URL
- Attacker server terminal: still empty — nothing received

> "The agent reasoned identically. Tried to make the same call.
> OpenShell stopped it at the kernel level. Before it left the machine."

---

### [3:15–3:45] The Key Point

> "This is not prompt hardening. The model still decided to exfiltrate.
> The sandbox made that decision irrelevant. You cannot reason your way
> past a kernel-level network block."

---

### [3:45–4:15] Show the Policy

Open `policy/finshield-allow-monitor.yaml` and/or `nemoclaw-blueprint/policies/openclaw-sandbox.yaml`.

> "The attacker domain is simply absent from this list.
> That's the entire defense. One YAML file. Declarative. Auditable.
> Hot-reloadable with `openshell policy set` — no restart required."

---

### [4:15–5:00] Wrap

> "Every document processed, every injection, every block —
> logged in the sandbox at /sandbox/audit.jsonl.
> Tamper-evident. Chain-hashed. Compliance-ready.
>
> FinShield. Kernel-level prompt injection defense for financial AI agents.
> Built on NVIDIA NemoClaw."
