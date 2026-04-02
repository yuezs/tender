from pathlib import Path

from docx import Document

from core.exceptions import BusinessException


def parse_text_file(file_path: Path) -> str:
    encodings = ["utf-8-sig", "utf-8", "gb18030"]
    for encoding in encodings:
        try:
            return file_path.read_text(encoding=encoding).strip()
        except UnicodeDecodeError:
            continue
    raise BusinessException("解析失败：无法识别 TXT 文件编码，请转为 UTF-8 或 GB18030 后重试。")


def parse_docx_file(file_path: Path) -> str:
    try:
        document = Document(str(file_path))
        lines = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
        return "\n".join(lines).strip()
    except Exception as exc:
        raise BusinessException(f"解析失败：DOCX 文件读取异常，{exc}") from exc


def parse_file_to_text(file_path: Path) -> str:
    extension = file_path.suffix.lower()

    if extension == ".txt":
        text = parse_text_file(file_path)
    elif extension == ".docx":
        text = parse_docx_file(file_path)
    elif extension == ".pdf":
        raise BusinessException("解析失败：PDF 解析接口已预留，当前 MVP 请优先上传 txt 或 docx 文件。")
    else:
        raise BusinessException("解析失败：不支持的文件类型。")

    if not text:
        raise BusinessException("解析失败：文件中未提取到有效文本。")

    return text
