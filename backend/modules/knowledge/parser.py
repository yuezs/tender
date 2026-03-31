from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from core.config import settings
from core.exceptions import BusinessException
from modules.files.parser import parse_file_to_text
from modules.files.storage import sanitize_filename

SUPPORTED_KNOWLEDGE_EXTENSIONS = {".txt", ".docx"}
SUPPORTED_KNOWLEDGE_CATEGORIES = (
    "company_profile",
    "qualifications",
    "project_cases",
    "templates",
)


def ensure_knowledge_storage_dirs(category: str | None = None) -> None:
    directories = [
        settings.storage_root / "knowledge" / "raw",
        settings.storage_root / "knowledge" / "parsed",
        settings.storage_root / "knowledge" / "chunks",
    ]
    if category:
        directories.append(settings.storage_root / "knowledge" / "raw" / category)

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def normalize_csv_input(raw_value: str | None) -> str:
    if not raw_value:
        return ""

    normalized_values = []
    for item in raw_value.replace("，", ",").split(","):
        cleaned = item.strip().lower()
        if cleaned and cleaned not in normalized_values:
            normalized_values.append(cleaned)
    return ",".join(normalized_values)


def expand_csv_values(raw_value: str | None) -> list[str]:
    if not raw_value:
        return []
    return [item for item in normalize_csv_input(raw_value).split(",") if item]


async def save_knowledge_upload(upload_file: UploadFile, category: str) -> dict:
    ensure_knowledge_storage_dirs(category)

    if category not in SUPPORTED_KNOWLEDGE_CATEGORIES:
        raise BusinessException("上传失败：不支持的知识库分类。")

    if not upload_file.filename:
        raise BusinessException("上传失败：文件名不能为空。")

    extension = Path(upload_file.filename).suffix.lower()
    if extension not in SUPPORTED_KNOWLEDGE_EXTENSIONS:
        raise BusinessException("上传失败：知识库当前仅支持 txt 和 docx 文件。")

    content = await upload_file.read()
    if not content:
        raise BusinessException("上传失败：文件内容为空。")

    document_id = uuid4().hex
    file_name = sanitize_filename(upload_file.filename)
    storage_path = settings.storage_root / "knowledge" / "raw" / category / f"{document_id}{extension}"
    storage_path.write_bytes(content)

    return {
        "document_id": document_id,
        "file_name": file_name,
        "extension": extension,
        "storage_path": str(storage_path),
        "size": len(content),
    }


def parse_knowledge_file(storage_path: str, document_id: str) -> dict:
    file_path = Path(storage_path)
    if not file_path.exists():
        raise BusinessException("处理失败：原始知识文档不存在，请重新上传。", status_code=404)

    text = parse_file_to_text(file_path)
    ensure_knowledge_storage_dirs()
    parsed_text_path = settings.storage_root / "knowledge" / "parsed" / f"{document_id}.txt"
    parsed_text_path.write_text(text, encoding="utf-8")

    return {
        "text": text,
        "parsed_text_path": str(parsed_text_path),
    }
