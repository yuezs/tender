import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from core.config import settings
from core.exceptions import BusinessException
from modules.agent.run_artifacts import AgentRunArtifactService
from modules.agent.service import AgentService
from modules.files.service import FileService
from modules.tender.repository import TenderRepository


class TenderService:
    def __init__(self) -> None:
        self.repository = TenderRepository()
        self.file_service = FileService()
        self.agent_service = AgentService()
        self.artifact_service = AgentRunArtifactService()

    def get_module_status(self) -> dict:
        return {
            "module": "tender",
            "status": "ready",
            "message": "tender module is ready for MVP flow",
            "mock": not settings.agent_use_real_llm,
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
                "extract_debug": {},
                "judge_debug": {},
                "generate_debug": {},
                "agent_artifacts": self._empty_agent_artifacts(),
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
        fallback_result = self._build_rule_extract_result(text=text, file_name=record["file_name"])
        prepared = self.agent_service.prepare_extract(
            parsed_text=text,
            fallback_result=fallback_result,
        )
        agent_payload = self._run_agent_step(
            file_id=file_id,
            step="extract",
            prepared=prepared,
            input_summary={
                "file_name": record["file_name"],
                "parsed_text_preview": text[:1000],
                "fallback_result": fallback_result,
            },
            execute_fn=self.agent_service.run_extract,
        )

        updated = self.repository.update_record(
            file_id,
            {
                "extract_status": "success",
                "extract_result": agent_payload["result"],
                "extract_debug": agent_payload["debug"],
                "agent_artifacts": self._load_record_agent_artifacts(file_id),
            },
        )
        return updated["extract_result"]

    def judge_tender(self, db: Session, file_id: str) -> dict:
        record = self._ensure_extracted_record(file_id)
        prepared = self.agent_service.prepare_judge(db, record)
        agent_payload = self._run_agent_step(
            file_id=file_id,
            step="judge",
            prepared=prepared,
            input_summary={
                "extract_result": record.get("extract_result", {}),
                "knowledge_context": self._summarize_knowledge_context(
                    prepared.get("knowledge_context", {})
                ),
            },
            execute_fn=self.agent_service.run_judge,
        )

        updated = self.repository.update_record(
            file_id,
            {
                "judge_status": "success",
                "judge_result": agent_payload["result"],
                "judge_debug": agent_payload["debug"],
                "agent_artifacts": self._load_record_agent_artifacts(file_id),
            },
        )
        return updated["judge_result"]

    def generate_tender(self, db: Session, file_id: str) -> dict:
        record = self._ensure_judged_record(db, file_id)
        judge_result = record["judge_result"]
        prepared = self.agent_service.prepare_generate(db, record, judge_result)
        agent_payload = self._run_agent_step(
            file_id=file_id,
            step="generate",
            prepared=prepared,
            input_summary={
                "extract_result": record.get("extract_result", {}),
                "judge_result": judge_result,
                "knowledge_context": self._summarize_knowledge_context(
                    prepared.get("knowledge_context", {})
                ),
            },
            execute_fn=self.agent_service.run_generate,
        )

        updated = self.repository.update_record(
            file_id,
            {
                "generate_status": "success",
                "generate_result": agent_payload["result"],
                "generate_debug": agent_payload["debug"],
                "agent_artifacts": self._load_record_agent_artifacts(file_id),
            },
        )
        return updated["generate_result"]

    def _run_agent_step(
        self,
        *,
        file_id: str,
        step: str,
        prepared: dict,
        input_summary: dict,
        execute_fn,
    ) -> dict:
        prepared_payload = deepcopy(prepared)
        paths = self.artifact_service.build_paths(file_id, step)
        self._update_agent_artifacts(file_id, step, paths)

        if self.artifact_service.has_reusable_output(file_id, step):
            output = self.artifact_service.read_output(file_id, step)
            return {
                "result": output["parsed_result"],
                "debug": output["debug"],
                "prompt": prepared_payload["prompt"],
                "raw_text": output["raw_text"],
            }

        status = self.artifact_service.read_status(file_id, step)
        input_payload = self.artifact_service.read_input(file_id, step)

        if status.get("state") == "running" and status.get("run_id"):
            prepared_payload["prompt"] = input_payload.get("prompt") or prepared_payload["prompt"]
            execution_context = {
                "session_key": input_payload.get("session_key")
                or self._build_session_key(file_id, step),
                "idempotency_key": input_payload.get("idempotency_key")
                or status.get("run_id"),
                "run_id": status.get("run_id"),
            }
            agent_payload = execute_fn(
                prepared_payload,
                execution_context=execution_context,
            )
            self._write_agent_step_success(
                file_id=file_id,
                step=step,
                execution_context=execution_context,
                agent_payload=agent_payload,
                started_at=status.get("started_at"),
            )
            return agent_payload

        if status or input_payload or self.artifact_service.read_output(file_id, step):
            paths = self.artifact_service.reset_step(file_id, step)
            self._update_agent_artifacts(file_id, step, paths)

        execution_context = self._build_execution_context(file_id, step)
        agent_input_payload = {
            "file_id": file_id,
            "step": step,
            "agent_id": prepared_payload["agent_id"],
            "input_summary": input_summary,
            "prompt": prepared_payload["prompt"],
            "session_key": execution_context["session_key"],
            "task_id": execution_context["idempotency_key"],
            "idempotency_key": execution_context["idempotency_key"],
        }
        started_at = self._utc_now()
        self.artifact_service.write_input(file_id, step, agent_input_payload)
        self.artifact_service.write_status(
            file_id,
            step,
            {
                "state": "running",
                "run_id": execution_context["idempotency_key"],
                "started_at": started_at,
                "finished_at": "",
                "error": "",
            },
        )

        try:
            agent_payload = execute_fn(
                prepared_payload,
                execution_context=execution_context,
            )
        except Exception as exc:
            self.artifact_service.write_status(
                file_id,
                step,
                {
                    "state": "error",
                    "run_id": execution_context["idempotency_key"],
                    "started_at": started_at,
                    "finished_at": self._utc_now(),
                    "error": str(exc),
                },
            )
            raise

        self._write_agent_step_success(
            file_id=file_id,
            step=step,
            execution_context=execution_context,
            agent_payload=agent_payload,
            started_at=started_at,
        )
        return agent_payload

    def _write_agent_step_success(
        self,
        *,
        file_id: str,
        step: str,
        execution_context: dict,
        agent_payload: dict,
        started_at: str | None,
    ) -> None:
        run_id = str(
            agent_payload.get("debug", {}).get("run_id")
            or execution_context.get("run_id")
            or execution_context.get("idempotency_key")
            or ""
        ).strip()
        self.artifact_service.write_output(
            file_id,
            step,
            {
                "raw_text": agent_payload.get("raw_text", ""),
                "parsed_result": agent_payload.get("result", {}),
                "debug": agent_payload.get("debug", {}),
            },
        )
        self.artifact_service.write_status(
            file_id,
            step,
            {
                "state": "success",
                "run_id": run_id,
                "started_at": started_at or self._utc_now(),
                "finished_at": self._utc_now(),
                "error": "",
            },
        )

    def _build_execution_context(self, file_id: str, step: str) -> dict:
        return {
            "session_key": self._build_session_key(file_id, step),
            "idempotency_key": uuid4().hex,
        }

    def _build_session_key(self, file_id: str, step: str) -> str:
        return f"tender:{file_id}:{step}"

    def _update_agent_artifacts(self, file_id: str, step: str, paths: dict[str, str]) -> None:
        record = self.repository.get_record(file_id)
        agent_artifacts = deepcopy(record.get("agent_artifacts") or self._empty_agent_artifacts())
        agent_artifacts[step] = paths
        self.repository.update_record(file_id, {"agent_artifacts": agent_artifacts})

    def _load_record_agent_artifacts(self, file_id: str) -> dict:
        return self.repository.get_record(file_id).get("agent_artifacts", self._empty_agent_artifacts())

    def _empty_agent_artifacts(self) -> dict:
        return {
            "extract": {},
            "judge": {},
            "generate": {},
        }

    def _summarize_knowledge_context(self, knowledge_context: dict) -> dict:
        chunks = knowledge_context.get("chunks", [])
        return {
            "task_type": knowledge_context.get("task_type", ""),
            "source_categories": knowledge_context.get("source_categories", []),
            "chunk_count": len(chunks),
            "documents": [
                {
                    "category": chunk.get("category", ""),
                    "document_title": chunk.get("document_title", ""),
                    "section_title": chunk.get("section_title", ""),
                }
                for chunk in chunks[:5]
            ],
        }

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

    def _ensure_judged_record(self, db: Session, file_id: str) -> dict:
        record = self._ensure_extracted_record(file_id)
        if record.get("judge_status") != "success" or not record.get("judge_result"):
            self.judge_tender(db, file_id)
            record = self.repository.get_record(file_id)
        return record

    def _build_rule_extract_result(self, *, text: str, file_name: str) -> dict:
        return {
            "project_name": self._find_project_name(text, file_name),
            "tender_company": self._find_first_match(
                text,
                [
                    r"(?:招标单位|采购单位|建设单位)[：:\s]*([^\n\r]+)",
                    r"(?:甲方|业主单位)[：:\s]*([^\n\r]+)",
                ],
            ),
            "budget": self._find_first_match(
                text,
                [
                    r"(?:预算金额|项目预算|控制价)[：:\s]*([^\n\r]+)",
                ],
            ),
            "deadline": self._find_first_match(
                text,
                [
                    r"(?:投标截止时间|开标时间|响应文件提交截止时间)[：:\s]*([^\n\r]+)",
                ],
            ),
            "qualification_requirements": self._collect_lines(
                text,
                ["资质", "资格", "证书", "认证"],
                limit=4,
            ),
            "delivery_requirements": self._collect_lines(
                text,
                ["交付", "工期", "上线", "实施", "服务期"],
                limit=4,
            ),
            "scoring_focus": self._collect_lines(
                text,
                ["评分", "评审", "技术方案", "项目团队", "类似案例"],
                limit=4,
            ),
        }

    def _find_project_name(self, text: str, file_name: str) -> str:
        matched = self._find_first_match(
            text,
            [
                r"(?:项目名称|招标项目名称|采购项目名称)[：:\s]*([^\n\r]+)",
                r"(?:项目编号.*?\n)?([^\n\r]*项目[^\n\r]*)",
            ],
        )
        return matched or Path(file_name).stem

    def _find_first_match(self, text: str, patterns: list[str]) -> str:
        for pattern in patterns:
            matched = re.search(pattern, text, re.IGNORECASE)
            if matched:
                return re.sub(r"\s+", " ", matched.group(1)).strip(" ：:;；")
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

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()
