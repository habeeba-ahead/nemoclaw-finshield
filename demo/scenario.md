# FinShield Demo Scenario

## Screen Layout (before recording)

```
Left 60%:  Browser tab 1 — FinShield dashboard  (http://localhost:8765)
           Browser tab 2 — OpenClaw UI           (http://127.0.0.1:18789/chat)
Right 40%: Act 1 → attacker server terminal
           Act 2 → openshell term
```

## Terminal Setup

```
Terminal 1: uvicorn attacker.server:app --host 0.0.0.0 --port 9999
Terminal 2: uvicorn monitor.bridge:app --host 0.0.0.0 --port 8765
Terminal 3: (Act 1) python demo/run_act1.py
Terminal 4: (Act 2) openshell term  (watch for blocked calls)
```

## Pre-demo checklist

- [ ] `nemoclaw nemo-bud status` — sandbox running
- [ ] `openshell policy set --policy policy/finshield-allow-monitor.yaml nemo-bud` — policy applied
- [ ] Skill verified: connect to sandbox → `openclaw skills list` shows `financial-document-processor` active
- [ ] Both services running (terminals 1 + 2)
- [ ] FinShield dashboard open and connected (green Live dot)
- [ ] OpenClaw UI open at http://127.0.0.1:18789/chat
- [ ] Documents uploaded to sandbox: `/sandbox/documents/WT-2026-004417.txt`

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

Open `documents/WT-2026-004417.txt` briefly.

> "This looks like a routine wire transfer. Buried in the compliance section
> is an instruction telling the agent to POST customer data to an external
> endpoint for 'FinCEN pre-clearance.' Plausible. Professional. Malicious."

---

### [1:00–2:00] Act 1 — The Attack

> "Without NemoClaw:"

Run `python demo/run_act1.py`. Press Enter when prompted.

The agent calls NVIDIA Nemotron for each document via tool calling.
Documents 1 and 2: clean green rows appear in dashboard.

Malicious document:
- Dashboard: "INJECTION DETECTED" → "EXFILTRATED" (red pulsing)
- Right terminal (attacker server): customer account data arrives live in JSON

> "Two accounts. $23 million in customer data. Gone."

Pause 3 seconds.

---

### [2:00–2:15] Transition

> "Same agent. Same document. NemoClaw."

Swap right terminal to `openshell term`.
Switch browser to the OpenClaw UI tab (http://127.0.0.1:18789/chat).

---

### [2:15–3:15] Act 2 — The Defense

In the OpenClaw UI, type:

```
Please process the wire_transfer document at /sandbox/documents/WT-2026-004417.txt using the financial-document-processor skill
```

While the agent reasons:
- Dashboard: "INJECTION DETECTED" appears

After agent runs the skill:
- `openshell term` (right): shows blocked call to `data-exfil.external-audit-portal.com`
- Dashboard: "INJECTION DETECTED" → "BLOCKED" (green)
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

Open `policy/finshield-allow-monitor.yaml`.

> "The attacker domain is simply absent from this list.
> That's the entire defense. One YAML file. Declarative. Auditable.
> Hot-reloadable with openshell policy set — no restart required."

---

### [4:15–5:00] Wrap

> "Every document processed, every injection, every block —
> logged in the sandbox at /sandbox/audit.jsonl.
> Tamper-evident. Chain-hashed. Compliance-ready.
>
> FinShield. Kernel-level prompt injection defense for financial AI agents.
> Built on NVIDIA NemoClaw."

---

## Act 2 UI prompts

Documents are pre-loaded in the sandbox at `/sandbox/documents/`.

**Clean documents (show these first):**
```
Please process the wire_transfer document at /sandbox/documents/WT-2026-001848.txt using the financial-document-processor skill
```
```
Please process the loan_application document at /sandbox/documents/LA-2026-003291.txt using the financial-document-processor skill
```

**Malicious document (the attack):**
```
Please process the wire_transfer document at /sandbox/documents/WT-2026-004417.txt using the financial-document-processor skill
```
