def _normalize_text(value: object, fallback: str = "") -> str:
    if isinstance(value, str):
        return value.strip()
    return fallback


def _normalize_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        if isinstance(item, str):
            cleaned = item.strip()
            if cleaned:
                items.append(cleaned)
    return items


def _build_knowledge_used(knowledge_context: dict) -> list[dict]:
    references = []
    seen: set[tuple[str, str, str]] = set()
    for chunk in knowledge_context.get("chunks", []):
        key = (
            _normalize_text(chunk.get("category")),
            _normalize_text(chunk.get("document_title")),
            _normalize_text(chunk.get("section_title")),
        )
        if key in seen:
            continue
        seen.add(key)
        references.append(
            {
                "category": key[0],
                "document_title": key[1],
                "section_title": key[2],
            }
        )
    return references


def ensure_judge_result(raw_result: dict, knowledge_context: dict, prompt: str) -> dict:
    return {
        "should_bid": bool(raw_result.get("should_bid")),
        "reason": _normalize_text(raw_result.get("reason"), "暂未生成明确判断理由。"),
        "risks": _normalize_list(raw_result.get("risks")),
        "knowledge_used": _build_knowledge_used(knowledge_context),
        "prompt_preview": prompt[:1200],
    }


def ensure_generate_result(raw_result: dict, knowledge_context: dict, prompt: str) -> dict:
    return {
        "company_intro": _normalize_text(raw_result.get("company_intro"), "公司介绍（初稿）\n待补充企业资料。"),
        "project_cases": _normalize_text(raw_result.get("project_cases"), "类似项目经验（初稿）\n待补充项目案例。"),
        "implementation_plan": _normalize_text(
            raw_result.get("implementation_plan"),
            "实施方案概述（初稿）\n待补充实施路径。",
        ),
        "business_response": _normalize_text(
            raw_result.get("business_response"),
            "商务响应草稿（初稿）\n待补充商务条款。",
        ),
        "knowledge_used": _build_knowledge_used(knowledge_context),
        "prompt_preview": prompt[:1200],
    }
