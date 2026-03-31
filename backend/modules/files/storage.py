import re
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from core.config import settings
from core.exceptions import BusinessException

SUPPORTED_UPLOAD_EXTENSIONS = {".txt", ".docx", ".pdf"}
SUPPORTED_PARSE_EXTENSIONS = {".txt", ".docx"}


def ensure_tender_storage_dirs() -> None:
    directories = [
        settings.storage_root / "tender" / "raw",
        settings.storage_root / "tender" / "parsed",
        settings.storage_root / "tender" / "records",
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def sanitize_filename(file_name: str) -> str:
    name = Path(file_name).name.strip()
    name = re.sub(r"[^\w.\-\u4e00-\u9fff]+", "_", name)
    return name or "uploaded_file"


async def save_upload_file(upload_file: UploadFile) -> dict:
    ensure_tender_storage_dirs()

    if not upload_file.filename:
        raise BusinessException("上传失败：文件名不能为空。")

    extension = Path(upload_file.filename).suffix.lower()
    if extension not in SUPPORTED_UPLOAD_EXTENSIONS:
        raise BusinessException("上传失败：当前仅支持 txt、docx、pdf 文件。")

    content = await upload_file.read()
    if not content:
        raise BusinessException("上传失败：文件内容为空。")

    file_id = uuid4().hex
    sanitized_name = sanitize_filename(upload_file.filename)
    stored_file_name = f"{file_id}{extension}"
    stored_path = settings.storage_root / "tender" / "raw" / stored_file_name
    stored_path.write_bytes(content)

    return {
        "file_id": file_id,
        "file_name": sanitized_name,
        "extension": extension,
        "storage_path": str(stored_path),
        "size": len(content),
    }


def build_parsed_text_path(file_id: str) -> Path:
    ensure_tender_storage_dirs()
    return settings.storage_root / "tender" / "parsed" / f"{file_id}.txt"
