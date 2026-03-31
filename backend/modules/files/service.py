from pathlib import Path

from fastapi import UploadFile

from core.exceptions import BusinessException
from modules.files.parser import parse_file_to_text
from modules.files.storage import build_parsed_text_path, save_upload_file


class FileService:
    def ping(self) -> dict:
        return {"module": "files", "status": "ready"}

    async def save_tender_file(self, upload_file: UploadFile) -> dict:
        return await save_upload_file(upload_file)

    def parse_tender_file(self, file_id: str, storage_path: str) -> dict:
        file_path = Path(storage_path)
        if not file_path.exists():
            raise BusinessException("解析失败：原始文件不存在，请重新上传。", status_code=404)
        text = parse_file_to_text(file_path)
        parsed_path = build_parsed_text_path(file_id)
        parsed_path.write_text(text, encoding="utf-8")

        return {
            "text": text,
            "text_path": str(parsed_path),
            "text_preview": text[:500],
        }
