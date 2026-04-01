from pydantic import BaseModel, Field


class DiscoveryStatusResponse(BaseModel):
    module: str
    status: str
    message: str
    mock: bool
    available_routes: list[str]
    supported_sources: list[str]
    repository_ready: bool


class DiscoveryRunRequest(BaseModel):
    source: str = Field(default="ggzy", min_length=1)


class DiscoveryRunSummary(BaseModel):
    run_id: str
    source: str
    trigger_type: str
    status: str
    started_at: str
    finished_at: str | None = None
    total_found: int
    total_new: int
    total_updated: int
    error_message: str


class DiscoveryRunListResponse(BaseModel):
    items: list[DiscoveryRunSummary]


class DiscoveryKnowledgeItem(BaseModel):
    category: str
    document_title: str
    section_title: str


class DiscoveryMatchResult(BaseModel):
    recommendation_score: int
    recommendation_level: str
    recommendation_reasons: list[str]
    risks: list[str]
    matched_knowledge: list[DiscoveryKnowledgeItem]


class DiscoveryExtractResult(BaseModel):
    project_name: str
    tender_unit: str
    project_code: str
    region: str
    budget_text: str
    deadline_text: str
    notice_type: str
    published_at: str
    qualification_requirements: list[str]
    keywords: list[str]


class DiscoveryProjectListItem(BaseModel):
    lead_id: str
    source: str
    title: str
    notice_type: str
    region: str
    published_at: str
    project_code: str
    tender_unit: str
    budget_text: str
    deadline_text: str
    recommendation_score: int
    recommendation_level: str
    recommendation_reasons: list[str]


class DiscoveryProjectListResponse(BaseModel):
    items: list[DiscoveryProjectListItem]
    total: int
    page: int
    page_size: int


class DiscoveryProjectDetail(BaseModel):
    lead_id: str
    source: str
    title: str
    notice_type: str
    region: str
    published_at: str
    detail_url: str
    canonical_url: str
    extract_result: DiscoveryExtractResult
    match_result: DiscoveryMatchResult
    detail_text: str
