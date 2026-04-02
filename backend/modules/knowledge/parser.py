import re
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from core.config import settings
from core.exceptions import BusinessException
from modules.files.parser import blocks_to_text, parse_file_to_blocks
from modules.files.storage import sanitize_filename

SUPPORTED_KNOWLEDGE_EXTENSIONS = {".txt", ".docx"}
SUPPORTED_KNOWLEDGE_CATEGORIES = (
    "company_profile",
    "qualifications",
    "project_cases",
    "templates",
)

CSV_SPLIT_RE = re.compile(r"[,，]+")
KEY_POINT_SPLIT_RE = re.compile(r"(?<=[。！？；;])\s*")
KEY_POINT_LIMIT = 5
COMPANY_PROFILE_HEADING_KEYWORDS = (
    "核心能力",
    "服务优势",
    "主营业务",
    "服务范围",
    "技术研发",
    "研发能力",
    "项目实施",
    "实施能力",
    "运营运维",
    "运维能力",
    "资质",
    "团队",
)
COMPANY_PROFILE_PRIORITY_KEYWORDS = {
    "核心能力": 5,
    "服务优势": 5,
    "主营业务": 4,
    "服务范围": 4,
    "技术研发": 4,
    "研发能力": 4,
    "自主研发": 4,
    "项目实施": 4,
    "实施能力": 4,
    "运营运维": 4,
    "运维能力": 4,
    "一体化交付": 4,
    "资质": 3,
    "证书": 3,
    "专利": 3,
    "团队": 3,
    "人员": 2,
    "方案": 2,
    "交付": 2,
    "达标": 2,
    "标准": 2,
    "经验": 2,
    "优势": 2,
}
COMPANY_PROFILE_FOCUS_MARKERS = ("一是", "二是", "三是", "四是", "五是", "首先", "其次", "再次", "最后", "另外", "此外")
COMPANY_PROFILE_EVIDENCE_RE = re.compile(
    r"(?:\d+(?:项|人|个|套|类|年|天|%)|GB\d{4,}-\d+|一级A|一级|二级|三级|甲级|乙级|专利号)"
)
HEADING_PREFIX_RE = re.compile(
    r"^\s*(?:第[一二三四五六七八九十百千万0-9]+(?:章|节|部分|篇)|"
    r"\d+(?:\.\d+){0,5}[、.．]?|"
    r"[一二三四五六七八九十百千万]+[、.．]|"
    r"[（(][一二三四五六七八九十百千万0-9]+[）)])\s*"
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

    normalized_values: list[str] = []
    for item in CSV_SPLIT_RE.split(raw_value):
        cleaned = item.strip().lower()
        if cleaned and cleaned not in normalized_values:
            normalized_values.append(cleaned)
    return ",".join(normalized_values)


def expand_csv_values(raw_value: str | None) -> list[str]:
    if not raw_value:
        return []
    return [item for item in normalize_csv_input(raw_value).split(",") if item]


def normalize_parsed_text(raw_text: str) -> str:
    normalized_lines: list[str] = []
    blank_pending = False
    for raw_line in raw_text.splitlines():
        line = raw_line.strip()
        if line:
            normalized_lines.append(line)
            blank_pending = False
            continue
        if normalized_lines and not blank_pending:
            normalized_lines.append("")
            blank_pending = True
    return "\n".join(normalized_lines).strip()


def build_parse_summary(text: str, blocks: list[dict]) -> dict:
    summary = {
        "block_count": len(blocks),
        "heading_count": 0,
        "paragraph_count": 0,
        "list_item_count": 0,
        "table_row_count": 0,
        "character_count": len(text),
        "line_count": len([line for line in text.splitlines() if line.strip()]),
    }

    for block in blocks:
        kind = str(block.get("kind", "paragraph")).strip()
        if kind == "heading":
            summary["heading_count"] += 1
        elif kind == "list_item":
            summary["list_item_count"] += 1
        elif kind == "table_row":
            summary["table_row_count"] += 1
        else:
            summary["paragraph_count"] += 1

    return summary


def build_parse_warnings(text: str, blocks: list[dict], summary: dict) -> list[str]:
    warnings: list[str] = []
    if not text.strip():
        warnings.append("No readable text extracted.")
    if summary["character_count"] < 80:
        warnings.append("Very little text was extracted from this file.")
    if summary["heading_count"] == 0:
        warnings.append("No heading structure detected.")
    if summary["table_row_count"] == 0:
        warnings.append("No table rows detected.")
    if len(blocks) <= 2:
        warnings.append("Document structure looks shallow; review chunk preview after processing.")
    return warnings


def _split_key_point_units(text: str) -> list[str]:
    normalized = normalize_parsed_text(text)
    if not normalized:
        return []

    units: list[str] = []
    for raw_line in normalized.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = [item.strip() for item in KEY_POINT_SPLIT_RE.split(line) if item.strip()]
        units.extend(parts or [line])
    return units


def _is_company_profile_heading(text: str) -> bool:
    return any(keyword in text for keyword in COMPANY_PROFILE_HEADING_KEYWORDS)


def _clean_heading_label(text: str) -> str:
    return HEADING_PREFIX_RE.sub("", text).strip()


def _score_company_profile_unit(text: str, heading_context: str) -> int:
    if len(text) < 10:
        return 0

    score = 0
    if any(text.startswith(marker) for marker in COMPANY_PROFILE_FOCUS_MARKERS):
        score += 4

    keyword_hits = 0
    for keyword, weight in COMPANY_PROFILE_PRIORITY_KEYWORDS.items():
        if keyword in text:
            score += weight
            keyword_hits += 1

    if keyword_hits >= 2:
        score += 2

    if COMPANY_PROFILE_EVIDENCE_RE.search(text):
        score += 2

    if heading_context and _is_company_profile_heading(heading_context):
        score += 2

    if 16 <= len(text) <= 180:
        score += 1

    return score


def extract_key_points(category: str, blocks: list[dict]) -> list[str]:
    if category != "company_profile" or not blocks:
        return []

    candidates: list[dict] = []
    current_heading = ""
    order = 0

    for block in blocks:
        kind = str(block.get("kind", "paragraph")).strip()
        text = str(block.get("text", "")).strip()
        if not text:
            continue

        if kind == "heading":
            current_heading = text
            continue

        if kind not in {"paragraph", "list_item", "table_row"}:
            continue

        for unit in _split_key_point_units(text):
            score = _score_company_profile_unit(unit, current_heading)
            if score <= 0:
                order += 1
                continue

            display_text = unit
            if (
                current_heading
                and _is_company_profile_heading(current_heading)
                and current_heading not in unit
                and len(unit) <= 80
            ):
                heading_label = _clean_heading_label(current_heading) or current_heading
                display_text = f"{heading_label}：{unit}"

            candidates.append(
                {
                    "text": display_text,
                    "score": score,
                    "order": order,
                }
            )
            order += 1

    unique_candidates: dict[str, dict] = {}
    for candidate in candidates:
        existing = unique_candidates.get(candidate["text"])
        if not existing or candidate["score"] > existing["score"]:
            unique_candidates[candidate["text"]] = candidate

    selected = sorted(unique_candidates.values(), key=lambda item: (-item["score"], item["order"]))[:KEY_POINT_LIMIT]
    selected.sort(key=lambda item: item["order"])
    return [item["text"] for item in selected]


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


def parse_knowledge_file(storage_path: str, document_id: str, category: str = "") -> dict:
    file_path = Path(storage_path)
    if not file_path.exists():
        raise BusinessException("处理失败：原始知识文档不存在，请重新上传。", status_code=404)

    blocks = parse_file_to_blocks(file_path)
    text = normalize_parsed_text(blocks_to_text(blocks))
    if not text:
        raise BusinessException("处理失败：文档中未提取到可用文本。")

    ensure_knowledge_storage_dirs()
    parsed_text_path = settings.storage_root / "knowledge" / "parsed" / f"{document_id}.txt"
    parsed_text_path.write_text(text, encoding="utf-8")

    parse_summary = build_parse_summary(text, blocks)
    warnings = build_parse_warnings(text, blocks, parse_summary)
    key_points = extract_key_points(category, blocks)

    return {
        "text": text,
        "blocks": blocks,
        "parsed_text_path": str(parsed_text_path),
        "parse_summary": parse_summary,
        "warnings": warnings,
        "key_points": key_points,
    }
