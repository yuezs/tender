import re


NUMBERED_SECTION_RE = re.compile(r"^\s*[0-9一二三四五六七八九十]+[、.．)]")
PROJECT_CASE_START_RE = re.compile(r"(项目名称|案例名称|项目概况|案例概况|客户名称|业主名称)")
QUALIFICATION_START_RE = re.compile(r"(证书名称|资质名称|资质证书|证书编号|发证机构|有效期|等级)")
SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[。！？；;])\s*")
CLAUSE_BOUNDARY_RE = re.compile(r"(?<=[，,、])\s*")


def _normalize_blocks(blocks: list[dict] | None, text: str) -> list[dict]:
    if blocks:
        normalized: list[dict] = []
        for block in blocks:
            block_text = str(block.get("text", "")).strip()
            if not block_text:
                continue
            normalized.append(
                {
                    "kind": str(block.get("kind", "paragraph")).strip(),
                    "text": block_text,
                    "level": int(block.get("level") or 0),
                }
            )
        if normalized:
            return normalized

    return [
        {"kind": "paragraph", "text": line.strip(), "level": 0}
        for line in text.splitlines()
        if line.strip()
    ]


def _update_heading_path(heading_path: list[str], heading: str, level: int) -> list[str]:
    safe_level = max(1, level or 1)
    if len(heading_path) >= safe_level:
        heading_path = heading_path[: safe_level - 1]
    heading_path.append(heading)
    return heading_path


def _format_heading_path(heading_path: list[str]) -> str:
    if not heading_path:
        return ""
    return " / ".join(heading_path[-3:])


def _looks_like_project_case_boundary(text: str) -> bool:
    if PROJECT_CASE_START_RE.search(text):
        return True
    return bool(NUMBERED_SECTION_RE.match(text) and ("项目" in text or "案例" in text))


def _looks_like_qualification_boundary(text: str) -> bool:
    if QUALIFICATION_START_RE.search(text):
        return True
    return bool(NUMBERED_SECTION_RE.match(text) and ("资质" in text or "证书" in text or "认证" in text))


def _should_force_new_segment(category: str, block: dict, current_lines: list[str]) -> bool:
    if not current_lines:
        return False

    kind = block["kind"]
    text = block["text"]
    if kind == "heading":
        return True
    if category == "project_cases":
        return _looks_like_project_case_boundary(text)
    if category == "qualifications":
        return _looks_like_qualification_boundary(text)
    return False


def _build_segments(blocks: list[dict], category: str) -> list[dict]:
    segments: list[dict] = []
    heading_path: list[str] = []
    current_lines: list[str] = []
    current_title = ""

    def flush_segment() -> None:
        nonlocal current_lines, current_title
        if not current_lines:
            return
        content = "\n".join(current_lines).strip()
        if not content:
            current_lines = []
            return
        derived_title = current_title or current_lines[0][:60]
        segments.append(
            {
                "section_title": derived_title,
                "content": content,
            }
        )
        current_lines = []

    for block in blocks:
        text = block["text"]
        kind = block["kind"]
        level = block["level"]

        if kind == "heading":
            flush_segment()
            heading_path = _update_heading_path(heading_path, text, level)
            current_title = _format_heading_path(heading_path)
            continue

        if _should_force_new_segment(category, block, current_lines):
            flush_segment()

        if not current_title:
            current_title = _format_heading_path(heading_path)

        current_lines.append(text)

    flush_segment()
    return segments


def _split_long_segment(section_title: str, content: str, chunk_size: int) -> list[dict]:
    lines: list[str] = []
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if len(line) <= chunk_size:
            lines.append(line)
            continue

        sentence_parts = [item.strip() for item in SENTENCE_BOUNDARY_RE.split(line) if item.strip()]
        if len(sentence_parts) == 1:
            sentence_parts = [item.strip() for item in CLAUSE_BOUNDARY_RE.split(line) if item.strip()]

        if len(sentence_parts) <= 1:
            lines.append(line)
            continue

        lines.extend(sentence_parts)

    if not lines:
        return []

    parts: list[dict] = []
    current_lines: list[str] = []

    for line in lines:
        candidate = "\n".join(current_lines + [line]).strip()
        if len(candidate) <= chunk_size:
            current_lines.append(line)
            continue
        if current_lines:
            parts.append({"section_title": section_title, "content": "\n".join(current_lines).strip()})
        current_lines = [line]

    if current_lines:
        parts.append({"section_title": section_title, "content": "\n".join(current_lines).strip()})

    if len(parts) <= 1:
        return parts

    indexed_parts: list[dict] = []
    for index, part in enumerate(parts, start=1):
        indexed_parts.append(
            {
                "section_title": f"{section_title} (part {index})" if section_title else f"chunk-{index}",
                "content": part["content"],
            }
        )
    return indexed_parts


def split_text_into_chunks(
    text: str = "",
    chunk_size: int = 800,
    *,
    blocks: list[dict] | None = None,
    category: str = "",
) -> list[dict]:
    normalized_blocks = _normalize_blocks(blocks, text)
    if not normalized_blocks:
        return []

    segments = _build_segments(normalized_blocks, category)
    if not segments:
        return []

    chunks: list[dict] = []
    for segment in segments:
        section_title = segment["section_title"][:120] if segment["section_title"] else ""
        content = segment["content"].strip()
        if not content:
            continue
        for piece in _split_long_segment(section_title, content, chunk_size):
            chunks.append(
                {
                    "section_title": piece["section_title"][:120] if piece["section_title"] else "chunk",
                    "content": piece["content"],
                    "chunk_index": len(chunks) + 1,
                    "char_count": len(piece["content"]),
                }
            )

    return chunks
