import json
from textwrap import dedent


def build_judge_prompt(tender_fields: dict, knowledge_context: dict) -> str:
    return dedent(
        f"""
        你是 judge_agent。
        任务：结合招标字段和企业知识片段，判断当前项目是否建议投标。

        输出 JSON：
        {{
          "should_bid": true,
          "reason": "简洁说明是否建议投标",
          "risks": ["风险1", "风险2"]
        }}

        招标字段：
        {json.dumps(tender_fields, ensure_ascii=False, indent=2)}

        企业知识片段：
        {knowledge_context.get("context_text") or "暂无可用知识片段"}

        约束：
        - 优先参考 qualifications 和 project_cases。
        - 如果知识不足，必须在 risks 中明确说明。
        - 输出必须是结构化 JSON。
        """
    ).strip()


def build_generate_prompt(tender_fields: dict, judge_result: dict, knowledge_context: dict) -> str:
    return dedent(
        f"""
        你是 generate_agent。
        任务：结合招标字段、投标判断结果和企业知识片段，生成标书初稿。

        输出 JSON：
        {{
          "company_intro": "",
          "project_cases": "",
          "implementation_plan": "",
          "business_response": ""
        }}

        招标字段：
        {json.dumps(tender_fields, ensure_ascii=False, indent=2)}

        投标判断：
        {json.dumps(judge_result, ensure_ascii=False, indent=2)}

        企业知识片段：
        {knowledge_context.get("context_text") or "暂无可用知识片段"}

        约束：
        - 优先参考 company_profile、templates、project_cases。
        - 标书内容必须分区输出，不能遗漏字段。
        - 输出必须是结构化 JSON。
        """
    ).strip()
