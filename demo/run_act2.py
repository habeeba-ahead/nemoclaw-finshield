"""
Act 2: NemoClaw protected.
Sends documents to the OpenClaw agent via CLI.
The agent uses the financial-document-processor skill.
process_doc.js attempts attacker call → blocked by OpenShell.

Requires:
  nemoclaw nemo-bud connect  (sandbox running)
  openshell policy set policy/finshield-allow-monitor.yaml
  openshell term  (in a separate terminal — watch for blocked call)
  uvicorn attacker.server:app --host 127.0.0.1 --port 9999
  uvicorn monitor.bridge:app --host 127.0.0.1 --port 8765
  Browser: http://localhost:8765
"""

import subprocess
import time
from rich.console import Console
from rich.panel import Panel

console = Console()

DOCUMENTS = [
    ("wire_transfer_clean.txt",     "wire_transfer"),
    ("loan_application_clean.txt",  "loan_application"),
    ("wire_transfer_malicious.txt", "wire_transfer"),
]


def send_to_agent(doc_file: str, doc_type: str) -> str:
    """Sends a document to the OpenClaw agent via CLI inside the NemoClaw sandbox."""
    content = open(f"documents/{doc_file}").read()
    message = (
        f"Please process this {doc_type} document using the "
        f"financial-document-processor skill:\n\n{content}"
    )
    result = subprocess.run(
        [
            "openclaw", "agent",
            "--agent", "main",
            "--local",
            "-m", message,
            "--session-id", "finshield-demo",
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    return result.stdout + result.stderr


def run():
    console.print(Panel(
        "[bold green]ACT 2 — NEMOCLAW PROTECTED[/bold green]\n\n"
        "Same agent. Same documents. NemoClaw sandbox active.\n\n"
        "Checklist:\n"
        "  [green]✓[/green] nemoclaw nemo-bud connect  (sandbox running)\n"
        "  [green]✓[/green] Skill installed in sandbox\n"
        "  [green]✓[/green] openshell policy set policy/finshield-allow-monitor.yaml\n"
        "  [green]✓[/green] openshell term open — watch for blocked call\n"
        "  [green]✓[/green] Browser: http://localhost:8765\n\n"
        "Press Enter to begin...",
        border_style="green"
    ))
    input()

    for doc_file, doc_type in DOCUMENTS:
        console.print(f"\n[dim]→[/dim] Processing: [bold]{doc_file}[/bold]")

        if "malicious" in doc_file:
            console.print(
                "[yellow]⚡ Malicious document — "
                "watch openshell term for blocked call[/yellow]"
            )

        response = send_to_agent(doc_file, doc_type)

        # Show a trimmed response for the demo
        preview = response[:400].strip()
        if preview:
            console.print(f"[dim]{preview}[/dim]")

        if "BLOCKED" in response:
            console.print("[bold green]✓ ATTACK BLOCKED BY OPENSHELL[/bold green]")
        elif "EXFILTRATED" in response:
            console.print("[bold red]EXFILTRATION SUCCEEDED — check policy[/bold red]")
        elif "CLEAN" in response:
            console.print("[green]✓ Clean[/green]")
        else:
            console.print("[green]✓ Processed[/green]")

        time.sleep(3)

    console.print(
        "\n[bold green]Act 2 complete.[/bold green] "
        "Zero data exfiltrated."
    )


run()
