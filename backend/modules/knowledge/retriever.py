from modules.knowledge.parser import expand_csv_values


def normalize_retrieve_filters(
    category: str | None,
    query: str | None,
    tags: list[str] | None,
    industry: list[str] | None,
    limit: int | None,
) -> dict:
    normalized_tags = expand_csv_values(",".join(tags or []))
    normalized_industry = expand_csv_values(",".join(industry or []))

    return {
        "category": (category or "").strip(),
        "query": (query or "").strip(),
        "tags": normalized_tags,
        "industry": normalized_industry,
        "limit": max(1, min(limit or 5, 20)),
    }
