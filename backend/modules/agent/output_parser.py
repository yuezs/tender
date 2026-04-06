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


def _normalize_projects(value: object) -> list[dict]:
    if not isinstance(value, list):
        return []

    normalized: list[dict] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        normalized.append(
            {
                "source": _normalize_text(item.get("source"), "ggzy"),
                "source_notice_id": _normalize_text(item.get("source_notice_id")),
                "title": _normalize_text(item.get("title")),
                "notice_type": _normalize_text(item.get("notice_type")),
                "region": _normalize_text(item.get("region")),
                "published_at": _normalize_text(item.get("published_at")),
                "detail_url": _normalize_text(item.get("detail_url")),
                "canonical_url": _normalize_text(item.get("canonical_url")),
                "project_code": _normalize_text(item.get("project_code")),
                "tender_unit": _normalize_text(item.get("tender_unit")),
                "budget_text": _normalize_text(item.get("budget_text")),
                "deadline_text": _normalize_text(item.get("deadline_text")),
                "detail_text": _normalize_text(item.get("detail_text")),
                "qualification_requirements": _normalize_list(
                    item.get("qualification_requirements")
                ),
                "keywords": _normalize_list(item.get("keywords")),
            }
        )
    return normalized


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


def _normalize_outline_item(item: object) -> dict | None:
    if not isinstance(item, dict):
        return None

    title = _normalize_text(item.get("title"))
    if not title:
        return None

    children = []
    for child in item.get("children", []):
        if not isinstance(child, dict):
            continue
        child_title = _normalize_text(child.get("title"))
        if not child_title:
            continue
        children.append(
            {
                "section_id": _normalize_text(child.get("section_id")),
                "title": child_title,
                "purpose": _normalize_text(child.get("purpose")),
                "writing_points": _normalize_list(child.get("writing_points"))[:5],
            }
        )

    return {
        "section_id": _normalize_text(item.get("section_id")),
        "title": title,
        "purpose": _normalize_text(item.get("purpose")),
        "children": children,
    }


def _normalize_outline(value: object) -> list[dict]:
    if not isinstance(value, list):
        return []

    normalized: list[dict] = []
    for item in value:
        normalized_item = _normalize_outline_item(item)
        if normalized_item:
            normalized.append(normalized_item)
    return normalized


def _first_items(items: list[str], *, limit: int, fallback: str) -> list[str]:
    normalized = [item for item in items if item][:limit]
    return normalized or [fallback]


def _build_default_generate_outline(
    tender_fields: dict,
    judge_result: dict,
    knowledge_context: dict,
) -> list[dict]:
    project_name = _normalize_text(tender_fields.get("project_name"), "当前招标项目")
    tender_company = _normalize_text(tender_fields.get("tender_company"), "当前招标单位")
    qualifications = _normalize_list(tender_fields.get("qualification_requirements"))
    delivery_requirements = _normalize_list(tender_fields.get("delivery_requirements"))
    scoring_focus = _normalize_list(tender_fields.get("scoring_focus"))
    risks = _normalize_list(judge_result.get("risks"))
    knowledge_used = _build_knowledge_used(knowledge_context)
    knowledge_titles = [
        item["document_title"]
        for item in knowledge_used
        if _normalize_text(item.get("document_title"))
    ][:3]
    knowledge_summary = "、".join(knowledge_titles) if knowledge_titles else "企业知识库资料"
    bid_summary = "建议推进" if bool(judge_result.get("should_bid")) else "建议谨慎评估"

    return [
        {
            "section_id": "1",
            "title": "项目响应总览",
            "purpose": f"概述《{project_name}》的项目背景、响应范围和总体投标判断。",
            "children": [
                {
                    "section_id": "1.1",
                    "title": "项目背景与招标目标",
                    "purpose": "说明项目背景、招标范围和项目目标。",
                    "writing_points": [
                        f"项目名称：{project_name}",
                        f"招标单位：{tender_company}",
                        "提炼项目建设背景与招标目标",
                    ],
                },
                {
                    "section_id": "1.2",
                    "title": "投标策略与总体判断",
                    "purpose": "概述是否建议投标以及总体响应策略。",
                    "writing_points": [
                        f"投标建议：{bid_summary}",
                        "说明本次响应的总体策略",
                        "突出对招标要求的整体把握",
                    ],
                },
            ],
        },
        {
            "section_id": "2",
            "title": "企业能力与资质响应",
            "purpose": "说明公司概况、资质条件和关键人员匹配性。",
            "children": [
                {
                    "section_id": "2.1",
                    "title": "公司介绍与核心能力",
                    "purpose": "说明企业概况、主营方向和本项目匹配优势。",
                    "writing_points": [
                        f"优先引用资料：{knowledge_summary}",
                        "突出与本项目最相关的核心能力",
                        "说明团队、交付和行业经验基础",
                    ],
                },
                {
                    "section_id": "2.2",
                    "title": "资质证书与关键人员响应",
                    "purpose": "逐项响应招标文件中的资质、证书和人员要求。",
                    "writing_points": _first_items(
                        qualifications,
                        limit=4,
                        fallback="待补充资质证书、项目负责人和关键人员信息",
                    ),
                },
            ],
        },
        {
            "section_id": "3",
            "title": "实施方案与案例支撑",
            "purpose": "组织项目案例、技术方案和服务承诺。",
            "children": [
                {
                    "section_id": "3.1",
                    "title": "类似项目经验",
                    "purpose": "组织与本项目场景接近的案例，作为履约能力证明。",
                    "writing_points": [
                        f"优先选择与《{project_name}》最接近的案例",
                        "突出业主类型、项目规模和交付成果",
                        "补充项目负责人参与经历和角色说明",
                    ],
                },
                {
                    "section_id": "3.2",
                    "title": "技术实施方案",
                    "purpose": "围绕招标要求组织实施思路、交付路径和技术安排。",
                    "writing_points": _first_items(
                        delivery_requirements + scoring_focus,
                        limit=4,
                        fallback="待补充实施步骤、资源安排、进度计划和技术重点",
                    ),
                },
                {
                    "section_id": "3.3",
                    "title": "服务承诺与风险控制",
                    "purpose": "说明服务承诺、质量保障、风险识别和应对措施。",
                    "writing_points": _first_items(
                        risks,
                        limit=4,
                        fallback="待补充质量承诺、进度承诺和风险控制措施",
                    ),
                },
            ],
        },
        {
            "section_id": "4",
            "title": "商务响应与附件",
            "purpose": "整理商务响应、报价说明和附件清单。",
            "children": [
                {
                    "section_id": "4.1",
                    "title": "商务响应要点",
                    "purpose": "汇总商务响应、偏离说明和投标承诺。",
                    "writing_points": [
                        "报价与商务偏离说明",
                        "投标函、授权书及承诺函",
                        f"投标策略：{bid_summary}",
                    ],
                },
                {
                    "section_id": "4.2",
                    "title": "附件与证明材料清单",
                    "purpose": "列出资质、案例、人员等证明材料目录。",
                    "writing_points": [
                        "资质、案例、人员证明材料附件",
                        "商务文件及响应性证明",
                        "后续按目录逐项补齐附件",
                    ],
                },
            ],
        },
    ]


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


def ensure_generate_result(
    raw_result: dict,
    tender_fields: dict,
    judge_result: dict,
    knowledge_context: dict,
    prompt: str,
) -> dict:
    proposal_outline = _normalize_outline(raw_result.get("proposal_outline"))
    if not proposal_outline:
        proposal_outline = _build_default_generate_outline(
            tender_fields,
            judge_result,
            knowledge_context,
        )

    return {
        "proposal_outline": proposal_outline,
        "section_contents": {},
        "company_intro": _normalize_text(
            raw_result.get("company_intro"),
            "当前先生成标书目录，后续再按目录补充公司介绍正文。",
        ),
        "project_cases": _normalize_text(
            raw_result.get("project_cases"),
            "当前先生成标书目录，后续再按目录补充项目案例正文。",
        ),
        "implementation_plan": _normalize_text(
            raw_result.get("implementation_plan"),
            "当前先生成标书目录，后续再按目录补充实施方案正文。",
        ),
        "business_response": _normalize_text(
            raw_result.get("business_response"),
            "当前先生成标书目录，后续再按目录补充商务响应正文。",
        ),
        "knowledge_used": _build_knowledge_used(knowledge_context),
        "prompt_preview": prompt[:1200],
    }


def ensure_generate_section_result(raw_result: dict, knowledge_context: dict, prompt: str) -> dict:
    return {
        "content": _normalize_text(
            raw_result.get("content"),
            "当前未能生成该小节正文，请稍后重试。",
        ),
        "knowledge_used": _build_knowledge_used(knowledge_context),
        "prompt_preview": prompt[:1200],
    }


def ensure_collect_result(raw_result: dict) -> dict:
    return {
        "projects": _normalize_projects(raw_result.get("projects")),
    }
