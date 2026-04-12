export type DiscoveryRunTargeting = {
  mode: "targeted" | "broad" | "keyword";
  profile_key: string;
  profile_title: string;
  keywords: string[];
  regions: string[];
  notice_types: string[];
  exclude_keywords: string[];
  qualification_terms: string[];
  industry_terms: string[];
};

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
  targeting: DiscoveryRunTargeting;
};

export type DiscoveryRunListResponse = {
  items: DiscoveryRunResponse[];
};

export type DiscoveryKnowledgeItem = {
  category: string;
  document_title: string;
  section_title: string;
};

export type DiscoveryProfileDocument = {
  category: string;
  document_title: string;
  section_title: string;
};

export type DiscoveryProfileDirection = {
  profile_key: string;
  title: string;
  description: string;
  confidence: string;
  keywords: string[];
  regions: string[];
  qualification_terms: string[];
  industry_terms: string[];
  reasons: string[];
  supporting_documents: DiscoveryProfileDocument[];
  gap_message: string;
};

export type DiscoveryProfile = {
  has_profile: boolean;
  message: string;
  document_counts: Record<string, number>;
  directions: DiscoveryProfileDirection[];
};

export type DiscoveryMatchResult = {
  recommendation_score: number;
  recommendation_level: "high" | "medium" | "low";
  knowledge_support_score: number;
  targeting_match_score: number;
  profile_key: string;
  profile_title: string;
  recommendation_reasons: string[];
  targeting_reasons: string[];
  risks: string[];
  knowledge_gaps: string[];
  matched_keywords: string[];
  matched_regions: string[];
  matched_qualification_terms: string[];
  matched_industry_terms: string[];
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
  targeting_match_score: number;
  profile_key: string;
  profile_title: string;
  matched_keywords: string[];
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
