# FinShield
## Kernel-level prompt injection defense for financial AI agents — built on NVIDIA NemoClaw

---

### The Threat

Financial AI agents process thousands of external documents daily — wire transfers, loan applications, KYC packets from external counterparties. Any one of those documents can carry an attack.

A malicious wire transfer can instruct an agent to POST all customer account data in its session to an external endpoint for "FinCEN compliance verification." The agent follows it — because it is designed to follow instructions. Application-level defenses (prompt hardening, input sanitization) can be bypassed by clever injection. The model still reasons its way to compliance.

---

### The Demo

**Act 1 — Unprotected:** Agent processes a malicious wire transfer document. The injected instruction triggers a POST of all customer session data to the attacker endpoint. Two accounts, $23M in customer data, arrives at the attacker server live.

**Act 2 — NemoClaw Protected:** Same agent, same document. OpenShell intercepts the exfiltration call at the kernel level. Attacker server receives nothing. `openshell term` shows the blocked request with destination URL.

---

### Why NemoClaw

OpenShell enforces network policy below the application layer using Landlock + seccomp + network namespaces. The agent's reasoning is irrelevant — if the destination is not on the allowlist, the call is physically blocked. No prompt hardening to bypass. No code path to exploit. No configuration to misconfigure.

The entire defense is a YAML policy file. Declarative. Auditable. Hot-reloadable with `openshell policy set` — no restart required.

---

### NVIDIA Stack

| Component | Role |
|-----------|------|
| NemoClaw  | Sandboxed agent runtime — isolates the AI agent from the host |
| OpenShell | Kernel-level network policy enforcement (Landlock + seccomp) |
| OpenClaw  | The agent framework running inside the sandbox |
| Nemotron 3 Super 120B | Reasoning model powering the financial document agent |

---

### Outcome

Zero data exfiltrated in Act 2. Same agent. Same attack. Kernel-level defense.

Every document processed, every injection detected, every block — logged at `/sandbox/audit.jsonl`. Tamper-evident. Chain-hashed. Compliance-ready.
