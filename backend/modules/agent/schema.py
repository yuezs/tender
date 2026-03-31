from pydantic import BaseModel


class AgentStatusResponse(BaseModel):
    module: str
    status: str
    mock: bool
    available_tasks: list[str]


class AgentKnowledgeReference(BaseModel):
    category: str
    document_id: str
    document_title: str
    section_title: str
    content: str


class AgentKnowledgeContext(BaseModel):
    task_type: str
    source_categories: list[str]
    chunks: list[AgentKnowledgeReference]
    context_text: str


class JudgeAgentResult(BaseModel):
    should_bid: bool
    reason: str
    risks: list[str]
    knowledge_used: list[dict]
    prompt_preview: str


class GenerateAgentResult(BaseModel):
    company_intro: str
    project_cases: str
    implementation_plan: str
    business_response: str
    knowledge_used: list[dict]
    prompt_preview: str
