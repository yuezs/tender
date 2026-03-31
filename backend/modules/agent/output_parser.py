def _normalize_text(value: object, fallback: str = "") -> str:
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or fallback
    return fallback


def _normalize_list(value: object) -> list[str]:
    if isinstance(value, list):
        items: list[str] = []
        for item in value:
            if isinstance(item, str):
                cleaned = item.strip()
                if cleaned:
                    items.append(cleaned)
        return items

    if isinstance(value, str):
        cleaned = value.strip()
        return [cleaned] if cleaned else []

    return []


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


def ensure_extract_result(raw_result: dict) -> dict:
    return {
        "project_name": _normalize_text(raw_result.get("project_name")),
        "tender_company": _normalize_text(raw_result.get("tender_company")),
        "budget": _normalize_text(raw_result.get("budget")),
        "deadline": _normalize_text(raw_result.get("deadline")),
        "qualification_requirements": _normalize_list(raw_result.get("qualification_requirements")),
        "delivery_requirements": _normalize_list(raw_result.get("delivery_requirements")),
        "scoring_focus": _normalize_list(raw_result.get("scoring_focus")),
    }


def ensure_judge_result(raw_result: dict, knowledge_context: dict, prompt: str) -> dict:
    return {
        "should_bid": bool(raw_result.get("should_bid")),
        "reason": _normalize_text(
            raw_result.get("reason"),
            "未能生成明确投标建议，请先人工复核招标要求和企业资料。",
        ),
        "risks": _normalize_list(raw_result.get("risks")),
        "knowledge_used": _build_knowledge_used(knowledge_context),
        "prompt_preview": prompt[:1200],
    }


def ensure_generate_result(raw_result: dict, knowledge_context: dict, prompt: str) -> dict:
    return {
        "company_intro": _normalize_text(
            raw_result.get("company_intro"),
            "公司介绍待补充，请完善企业知识资料后重试。",
        ),
        "project_cases": _normalize_text(
            raw_result.get("project_cases"),
            "项目案例待补充，请完善项目案例资料后重试。",
        ),
        "implementation_plan": _normalize_text(
            raw_result.get("implementation_plan"),
            "实施方案待补充，请补充模板和项目要求后重试。",
        ),
        "business_response": _normalize_text(
            raw_result.get("business_response"),
            "商务响应待补充，请补充商务模板和投标判断结果后重试。",
        ),
        "knowledge_used": _build_knowledge_used(knowledge_context),
        "prompt_preview": prompt[:1200],
    }
