import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from docx import Document


ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from modules.agent.orchestrator import AgentOrchestrator
from modules.agent.output_parser import ensure_generate_result
from modules.agent.generate_agent import GenerateAgent
from modules.agent.prompt_templates import build_generate_prompt
from modules.tender.document_service import ProposalDocumentService


class GenerateProposalTests(unittest.TestCase):
    def test_ensure_generate_result_returns_legacy_fields_and_proposal_sections(self):
        result = ensure_generate_result(
            raw_result={
                "cover_summary": "封面摘要",
                "table_of_contents": "目录",
                "company_intro": "公司介绍",
                "qualification_response": "资质响应",
                "project_cases": "案例章节",
                "implementation_plan": "实施方案",
                "service_commitment": "服务承诺",
                "business_response": "商务响应",
            },
            knowledge_context={
                "chunks": [
                    {
                        "category": "company_profile",
                        "document_title": "企业介绍",
                        "section_title": "核心能力",
                    }
                ]
            },
            prompt="demo prompt",
        )

        self.assertEqual(result["company_intro"], "公司介绍")
        self.assertEqual(result["project_cases"], "案例章节")
        self.assertIn("proposal_sections", result)
        self.assertEqual(result["proposal_sections"]["qualification_response"], "资质响应")
        self.assertEqual(result["proposal_sections"]["service_commitment"], "服务承诺")
        self.assertEqual(len(result["knowledge_used"]), 1)

    def test_ensure_generate_result_marks_missing_qualification_as_pending(self):
        result = ensure_generate_result(
            raw_result={
                "company_intro": "公司介绍",
                "project_cases": "案例章节",
                "implementation_plan": "实施方案",
                "business_response": "商务响应",
            },
            knowledge_context={"chunks": []},
            prompt="demo prompt",
        )

        self.assertIn("待补充", result["proposal_sections"]["qualification_response"])

    def test_generate_sources_include_qualifications(self):
        orchestrator = AgentOrchestrator()
        self.assertIn("qualifications", orchestrator.select_sources("generate"))

    def test_generate_knowledge_context_falls_back_to_latest_chunks_when_query_misses(self):
        orchestrator = AgentOrchestrator()

        class StubKnowledgeService:
            def __init__(self) -> None:
                self.calls = []

            def retrieve(self, db, payload):
                self.calls.append(
                    {
                        "category": payload["category"],
                        "query": payload["query"],
                        "limit": payload["limit"],
                    }
                )
                if payload["query"]:
                    return {"chunks": []}

                category = payload["category"]
                return {
                    "chunks": [
                        {
                            "id": f"{category}-1",
                            "document_id": f"{category}-doc",
                            "category": category,
                            "document_title": f"{category}-doc",
                            "section_title": f"{category}-section",
                            "content": f"{category} fallback content",
                        }
                    ]
                }

        stub = StubKnowledgeService()
        orchestrator.knowledge_service = stub

        knowledge_context = orchestrator._build_knowledge_context(
            db=None,
            task_type="generate",
            tender_fields={
                "project_name": "Building Upgrade Project",
                "tender_company": "City Construction Bureau",
                "qualification_requirements": ["Electronic engineering level II"],
                "delivery_requirements": ["Deliver within 60 days"],
                "scoring_focus": ["Similar project cases"],
            },
        )

        self.assertEqual(len(knowledge_context["chunks"]), 4)
        self.assertEqual(
            knowledge_context["retrieval_stats"]["company_profile"]["fallback_count"],
            1,
        )
        self.assertEqual(
            knowledge_context["retrieval_stats"]["qualifications"]["fallback_count"],
            1,
        )
        self.assertIn("company_profile fallback content", knowledge_context["company_profile_context"])
        self.assertIn("templates fallback content", knowledge_context["templates_context"])

    def test_generate_agent_fallback_uses_category_specific_knowledge(self):
        agent = GenerateAgent()
        knowledge_context = {
            "chunks": [
                {
                    "id": "company-1",
                    "category": "company_profile",
                    "document_title": "company-profile",
                    "section_title": "overview",
                    "content": "Acme Water operates 86 sewage treatment projects and has 230 employees.",
                },
                {
                    "id": "qualification-1",
                    "category": "qualifications",
                    "document_title": "qualifications",
                    "section_title": "certificates",
                    "content": "The company holds ISO9001 and Class II environmental engineering qualifications.",
                },
                {
                    "id": "case-1",
                    "category": "project_cases",
                    "document_title": "project-cases",
                    "section_title": "case-a",
                    "content": "Hanzhong sewage plant expansion was delivered on schedule with一级A discharge quality.",
                },
                {
                    "id": "template-1",
                    "category": "templates",
                    "document_title": "templates",
                    "section_title": "delivery-plan",
                    "content": "Implementation follows four phases: design, procurement, installation, and commissioning.",
                },
            ],
            "company_profile_context": "Acme Water operates 86 sewage treatment projects and has 230 employees.",
            "qualifications_context": "The company holds ISO9001 and Class II environmental engineering qualifications.",
            "project_cases_context": "Hanzhong sewage plant expansion was delivered on schedule.",
            "templates_context": "Implementation follows four phases: design, procurement, installation, and commissioning.",
            "context_text": "Knowledge summary",
        }

        with patch(
            "modules.agent.generate_agent.settings",
            SimpleNamespace(
                agent_use_real_llm=False,
                openclaw_agent_generate="tender-generate",
            ),
        ):
            payload = agent.run(
                tender_fields={
                    "project_name": "Building Upgrade Project",
                    "tender_company": "City Construction Bureau",
                    "qualification_requirements": ["Electronic engineering level II"],
                    "delivery_requirements": ["Deliver within 60 days"],
                    "scoring_focus": ["Similar project cases", "Implementation plan"],
                },
                judge_result={
                    "should_bid": True,
                    "reason": "Capabilities are aligned with delivery requirements.",
                    "risks": [],
                },
                knowledge_context=knowledge_context,
            )

        sections = payload["result"]["proposal_sections"]
        self.assertIn("Acme Water operates 86 sewage treatment projects", sections["company_intro"])
        self.assertIn("ISO9001", sections["qualification_response"])
        self.assertIn("Hanzhong sewage plant expansion", sections["project_cases"])
        self.assertIn("Implementation follows four phases", sections["implementation_plan"])
        self.assertNotIn("待补充", sections["company_intro"])
        self.assertNotIn("待补充", sections["qualification_response"])

    def test_generate_prompt_includes_category_specific_context_sections(self):
        prompt = build_generate_prompt(
            tender_fields={"project_name": "Building Upgrade Project"},
            judge_result={"should_bid": True, "reason": "aligned", "risks": []},
            knowledge_context={
                "company_profile_context": "company facts",
                "qualifications_context": "qualification facts",
                "project_cases_context": "case facts",
                "templates_context": "template facts",
                "context_text": "summary text",
            },
        )

        self.assertIn("Company profile evidence", prompt)
        self.assertIn("Qualification evidence", prompt)
        self.assertIn("Project case evidence", prompt)
        self.assertIn("Template evidence", prompt)
        self.assertIn("company facts", prompt)
        self.assertIn("template facts", prompt)

    def test_proposal_document_service_exports_docx_with_core_sections(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            service = ProposalDocumentService(storage_root=Path(tmp_dir))
            exported = service.export(
                file_id="demo-file",
                tender_record={
                    "extract_result": {
                        "project_name": "智慧园区平台项目",
                        "tender_company": "某市大数据局",
                    }
                },
                generate_result={
                    "proposal_sections": {
                        "cover_summary": "封面摘要",
                        "table_of_contents": "一、公司介绍\n二、实施方案",
                        "company_intro": "公司介绍正文",
                        "qualification_response": "资质响应正文",
                        "project_cases": "案例正文",
                        "implementation_plan": "实施方案正文",
                        "service_commitment": "服务承诺正文",
                        "business_response": "商务响应正文",
                    }
                },
            )

            self.assertTrue(Path(exported["storage_path"]).exists())
            self.assertTrue(exported["file_name"].endswith(".docx"))
            self.assertIn("/api/tender/documents/", exported["download_url"])

            doc = Document(exported["storage_path"])
            text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
            self.assertIn("智慧园区平台项目", text)
            self.assertIn("公司介绍正文", text)
            self.assertIn("商务响应正文", text)


if __name__ == "__main__":
    unittest.main()
