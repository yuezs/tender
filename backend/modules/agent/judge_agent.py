from modules.agent.output_parser import ensure_judge_result
from modules.agent.prompt_templates import build_judge_prompt


class JudgeAgent:
    def run(self, tender_fields: dict, knowledge_context: dict) -> dict:
        prompt = build_judge_prompt(tender_fields, knowledge_context)
        knowledge_chunks = knowledge_context.get("chunks", [])
        qualification_hits = [chunk for chunk in knowledge_chunks if chunk.get("category") == "qualifications"]
        case_hits = [chunk for chunk in knowledge_chunks if chunk.get("category") == "project_cases"]

        risks: list[str] = []
        if not tender_fields.get("budget"):
            risks.append("预算金额未明确，项目投入产出比需要人工复核。")
        if not tender_fields.get("deadline"):
            risks.append("投标截止时间未明确，时间窗口存在不确定性。")
        if not qualification_hits:
            risks.append("知识库未检索到可复用的资质材料，资质响应支撑不足。")
        if not case_hits:
            risks.append("知识库未检索到类似项目案例，案例支撑不足。")
        if not tender_fields.get("qualification_requirements"):
            risks.append("招标文件中的资质要求提取不足，需人工核验准入条件。")

        should_bid = len(risks) <= 2 and (bool(qualification_hits) or bool(case_hits))
        if should_bid:
            reason = "已检索到可复用的企业资质或项目案例，且当前关键信息相对完整，建议继续推进投标评估。"
        else:
            reason = "知识支撑或关键信息仍不充分，建议先补齐资质材料与案例证据后再决定是否投标。"

        raw_result = {
            "should_bid": should_bid,
            "reason": reason,
            "risks": risks,
        }
        return ensure_judge_result(raw_result, knowledge_context, prompt)
