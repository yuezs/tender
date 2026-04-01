export type DiscoveryRunResponse = {
  run_id: string;
  source: string;
  trigger_type: string;
  status: string;
  started_at: string;
  finished_at?: string | null;
  total_found: number;
  total_new: number;
  total_updated: number;
  error_message: string;
};

export type DiscoveryRunListResponse = {
  items: DiscoveryRunResponse[];
};

export type DiscoveryKnowledgeItem = {
  category: string;
  document_title: string;
  section_title: string;
};

export type DiscoveryMatchResult = {
  recommendation_score: number;
  recommendation_level: "high" | "medium" | "low";
  recommendation_reasons: string[];
  risks: string[];
  matched_knowledge: DiscoveryKnowledgeItem[];
};

export type DiscoveryExtractResult = {
  project_name: string;
  tender_unit: string;
  project_code: string;
  region: string;
  budget_text: string;
  deadline_text: string;
  notice_type: string;
  published_at: string;
  qualification_requirements: string[];
  keywords: string[];
};

export type DiscoveryProject = {
  lead_id: string;
  source: string;
  title: string;
  notice_type: string;
  region: string;
  published_at: string;
  project_code: string;
  tender_unit: string;
  budget_text: string;
  deadline_text: string;
  recommendation_score: number;
  recommendation_level: "high" | "medium" | "low";
  recommendation_reasons: string[];
};

export type DiscoveryProjectListResponse = {
  items: DiscoveryProject[];
  total: number;
  page: number;
  page_size: number;
};

export type DiscoveryProjectDetail = {
  lead_id: string;
  source: string;
  title: string;
  notice_type: string;
  region: string;
  published_at: string;
  detail_url: string;
  canonical_url: string;
  extract_result: DiscoveryExtractResult;
  match_result: DiscoveryMatchResult;
  detail_text: string;
};
