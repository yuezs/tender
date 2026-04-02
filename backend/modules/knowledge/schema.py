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
    content_length: int
    error_message: str
    created_at: str
    updated_at: str


class KnowledgeDocumentListResponse(BaseModel):
    items: list[KnowledgeDocumentItem]


class KnowledgeParseSummary(BaseModel):
    block_count: int
    heading_count: int
    paragraph_count: int
    list_item_count: int
    table_row_count: int
    character_count: int
    line_count: int


class KnowledgeChunkPreviewItem(BaseModel):
    section_title: str
    content_preview: str
    char_count: int


class KnowledgeProcessResponse(BaseModel):
    document_id: str
    chunk_count: int
    status: str
    content_length: int
    parse_summary: KnowledgeParseSummary
    warnings: list[str]
    key_points: list[str]
    chunk_preview: list[KnowledgeChunkPreviewItem]


class KnowledgeDocumentContentResponse(BaseModel):
    document_id: str
    title: str
    category: str
    status: str
    source: str
    content: str


class KnowledgeDeleteResponse(BaseModel):
    document_id: str
    title: str


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
