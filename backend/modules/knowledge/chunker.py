def split_text_into_chunks(text: str, chunk_size: int = 600) -> list[dict]:
    cleaned_lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not cleaned_lines:
        return []

    segments: list[str] = []
    current = ""

    for line in cleaned_lines:
        candidate = f"{current}\n{line}".strip() if current else line
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                segments.append(current)
            current = line

    if current:
        segments.append(current)

    chunks: list[dict] = []
    for index, segment in enumerate(segments, start=1):
        first_line = segment.splitlines()[0]
        section_title = first_line[:60] if first_line else f"chunk-{index}"
        chunks.append(
            {
                "section_title": section_title,
                "content": segment,
                "chunk_index": index,
            }
        )
    return chunks
