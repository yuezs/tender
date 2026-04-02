import re
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from docx import Document

from core.config import settings


class ProposalDocumentService:
    SECTION_ORDER = [
        "cover_summary",
        "table_of_contents",
        "company_intro",
        "qualification_response",
        "project_cases",
        "implementation_plan",
        "service_commitment",
        "business_response",
    ]

    SECTION_LABELS = {
        "cover_summary": "封面摘要",
        "table_of_contents": "目录",
        "company_intro": "公司介绍",
        "qualification_response": "资质响应",
        "project_cases": "类似项目经验",
        "implementation_plan": "实施方案",
        "service_commitment": "服务承诺",
        "business_response": "商务响应",
    }

    def __init__(self, storage_root: Path | None = None) -> None:
        self.storage_root = Path(storage_root or settings.storage_root)
        self.documents_dir = self.storage_root / "tender" / "documents"
        self.documents_dir.mkdir(parents=True, exist_ok=True)

    def export(self, *, file_id: str, tender_record: dict, generate_result: dict) -> dict:
        document_id = uuid4().hex
        target_dir = self.documents_dir / file_id
        target_dir.mkdir(parents=True, exist_ok=True)

        project_name = self._normalize_text(
            tender_record.get("extract_result", {}).get("project_name"),
            "标书初稿",
        )
        tender_company = self._normalize_text(
            tender_record.get("extract_result", {}).get("tender_company"),
            "待确认招标单位",
        )
        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        file_name = f"{self._sanitize_file_name(project_name)}-{document_id[:8]}.docx"
        storage_path = target_dir / file_name
        proposal_sections = self._normalize_sections(generate_result)

        document = Document()
        document.add_heading("技术商务标书初稿", level=0)
        document.add_paragraph(f"项目名称：{project_name}")
        document.add_paragraph(f"招标单位：{tender_company}")
        document.add_paragraph(f"生成时间：{generated_at}")
        document.add_page_break()

        for section_name in self.SECTION_ORDER:
            document.add_heading(self.SECTION_LABELS[section_name], level=1)
            for block in self._split_blocks(proposal_sections.get(section_name, "")):
                document.add_paragraph(block)
            if section_name != self.SECTION_ORDER[-1]:
                document.add_paragraph("")

        document.save(storage_path)

        return {
            "document_id": document_id,
            "file_name": file_name,
            "storage_path": str(storage_path),
            "download_url": f"/api/tender/documents/{document_id}/download",
            "generated_at": generated_at,
        }

    def _normalize_sections(self, generate_result: dict) -> dict[str, str]:
        proposal_sections = generate_result.get("proposal_sections")
        if not isinstance(proposal_sections, dict):
            proposal_sections = {}

        return {
            section_name: self._normalize_text(
                proposal_sections.get(section_name, generate_result.get(section_name)),
                "待补充",
            )
            for section_name in self.SECTION_ORDER
        }

    def _sanitize_file_name(self, value: str) -> str:
        cleaned = re.sub(r'[\\/:*?"<>|]+', "-", value).strip()
        cleaned = re.sub(r"\s+", "-", cleaned)
        return cleaned[:80] or "proposal"

    def _normalize_text(self, value: object, fallback: str) -> str:
        if isinstance(value, str):
            cleaned = value.strip()
            return cleaned or fallback
        return fallback

    def _split_blocks(self, value: str) -> list[str]:
        blocks = [block.strip() for block in value.splitlines() if block.strip()]
        return blocks or ["待补充"]
