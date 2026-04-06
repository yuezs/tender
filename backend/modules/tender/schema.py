from pydantic import BaseModel, Field


class TenderStatusResponse(BaseModel):
    module: str
    status: str
    message: str
    mock: bool
    available_routes: list[str]
    repository_ready: bool


class TenderProcessRequest(BaseModel):
    file_id: str = Field(..., min_length=1)


class TenderSectionGenerateRequest(BaseModel):
    file_id: str = Field(..., min_length=1)
    section_id: str = Field(..., min_length=1)


class TenderDocumentExportResponse(BaseModel):
    document_id: str
    file_name: str
    download_url: str
    generated_at: str


class TenderExtractResult(BaseModel):
    project_name: str
    tender_company: str
    budget: str
    deadline: str
    qualification_requirements: list[str]
    delivery_requirements: list[str]
    scoring_focus: list[str]


class TenderJudgeResult(BaseModel):
    should_bid: bool
    reason: str
    risks: list[str]


class TenderProposalSections(BaseModel):
    cover_summary: str = ""
    table_of_contents: str = ""
    company_intro: str = ""
    qualification_response: str = ""
    project_cases: str = ""
    implementation_plan: str = ""
    service_commitment: str = ""
    business_response: str = ""


class TenderProposalOutlineChild(BaseModel):
    section_id: str = ""
    title: str
    purpose: str = ""
    writing_points: list[str] = []


class TenderProposalOutlineItem(BaseModel):
    section_id: str = ""
    title: str
    purpose: str = ""
    children: list[TenderProposalOutlineChild] = []


class TenderSectionContent(BaseModel):
    section_id: str
    parent_section_id: str = ""
    title: str
    status: str = "pending"
    content: str = ""
    error_message: str = ""
    updated_at: str = ""
    knowledge_used: list[dict] = []
    prompt_preview: str = ""


class TenderGenerateResult(BaseModel):
    company_intro: str
    project_cases: str
    implementation_plan: str
    business_response: str
    proposal_outline: list[TenderProposalOutlineItem] = []
    section_contents: dict[str, TenderSectionContent] = {}
    proposal_sections: TenderProposalSections | None = None
    download_ready: bool = False
    document_id: str = ""
    document_file_name: str = ""
    download_url: str = ""


class TenderUploadSummary(BaseModel):
    file_id: str
    file_name: str
    source_type: str
    extension: str


class TenderStepSummary(BaseModel):
    status: str
    message: str


class TenderStepSnapshot(BaseModel):
    upload: TenderStepSummary
    parse: TenderStepSummary
    extract: TenderStepSummary
    judge: TenderStepSummary
    generate: TenderStepSummary


class TenderParseSnapshot(BaseModel):
    file_id: str
    text: str


class TenderResultSnapshot(BaseModel):
    uploaded_at: str
    updated_at: str
    upload: TenderUploadSummary
    steps: TenderStepSnapshot
    parse: TenderParseSnapshot
    extract: dict
    judge: dict
    generate: dict


class TenderSectionContentResponse(BaseModel):
    section_id: str
    parent_section_id: str = ""
    title: str
    scope: str
    status: str
    content: str
    completed_children: int = 0
    total_children: int = 0
