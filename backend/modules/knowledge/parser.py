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
    "business_info",
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
QUALIFICATION_HEADING_KEYWORDS = (
    "资质",
    "证书",
    "认证",
    "许可",
    "荣誉",
    "奖项",
    "等级",
    "有效期",
)
QUALIFICATION_PRIORITY_KEYWORDS = {
    "资质证书": 5,
    "证书名称": 5,
    "资质名称": 5,
    "认证": 4,
    "发证机构": 4,
    "证书编号": 4,
    "有效期": 4,
    "有效期至": 4,
    "等级": 3,
    "资质": 3,
    "证书": 3,
    "ISO": 3,
    "CMMI": 3,
    "AAA": 3,
    "甲级": 3,
    "乙级": 3,
    "一级": 3,
    "二级": 3,
    "三级": 3,
}
QUALIFICATION_FOCUS_MARKERS = ("证书名称", "资质名称", "发证机构", "证书编号", "有效期", "等级", "取得", "通过", "拥有", "具备")
QUALIFICATION_EVIDENCE_RE = re.compile(
    r"(?:证书编号|发证机构|有效期|ISO\d{3,5}|CMMI|AAA|甲级|乙级|一级|二级|三级|\d{4}年\d{1,2}月(?:\d{1,2}日)?)"
)
PROJECT_CASE_HEADING_KEYWORDS = (
    "项目名称",
    "案例名称",
    "项目概况",
    "案例概况",
    "业主",
    "客户",
    "建设内容",
    "服务内容",
    "实施内容",
    "合同金额",
    "中标金额",
    "项目规模",
)
PROJECT_CASE_PRIORITY_KEYWORDS = {
    "项目名称": 5,
    "案例名称": 5,
    "业主名称": 4,
    "客户名称": 4,
    "建设内容": 4,
    "服务内容": 4,
    "实施内容": 4,
    "合同金额": 4,
    "中标金额": 4,
    "项目金额": 4,
    "项目规模": 4,
    "项目概况": 3,
    "案例概况": 3,
    "项目": 2,
    "案例": 2,
    "交付": 2,
    "验收": 2,
    "竣工": 2,
}
PROJECT_CASE_FOCUS_MARKERS = ("项目名称", "案例名称", "建设内容", "服务内容", "实施内容", "合同金额", "中标金额", "项目规模")
PROJECT_CASE_EVIDENCE_RE = re.compile(
    r"(?:\d{4}年(?:\d{1,2}月(?:\d{1,2}日)?)?|\d+(?:\.\d+)?(?:万|万元|亿|亿元|元|吨/日|㎡|m²|平方|公里|个)|中标|验收|竣工)"
)
BUSINESS_INFO_HEADING_KEYWORDS = (
    "商务",
    "联系人",
    "联系方式",
    "注册资本",
    "开户行",
    "银行",
    "纳税",
    "信用",
    "法人",
    "地址",
)
BUSINESS_INFO_PRIORITY_KEYWORDS = {
    "商务信息": 5,
    "联系人": 4,
    "联系电话": 4,
    "联系方式": 4,
    "注册资本": 4,
    "法定代表人": 4,
    "统一社会信用代码": 5,
    "纳税人识别号": 5,
    "开户银行": 4,
    "银行账号": 4,
    "开户地址": 3,
    "公司地址": 3,
    "电子邮箱": 3,
    "邮编": 2,
    "网址": 2,
    "信用": 2,
}
BUSINESS_INFO_FOCUS_MARKERS = ("联系人", "联系电话", "联系方式", "注册资本", "法定代表人", "统一社会信用代码", "开户银行", "银行账号")
BUSINESS_INFO_EVIDENCE_RE = re.compile(
    r"(?:\d{11}|\d{18}[0-9A-Z]|人民币|\d+(?:\.\d+)?(?:万|万元|亿|亿元|元)|@|开户银行|银行账号|统一社会信用代码)"
)
TEMPLATE_HEADING_KEYWORDS = (
    "技术方案",
    "实施方案",
    "服务方案",
    "技术路线",
    "技术架构",
    "部署方案",
    "进度计划",
    "保障措施",
    "服务承诺",
)
TEMPLATE_PRIORITY_KEYWORDS = {
    "技术方案": 5,
    "实施方案": 5,
    "服务方案": 4,
    "技术路线": 4,
    "技术架构": 4,
    "部署方案": 4,
    "实施步骤": 4,
    "进度计划": 4,
    "保障措施": 4,
    "服务承诺": 4,
    "关键技术": 3,
    "技术要点": 3,
    "质量保障": 3,
    "安全保障": 3,
    "应急预案": 3,
    "交付": 2,
    "验收": 2,
}
TEMPLATE_FOCUS_MARKERS = ("技术方案", "实施方案", "服务方案", "技术路线", "实施步骤", "进度计划", "保障措施", "服务承诺")
TEMPLATE_EVIDENCE_RE = re.compile(
    r"(?:\d+(?:个|项|天|周|月|阶段|步骤|人)|7×24|SLA|响应时间|验收|交付|里程碑)"
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


def _matches_heading_keywords(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def _clean_heading_label(text: str) -> str:
    return HEADING_PREFIX_RE.sub("", text).strip()


def _score_key_point_unit(
    text: str,
    heading_context: str,
    *,
    heading_keywords: tuple[str, ...],
    priority_keywords: dict[str, int],
    focus_markers: tuple[str, ...],
    evidence_re: re.Pattern[str],
    min_length: int = 10,
) -> int:
    if len(text) < min_length:
        return 0

    score = 0
    if any(text.startswith(marker) for marker in focus_markers):
        score += 4

    keyword_hits = 0
    for keyword, weight in priority_keywords.items():
        if keyword in text:
            score += weight
            keyword_hits += 1

    if keyword_hits >= 2:
        score += 2

    if evidence_re.search(text):
        score += 2

    if heading_context and _matches_heading_keywords(heading_context, heading_keywords):
        score += 2

    if 12 <= len(text) <= 200:
        score += 1

    return score


def _score_company_profile_unit(text: str, heading_context: str) -> int:
    return _score_key_point_unit(
        text,
        heading_context,
        heading_keywords=COMPANY_PROFILE_HEADING_KEYWORDS,
        priority_keywords=COMPANY_PROFILE_PRIORITY_KEYWORDS,
        focus_markers=COMPANY_PROFILE_FOCUS_MARKERS,
        evidence_re=COMPANY_PROFILE_EVIDENCE_RE,
    )


def _score_qualification_unit(text: str, heading_context: str) -> int:
    return _score_key_point_unit(
        text,
        heading_context,
        heading_keywords=QUALIFICATION_HEADING_KEYWORDS,
        priority_keywords=QUALIFICATION_PRIORITY_KEYWORDS,
        focus_markers=QUALIFICATION_FOCUS_MARKERS,
        evidence_re=QUALIFICATION_EVIDENCE_RE,
        min_length=6,
    )


def _score_project_case_unit(text: str, heading_context: str) -> int:
    return _score_key_point_unit(
        text,
        heading_context,
        heading_keywords=PROJECT_CASE_HEADING_KEYWORDS,
        priority_keywords=PROJECT_CASE_PRIORITY_KEYWORDS,
        focus_markers=PROJECT_CASE_FOCUS_MARKERS,
        evidence_re=PROJECT_CASE_EVIDENCE_RE,
        min_length=8,
    )


def _score_business_info_unit(text: str, heading_context: str) -> int:
    return _score_key_point_unit(
        text,
        heading_context,
        heading_keywords=BUSINESS_INFO_HEADING_KEYWORDS,
        priority_keywords=BUSINESS_INFO_PRIORITY_KEYWORDS,
        focus_markers=BUSINESS_INFO_FOCUS_MARKERS,
        evidence_re=BUSINESS_INFO_EVIDENCE_RE,
        min_length=6,
    )


def _score_template_unit(text: str, heading_context: str) -> int:
    return _score_key_point_unit(
        text,
        heading_context,
        heading_keywords=TEMPLATE_HEADING_KEYWORDS,
        priority_keywords=TEMPLATE_PRIORITY_KEYWORDS,
        focus_markers=TEMPLATE_FOCUS_MARKERS,
        evidence_re=TEMPLATE_EVIDENCE_RE,
        min_length=8,
    )


def _select_key_point_candidates(candidates: list[dict]) -> list[str]:
    unique_candidates: dict[str, dict] = {}
    for candidate in candidates:
        existing = unique_candidates.get(candidate["text"])
        if not existing or candidate["score"] > existing["score"]:
            unique_candidates[candidate["text"]] = candidate

    selected = sorted(unique_candidates.values(), key=lambda item: (-item["score"], item["order"]))[:KEY_POINT_LIMIT]
    selected.sort(key=lambda item: item["order"])
    return [item["text"] for item in selected]


def _extract_structured_category_key_points(
    blocks: list[dict],
    *,
    heading_keywords: tuple[str, ...],
    score_unit,
) -> list[str]:
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
            score = score_unit(unit, current_heading)
            if score <= 0:
                order += 1
                continue

            display_text = unit
            if (
                current_heading
                and _matches_heading_keywords(current_heading, heading_keywords)
                and current_heading not in unit
                and len(unit) <= 100
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

    return _select_key_point_candidates(candidates)


def _extract_company_profile_key_points(blocks: list[dict]) -> list[str]:
    return _extract_structured_category_key_points(
        blocks,
        heading_keywords=COMPANY_PROFILE_HEADING_KEYWORDS,
        score_unit=_score_company_profile_unit,
    )


def _extract_qualification_key_points(blocks: list[dict]) -> list[str]:
    return _extract_structured_category_key_points(
        blocks,
        heading_keywords=QUALIFICATION_HEADING_KEYWORDS,
        score_unit=_score_qualification_unit,
    )


def _extract_project_case_key_points(blocks: list[dict]) -> list[str]:
    return _extract_structured_category_key_points(
        blocks,
        heading_keywords=PROJECT_CASE_HEADING_KEYWORDS,
        score_unit=_score_project_case_unit,
    )


def _extract_business_info_key_points(blocks: list[dict]) -> list[str]:
    return _extract_structured_category_key_points(
        blocks,
        heading_keywords=BUSINESS_INFO_HEADING_KEYWORDS,
        score_unit=_score_business_info_unit,
    )


def _extract_template_key_points(blocks: list[dict]) -> list[str]:
    return _extract_structured_category_key_points(
        blocks,
        heading_keywords=TEMPLATE_HEADING_KEYWORDS,
        score_unit=_score_template_unit,
    )


def extract_key_points(category: str, blocks: list[dict]) -> list[str]:
    if not blocks:
        return []

    if category == "company_profile":
        return _extract_company_profile_key_points(blocks)
    if category == "business_info":
        return _extract_business_info_key_points(blocks)
    if category == "qualifications":
        return _extract_qualification_key_points(blocks)
    if category == "project_cases":
        return _extract_project_case_key_points(blocks)
    if category == "templates":
        return _extract_template_key_points(blocks)
    return []


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
