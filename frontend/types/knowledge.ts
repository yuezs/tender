export type KnowledgeCategory = "company_profile" | "qualifications" | "project_cases" | "templates";

export type KnowledgeDocumentStatus = "uploaded" | "processed" | "error";

export type UploadKnowledgeResponse = {
  document_id: string;
  title: string;
  category: KnowledgeCategory;
};

export type KnowledgeDocumentItem = {
  document_id: string;
  title: string;
  category: KnowledgeCategory;
  file_name: string;
  tags: string[];
  industry: string[];
  status: KnowledgeDocumentStatus;
  chunk_count: number;
  content_length: number;
  error_message: string;
  created_at: string;
  updated_at: string;
};

export type ListKnowledgeDocumentsResponse = {
  items: KnowledgeDocumentItem[];
};

export type KnowledgeParseSummary = {
  block_count: number;
  heading_count: number;
  paragraph_count: number;
  list_item_count: number;
  table_row_count: number;
  character_count: number;
  line_count: number;
};

export type KnowledgeChunkPreviewItem = {
  section_title: string;
  content_preview: string;
  char_count: number;
};

export type ProcessKnowledgeDocumentResponse = {
  document_id: string;
  chunk_count: number;
  status: KnowledgeDocumentStatus;
  content_length: number;
  parse_summary: KnowledgeParseSummary;
  warnings: string[];
  key_points: string[];
  chunk_preview: KnowledgeChunkPreviewItem[];
};

export type KnowledgeDocumentContentResponse = {
  document_id: string;
  title: string;
  category: KnowledgeCategory;
  status: KnowledgeDocumentStatus;
  source: string;
  content: string;
};

export type DeleteKnowledgeDocumentResponse = {
  document_id: string;
  title: string;
};

export type KnowledgeChunkItem = {
  id: string;
  document_id: string;
  document_title: string;
  section_title: string;
  content: string;
};

export type RetrieveKnowledgeResponse = {
  chunks: KnowledgeChunkItem[];
};
