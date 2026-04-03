import {
  ExtractTenderResponse,
  GenerateTenderResponse,
  JudgeTenderResponse,
  ParseTenderResponse,
  TenderDocumentExportResponse,
  TenderSectionContentResponse,
  TenderResultSnapshot,
  UploadTenderResponse
} from "@/types/tender";
import {
  DiscoveryProfile,
  DiscoveryProjectDetail,
  DiscoveryProjectListResponse,
  DiscoveryRunListResponse,
  DiscoveryRunResponse,
  DiscoveryRunTargeting
} from "@/types/discovery";
import {
  DeleteKnowledgeDocumentResponse,
  KnowledgeCategory,
  KnowledgeDocumentContentResponse,
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

export function resolveApiUrl(path: string): string {
  if (!path) {
    return API_BASE_URL;
  }
  if (/^https?:\/\//i.test(path)) {
    return path;
  }
  return `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

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

export function generateTenderFullDocument(fileId: string) {
  return postByFileId<TenderDocumentExportResponse>("/api/tender/documents/fulltext", fileId);
}

export async function generateTenderSection(fileId: string, sectionId: string): Promise<TenderSectionContentResponse> {
  const response = await fetch(`${API_BASE_URL}/api/tender/generate/section`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ file_id: fileId, section_id: sectionId })
  });
  return parseResponse<TenderSectionContentResponse>(response);
}

export async function getTenderSectionContent(
  fileId: string,
  sectionId: string
): Promise<TenderSectionContentResponse> {
  const encodedSectionId = encodeURIComponent(sectionId);
  const response = await fetch(`${API_BASE_URL}/api/tender/sections/${fileId}/${encodedSectionId}`, {
    cache: "no-store"
  });
  return parseResponse<TenderSectionContentResponse>(response);
}

export async function getLatestTenderResult(): Promise<TenderResultSnapshot> {
  const response = await fetch(`${API_BASE_URL}/api/tender/results/latest`, {
    cache: "no-store"
  });
  return parseResponse<TenderResultSnapshot>(response);
}

export async function getTenderResult(fileId: string): Promise<TenderResultSnapshot> {
  const response = await fetch(`${API_BASE_URL}/api/tender/results/${fileId}`, {
    cache: "no-store"
  });
  return parseResponse<TenderResultSnapshot>(response);
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

export async function getKnowledgeDocumentContent(documentId: string): Promise<KnowledgeDocumentContentResponse> {
  const response = await fetch(`${API_BASE_URL}/api/knowledge/documents/${documentId}/content`, {
    cache: "no-store"
  });
  return parseResponse<KnowledgeDocumentContentResponse>(response);
}

export function getKnowledgeDocumentDownloadUrl(documentId: string): string {
  return `${API_BASE_URL}/api/knowledge/documents/${documentId}/download`;
}

export async function deleteKnowledgeDocument(documentId: string): Promise<DeleteKnowledgeDocumentResponse> {
  const response = await fetch(`${API_BASE_URL}/api/knowledge/documents/${documentId}`, {
    method: "DELETE"
  });
  return parseResponse<DeleteKnowledgeDocumentResponse>(response);
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

export async function getDiscoveryProfile(): Promise<DiscoveryProfile> {
  const response = await fetch(`${API_BASE_URL}/api/discovery/profile`);
  return parseResponse<DiscoveryProfile>(response);
}

export async function runDiscoveryCollection(payload?: {
  source?: string;
  mode?: DiscoveryRunTargeting["mode"];
  profile_key?: string;
  profile_title?: string;
  keywords?: string[];
  regions?: string[];
  qualification_terms?: string[];
  industry_terms?: string[];
}): Promise<DiscoveryRunResponse> {
  const response = await fetch(`${API_BASE_URL}/api/discovery/runs`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      source: payload?.source ?? "ggzy",
      mode: payload?.mode ?? "broad",
      profile_key: payload?.profile_key ?? "",
      profile_title: payload?.profile_title ?? "",
      keywords: payload?.keywords ?? [],
      regions: payload?.regions ?? [],
      qualification_terms: payload?.qualification_terms ?? [],
      industry_terms: payload?.industry_terms ?? []
    })
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
  profile_key?: string;
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
