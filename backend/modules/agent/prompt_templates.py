import base64
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


def build_collect_prompt(source: str, targeting: dict | None = None) -> str:
    targeting = targeting or {
        "mode": "broad",
        "profile_key": "",
        "profile_title": "",
        "keywords": [],
        "regions": [],
        "notice_types": [],
        "exclude_keywords": [],
        "qualification_terms": [],
        "industry_terms": [],
    }
    command = "python scripts/collect_ggzy.py"
    if targeting.get("mode") in {"targeted", "keyword"}:
        targeting_payload = base64.urlsafe_b64encode(
            json.dumps(targeting, ensure_ascii=False).encode("utf-8")
        ).decode("ascii")
        command += f" --targeting-json-b64 \"{targeting_payload}\""

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
        - Collect targeting:
        {json.dumps(targeting, ensure_ascii=False, indent=2)}
        - In the collect workspace, run exactly:
          {command}
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
        First generate a bid proposal outline only.
        Do not write long body paragraphs yet.

        Return exactly one JSON object:
        {{
          "proposal_outline": [
            {{
              "section_id": "1",
              "title": "",
              "purpose": "",
              "children": [
                {{
                  "section_id": "1.1",
                  "title": "",
                  "purpose": "",
                  "writing_points": ["", "", ""]
                }}
              ]
            }}
          ],
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
        - proposal_outline should contain 4 to 6 parent chapters
        - Each parent chapter should contain 2 to 4 child sections
        - Child sections should have short writing points, not long paragraphs
        - Body fields should only contain short drafting notes for later expansion
        - Keep the output business-oriented and reusable
        - JSON only
        """
    ).strip()


def build_generate_section_prompt(
    tender_fields: dict,
    judge_result: dict,
    knowledge_context: dict,
    parent_section: dict,
    child_section: dict,
) -> str:
    return dedent(
        f"""
        You are generate_agent.
        Write the body content for one bid proposal subsection only.

        Return exactly one JSON object:
        {{
          "content": ""
        }}

        Parent chapter:
        {json.dumps(parent_section, ensure_ascii=False, indent=2)}

        Current subsection:
        {json.dumps(child_section, ensure_ascii=False, indent=2)}

        Tender fields:
        {json.dumps(tender_fields, ensure_ascii=False, indent=2)}

        Judge result:
        {json.dumps(judge_result, ensure_ascii=False, indent=2)}

        Enterprise knowledge:
        {knowledge_context.get("context_text") or "No knowledge snippets found."}

        Constraints:
        - Only generate the current subsection body
        - Do not repeat unrelated chapters
        - Keep the content practical, formal, and suitable for bid writing
        - Prefer concise paragraphs and bullet-friendly wording
        - JSON only
        """
    ).strip()
