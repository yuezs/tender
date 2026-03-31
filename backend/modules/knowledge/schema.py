from pydantic import BaseModel, Field


class KnowledgeStatusResponse(BaseModel):
    module: str
    status: str
    message: str
    mock: bool
    available_routes: list[str]
    supported_categories: list[str]
    repository_ready: bool


class KnowledgeUploadResponse(BaseModel):
    document_id: str
    title: str
    category: str


class KnowledgeDocumentItem(BaseModel):
    document_id: str
    title: str
    category: str
    file_name: str
    tags: list[str]
    industry: list[str]
    status: str
    chunk_count: int
    created_at: str
    updated_at: str


class KnowledgeDocumentListResponse(BaseModel):
    items: list[KnowledgeDocumentItem]


class KnowledgeProcessResponse(BaseModel):
    document_id: str
    chunk_count: int
    status: str


class KnowledgeRetrieveRequest(BaseModel):
    category: str | None = None
    query: str | None = None
    tags: list[str] | None = None
    industry: list[str] | None = None
    limit: int = Field(default=5, ge=1, le=20)


class KnowledgeChunkItem(BaseModel):
    id: str
    document_id: str
    document_title: str
    section_title: str
    content: str


class KnowledgeRetrieveResponse(BaseModel):
    chunks: list[KnowledgeChunkItem]
