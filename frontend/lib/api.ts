import {
  ExtractTenderResponse,
  GenerateTenderResponse,
  JudgeTenderResponse,
  ParseTenderResponse,
  UploadTenderResponse
} from "@/types/tender";
import {
  DiscoveryProjectDetail,
  DiscoveryProjectListResponse,
  DiscoveryRunListResponse,
  DiscoveryRunResponse
} from "@/types/discovery";
import {
  KnowledgeCategory,
  ListKnowledgeDocumentsResponse,
  ProcessKnowledgeDocumentResponse,
  RetrieveKnowledgeResponse,
  UploadKnowledgeResponse
} from "@/types/knowledge";

type ApiEnvelope<T> = {
  success: boolean;
  message: string;
  data: T;
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

async function parseResponse<T>(response: Response): Promise<T> {
  const payload = (await response.json()) as ApiEnvelope<T>;
  if (!response.ok || !payload.success) {
    throw new Error(payload.message || "请求失败");
  }
  return payload.data;
}

export async function uploadTenderFile(file: File): Promise<UploadTenderResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("source_type", "upload");

  const response = await fetch(`${API_BASE_URL}/api/tender/upload`, {
    method: "POST",
    body: formData
  });

  return parseResponse<UploadTenderResponse>(response);
}

async function postByFileId<T>(path: string, fileId: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ file_id: fileId })
  });

  return parseResponse<T>(response);
}

export function parseTender(fileId: string) {
  return postByFileId<ParseTenderResponse>("/api/tender/parse", fileId);
}

export function extractTender(fileId: string) {
  return postByFileId<ExtractTenderResponse>("/api/tender/extract", fileId);
}

export function judgeTender(fileId: string) {
  return postByFileId<JudgeTenderResponse>("/api/tender/judge", fileId);
}

export function generateTender(fileId: string) {
  return postByFileId<GenerateTenderResponse>("/api/tender/generate", fileId);
}

function buildQueryString(params: Record<string, string | number | boolean | undefined>) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === "" || value === false) {
      return;
    }
    search.set(key, String(value));
  });
  const query = search.toString();
  return query ? `?${query}` : "";
}

export async function uploadKnowledgeDocument(payload: {
  file: File;
  title: string;
  category: KnowledgeCategory;
  tags?: string;
  industry?: string;
}): Promise<UploadKnowledgeResponse> {
  const formData = new FormData();
  formData.append("file", payload.file);
  formData.append("title", payload.title);
  formData.append("category", payload.category);
  if (payload.tags) {
    formData.append("tags", payload.tags);
  }
  if (payload.industry) {
    formData.append("industry", payload.industry);
  }

  const response = await fetch(`${API_BASE_URL}/api/knowledge/documents/upload`, {
    method: "POST",
    body: formData
  });

  return parseResponse<UploadKnowledgeResponse>(response);
}

export async function listKnowledgeDocuments(filters?: {
  category?: KnowledgeCategory | "";
  status?: string;
}): Promise<ListKnowledgeDocumentsResponse> {
  const params = new URLSearchParams();
  if (filters?.category) {
    params.set("category", filters.category);
  }
  if (filters?.status) {
    params.set("status", filters.status);
  }

  const url = `${API_BASE_URL}/api/knowledge/documents${params.size ? `?${params.toString()}` : ""}`;
  const response = await fetch(url, { cache: "no-store" });
  return parseResponse<ListKnowledgeDocumentsResponse>(response);
}

export async function processKnowledgeDocument(documentId: string): Promise<ProcessKnowledgeDocumentResponse> {
  const response = await fetch(`${API_BASE_URL}/api/knowledge/documents/${documentId}/process`, {
    method: "POST"
  });
  return parseResponse<ProcessKnowledgeDocumentResponse>(response);
}

export async function retrieveKnowledge(payload: {
  category?: KnowledgeCategory | "";
  query?: string;
  tags?: string[];
  industry?: string[];
  limit?: number;
}): Promise<RetrieveKnowledgeResponse> {
  const response = await fetch(`${API_BASE_URL}/api/knowledge/retrieve`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      category: payload.category || undefined,
      query: payload.query || undefined,
      tags: payload.tags?.length ? payload.tags : undefined,
      industry: payload.industry?.length ? payload.industry : undefined,
      limit: payload.limit ?? 5
    })
  });
  return parseResponse<RetrieveKnowledgeResponse>(response);
}

export async function runDiscoveryCollection(source = "ggzy"): Promise<DiscoveryRunResponse> {
  const response = await fetch(`${API_BASE_URL}/api/discovery/runs`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ source })
  });

  return parseResponse<DiscoveryRunResponse>(response);
}

export async function listDiscoveryRuns(): Promise<DiscoveryRunListResponse> {
  const response = await fetch(`${API_BASE_URL}/api/discovery/runs`);
  return parseResponse<DiscoveryRunListResponse>(response);
}

export async function listDiscoveryProjects(params: {
  keyword?: string;
  region?: string;
  notice_type?: string;
  recommendation_level?: string;
  recommended_only?: boolean;
  page?: number;
  page_size?: number;
}): Promise<DiscoveryProjectListResponse> {
  const query = buildQueryString(params);
  const response = await fetch(`${API_BASE_URL}/api/discovery/projects${query}`);
  return parseResponse<DiscoveryProjectListResponse>(response);
}

export async function getDiscoveryProjectDetail(leadId: string): Promise<DiscoveryProjectDetail> {
  const response = await fetch(`${API_BASE_URL}/api/discovery/projects/${leadId}`);
  return parseResponse<DiscoveryProjectDetail>(response);
}
