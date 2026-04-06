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

export type TenderProposalOutlineChild = {
  section_id: string;
  title: string;
  purpose: string;
  writing_points: string[];
};

export type TenderProposalOutlineItem = {
  section_id: string;
  title: string;
  purpose: string;
  children: TenderProposalOutlineChild[];
};

export type TenderSectionContent = {
  section_id: string;
  parent_section_id: string;
  title: string;
  status: StepStatus;
  content: string;
  error_message: string;
  updated_at: string;
  knowledge_used?: KnowledgeUsedItem[];
  prompt_preview?: string;
};

export type GenerateTenderResponse = {
  proposal_outline?: TenderProposalOutlineItem[];
  section_contents?: Record<string, TenderSectionContent>;
  company_intro: string;
  project_cases: string;
  implementation_plan: string;
  business_response: string;
  proposal_sections?: {
    cover_summary: string;
    table_of_contents: string;
    company_intro: string;
    qualification_response: string;
    project_cases: string;
    implementation_plan: string;
    service_commitment: string;
    business_response: string;
  };
  download_ready?: boolean;
  document_id?: string;
  document_file_name?: string;
  download_url?: string;
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

export type TenderStepSummary = {
  status: StepStatus;
  message: string;
};

export type TenderResultSnapshot = {
  uploaded_at: string;
  updated_at: string;
  upload: UploadTenderResponse;
  steps: {
    upload: TenderStepSummary;
    parse: TenderStepSummary;
    extract: TenderStepSummary;
    judge: TenderStepSummary;
    generate: TenderStepSummary;
  };
  parse: ParseTenderResponse;
  extract: ExtractTenderResponse;
  judge: JudgeTenderResponse;
  generate: GenerateTenderResponse;
};

export type TenderSectionContentResponse = {
  section_id: string;
  parent_section_id: string;
  title: string;
  scope: "section" | "chapter";
  status: StepStatus;
  content: string;
  completed_children: number;
  total_children: number;
};

export type TenderDocumentExportResponse = {
  document_id: string;
  file_name: string;
  download_url: string;
  generated_at: string;
};
