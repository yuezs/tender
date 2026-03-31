import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT / "backend"
OPENCLAW_DIR = BACKEND_DIR / "openclaw_agents"

OPENCLAW_COMMAND = "openclaw.ps1" if os.name == "nt" else "openclaw"
MODEL = "openai-codex/gpt-5.4"
AGENTS = {
    "tender-extract": OPENCLAW_DIR / "extract",
    "tender-judge": OPENCLAW_DIR / "judge",
    "tender-generate": OPENCLAW_DIR / "generate",
}


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    if command and command[0].endswith(".ps1"):
        command_path = _resolve_command_path(command[0])
        command = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            command_path,
            *command[1:],
        ]
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def _resolve_command_path(command: str) -> str:
    resolved = shutil.which(command)
    if resolved:
        return resolved

    if command.endswith(".ps1"):
        result = subprocess.run(
            ["where.exe", command],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                candidate = line.strip()
                if candidate:
                    return candidate

    return command


def list_agents() -> str:
    result = run_command([OPENCLAW_COMMAND, "agents", "list"])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "failed to list OpenClaw agents")
    return result.stdout


def add_agent(name: str, workspace: Path) -> None:
    result = run_command(
        [
            OPENCLAW_COMMAND,
            "agents",
            "add",
            name,
            "--workspace",
            str(workspace),
            "--model",
            MODEL,
            "--non-interactive",
            "--json",
        ]
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"failed to add agent {name}")


def main() -> int:
    current_agents = list_agents()

    for name, workspace in AGENTS.items():
        workspace.mkdir(parents=True, exist_ok=True)
        if f"- {name}" in current_agents:
            print(f"[skip] {name} already exists")
            continue
        add_agent(name, workspace)
        print(f"[ok] created {name} -> {workspace}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"[error] {exc}", file=sys.stderr)
        raise SystemExit(1)
