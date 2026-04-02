import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from core.exceptions import BusinessException
from modules.agent.extract_agent import ExtractAgent


class ExtractAgentFallbackTests(unittest.TestCase):
    def test_extract_agent_falls_back_when_gateway_requires_pairing(self):
        agent = ExtractAgent()
        fallback_result = {
            "project_name": "演示项目",
            "tender_company": "演示招标单位",
            "budget": "100万",
            "deadline": "2026-04-30 09:00:00",
            "qualification_requirements": ["具备相关资质"],
            "delivery_requirements": ["按期交付"],
            "scoring_focus": ["实施方案"],
        }

        with patch.object(
            agent,
            "_run_llm",
            side_effect=BusinessException("OpenClaw Gateway connect failed: pairing required"),
        ):
            result = agent.run(
                parsed_text="演示招标文本",
                fallback_result=fallback_result,
                execution_context={
                    "session_key": "test-session",
                    "idempotency_key": "test-idempotency",
                },
            )

        self.assertEqual(result["result"]["project_name"], "演示项目")
        self.assertTrue(result["debug"]["used_fallback"])
        self.assertIn("pairing required", result["debug"]["failure_reason"])


if __name__ == "__main__":
    unittest.main()
