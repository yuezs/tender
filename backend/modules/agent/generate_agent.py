from core.config import settings
from core.exceptions import BusinessException
from modules.agent.openclaw_client import OpenClawClient
from modules.agent.output_parser import ensure_generate_result, ensure_generate_section_result
from modules.agent.prompt_templates import build_generate_prompt, build_generate_section_prompt


class GenerateAgent:
    def __init__(self) -> None:
        self.client = OpenClawClient()

    def build_prompt(self, tender_fields: dict, judge_result: dict, knowledge_context: dict) -> str:
        return build_generate_prompt(tender_fields, judge_result, knowledge_context)

    def build_section_prompt(
        self,
        tender_fields: dict,
        judge_result: dict,
        knowledge_context: dict,
        parent_section: dict,
        child_section: dict,
    ) -> str:
        return build_generate_section_prompt(
            tender_fields,
            judge_result,
            knowledge_context,
            parent_section,
            child_section,
        )

    def run(
        self,
        tender_fields: dict,
        judge_result: dict,
        knowledge_context: dict,
        *,
        execution_context: dict | None = None,
        prompt: str | None = None,
    ) -> dict:
        prompt = prompt or self.build_prompt(tender_fields, judge_result, knowledge_context)
        execution_context = execution_context or {}
        if not settings.agent_use_real_llm:
            raise BusinessException(
                "Tender generate requires real OpenClaw. Set AGENT_USE_REAL_LLM=true and restart backend."
            )

        llm_response = self._run_llm(prompt=prompt, execution_context=execution_context)
        raw_result = self.client.parse_json_object(llm_response["text"])
        return {
            "result": ensure_generate_result(
                raw_result,
                tender_fields,
                judge_result,
                knowledge_context,
                prompt,
            ),
            "debug": llm_response["debug"],
            "prompt": prompt,
            "raw_text": llm_response["text"],
        }

    def run_section(
        self,
        tender_fields: dict,
        judge_result: dict,
        knowledge_context: dict,
        parent_section: dict,
        child_section: dict,
        *,
        execution_context: dict | None = None,
        prompt: str | None = None,
    ) -> dict:
        prompt = prompt or self.build_section_prompt(
            tender_fields,
            judge_result,
            knowledge_context,
            parent_section,
            child_section,
        )
        execution_context = execution_context or {}
        if not settings.agent_use_real_llm:
            raise BusinessException(
                "Tender generate requires real OpenClaw. Set AGENT_USE_REAL_LLM=true and restart backend."
            )

        llm_response = self._run_llm(prompt=prompt, execution_context=execution_context)
        raw_result = self.client.parse_json_object(llm_response["text"])
        return {
            "result": ensure_generate_section_result(raw_result, knowledge_context, prompt),
            "debug": llm_response["debug"],
            "prompt": prompt,
            "raw_text": llm_response["text"],
        }

    def _run_llm(self, *, prompt: str, execution_context: dict) -> dict:
        run_id = str(execution_context.get("run_id", "")).strip()
        common_kwargs = {
            "agent_id": settings.openclaw_agent_generate,
            "message": prompt,
            "session_key": execution_context["session_key"],
            "idempotency_key": execution_context["idempotency_key"],
        }
        if run_id:
            return self.client.wait_agent_run(run_id=run_id, **common_kwargs)
        return self.client.run_agent(**common_kwargs)

    def _build_fallback_result(
        self,
        tender_fields: dict,
        judge_result: dict,
        knowledge_context: dict,
    ) -> dict:
        chunks = knowledge_context.get("chunks", [])

        company_profile_chunks = [
            chunk for chunk in chunks if chunk.get("category") == "company_profile"
        ]
        template_chunks = [chunk for chunk in chunks if chunk.get("category") == "templates"]
        project_case_chunks = [
            chunk for chunk in chunks if chunk.get("category") == "project_cases"
        ]

        project_name = tender_fields.get("project_name") or "待确认项目"
        tender_company = tender_fields.get("tender_company") or "待确认招标单位"
        scoring_focus = tender_fields.get("scoring_focus") or []
        delivery_requirements = tender_fields.get("delivery_requirements") or []

        company_snippet = self._join_chunk_contents(
            company_profile_chunks,
            fallback="建议补充公司概况、核心能力和行业资质。",
        )
        template_snippet = self._join_chunk_contents(
            template_chunks,
            fallback="建议补充实施方案模板、商务响应模板和交付模板。",
        )
        case_snippet = self._join_chunk_contents(
            project_case_chunks,
            fallback="建议补充行业相关案例、项目成果和交付经验。",
        )

        scoring_text = "、".join(scoring_focus[:3]) if scoring_focus else "待补充评分重点"
        delivery_text = (
            "、".join(delivery_requirements[:3]) if delivery_requirements else "待补充交付要求"
        )
        bid_text = "建议推进" if judge_result.get("should_bid") else "建议谨慎评估"

        return {
            "company_intro": (
                "公司介绍（初稿）\n"
                f"本次拟响应项目为《{project_name}》，招标单位为 {tender_company}。\n"
                f"可直接复用的企业资料摘要：{company_snippet}"
            ),
            "project_cases": (
                "类似项目经验（初稿）\n"
                f"建议优先引用与《{project_name}》场景接近的案例。\n"
                f"当前可复用案例摘要：{case_snippet}"
            ),
            "implementation_plan": (
                "实施方案概述（初稿）\n"
                f"建议围绕评分重点 {scoring_text} 组织实施章节。\n"
                f"关键交付要求：{delivery_text}。\n"
                f"可复用模板摘要：{template_snippet}"
            ),
            "business_response": (
                "商务响应草稿（初稿）\n"
                f"投标建议：{bid_text}。\n"
                f"判断理由：{judge_result.get('reason', '待补充判断理由')}。\n"
                "正式版本仍需补充报价、商务偏离表、服务承诺和履约安排。"
            ),
        }

    def _join_chunk_contents(self, chunks: list[dict], fallback: str) -> str:
        if not chunks:
            return fallback

        snippets: list[str] = []
        for chunk in chunks[:3]:
            content = str(chunk.get("content", "")).strip().replace("\n", " ")
            if content:
                snippets.append(content[:160])
        return "；".join(snippets) if snippets else fallback
