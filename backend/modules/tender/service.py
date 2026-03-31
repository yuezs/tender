import re
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from modules.agent.service import AgentService
from core.exceptions import BusinessException
from modules.files.service import FileService
from modules.tender.repository import TenderRepository


class TenderService:
    def __init__(self) -> None:
        self.repository = TenderRepository()
        self.file_service = FileService()
        self.agent_service = AgentService()

    def get_module_status(self) -> dict:
        return {
            "module": "tender",
            "status": "ready",
            "message": "tender module is ready for MVP flow",
            "mock": True,
            "available_routes": [
                "/api/tender/status",
                "/api/tender/upload",
                "/api/tender/parse",
                "/api/tender/extract",
                "/api/tender/judge",
                "/api/tender/generate",
            ],
            "repository_ready": self.repository.is_ready(),
        }

    async def upload_tender_file(
        self,
        upload_file: UploadFile,
        source_type: str,
        source_url: str | None = None,
    ) -> dict:
        if source_type not in {"upload", "url"}:
            raise BusinessException("上传失败：source_type 仅支持 upload 或 url。")
        saved_file = await self.file_service.save_tender_file(upload_file)
        record = self.repository.create_record(
            {
                "file_id": saved_file["file_id"],
                "file_name": saved_file["file_name"],
                "source_type": source_type,
                "source_url": source_url or "",
                "extension": saved_file["extension"],
                "storage_path": saved_file["storage_path"],
                "size": saved_file["size"],
                "parse_status": "pending",
                "extract_status": "pending",
                "judge_status": "pending",
                "generate_status": "pending",
                "parsed_text": "",
                "text_path": "",
                "extract_result": {},
                "judge_result": {},
                "generate_result": {},
            }
        )
        return {
            "file_id": record["file_id"],
            "file_name": record["file_name"],
            "source_type": record["source_type"],
            "extension": record["extension"],
        }

    def parse_tender(self, file_id: str) -> dict:
        record = self.repository.get_record(file_id)
        try:
            parsed = self.file_service.parse_tender_file(file_id, record["storage_path"])
        except BusinessException as exc:
            self.repository.update_record(file_id, {"parse_status": "error"})
            raise exc

        updated = self.repository.update_record(
            file_id,
            {
                "parse_status": "success",
                "parsed_text": parsed["text"],
                "text_path": parsed["text_path"],
                "text_preview": parsed["text_preview"],
            },
        )

        return {
            "file_id": updated["file_id"],
            "text": updated["parsed_text"],
        }

    def extract_tender(self, file_id: str) -> dict:
        record = self._ensure_parsed_record(file_id)
        text = record["parsed_text"]

        extract_result = {
            "project_name": self._find_project_name(text, record["file_name"]),
            "tender_company": self._find_first_match(
                text,
                [
                    r"(?:招标人|招标单位|采购人)[：:\s]*([^\n\r]+)",
                    r"(?:项目业主|建设单位)[：:\s]*([^\n\r]+)",
                ],
            ),
            "budget": self._find_first_match(
                text,
                [
                    r"(?:预算金额|项目金额|采购预算|最高限价)[：:\s]*([^\n\r]+)",
                ],
            ),
            "deadline": self._find_first_match(
                text,
                [
                    r"(?:投标截止时间|提交截止时间|开标时间|响应文件递交截止时间)[：:\s]*([^\n\r]+)",
                ],
            ),
            "qualification_requirements": self._collect_lines(
                text, ["资质", "资格", "证书", "认证"], limit=4
            ),
            "delivery_requirements": self._collect_lines(
                text, ["交付", "工期", "服务期", "实施周期", "履约"], limit=4
            ),
            "scoring_focus": self._collect_lines(
                text, ["评分", "评审", "打分", "综合得分"], limit=4
            ),
        }

        updated = self.repository.update_record(
            file_id,
            {
                "extract_status": "success",
                "extract_result": extract_result,
            },
        )

        return updated["extract_result"]

    def judge_tender(self, db: Session, file_id: str) -> dict:
        record = self._ensure_extracted_record(file_id)
        judge_result = self.agent_service.run_judge(db, record)

        updated = self.repository.update_record(
            file_id,
            {
                "judge_status": "success",
                "judge_result": judge_result,
            },
        )
        return updated["judge_result"]

    def generate_tender(self, db: Session, file_id: str) -> dict:
        record = self._ensure_extracted_record(file_id)
        judge_result = self.judge_tender(db, file_id)
        generate_result = self.agent_service.run_generate(db, record, judge_result)

        updated = self.repository.update_record(
            file_id,
            {
                "generate_status": "success",
                "generate_result": generate_result,
                "judge_result": judge_result,
            },
        )
        return updated["generate_result"]

    def _ensure_parsed_record(self, file_id: str) -> dict:
        record = self.repository.get_record(file_id)
        if record.get("parse_status") != "success" or not record.get("parsed_text"):
            self.parse_tender(file_id)
            record = self.repository.get_record(file_id)
        return record

    def _ensure_extracted_record(self, file_id: str) -> dict:
        record = self._ensure_parsed_record(file_id)
        if record.get("extract_status") != "success" or not record.get("extract_result"):
            self.extract_tender(file_id)
            record = self.repository.get_record(file_id)
        return record

    def _find_project_name(self, text: str, file_name: str) -> str:
        matched = self._find_first_match(
            text,
            [
                r"(?:项目名称|采购项目名称|招标项目名称)[：:\s]*([^\n\r]+)",
                r"(?:项目编号及名称)[：:\s]*([^\n\r]+)",
            ],
        )
        return matched or Path(file_name).stem

    def _find_first_match(self, text: str, patterns: list[str]) -> str:
        for pattern in patterns:
            matched = re.search(pattern, text, re.IGNORECASE)
            if matched:
                return re.sub(r"\s+", " ", matched.group(1)).strip(" ：:")
        return ""

    def _collect_lines(self, text: str, keywords: list[str], limit: int = 3) -> list[str]:
        lines: list[str] = []
        for raw_line in text.splitlines():
            cleaned = re.sub(r"\s+", " ", raw_line).strip()
            if not cleaned:
                continue
            if any(keyword in cleaned for keyword in keywords) and cleaned not in lines:
                lines.append(cleaned[:160])
            if len(lines) >= limit:
                break
        return lines
