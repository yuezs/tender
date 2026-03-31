from modules.agent.generate_agent import GenerateAgent
from modules.agent.judge_agent import JudgeAgent
from modules.knowledge.service import KnowledgeService


class AgentOrchestrator:
    TASK_SOURCE_MAP = {
        "judge": ["qualifications", "project_cases"],
        "generate": ["company_profile", "templates", "project_cases"],
    }

    def __init__(self) -> None:
        self.knowledge_service = KnowledgeService()
        self.judge_agent = JudgeAgent()
        self.generate_agent = GenerateAgent()

    def run_judge(self, db, tender_record: dict) -> dict:
        tender_fields = tender_record.get("extract_result", {})
        knowledge_context = self._build_knowledge_context(db, task_type="judge", tender_fields=tender_fields)
        return self.judge_agent.run(tender_fields=tender_fields, knowledge_context=knowledge_context)

    def run_generate(self, db, tender_record: dict, judge_result: dict) -> dict:
        tender_fields = tender_record.get("extract_result", {})
        knowledge_context = self._build_knowledge_context(db, task_type="generate", tender_fields=tender_fields)
        return self.generate_agent.run(
            tender_fields=tender_fields,
            judge_result=judge_result,
            knowledge_context=knowledge_context,
        )

    def select_sources(self, task_type: str) -> list[str]:
        return self.TASK_SOURCE_MAP.get(task_type, [])

    def _build_knowledge_context(self, db, task_type: str, tender_fields: dict) -> dict:
        source_categories = self.select_sources(task_type)
        collected_chunks: list[dict] = []
        seen_ids: set[str] = set()

        for category in source_categories:
            payload = {
                "category": category,
                "query": self._build_query(category, tender_fields),
                "tags": [],
                "industry": [],
                "limit": self._build_limit(task_type, category),
            }
            retrieved = self.knowledge_service.retrieve(db, payload)
            for chunk in retrieved.get("chunks", []):
                chunk_id = str(chunk.get("id", "")).strip()
                if not chunk_id or chunk_id in seen_ids:
                    continue
                seen_ids.add(chunk_id)
                collected_chunks.append(
                    {
                        "id": chunk_id,
                        "category": category,
                        "document_id": chunk.get("document_id", ""),
                        "document_title": chunk.get("document_title", ""),
                        "section_title": chunk.get("section_title", ""),
                        "content": chunk.get("content", ""),
                    }
                )

        return {
            "task_type": task_type,
            "source_categories": source_categories,
            "chunks": collected_chunks,
            "context_text": self._format_context_text(collected_chunks),
        }

    def _build_query(self, category: str, tender_fields: dict) -> str:
        project_name = str(tender_fields.get("project_name", "")).strip()
        tender_company = str(tender_fields.get("tender_company", "")).strip()
        qualifications = tender_fields.get("qualification_requirements") or []
        delivery_requirements = tender_fields.get("delivery_requirements") or []
        scoring_focus = tender_fields.get("scoring_focus") or []

        if category == "qualifications":
            return str(qualifications[0]).strip()[:40] if qualifications else "资质"
        if category == "project_cases":
            return project_name[:40] or tender_company[:40] or "项目案例"
        if category == "templates":
            return (
                (str(scoring_focus[0]).strip()[:40] if scoring_focus else "")
                or (str(delivery_requirements[0]).strip()[:40] if delivery_requirements else "")
                or "实施方案"
            )
        if category == "company_profile":
            return ""
        return project_name[:40]

    def _build_limit(self, task_type: str, category: str) -> int:
        if task_type == "generate" and category == "templates":
            return 3
        return 2

    def _format_context_text(self, chunks: list[dict]) -> str:
        if not chunks:
            return "暂无可用知识片段。"

        lines: list[str] = []
        for chunk in chunks:
            category = chunk.get("category", "")
            document_title = chunk.get("document_title", "")
            section_title = chunk.get("section_title", "")
            content = str(chunk.get("content", "")).strip().replace("\n", " ")
            lines.append(
                f"[{category}] {document_title} / {section_title}: {content[:220]}"
            )
        return "\n".join(lines)
