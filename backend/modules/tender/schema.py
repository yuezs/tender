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


class TenderGenerateResult(BaseModel):
    company_intro: str
    project_cases: str
    implementation_plan: str
    business_response: str
