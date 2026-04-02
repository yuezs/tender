import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from core.exceptions import BusinessException
from modules.agent.judge_agent import JudgeAgent


class JudgeAgentFallbackTests(unittest.TestCase):
    def test_judge_agent_falls_back_when_gateway_requires_pairing(self):
        agent = JudgeAgent()
        tender_fields = {
            "project_name": "演示项目",
            "budget": "100万",
            "deadline": "2026-04-30 09:00:00",
            "qualification_requirements": ["具备相关资质"],
        }
        knowledge_context = {
            "chunks": [
                {"category": "qualifications", "document_title": "资质资料", "section_title": "系统集成"},
                {"category": "project_cases", "document_title": "案例资料", "section_title": "智慧园区"},
            ]
        }

        with patch.object(
            agent,
            "_run_llm",
            side_effect=BusinessException("OpenClaw Gateway connect failed: pairing required"),
        ):
            result = agent.run(
                tender_fields=tender_fields,
                knowledge_context=knowledge_context,
                execution_context={
                    "session_key": "test-session",
                    "idempotency_key": "test-idempotency",
                },
            )

        self.assertIn("should_bid", result["result"])
        self.assertTrue(result["debug"]["used_fallback"])
        self.assertIn("pairing required", result["debug"]["failure_reason"])


if __name__ == "__main__":
    unittest.main()
