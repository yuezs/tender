import json
import shutil
from pathlib import Path
from typing import Any

from core.config import settings


class AgentRunArtifactService:
    STEPS = {"extract", "judge", "generate"}
    SECTION_STEP_PREFIX = "generate-section-"

    def __init__(self) -> None:
        self.root_dir = settings.storage_root / "tender" / "agent_runs"
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def build_paths(self, file_id: str, step: str) -> dict[str, str]:
        step_dir = self._get_step_dir(file_id, step)
        return {
            "input": str(step_dir / "input.json"),
            "status": str(step_dir / "status.json"),
            "output": str(step_dir / "output.json"),
        }

    def reset_step(self, file_id: str, step: str) -> dict[str, str]:
        step_dir = self._get_step_dir(file_id, step)
        if step_dir.exists():
            shutil.rmtree(step_dir)
        step_dir.mkdir(parents=True, exist_ok=True)
        return self.build_paths(file_id, step)

    def write_input(self, file_id: str, step: str, payload: dict[str, Any]) -> None:
        self._write_json(self._get_step_dir(file_id, step) / "input.json", payload)

    def write_status(self, file_id: str, step: str, payload: dict[str, Any]) -> None:
        self._write_json(self._get_step_dir(file_id, step) / "status.json", payload)

    def write_output(self, file_id: str, step: str, payload: dict[str, Any]) -> None:
        self._write_json(self._get_step_dir(file_id, step) / "output.json", payload)

    def read_input(self, file_id: str, step: str) -> dict[str, Any]:
        return self._read_json(self._get_step_dir(file_id, step) / "input.json")

    def read_status(self, file_id: str, step: str) -> dict[str, Any]:
        return self._read_json(self._get_step_dir(file_id, step) / "status.json")

    def read_output(self, file_id: str, step: str) -> dict[str, Any]:
        return self._read_json(self._get_step_dir(file_id, step) / "output.json")

    def has_reusable_output(self, file_id: str, step: str) -> bool:
        status = self.read_status(file_id, step)
        if status.get("state") != "success":
            return False
        output = self.read_output(file_id, step)
        return self.is_output_complete(output)

    def is_output_complete(self, payload: dict[str, Any]) -> bool:
        if not isinstance(payload, dict):
            return False
        return all(key in payload for key in {"raw_text", "parsed_result", "debug"})

    def _get_step_dir(self, file_id: str, step: str) -> Path:
        normalized_step = step.strip().lower()
        if not self._is_supported_step(normalized_step):
            raise ValueError(f"Unsupported agent step: {step}")
        step_dir = self.root_dir / file_id / normalized_step
        step_dir.mkdir(parents=True, exist_ok=True)
        return step_dir

    def _is_supported_step(self, step: str) -> bool:
        return step in self.STEPS or step.startswith(self.SECTION_STEP_PREFIX)

    def _read_json(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return payload if isinstance(payload, dict) else {}

    def _write_json(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
