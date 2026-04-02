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
    mode: str = Field(default="broad", min_length=1)
    profile_key: str = Field(default="", min_length=0)
    profile_title: str = Field(default="", min_length=0)
    keywords: list[str] = Field(default_factory=list)
    regions: list[str] = Field(default_factory=list)
    qualification_terms: list[str] = Field(default_factory=list)
    industry_terms: list[str] = Field(default_factory=list)


class DiscoveryRunTargeting(BaseModel):
    mode: str
    profile_key: str
    profile_title: str
    keywords: list[str]
    regions: list[str]
    qualification_terms: list[str]
    industry_terms: list[str]


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
    targeting: DiscoveryRunTargeting


class DiscoveryRunListResponse(BaseModel):
    items: list[DiscoveryRunSummary]


class DiscoveryKnowledgeItem(BaseModel):
    category: str
    document_title: str
    section_title: str


class DiscoveryProfileDocument(BaseModel):
    category: str
    document_title: str
    section_title: str


class DiscoveryProfileDirection(BaseModel):
    profile_key: str
    title: str
    description: str
    confidence: str
    keywords: list[str]
    regions: list[str]
    qualification_terms: list[str]
    industry_terms: list[str]
    reasons: list[str]
    supporting_documents: list[DiscoveryProfileDocument]
    gap_message: str


class DiscoveryProfileResponse(BaseModel):
    has_profile: bool
    message: str
    document_counts: dict[str, int]
    directions: list[DiscoveryProfileDirection]


class DiscoveryMatchResult(BaseModel):
    recommendation_score: int
    recommendation_level: str
    knowledge_support_score: int
    targeting_match_score: int
    profile_key: str
    profile_title: str
    recommendation_reasons: list[str]
    targeting_reasons: list[str]
    risks: list[str]
    knowledge_gaps: list[str]
    matched_keywords: list[str]
    matched_regions: list[str]
    matched_qualification_terms: list[str]
    matched_industry_terms: list[str]
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
    targeting_match_score: int
    profile_key: str
    profile_title: str
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
