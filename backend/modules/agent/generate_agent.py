from modules.agent.output_parser import ensure_generate_result
from modules.agent.prompt_templates import build_generate_prompt


class GenerateAgent:
    def run(self, tender_fields: dict, judge_result: dict, knowledge_context: dict) -> dict:
        prompt = build_generate_prompt(tender_fields, judge_result, knowledge_context)
        chunks = knowledge_context.get("chunks", [])

        company_profile_chunks = [chunk for chunk in chunks if chunk.get("category") == "company_profile"]
        template_chunks = [chunk for chunk in chunks if chunk.get("category") == "templates"]
        project_case_chunks = [chunk for chunk in chunks if chunk.get("category") == "project_cases"]

        project_name = tender_fields.get("project_name") or "待确认项目"
        tender_company = tender_fields.get("tender_company") or "待确认招标单位"
        scoring_focus = tender_fields.get("scoring_focus") or []
        delivery_requirements = tender_fields.get("delivery_requirements") or []

        company_snippet = self._join_chunk_contents(company_profile_chunks, fallback="建议补充公司概况、核心能力和行业资质。")
        template_snippet = self._join_chunk_contents(template_chunks, fallback="建议补充实施方案模板、商务响应模板和交付模板。")
        case_snippet = self._join_chunk_contents(project_case_chunks, fallback="建议补充行业相关案例、项目成果和交付经验。")

        raw_result = {
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
                f"建议围绕评分重点 {'；'.join(scoring_focus[:3]) or '待补充评分重点'} 组织实施章节。\n"
                f"关键交付要求：{'；'.join(delivery_requirements[:3]) or '待补充交付要求'}。\n"
                f"可复用模板摘要：{template_snippet}"
            ),
            "business_response": (
                "商务响应草稿（初稿）\n"
                f"投标建议：{'建议推进' if judge_result.get('should_bid') else '建议谨慎评估'}。\n"
                f"判断理由：{judge_result.get('reason', '待补充判断理由')}。\n"
                "正式版本需补充报价、商务偏离表、服务承诺和履约安排。"
            ),
        }

        return ensure_generate_result(raw_result, knowledge_context, prompt)

    def _join_chunk_contents(self, chunks: list[dict], fallback: str) -> str:
        if not chunks:
            return fallback

        snippets: list[str] = []
        for chunk in chunks[:3]:
            content = str(chunk.get("content", "")).strip().replace("\n", " ")
            if content:
                snippets.append(content[:160])
        return "；".join(snippets) if snippets else fallback
