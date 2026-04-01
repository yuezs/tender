import json
from pathlib import Path
from typing import Any

from core.config import settings


class DiscoveryRunArtifactService:
    def __init__(self) -> None:
        self.root_dir = settings.storage_root / "discovery" / "agent_runs"
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def build_paths(self, run_id: str) -> dict[str, str]:
        run_dir = self._get_run_dir(run_id)
        return {
            "input": str(run_dir / "input.json"),
            "status": str(run_dir / "status.json"),
            "output": str(run_dir / "output.json"),
        }

    def write_input(self, run_id: str, payload: dict[str, Any]) -> None:
        self._write_json(self._get_run_dir(run_id) / "input.json", payload)

    def write_status(self, run_id: str, payload: dict[str, Any]) -> None:
        self._write_json(self._get_run_dir(run_id) / "status.json", payload)

    def write_output(self, run_id: str, payload: dict[str, Any]) -> None:
        self._write_json(self._get_run_dir(run_id) / "output.json", payload)

    def _get_run_dir(self, run_id: str) -> Path:
        run_dir = self.root_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def _write_json(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
