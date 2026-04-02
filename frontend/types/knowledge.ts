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
  created_at: string;
  updated_at: string;
};

export type ListKnowledgeDocumentsResponse = {
  items: KnowledgeDocumentItem[];
};

export type ProcessKnowledgeDocumentResponse = {
  document_id: string;
  chunk_count: number;
  status: KnowledgeDocumentStatus;
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

