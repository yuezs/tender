import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path

from core.config import settings
from core.exceptions import BusinessException


class TenderRepository:
    def __init__(self) -> None:
        self.records_dir = settings.storage_root / "tender" / "records"
        self.records_dir.mkdir(parents=True, exist_ok=True)

    def is_ready(self) -> bool:
        return self.records_dir.exists()

    def create_record(self, record: dict) -> dict:
        now = datetime.utcnow().isoformat()
        payload = self._ensure_default_fields(deepcopy(record))
        payload["created_at"] = now
        payload["updated_at"] = now
        self._write_record(payload["file_id"], payload)
        return payload

    def get_record(self, file_id: str) -> dict:
        path = self._get_record_path(file_id)
        if not path.exists():
            raise BusinessException("未找到对应的招标文件，请先重新上传。", status_code=404)
        record = json.loads(path.read_text(encoding="utf-8"))
        return self._ensure_default_fields(record)

    def get_latest_record(self) -> dict:
        records = self.list_records(limit=1)
        if not records:
            raise BusinessException("暂无可用的招标处理结果。", status_code=404)
        return records[0]

    def update_record(self, file_id: str, updates: dict) -> dict:
        record = self.get_record(file_id)
        record.update(updates)
        record = self._ensure_default_fields(record)
        record["updated_at"] = datetime.utcnow().isoformat()
        self._write_record(file_id, record)
        return record

    def find_record_by_document_id(self, document_id: str) -> dict:
        target_id = str(document_id).strip()
        if not target_id:
            raise BusinessException("缺少文档标识。", status_code=400)

        for path in sorted(self.records_dir.glob("*.json")):
            record = json.loads(path.read_text(encoding="utf-8"))
            generate_document = record.get("generate_document") or {}
            fulltext_document = record.get("fulltext_document") or {}
            if (
                str(generate_document.get("document_id", "")).strip() == target_id
                or str(fulltext_document.get("document_id", "")).strip() == target_id
            ):
                return self._ensure_default_fields(record)

        raise BusinessException("未找到对应的标书文档，请重新生成。", status_code=404)

    def list_records(self, limit: int | None = None) -> list[dict]:
        records: list[dict] = []
        for path in sorted(self.records_dir.glob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(payload, dict):
                records.append(self._ensure_default_fields(payload))

        records.sort(
            key=lambda item: (
                str(item.get("updated_at", "")),
                str(item.get("created_at", "")),
            ),
            reverse=True,
        )
        if limit is None:
            return records
        return records[:limit]

    def _ensure_default_fields(self, record: dict) -> dict:
        agent_artifacts = deepcopy(record.get("agent_artifacts") or {})
        for step in ("extract", "judge", "generate"):
            agent_artifacts.setdefault(step, {})
        record["agent_artifacts"] = agent_artifacts
        for field in ("parse_error", "extract_error", "judge_error", "generate_error", "text_preview"):
            record.setdefault(field, "")
        record.setdefault("generate_document", {})
        record.setdefault("fulltext_document", {})
        return record

    def _get_record_path(self, file_id: str) -> Path:
        return self.records_dir / f"{file_id}.json"

    def _write_record(self, file_id: str, payload: dict) -> None:
        path = self._get_record_path(file_id)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
