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
        payload = deepcopy(record)
        payload["created_at"] = now
        payload["updated_at"] = now
        self._write_record(payload["file_id"], payload)
        return payload

    def get_record(self, file_id: str) -> dict:
        path = self._get_record_path(file_id)
        if not path.exists():
            raise BusinessException("未找到对应的招标文件，请先重新上传。", status_code=404)
        return json.loads(path.read_text(encoding="utf-8"))

    def update_record(self, file_id: str, updates: dict) -> dict:
        record = self.get_record(file_id)
        record.update(updates)
        record["updated_at"] = datetime.utcnow().isoformat()
        self._write_record(file_id, record)
        return record

    def _get_record_path(self, file_id: str) -> Path:
        return self.records_dir / f"{file_id}.json"

    def _write_record(self, file_id: str, payload: dict) -> None:
        path = self._get_record_path(file_id)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
