import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

from sqlalchemy.orm import Session

from core.config import settings
from core.exceptions import BusinessException
from modules.agent.service import AgentService
from modules.discovery.artifacts import DiscoveryRunArtifactService
from modules.discovery.repository import DiscoveryRepository
from modules.knowledge.service import KnowledgeService


class DiscoveryService:
    SUPPORTED_SOURCES = ("ggzy",)

    def __init__(self) -> None:
        self.repository = DiscoveryRepository()
        self.agent_service = AgentService()
        self.knowledge_service = KnowledgeService()
        self.artifact_service = DiscoveryRunArtifactService()
        self.storage_root = settings.storage_root / "discovery" / "leads"
        self.storage_root.mkdir(parents=True, exist_ok=True)

    def get_module_status(self) -> dict:
        if settings.agent_use_real_llm and settings.discovery_collect_use_openclaw_agent:
            collect_mode = "openclaw-agent"
        else:
            collect_mode = "disabled"
        return {
            "module": "discovery",
            "status": "ready",
            "message": "discovery module is ready for manual project collection",
            "mock": False,
            "collect_mode": collect_mode,
            "available_routes": [
                "/api/discovery/status",
                "/api/discovery/runs",
                "/api/discovery/projects",
                "/api/discovery/projects/{lead_id}",
            ],
            "supported_sources": list(self.SUPPORTED_SOURCES),
            "repository_ready": self.repository.is_ready(),
        }

    def run_collection(self, db: Session, source: str) -> dict:
        normalized_source = source.strip().lower()
        self._validate_source(normalized_source)

        run_id = uuid4().hex
        started_at = datetime.utcnow()
        run = self.repository.create_run(
            db,
            {
                "run_id": run_id,
                "source": normalized_source,
                "trigger_type": "manual",
                "status": "running",
                "started_at": started_at,
                "finished_at": None,
                "total_found": 0,
                "total_new": 0,
                "total_updated": 0,
                "error_message": "",
            },
        )

        prepared = self.agent_service.prepare_collect(source=normalized_source)
        execution_context = {
            "session_key": f"agent:{prepared['agent_id']}:discovery:{run_id}:collect",
            "idempotency_key": run_id,
        }

        self.artifact_service.write_input(
            run_id,
            {
                "run_id": run_id,
                "source": normalized_source,
                "agent_id": prepared["agent_id"],
                "prompt": prepared["prompt"],
                "session_key": execution_context["session_key"],
                "idempotency_key": execution_context["idempotency_key"],
            },
        )
        self.artifact_service.write_status(
            run_id,
            {
                "state": "running",
                "started_at": started_at.isoformat(),
                "finished_at": "",
                "error": "",
            },
        )

        try:
            agent_payload = self.agent_service.run_collect(
                prepared,
                execution_context=execution_context,
            )
            self.artifact_service.write_output(
                run_id,
                {
                    "raw_text": agent_payload.get("raw_text", ""),
                    "parsed_result": agent_payload.get("result", {}),
                    "debug": agent_payload.get("debug", {}),
                },
            )
            self.artifact_service.write_status(
                run_id,
                {
                    "state": "success",
                    "started_at": started_at.isoformat(),
                    "finished_at": datetime.utcnow().isoformat(),
                    "error": "",
                },
            )

            total_new = 0
            total_updated = 0
            projects = agent_payload["result"].get("projects", [])
            for raw_project in projects:
                change_type = self._upsert_project_lead(db, normalized_source, raw_project)
                if change_type == "created":
                    total_new += 1
                elif change_type == "updated":
                    total_updated += 1

            updated_run = self.repository.update_run(
                db,
                run.run_id,
                {
                    "status": "success",
                    "finished_at": datetime.utcnow(),
                    "total_found": len(projects),
                    "total_new": total_new,
                    "total_updated": total_updated,
                    "error_message": "",
                },
            )
            return self._serialize_run(updated_run)
        except BusinessException as exc:
            self.artifact_service.write_status(
                run_id,
                {
                    "state": "error",
                    "started_at": started_at.isoformat(),
                    "finished_at": datetime.utcnow().isoformat(),
                    "error": exc.message,
                },
            )
            self.repository.update_run(
                db,
                run.run_id,
                {
                    "status": "error",
                    "finished_at": datetime.utcnow(),
                    "error_message": exc.message,
                },
            )
            raise

    def list_runs(self, db: Session) -> dict:
        return {
            "items": [self._serialize_run(item) for item in self.repository.list_runs(db)],
        }

    def list_projects(
        self,
        db: Session,
        *,
        keyword: str,
        region: str,
        notice_type: str,
        recommendation_level: str,
        recommended_only: bool,
        page: int,
        page_size: int,
    ) -> dict:
        items, total = self.repository.list_projects(
            db,
            keyword=keyword.strip(),
            region=region.strip(),
            notice_type=notice_type.strip(),
            recommendation_level=recommendation_level.strip(),
            recommended_only=recommended_only,
            page=page,
            page_size=page_size,
        )
        return {
            "items": [self._serialize_lead_list_item(item) for item in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def get_project_detail(self, db: Session, lead_id: str) -> dict:
        lead = self.repository.get_lead(db, lead_id)
        extract_result = self._load_json(lead.extract_result_json)
        match_result = self._load_json(lead.match_result_json)
        return {
            "lead_id": lead.lead_id,
            "source": lead.source,
            "title": lead.title,
            "notice_type": lead.notice_type,
            "region": lead.region,
            "published_at": self._format_datetime(lead.published_at) or "",
            "detail_url": lead.detail_url,
            "canonical_url": lead.canonical_url,
            "extract_result": {
                "project_name": extract_result.get("project_name", ""),
                "tender_unit": extract_result.get("tender_unit", ""),
                "project_code": extract_result.get("project_code", ""),
                "region": extract_result.get("region", ""),
                "budget_text": extract_result.get("budget_text", ""),
                "deadline_text": extract_result.get("deadline_text", ""),
                "notice_type": extract_result.get("notice_type", ""),
                "published_at": extract_result.get("published_at", ""),
                "qualification_requirements": extract_result.get("qualification_requirements", []),
                "keywords": extract_result.get("keywords", []),
            },
            "match_result": {
                "recommendation_score": int(match_result.get("recommendation_score", 0)),
                "recommendation_level": str(match_result.get("recommendation_level", "low")),
                "recommendation_reasons": match_result.get("recommendation_reasons", []),
                "risks": match_result.get("risks", []),
                "matched_knowledge": match_result.get("matched_knowledge", []),
            },
            "detail_text": self._read_text(lead.detail_text_path),
        }

    def _validate_source(self, source: str) -> None:
        if source not in self.SUPPORTED_SOURCES:
            raise BusinessException("unsupported discovery source")
        if source == "ggzy" and not settings.discovery_source_enabled_ggzy:
            raise BusinessException("ggzy discovery source is disabled")

    def _upsert_project_lead(self, db: Session, source: str, raw_project: dict) -> str:
        normalized = self._normalize_project(raw_project, source)
        existing = self.repository.find_existing_lead(
            db,
            source=source,
            canonical_url=normalized["canonical_url"],
            source_notice_id=normalized["source_notice_id"],
            title=normalized["title"],
            published_at=normalized["published_at"],
        )

        lead_id = existing.lead_id if existing else uuid4().hex
        extract_result = self._extract_fields(normalized)
        match_result = self._build_match_result(db, extract_result)
        paths = self._persist_lead_files(lead_id, normalized)

        payload = {
            "source": source,
            "source_notice_id": normalized["source_notice_id"],
            "title": normalized["title"],
            "notice_type": extract_result["notice_type"],
            "region": extract_result["region"],
            "published_at": normalized["published_at"],
            "detail_url": normalized["detail_url"],
            "canonical_url": normalized["canonical_url"],
            "project_code": extract_result["project_code"],
            "tender_unit": extract_result["tender_unit"],
            "budget_text": extract_result["budget_text"],
            "deadline_text": extract_result["deadline_text"],
            "detail_text_path": paths["detail_text_path"],
            "raw_snapshot_path": paths["raw_snapshot_path"],
            "extract_result_json": json.dumps(extract_result, ensure_ascii=False),
            "match_result_json": json.dumps(match_result, ensure_ascii=False),
            "recommendation_score": int(match_result["recommendation_score"]),
            "recommendation_level": str(match_result["recommendation_level"]),
            "status": "active",
        }

        if existing:
            self.repository.update_lead(db, lead_id, payload)
            return "updated"

        self.repository.create_lead(
            db,
            {
                "lead_id": lead_id,
                **payload,
            },
        )
        return "created"

    def _normalize_project(self, raw_project: dict, source: str) -> dict:
        title = str(raw_project.get("title", "")).strip()
        if not title:
            raise BusinessException("collect result item is missing title")

        detail_url = str(raw_project.get("detail_url", "")).strip()
        if not detail_url:
            raise BusinessException("collect result item is missing detail_url")

        canonical_url = str(raw_project.get("canonical_url", "")).strip() or detail_url
        detail_text = str(raw_project.get("detail_text", "")).strip()
        source_notice_id = str(raw_project.get("source_notice_id", "")).strip() or self._extract_notice_id(
            canonical_url
        )

        return {
            "source": source,
            "source_notice_id": source_notice_id,
            "title": title,
            "notice_type": str(raw_project.get("notice_type", "")).strip(),
            "region": str(raw_project.get("region", "")).strip(),
            "published_at": self._parse_datetime(raw_project.get("published_at")),
            "detail_url": detail_url,
            "canonical_url": canonical_url,
            "project_code": str(raw_project.get("project_code", "")).strip(),
            "tender_unit": str(raw_project.get("tender_unit", "")).strip(),
            "budget_text": str(raw_project.get("budget_text", "")).strip(),
            "deadline_text": str(raw_project.get("deadline_text", "")).strip(),
            "detail_text": detail_text,
            "qualification_requirements": self._normalize_list(
                raw_project.get("qualification_requirements")
            ),
            "keywords": self._normalize_list(raw_project.get("keywords")),
            "published_at_text": str(raw_project.get("published_at", "")).strip(),
        }

    def _extract_fields(self, normalized: dict) -> dict:
        detail_text = normalized["detail_text"]
        title = normalized["title"]

        notice_type = normalized["notice_type"] or self._infer_notice_type(title)
        tender_unit = normalized["tender_unit"] or self._find_first_match(
            detail_text,
            [r"(?:招标人|采购人|招标单位|采购单位)[:：]\s*([^\n\r]+)"],
        )
        project_code = normalized["project_code"] or self._find_first_match(
            detail_text,
            [r"(?:项目编号|招标编号|采购编号|项目代码)[:：]\s*([^\n\r]+)"],
        )
        budget_text = normalized["budget_text"] or self._find_first_match(
            detail_text,
            [r"(?:预算金额|项目预算|最高限价|控制价)[:：]?\s*([^\n\r]+)"],
        )
        deadline_text = normalized["deadline_text"] or self._find_first_match(
            detail_text,
            [r"(?:投标截止时间|开标时间|响应文件提交截止时间)[:：]?\s*([^\n\r]+)"],
        )
        qualifications = normalized["qualification_requirements"] or self._collect_lines(
            detail_text,
            ["资质", "资格", "证书", "业绩"],
            limit=4,
        )
        project_name = self._find_first_match(
            detail_text,
            [r"(?:项目名称|招标项目名称|采购项目名称)[:：]\s*([^\n\r]+)"],
        ) or title
        published_at_text = normalized["published_at_text"] or self._format_datetime(
            normalized["published_at"]
        ) or ""

        keywords = self._build_keywords(
            normalized["keywords"],
            [
                project_name,
                normalized["region"],
                project_code,
                title,
                *qualifications[:2],
            ],
        )

        return {
            "project_name": project_name,
            "tender_unit": tender_unit,
            "project_code": project_code,
            "region": normalized["region"],
            "budget_text": budget_text,
            "deadline_text": deadline_text,
            "notice_type": notice_type,
            "published_at": published_at_text,
            "qualification_requirements": qualifications,
            "keywords": keywords,
        }

    def _build_match_result(self, db: Session, extract_result: dict) -> dict:
        qualification_query = (
            extract_result["qualification_requirements"][0]
            if extract_result["qualification_requirements"]
            else (extract_result["project_name"] or "资质")
        )
        project_case_query = (
            extract_result["keywords"][0]
            if extract_result["keywords"]
            else (extract_result["project_name"] or "项目案例")
        )

        qualifications = self.knowledge_service.retrieve(
            db,
            {
                "category": "qualifications",
                "query": qualification_query,
                "tags": [],
                "industry": [],
                "limit": 3,
            },
        ).get("chunks", [])
        project_cases = self.knowledge_service.retrieve(
            db,
            {
                "category": "project_cases",
                "query": project_case_query,
                "tags": [],
                "industry": [],
                "limit": 3,
            },
        ).get("chunks", [])
        company_profile = self.knowledge_service.retrieve(
            db,
            {
                "category": "company_profile",
                "query": "",
                "tags": [],
                "industry": [],
                "limit": 2,
            },
        ).get("chunks", [])

        score = 0
        reasons: list[str] = []
        risks: list[str] = []

        if qualifications:
            score += 35
            reasons.append("命中企业资质材料，可支撑资格匹配。")
        else:
            risks.append("未命中相关资质材料，资格匹配支撑不足。")

        if project_cases:
            score += 30
            reasons.append("命中同类项目案例，可支撑履约经验说明。")
        else:
            risks.append("未命中同类项目案例，案例支撑不足。")

        if company_profile:
            score += 10
            reasons.append("可复用企业基础资料补充推荐说明。")

        complete_fields = [
            extract_result.get("project_name"),
            extract_result.get("tender_unit"),
            extract_result.get("project_code"),
            extract_result.get("budget_text"),
            extract_result.get("deadline_text"),
            extract_result.get("published_at"),
        ]
        completeness_hits = sum(1 for item in complete_fields if str(item).strip())
        if completeness_hits:
            score += min(completeness_hits * 5, 25)
            reasons.append(f"关键字段完整度较好，已识别 {completeness_hits} 项核心信息。")

        if not extract_result.get("qualification_requirements"):
            score -= 15
            risks.append("资格要求提取不足，需要人工复核。")
        if not extract_result.get("budget_text"):
            score -= 10
            risks.append("预算信息缺失，需要补充商务评估。")
        if self._is_deadline_urgent(extract_result.get("deadline_text", "")):
            score -= 10
            risks.append("截止时间较近，推进窗口偏紧。")

        score = max(0, min(score, 100))
        recommendation_level = self._map_recommendation_level(score)

        matched_knowledge = []
        for category, chunks in (
            ("qualifications", qualifications),
            ("project_cases", project_cases),
            ("company_profile", company_profile),
        ):
            for chunk in chunks:
                matched_knowledge.append(
                    {
                        "category": category,
                        "document_title": chunk.get("document_title", ""),
                        "section_title": chunk.get("section_title", ""),
                    }
                )

        return {
            "recommendation_score": score,
            "recommendation_level": recommendation_level,
            "recommendation_reasons": reasons,
            "risks": risks,
            "matched_knowledge": matched_knowledge,
        }

    def _persist_lead_files(self, lead_id: str, normalized: dict) -> dict:
        lead_dir = self.storage_root / lead_id
        lead_dir.mkdir(parents=True, exist_ok=True)

        detail_text_path = lead_dir / "detail.txt"
        raw_snapshot_path = lead_dir / "raw_snapshot.json"

        detail_text_path.write_text(normalized.get("detail_text", ""), encoding="utf-8")
        raw_snapshot_path.write_text(
            json.dumps(normalized, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )

        return {
            "detail_text_path": str(detail_text_path),
            "raw_snapshot_path": str(raw_snapshot_path),
        }

    def _serialize_run(self, item) -> dict:
        return {
            "run_id": item.run_id,
            "source": item.source,
            "trigger_type": item.trigger_type,
            "status": item.status,
            "started_at": self._format_datetime(item.started_at) or "",
            "finished_at": self._format_datetime(item.finished_at),
            "total_found": item.total_found,
            "total_new": item.total_new,
            "total_updated": item.total_updated,
            "error_message": item.error_message,
        }

    def _serialize_lead_list_item(self, item) -> dict:
        match_result = self._load_json(item.match_result_json)
        return {
            "lead_id": item.lead_id,
            "source": item.source,
            "title": item.title,
            "notice_type": item.notice_type,
            "region": item.region,
            "published_at": self._format_datetime(item.published_at) or "",
            "project_code": item.project_code,
            "tender_unit": item.tender_unit,
            "budget_text": item.budget_text,
            "deadline_text": item.deadline_text,
            "recommendation_score": item.recommendation_score,
            "recommendation_level": item.recommendation_level,
            "recommendation_reasons": match_result.get("recommendation_reasons", []),
        }

    def _load_json(self, raw_value: str) -> dict:
        try:
            data = json.loads(raw_value)
        except (TypeError, json.JSONDecodeError):
            return {}
        return data if isinstance(data, dict) else {}

    def _read_text(self, path_value: str) -> str:
        if not path_value:
            return ""
        path = Path(path_value)
        if not path.exists():
            return ""
        try:
            return path.read_text(encoding="utf-8")
        except OSError:
            return ""

    def _parse_datetime(self, value: object) -> datetime | None:
        if isinstance(value, datetime):
            return value
        if not isinstance(value, str):
            return None

        candidate = value.strip()
        if not candidate:
            return None
        candidate = candidate.replace("/", "-")

        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                return datetime.strptime(candidate, fmt)
            except ValueError:
                continue
        return None

    def _format_datetime(self, value: datetime | None) -> str | None:
        if value is None:
            return None
        return value.isoformat(sep=" ", timespec="seconds")

    def _normalize_list(self, value: object) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        return []

    def _find_first_match(self, text: str, patterns: list[str]) -> str:
        for pattern in patterns:
            matched = re.search(pattern, text, re.IGNORECASE)
            if matched:
                return re.sub(r"\s+", " ", matched.group(1)).strip(" ：:;，。")
        return ""

    def _collect_lines(self, text: str, keywords: list[str], limit: int = 4) -> list[str]:
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

    def _infer_notice_type(self, title: str) -> str:
        if "公开招标" in title:
            return "公开招标公告"
        if "采购公告" in title:
            return "采购公告"
        if "招标公告" in title:
            return "招标公告"
        return ""

    def _build_keywords(self, existing: list[str], candidates: list[str]) -> list[str]:
        keywords: list[str] = []
        for value in [*existing, *candidates]:
            cleaned = str(value).strip()
            if cleaned and cleaned not in keywords:
                keywords.append(cleaned[:80])
        return keywords[:6]

    def _extract_notice_id(self, url: str) -> str:
        for pattern in (
            r"([A-Z]{2,}\d{4,})",
            r"/([A-Za-z0-9_-]{8,})$",
            r"tenderproject/([^/?]+)",
        ):
            matched = re.search(pattern, url)
            if matched:
                return matched.group(1)
        return ""

    def _map_recommendation_level(self, score: int) -> str:
        if score >= 80:
            return "high"
        if score >= 60:
            return "medium"
        return "low"

    def _is_deadline_urgent(self, deadline_text: str) -> bool:
        deadline = self._parse_datetime(deadline_text)
        if deadline is None:
            return False
        return deadline <= datetime.utcnow() + timedelta(days=7)
