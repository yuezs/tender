import json
from textwrap import dedent


def build_extract_prompt(parsed_text: str) -> str:
    preview_text = parsed_text[:12000]
    return dedent(
        f"""
        You are extract_agent.
        Read the tender text and return exactly one JSON object.

        Required JSON schema:
        {{
          "project_name": "",
          "tender_company": "",
          "budget": "",
          "deadline": "",
          "qualification_requirements": [],
          "delivery_requirements": [],
          "scoring_focus": []
        }}

        Rules:
        - JSON only
        - No markdown
        - Unknown string fields must be ""
        - Unknown list fields must be []

        Tender text:
        {preview_text}
        """
    ).strip()


def build_collect_prompt(source: str) -> str:
    return dedent(
        f"""
        You are collect_agent.
        Collect public project notice leads from {source}.

        Return exactly one JSON object:
        {{
          "projects": [
            {{
              "source": "ggzy",
              "source_notice_id": "",
              "title": "",
              "notice_type": "",
              "region": "",
              "published_at": "",
              "detail_url": "",
              "canonical_url": "",
              "project_code": "",
              "tender_unit": "",
              "budget_text": "",
              "deadline_text": "",
              "detail_text": "",
              "qualification_requirements": [],
              "keywords": []
            }}
          ]
        }}

        Constraints:
        - Source must be ggzy only
        - Start from https://www.ggzy.gov.cn/
        - In the collect workspace, run: python scripts/collect_ggzy.py
        - Return the exact JSON printed by that script
        - Do not add markdown, explanations, or commentary
        - Do not download attachments
        - Do not output any attachment urls or local file paths
        - Do not enter the bid-generation workflow
        - JSON only
        """
    ).strip()


def build_judge_prompt(tender_fields: dict, knowledge_context: dict) -> str:
    return dedent(
        f"""
        You are judge_agent.
        Decide whether this tender is recommended for bidding.

        Return exactly one JSON object:
        {{
          "should_bid": true,
          "reason": "short business judgement",
          "risks": ["risk 1", "risk 2"]
        }}

        Tender fields:
        {json.dumps(tender_fields, ensure_ascii=False, indent=2)}

        Enterprise knowledge:
        {knowledge_context.get("context_text") or "No knowledge snippets found."}

        Constraints:
        - Prioritize qualifications and project cases
        - If knowledge is weak, say so in risks
        - JSON only
        """
    ).strip()


def build_generate_prompt(tender_fields: dict, judge_result: dict, knowledge_context: dict) -> str:
    return dedent(
        f"""
        You are generate_agent.
        Generate a first draft for the bid response using tender fields, bid judgement, and enterprise knowledge.

        Return exactly one JSON object:
        {{
          "company_intro": "",
          "project_cases": "",
          "implementation_plan": "",
          "business_response": ""
        }}

        Tender fields:
        {json.dumps(tender_fields, ensure_ascii=False, indent=2)}

        Judge result:
        {json.dumps(judge_result, ensure_ascii=False, indent=2)}

        Enterprise knowledge:
        {knowledge_context.get("context_text") or "No knowledge snippets found."}

        Constraints:
        - Prioritize company_profile, templates, and project_cases
        - Keep the content business-oriented and reusable
        - JSON only
        """
    ).strip()
