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
from modules.tender.document_service import ProposalDocumentService
from modules.tender.repository import TenderRepository


class TenderService:
    def __init__(self) -> None:
        self.repository = TenderRepository()
        self.file_service = FileService()
        self.agent_service = AgentService()
        self.artifact_service = AgentRunArtifactService()
        self.document_service = ProposalDocumentService()

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
                "/api/tender/results/latest",
                "/api/tender/results/{file_id}",
                "/api/tender/generate/section",
                "/api/tender/sections/{file_id}/{section_id}",
                "/api/tender/documents/fulltext",
                "/api/tender/documents/{document_id}/download",
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
                "parse_error": "",
                "extract_error": "",
                "judge_error": "",
                "generate_error": "",
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
            self.repository.update_record(
                file_id,
                {
                    "parse_status": "error",
                    "parse_error": exc.message,
                },
            )
            raise exc
        except Exception as exc:
            message = "招标文件解析失败，请稍后重试。"
            self.repository.update_record(
                file_id,
                {
                    "parse_status": "error",
                    "parse_error": message,
                },
            )
            raise BusinessException(message) from exc

        updated = self.repository.update_record(
            file_id,
            {
                "parse_status": "success",
                "parse_error": "",
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
        try:
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
        except BusinessException as exc:
            self._mark_step_error(file_id, "extract", exc.message)
            raise
        except Exception as exc:
            message = "核心字段抽取失败，请稍后重试。"
            self._mark_step_error(file_id, "extract", message)
            raise BusinessException(message) from exc

        updated = self.repository.update_record(
            file_id,
            {
                "extract_status": "success",
                "extract_error": "",
                "extract_result": agent_payload["result"],
                "extract_debug": agent_payload["debug"],
                "agent_artifacts": self._load_record_agent_artifacts(file_id),
            },
        )
        return updated["extract_result"]

    def judge_tender(self, db: Session, file_id: str) -> dict:
        record = self._ensure_extracted_record(file_id)
        prepared = self.agent_service.prepare_judge(db, record)
        try:
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
        except BusinessException as exc:
            self._mark_step_error(file_id, "judge", exc.message)
            raise
        except Exception as exc:
            message = "投标判断失败，请稍后重试。"
            self._mark_step_error(file_id, "judge", message)
            raise BusinessException(message) from exc

        updated = self.repository.update_record(
            file_id,
            {
                "judge_status": "success",
                "judge_error": "",
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
        try:
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
        except BusinessException as exc:
            self._mark_step_error(file_id, "generate", exc.message)
            raise
        except Exception as exc:
            message = "标书初稿生成失败，请稍后重试。"
            self._mark_step_error(file_id, "generate", message)
            raise BusinessException(message) from exc

        existing_generate_result = record.get("generate_result", {}) or {}
        hydrated_generate_result = self._initialize_generate_result(
            agent_payload["result"],
            existing_generate_result.get("section_contents", {}),
        )
        updated = self.repository.update_record(
            file_id,
            {
                "generate_status": "success",
                "generate_error": "",
                "generate_result": hydrated_generate_result,
                "generate_debug": agent_payload["debug"],
                "agent_artifacts": self._load_record_agent_artifacts(file_id),
            },
        )
        document_payload = self.document_service.export(
            file_id=file_id,
            tender_record=updated,
            generate_result=updated["generate_result"],
        )
        generate_result = {
            **updated["generate_result"],
            "download_ready": True,
            "document_id": document_payload["document_id"],
            "document_file_name": document_payload["file_name"],
            "download_url": document_payload["download_url"],
        }
        updated = self.repository.update_record(
            file_id,
            {
                "generate_result": generate_result,
                "generate_document": document_payload,
            },
        )
        return updated["generate_result"]

    def get_generated_document(self, document_id: str) -> dict:
        record = self.repository.find_record_by_document_id(document_id)
        document_payload = record.get("generate_document") or {}
        storage_path = str(document_payload.get("storage_path", "")).strip()
        file_name = str(document_payload.get("file_name", "")).strip()
        if not storage_path or not Path(storage_path).exists():
            raise BusinessException("标书文档不存在，请重新生成。", status_code=404)
        if not file_name:
            file_name = Path(storage_path).name
        return {
            "storage_path": storage_path,
            "file_name": file_name,
        }

    def get_latest_result(self) -> dict:
        record = self.repository.get_latest_record()
        return self._serialize_tender_snapshot(record)

    def get_tender_result(self, file_id: str) -> dict:
        record = self.repository.get_record(file_id)
        return self._serialize_tender_snapshot(record)

    def generate_full_text_document(self, db: Session, file_id: str) -> dict:
        record = self._ensure_generated_outline_record(db, file_id)
        generate_result = self._initialize_generate_result(record.get("generate_result", {}) or {})
        document_payload = self.document_service.export_full_text(
            file_id=file_id,
            tender_record=record,
            generate_result=generate_result,
        )
        self.repository.update_record(
            file_id,
            {
                "fulltext_document": document_payload,
            },
        )
        return {
            "document_id": document_payload["document_id"],
            "file_name": document_payload["file_name"],
            "download_url": document_payload["download_url"],
            "generated_at": document_payload["generated_at"],
        }

    def generate_tender_section(self, db: Session, file_id: str, section_id: str) -> dict:
        record = self._ensure_generated_outline_record(db, file_id)
        generate_result = self._initialize_generate_result(record.get("generate_result", {}) or {})
        parent_section, child_section = self._locate_outline_section(
            generate_result.get("proposal_outline", []),
            section_id,
        )
        if not parent_section or not child_section:
            raise BusinessException("当前仅支持按小节生成正文，请选择具体小节。", status_code=400)

        section_contents = deepcopy(generate_result.get("section_contents", {}) or {})
        section_contents[section_id] = self._build_section_content_entry(
            parent_section=parent_section,
            child_section=child_section,
            existing=section_contents.get(section_id),
            status="loading",
            content=str((section_contents.get(section_id) or {}).get("content", "")).strip(),
            error_message="",
        )
        self.repository.update_record(
            file_id,
            {
                "generate_result": {
                    **generate_result,
                    "section_contents": section_contents,
                }
            },
        )

        prepared = self.agent_service.prepare_generate_section(
            db,
            record,
            record["judge_result"],
            parent_section,
            child_section,
        )
        step = self._build_section_agent_step(section_id)
        try:
            agent_payload = self._run_agent_step(
                file_id=file_id,
                step=step,
                prepared=prepared,
                input_summary={
                    "parent_section": parent_section,
                    "child_section": child_section,
                    "extract_result": record.get("extract_result", {}),
                    "judge_result": record.get("judge_result", {}),
                    "knowledge_context": self._summarize_knowledge_context(
                        prepared.get("knowledge_context", {})
                    ),
                },
                execute_fn=self.agent_service.run_generate_section,
            )
        except BusinessException as exc:
            self._update_section_content_error(file_id, generate_result, parent_section, child_section, exc.message)
            raise
        except Exception as exc:
            message = "小节正文生成失败，请稍后重试。"
            self._update_section_content_error(file_id, generate_result, parent_section, child_section, message)
            raise BusinessException(message) from exc

        refreshed_record = self.repository.get_record(file_id)
        refreshed_generate_result = self._initialize_generate_result(refreshed_record.get("generate_result", {}) or {})
        refreshed_section_contents = deepcopy(refreshed_generate_result.get("section_contents", {}) or {})
        refreshed_section_contents[section_id] = self._build_section_content_entry(
            parent_section=parent_section,
            child_section=child_section,
            existing=refreshed_section_contents.get(section_id),
            status="success",
            content=str(agent_payload["result"].get("content", "")).strip(),
            error_message="",
            knowledge_used=agent_payload["result"].get("knowledge_used", []),
            prompt_preview=str(agent_payload["result"].get("prompt_preview", "")).strip(),
        )

        next_generate_result = {
            **refreshed_generate_result,
            "section_contents": refreshed_section_contents,
        }
        document_payload = self.document_service.export(
            file_id=file_id,
            tender_record=refreshed_record,
            generate_result=next_generate_result,
        )
        next_generate_result = {
            **next_generate_result,
            "download_ready": True,
            "document_id": document_payload["document_id"],
            "document_file_name": document_payload["file_name"],
            "download_url": document_payload["download_url"],
        }
        updated = self.repository.update_record(
            file_id,
            {
                "generate_result": next_generate_result,
                "generate_document": document_payload,
                "agent_artifacts": self._load_record_agent_artifacts(file_id),
            },
        )
        return self._build_section_content_response(updated["generate_result"], section_id)

    def get_tender_section_content(self, file_id: str, section_id: str) -> dict:
        record = self.repository.get_record(file_id)
        generate_result = self._initialize_generate_result(record.get("generate_result", {}) or {})
        return self._build_section_content_response(generate_result, section_id)

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
                or self._build_session_key(
                    file_id=file_id,
                    step=step,
                    agent_id=prepared_payload["agent_id"],
                ),
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

        execution_context = self._build_execution_context(
            file_id=file_id,
            step=step,
            agent_id=prepared_payload["agent_id"],
        )
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

    def _build_execution_context(self, *, file_id: str, step: str, agent_id: str) -> dict:
        return {
            "session_key": self._build_session_key(
                file_id=file_id,
                step=step,
                agent_id=agent_id,
            ),
            "idempotency_key": uuid4().hex,
        }

    def _build_session_key(self, *, file_id: str, step: str, agent_id: str) -> str:
        return f"agent:{agent_id}:tender:{file_id}:{step}"

    def _update_agent_artifacts(self, file_id: str, step: str, paths: dict[str, str]) -> None:
        record = self.repository.get_record(file_id)
        agent_artifacts = deepcopy(record.get("agent_artifacts") or self._empty_agent_artifacts())
        agent_artifacts[step] = paths
        self.repository.update_record(file_id, {"agent_artifacts": agent_artifacts})

    def _load_record_agent_artifacts(self, file_id: str) -> dict:
        return self.repository.get_record(file_id).get("agent_artifacts", self._empty_agent_artifacts())

    def _ensure_generated_outline_record(self, db: Session, file_id: str) -> dict:
        record = self._ensure_judged_record(db, file_id)
        generate_result = record.get("generate_result", {}) or {}
        if record.get("generate_status") != "success" or not generate_result.get("proposal_outline"):
            self.generate_tender(db, file_id)
            record = self.repository.get_record(file_id)
        return record

    def _initialize_generate_result(
        self,
        generate_result: dict,
        existing_section_contents: dict | None = None,
    ) -> dict:
        proposal_outline = self._normalize_outline(generate_result.get("proposal_outline") or [])
        normalized_generate_result = deepcopy(generate_result)
        normalized_generate_result["proposal_outline"] = proposal_outline

        section_contents = self._initialize_section_contents(
            proposal_outline,
            existing_section_contents or normalized_generate_result.get("section_contents", {}) or {},
        )
        normalized_generate_result["section_contents"] = section_contents
        return normalized_generate_result

    def _normalize_outline(self, proposal_outline: list[dict]) -> list[dict]:
        normalized_outline: list[dict] = []

        for index, item in enumerate(proposal_outline):
            if not isinstance(item, dict):
                continue

            section_id = str(item.get("section_id", "")).strip() or str(index + 1)
            title = str(item.get("title", "")).strip()
            if not title:
                continue

            purpose = str(item.get("purpose", "")).strip() or "按当前目录规划逐节生成正文。"
            raw_children = item.get("children", []) or []
            if isinstance(raw_children, list) and raw_children:
                normalized_children: list[dict] = []
                for child_index, child in enumerate(raw_children):
                    if not isinstance(child, dict):
                        continue
                    child_title = str(child.get("title", "")).strip()
                    if not child_title:
                        continue
                    normalized_children.append(
                        {
                            "section_id": str(child.get("section_id", "")).strip()
                            or f"{section_id}.{child_index + 1}",
                            "title": child_title,
                            "purpose": str(child.get("purpose", "")).strip()
                            or "按本小节目录要求生成正文。",
                            "writing_points": [
                                str(point).strip()
                                for point in (child.get("writing_points", []) or [])
                                if str(point).strip()
                            ][:5],
                        }
                    )
            else:
                normalized_children = [
                    {
                        "section_id": f"{section_id}.1",
                        "title": f"{title}正文",
                        "purpose": purpose,
                        "writing_points": [
                            str(point).strip()
                            for point in (item.get("writing_points", []) or [])
                            if str(point).strip()
                        ][:5],
                    }
                ]

            normalized_outline.append(
                {
                    "section_id": section_id,
                    "title": title,
                    "purpose": purpose,
                    "children": normalized_children,
                }
            )

        return normalized_outline

    def _initialize_section_contents(self, proposal_outline: list[dict], existing: dict) -> dict[str, dict]:
        normalized: dict[str, dict] = {}
        existing = existing if isinstance(existing, dict) else {}

        for parent_section in proposal_outline:
            parent_section_id = str(parent_section.get("section_id", "")).strip()
            for child_section in parent_section.get("children", []) or []:
                section_id = str(child_section.get("section_id", "")).strip()
                if not section_id:
                    continue
                normalized[section_id] = self._build_section_content_entry(
                    parent_section=parent_section,
                    child_section=child_section,
                    existing=existing.get(section_id),
                )

        for section_id, payload in existing.items():
            if section_id in normalized:
                continue
            if not isinstance(payload, dict):
                continue
            normalized[section_id] = {
                "section_id": str(payload.get("section_id", section_id)).strip() or str(section_id),
                "parent_section_id": str(payload.get("parent_section_id", "")).strip(),
                "title": str(payload.get("title", "未命名小节")).strip() or "未命名小节",
                "status": str(payload.get("status", "pending")).strip() or "pending",
                "content": str(payload.get("content", "")).strip(),
                "error_message": str(payload.get("error_message", "")).strip(),
                "updated_at": str(payload.get("updated_at", "")).strip(),
                "knowledge_used": payload.get("knowledge_used", []) or [],
                "prompt_preview": str(payload.get("prompt_preview", "")).strip(),
            }

        return normalized

    def _build_section_content_entry(
        self,
        *,
        parent_section: dict,
        child_section: dict,
        existing: dict | None = None,
        status: str | None = None,
        content: str | None = None,
        error_message: str | None = None,
        knowledge_used: list[dict] | None = None,
        prompt_preview: str | None = None,
    ) -> dict:
        existing = existing if isinstance(existing, dict) else {}
        return {
            "section_id": str(child_section.get("section_id", "")).strip(),
            "parent_section_id": str(parent_section.get("section_id", "")).strip(),
            "title": str(child_section.get("title", "未命名小节")).strip() or "未命名小节",
            "status": status or str(existing.get("status", "pending")).strip() or "pending",
            "content": content if content is not None else str(existing.get("content", "")).strip(),
            "error_message": (
                error_message
                if error_message is not None
                else str(existing.get("error_message", "")).strip()
            ),
            "updated_at": self._utc_now() if status else str(existing.get("updated_at", "")).strip(),
            "knowledge_used": knowledge_used if knowledge_used is not None else existing.get("knowledge_used", []) or [],
            "prompt_preview": (
                prompt_preview
                if prompt_preview is not None
                else str(existing.get("prompt_preview", "")).strip()
            ),
        }

    def _locate_outline_section(self, proposal_outline: list[dict], section_id: str) -> tuple[dict | None, dict | None]:
        target_section_id = str(section_id).strip()
        for parent_section in proposal_outline:
            parent_section_id = str(parent_section.get("section_id", "")).strip()
            if parent_section_id == target_section_id:
                return parent_section, None
            for child_section in parent_section.get("children", []) or []:
                child_section_id = str(child_section.get("section_id", "")).strip()
                if child_section_id == target_section_id:
                    return parent_section, child_section
        return None, None

    def _build_section_content_response(self, generate_result: dict, section_id: str) -> dict:
        proposal_outline = generate_result.get("proposal_outline", []) or []
        section_contents = generate_result.get("section_contents", {}) or {}
        parent_section, child_section = self._locate_outline_section(proposal_outline, section_id)
        if not parent_section:
            raise BusinessException("未找到对应目录章节。", status_code=404)

        if child_section:
            payload = section_contents.get(section_id) or self._build_section_content_entry(
                parent_section=parent_section,
                child_section=child_section,
            )
            content = str(payload.get("content", "")).strip()
            if not content:
                content = "当前小节尚未生成正文，请先点击“生成正文”。"
            return {
                "section_id": str(payload.get("section_id", section_id)).strip(),
                "parent_section_id": str(payload.get("parent_section_id", "")).strip(),
                "title": str(payload.get("title", "未命名小节")).strip() or "未命名小节",
                "scope": "section",
                "status": str(payload.get("status", "pending")).strip() or "pending",
                "content": content,
                "completed_children": 1 if str(payload.get("status", "")).strip() == "success" else 0,
                "total_children": 1,
            }

        child_sections = parent_section.get("children", []) or []
        completed_children = 0
        rendered_sections: list[str] = []
        for item in child_sections:
            child_section_id = str(item.get("section_id", "")).strip()
            child_title = str(item.get("title", "未命名小节")).strip() or "未命名小节"
            payload = section_contents.get(child_section_id) or self._build_section_content_entry(
                parent_section=parent_section,
                child_section=item,
            )
            child_status = str(payload.get("status", "pending")).strip() or "pending"
            if child_status == "success":
                completed_children += 1
            child_content = str(payload.get("content", "")).strip() or "当前小节尚未生成正文。"
            rendered_sections.append(f"{child_section_id} {child_title}\n{child_content}")

        total_children = len(child_sections)
        parent_status = "success" if total_children and completed_children == total_children else "pending"
        if any(str((section_contents.get(str(item.get('section_id', '')).strip()) or {}).get("status", "")).strip() == "loading" for item in child_sections):
            parent_status = "loading"
        elif any(str((section_contents.get(str(item.get('section_id', '')).strip()) or {}).get("status", "")).strip() == "error" for item in child_sections):
            parent_status = "error" if completed_children == 0 else parent_status

        return {
            "section_id": str(parent_section.get("section_id", "")).strip(),
            "parent_section_id": "",
            "title": str(parent_section.get("title", "未命名章节")).strip() or "未命名章节",
            "scope": "chapter",
            "status": parent_status,
            "content": "\n\n".join(rendered_sections) if rendered_sections else "当前大章节下暂无小节内容。",
            "completed_children": completed_children,
            "total_children": total_children,
        }

    def _update_section_content_error(
        self,
        file_id: str,
        generate_result: dict,
        parent_section: dict,
        child_section: dict,
        message: str,
    ) -> None:
        section_id = str(child_section.get("section_id", "")).strip()
        section_contents = deepcopy(generate_result.get("section_contents", {}) or {})
        section_contents[section_id] = self._build_section_content_entry(
            parent_section=parent_section,
            child_section=child_section,
            existing=section_contents.get(section_id),
            status="error",
            content=str((section_contents.get(section_id) or {}).get("content", "")).strip(),
            error_message=message,
        )
        self.repository.update_record(
            file_id,
            {
                "generate_result": {
                    **generate_result,
                    "section_contents": section_contents,
                }
            },
        )

    def _build_section_agent_step(self, section_id: str) -> str:
        normalized = re.sub(r"[^0-9A-Za-z_-]+", "-", str(section_id).strip())
        return f"generate-section-{normalized}"

    def _mark_step_error(self, file_id: str, step: str, message: str) -> None:
        status_field = f"{step}_status"
        error_field = f"{step}_error"
        self.repository.update_record(
            file_id,
            {
                status_field: "error",
                error_field: message,
            },
        )

    def _empty_agent_artifacts(self) -> dict:
        return {
            "extract": {},
            "judge": {},
            "generate": {},
        }

    def _serialize_tender_snapshot(self, record: dict) -> dict:
        file_id = str(record.get("file_id", "")).strip()
        return {
            "uploaded_at": str(record.get("created_at", "")).strip(),
            "updated_at": str(record.get("updated_at", "")).strip(),
            "upload": {
                "file_id": file_id,
                "file_name": str(record.get("file_name", "")).strip(),
                "source_type": str(record.get("source_type", "")).strip(),
                "extension": str(record.get("extension", "")).strip(),
            },
            "steps": {
                "upload": {
                    "status": "success",
                    "message": "文件已上传" if file_id else "未上传文件",
                },
                "parse": self._build_step_state(record, "parse"),
                "extract": self._build_step_state(record, "extract"),
                "judge": self._build_step_state(record, "judge"),
                "generate": self._build_step_state(record, "generate"),
            },
            "parse": {
                "file_id": file_id,
                "text": str(record.get("parsed_text", "")),
            },
            "extract": record.get("extract_result", {}) or {},
            "judge": record.get("judge_result", {}) or {},
            "generate": self._initialize_generate_result(record.get("generate_result", {}) or {}),
        }

    def _build_step_state(self, record: dict, step: str) -> dict:
        status = str(record.get(f"{step}_status", "pending") or "pending").strip() or "pending"
        if status == "success":
            return {"status": "success", "message": self._get_step_success_message(step)}
        if status == "error":
            return {
                "status": "error",
                "message": self._get_step_error_message(record, step),
            }
        if status == "loading":
            return {"status": "loading", "message": self._get_step_loading_message(step)}
        return {"status": "pending", "message": self._get_step_pending_message(step)}

    def _get_step_error_message(self, record: dict, step: str) -> str:
        record_message = str(record.get(f"{step}_error", "") or "").strip()
        if record_message:
            return record_message
        if step in self._empty_agent_artifacts():
            status_payload = self.artifact_service.read_status(str(record.get("file_id", "")), step)
            artifact_message = str(status_payload.get("error", "") or "").strip()
            if artifact_message:
                return artifact_message
        return f"{step} step failed"

    def _get_step_success_message(self, step: str) -> str:
        return {
            "parse": "文本解析完成",
            "extract": "字段抽取完成",
            "judge": "投标判断完成",
            "generate": "标书生成完成",
        }.get(step, "处理完成")

    def _get_step_loading_message(self, step: str) -> str:
        return {
            "parse": "正在解析文本...",
            "extract": "正在抽取核心字段...",
            "judge": "正在生成投标建议...",
            "generate": "正在生成标书初稿...",
        }.get(step, "处理中...")

    def _get_step_pending_message(self, step: str) -> str:
        return {
            "parse": "等待解析",
            "extract": "等待抽取",
            "judge": "等待判断",
            "generate": "等待生成",
        }.get(step, "等待处理")

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
