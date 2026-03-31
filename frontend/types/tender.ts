export type StepStatus = "pending" | "loading" | "success" | "error";

export type StepState = {
  status: StepStatus;
  message: string;
};

export type KnowledgeUsedItem = {
  category: string;
  document_title: string;
  section_title: string;
};

export type UploadTenderResponse = {
  file_id: string;
  file_name: string;
  source_type: string;
  extension: string;
};

export type ParseTenderResponse = {
  file_id: string;
  text: string;
};

export type ExtractTenderResponse = {
  project_name: string;
  tender_company: string;
  budget: string;
  deadline: string;
  qualification_requirements: string[];
  delivery_requirements: string[];
  scoring_focus: string[];
};

export type JudgeTenderResponse = {
  should_bid: boolean;
  reason: string;
  risks: string[];
  knowledge_used?: KnowledgeUsedItem[];
  prompt_preview?: string;
};

export type GenerateTenderResponse = {
  company_intro: string;
  project_cases: string;
  implementation_plan: string;
  business_response: string;
  knowledge_used?: KnowledgeUsedItem[];
  prompt_preview?: string;
};

export type TenderFlowSnapshot = {
  uploadedAt: string;
  upload: UploadTenderResponse;
  parse: ParseTenderResponse;
  extract: ExtractTenderResponse;
  judge: JudgeTenderResponse;
  generate: GenerateTenderResponse;
};
