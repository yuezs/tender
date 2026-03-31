import {
  ExtractTenderResponse,
  GenerateTenderResponse,
  JudgeTenderResponse,
  ParseTenderResponse,
  UploadTenderResponse
} from "@/types/tender";

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
