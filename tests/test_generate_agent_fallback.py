import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from core.exceptions import BusinessException
from modules.agent.generate_agent import GenerateAgent


class GenerateAgentFallbackTests(unittest.TestCase):
    def test_generate_agent_falls_back_when_openclaw_requires_pairing(self):
        agent = GenerateAgent()
        tender_fields = {
            "project_name": "建筑智能化改造项目",
            "tender_company": "某建设局",
            "qualification_requirements": ["电子与智能化工程专业承包贰级及以上"],
            "delivery_requirements": ["60日内完成实施交付"],
            "scoring_focus": ["类似项目业绩", "实施方案"],
        }
        judge_result = {
            "should_bid": True,
            "reason": "企业能力与项目要求基本匹配。",
            "risks": [],
        }
        knowledge_context = {
            "chunks": [],
        }

        with patch(
            "modules.agent.generate_agent.settings",
            SimpleNamespace(
                agent_use_real_llm=True,
                openclaw_agent_generate="tender-generate",
            ),
        ), patch.object(
            GenerateAgent,
            "_run_llm",
            side_effect=BusinessException(
                "OpenClaw Gateway connect failed: pairing required"
            ),
        ):
            payload = agent.run(
                tender_fields=tender_fields,
                judge_result=judge_result,
                knowledge_context=knowledge_context,
                execution_context={
                    "session_key": "agent:tender-generate:test",
                    "idempotency_key": "generate-fallback-test",
                },
            )

        self.assertTrue(payload["debug"]["used_fallback"])
        self.assertEqual(payload["debug"]["provider"], "fallback-rule")
        self.assertIn("pairing required", payload["debug"]["failure_reason"])
        self.assertIn("proposal_sections", payload["result"])
        self.assertEqual(
            payload["result"]["proposal_sections"]["company_intro"],
            payload["result"]["company_intro"],
        )
        self.assertEqual(
            payload["result"]["proposal_sections"]["business_response"],
            payload["result"]["business_response"],
        )


if __name__ == "__main__":
    unittest.main()
