import math
import re
from pathlib import Path

from docx import Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph

from core.exceptions import BusinessException

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - dependency is declared in requirements
    PdfReader = None


HEADING_STYLE_PREFIXES = ("heading", "标题")
LIST_STYLE_KEYWORDS = ("list", "bullet", "编号", "列表")
SPACE_RE = re.compile(r"[ \t]+")
MAX_HEADING_TEXT_LENGTH = 80
LONG_PARAGRAPH_THRESHOLD = 180
HIERARCHICAL_HEADING_RE = re.compile(r"^(?P<number>\d+(?:\.\d+){1,5})\s*[、.)．-]?\s*(?P<title>\S.*)$")
NUMBERED_HEADING_RE = re.compile(r"^(?P<number>\d+)[、.)．-]\s*(?P<title>\S.*)$")
CHINESE_HEADING_RE = re.compile(
    r"^(?P<number>[一二三四五六七八九十百千万]+)[、.)．-]\s*(?P<title>\S.*)$"
)
PAREN_HEADING_RE = re.compile(
    r"^[（(](?P<number>[一二三四五六七八九十百千万0-9]+)[)）]\s*(?P<title>\S.*)$"
)
CHAPTER_HEADING_RE = re.compile(
    r"^第(?P<number>[一二三四五六七八九十百千万0-9]+)(?P<unit>章|节|部分|篇)\s*(?P<title>\S.*)?$"
)
INLINE_HEADING_BOUNDARY_RE = re.compile(
    r"(?P<prefix>[。！；;）)\]】])\s*(?P<heading>"
    r"(?:第[一二三四五六七八九十百千万0-9]+(?:章|节|部分|篇)|"
    r"\d+(?:\.\d+){1,5}|"
    r"\d+[、.)．-]|"
    r"[一二三四五六七八九十百千万]+[、.)．-]|"
    r"[（(][一二三四五六七八九十百千万0-9]+[)）])"
    r"\s*\S.*)"
)
FOCUS_POINT_BOUNDARY_RE = re.compile(
    r"(?P<prefix>[：:])\s*(?P<marker>(?:一是|二是|三是|首先|其次|再次|最后|另外|此外))"
)
PARAGRAPH_BREAK_RE = re.compile(r"(?<=[。！；;])\s*")
CLAUSE_BREAK_RE = re.compile(r"(?<=[：:，,])\s*")

PDF_MIN_EFFECTIVE_PAGE_TEXT_CHARS = 40
PDF_MIN_TOTAL_TEXT_CHARS = 200
PDF_MIN_STABLE_TEXT_PAGE_RATIO = 0.6
PDF_MIN_NONEMPTY_TEXT_PAGE_RATIO = 0.75
PDF_REJECTION_MESSAGE = (
    "当前 PDF 疑似扫描件或混合型 PDF，暂仅支持可直接提取文本的 PDF，"
    "请优先上传 txt、docx 或可选中文字的 PDF。"
)


def _normalize_line(raw_text: str) -> str:
    cleaned = (
        raw_text.replace("\u3000", " ")
        .replace("\xa0", " ")
        .replace("\t", " ")
        .replace("\r", "")
        .strip()
    )
    cleaned = (
        cleaned.replace("•", "- ")
        .replace("●", "- ")
        .replace("·", "- ")
        .replace("■", "- ")
    )
    cleaned = SPACE_RE.sub(" ", cleaned)
    return cleaned.strip()


def _normalize_multiline_text(raw_text: str) -> str:
    normalized_lines: list[str] = []
    blank_count = 0
    for raw_line in raw_text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = _normalize_line(raw_line)
        if line:
            normalized_lines.append(line)
            blank_count = 0
            continue
        if normalized_lines and blank_count == 0:
            normalized_lines.append("")
        blank_count += 1
    return "\n".join(normalized_lines).strip()


def _split_long_fragment(text: str) -> list[str]:
    if len(text) <= LONG_PARAGRAPH_THRESHOLD:
        return [text]

    fragments = [item.strip() for item in PARAGRAPH_BREAK_RE.split(text) if item.strip()]
    if len(fragments) == 1:
        fragments = [item.strip() for item in CLAUSE_BREAK_RE.split(text) if item.strip()]

    if len(fragments) <= 1:
        return [text]

    normalized_fragments: list[str] = []
    for fragment in fragments:
        if len(fragment) > LONG_PARAGRAPH_THRESHOLD and fragment != text:
            normalized_fragments.extend(_split_long_fragment(fragment))
        else:
            normalized_fragments.append(fragment)
    return normalized_fragments


def _split_focus_point_fragment(text: str) -> list[str]:
    normalized = FOCUS_POINT_BOUNDARY_RE.sub(r"\g<prefix>\n\g<marker>", text)
    if normalized == text:
        return [text]
    return [_normalize_line(item) for item in normalized.splitlines() if _normalize_line(item)]


def _detect_numbered_heading_level(text: str) -> int:
    if not text or len(text) > MAX_HEADING_TEXT_LENGTH:
        return 0

    if any(marker in text for marker in ("。", "，", "；", "：")):
        return 0

    hierarchical_match = HIERARCHICAL_HEADING_RE.match(text)
    if hierarchical_match:
        return min(hierarchical_match.group("number").count(".") + 1, 6)

    if NUMBERED_HEADING_RE.match(text):
        return 1
    if CHINESE_HEADING_RE.match(text):
        return 1
    if PAREN_HEADING_RE.match(text):
        return 2
    if CHAPTER_HEADING_RE.match(text):
        return 1
    return 0


def _paragraph_kind(paragraph: Paragraph, text: str) -> tuple[str, int]:
    style_name = (paragraph.style.name or "").strip().lower() if paragraph.style else ""
    if style_name.startswith(HEADING_STYLE_PREFIXES):
        match = re.search(r"(\d+)", style_name)
        return "heading", int(match.group(1)) if match else 1

    heading_level = _detect_numbered_heading_level(text)
    if heading_level:
        return "heading", heading_level

    paragraph_properties = getattr(paragraph._p, "pPr", None)
    if paragraph_properties is not None and getattr(paragraph_properties, "numPr", None) is not None:
        return "list_item", 0

    if any(keyword in style_name for keyword in LIST_STYLE_KEYWORDS):
        return "list_item", 0
    return "paragraph", 0


def _text_block_kind(text: str) -> tuple[str, int]:
    heading_level = _detect_numbered_heading_level(text)
    if heading_level:
        return "heading", heading_level
    return "paragraph", 0


def _split_paragraph_text(text: str) -> list[str]:
    normalized = _normalize_line(text)
    if not normalized:
        return []

    normalized = INLINE_HEADING_BOUNDARY_RE.sub(r"\g<prefix>\n\g<heading>", normalized)
    fragments: list[str] = []

    for raw_fragment in normalized.splitlines():
        fragment = _normalize_line(raw_fragment)
        if not fragment:
            continue

        for item in _split_focus_point_fragment(fragment):
            if _detect_numbered_heading_level(item):
                fragments.append(item)
                continue
            fragments.extend(_split_long_fragment(item))

    return [fragment for fragment in fragments if fragment]


def _iter_docx_blocks(document) -> list[Paragraph | Table]:
    blocks: list[Paragraph | Table] = []
    for child in document.element.body.iterchildren():
        if isinstance(child, CT_P):
            blocks.append(Paragraph(child, document))
        elif isinstance(child, CT_Tbl):
            blocks.append(Table(child, document))
    return blocks


def _format_table_row(cells: list[str]) -> str:
    if len(cells) == 2:
        return f"{cells[0]}: {cells[1]}"
    return " | ".join(cells)


def _append_text_fragments(blocks: list[dict], text: str) -> None:
    for fragment in _split_paragraph_text(text):
        kind, level = _text_block_kind(fragment)
        blocks.append({"kind": kind, "text": fragment, "level": level})


def parse_text_file(file_path: Path) -> str:
    encodings = ["utf-8-sig", "utf-8", "gb18030"]
    for encoding in encodings:
        try:
            return _normalize_multiline_text(file_path.read_text(encoding=encoding))
        except UnicodeDecodeError:
            continue
    raise BusinessException("解析失败：无法识别 TXT 文件编码，请转为 UTF-8 或 GB18030 后重试。")


def parse_text_file_to_blocks(file_path: Path) -> list[dict]:
    text = parse_text_file(file_path)
    blocks: list[dict] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        _append_text_fragments(blocks, line)
    return blocks


def parse_docx_file_to_blocks(file_path: Path) -> list[dict]:
    try:
        document = Document(str(file_path))
        blocks: list[dict] = []

        for block in _iter_docx_blocks(document):
            if isinstance(block, Paragraph):
                text = _normalize_line(block.text)
                if not text:
                    continue
                paragraph_fragments = _split_paragraph_text(text)
                if len(paragraph_fragments) == 1 and paragraph_fragments[0] == text:
                    kind, level = _paragraph_kind(block, text)
                    blocks.append({"kind": kind, "text": text, "level": level})
                    continue

                for fragment in paragraph_fragments:
                    kind, level = _text_block_kind(fragment)
                    blocks.append({"kind": kind, "text": fragment, "level": level})
                continue

            if isinstance(block, Table):
                for row in block.rows:
                    cells = [_normalize_line(cell.text) for cell in row.cells]
                    cells = [cell for cell in cells if cell]
                    if not cells:
                        continue
                    blocks.append(
                        {
                            "kind": "table_row",
                            "text": _format_table_row(cells),
                            "level": 0,
                        }
                    )

        return blocks
    except Exception as exc:
        raise BusinessException(f"解析失败：DOCX 文件读取异常：{exc}") from exc


def _get_pdf_reader(file_path: Path) -> PdfReader:
    if PdfReader is None:
        raise BusinessException("解析失败：缺少 pypdf 依赖，请先安装后端 requirements。")
    try:
        return PdfReader(str(file_path))
    except Exception as exc:
        raise BusinessException(f"解析失败：PDF 文件读取异常：{exc}") from exc


def _extract_pdf_page_texts(file_path: Path) -> list[str]:
    reader = _get_pdf_reader(file_path)
    page_texts: list[str] = []
    for page in reader.pages:
        try:
            raw_text = page.extract_text() or ""
        except Exception:
            raw_text = ""
        page_texts.append(_normalize_multiline_text(raw_text))
    return page_texts


def _validate_pdf_page_texts(page_texts: list[str]) -> None:
    total_pages = len(page_texts)
    if total_pages <= 0:
        raise BusinessException(PDF_REJECTION_MESSAGE)

    normalized_lengths = [len(text.replace("\n", "").strip()) for text in page_texts]
    total_text_chars = sum(normalized_lengths)
    nonempty_pages = sum(1 for length in normalized_lengths if length > 0)
    effective_pages = sum(
        1 for length in normalized_lengths if length >= PDF_MIN_EFFECTIVE_PAGE_TEXT_CHARS
    )

    min_effective_pages = max(1, math.ceil(total_pages * PDF_MIN_STABLE_TEXT_PAGE_RATIO))
    min_nonempty_pages = max(1, math.ceil(total_pages * PDF_MIN_NONEMPTY_TEXT_PAGE_RATIO))

    if total_text_chars < PDF_MIN_TOTAL_TEXT_CHARS:
        raise BusinessException(PDF_REJECTION_MESSAGE)
    if nonempty_pages < min_nonempty_pages:
        raise BusinessException(PDF_REJECTION_MESSAGE)
    if effective_pages < min_effective_pages:
        raise BusinessException(PDF_REJECTION_MESSAGE)


def parse_pdf_file_to_blocks(file_path: Path) -> list[dict]:
    page_texts = _extract_pdf_page_texts(file_path)
    _validate_pdf_page_texts(page_texts)

    blocks: list[dict] = []
    for page_text in page_texts:
        if not page_text:
            continue
        for line in page_text.splitlines():
            if not line.strip():
                continue
            _append_text_fragments(blocks, line)
    return blocks


def blocks_to_text(blocks: list[dict]) -> str:
    lines: list[str] = []
    for block in blocks:
        kind = str(block.get("kind", "paragraph")).strip()
        text = _normalize_line(str(block.get("text", "")))
        if not text:
            continue
        if kind == "heading":
            level = int(block.get("level") or 1)
            lines.append(f"{'#' * max(1, min(level, 6))} {text}")
        elif kind == "list_item":
            if text.startswith("- "):
                lines.append(text)
            else:
                lines.append(f"- {text}")
        else:
            lines.append(text)
    return _normalize_multiline_text("\n".join(lines))


def parse_docx_file(file_path: Path) -> str:
    return blocks_to_text(parse_docx_file_to_blocks(file_path))


def parse_pdf_file(file_path: Path) -> str:
    return blocks_to_text(parse_pdf_file_to_blocks(file_path))


def parse_file_to_blocks(file_path: Path) -> list[dict]:
    extension = file_path.suffix.lower()

    if extension == ".txt":
        return parse_text_file_to_blocks(file_path)
    if extension == ".docx":
        return parse_docx_file_to_blocks(file_path)
    if extension == ".pdf":
        return parse_pdf_file_to_blocks(file_path)
    raise BusinessException("解析失败：不支持的文件类型。")


def parse_file_to_text(file_path: Path) -> str:
    text = blocks_to_text(parse_file_to_blocks(file_path))
    if not text:
        raise BusinessException("解析失败：文件中未提取到有效文本。")
    return text
