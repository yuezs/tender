import json

from core.config import settings
from core.exceptions import BusinessException
from modules.agent.openclaw_client import OpenClawClient
from modules.agent.output_parser import ensure_judge_result
from modules.agent.prompt_templates import build_judge_prompt


class JudgeAgent:
    def __init__(self) -> None:
        self.client = OpenClawClient()

    def build_prompt(self, tender_fields: dict, knowledge_context: dict) -> str:
        return build_judge_prompt(tender_fields, knowledge_context)

    def run(
        self,
        tender_fields: dict,
        knowledge_context: dict,
        *,
        execution_context: dict | None = None,
        prompt: str | None = None,
    ) -> dict:
        prompt = prompt or self.build_prompt(tender_fields, knowledge_context)
        execution_context = execution_context or {}

        if settings.agent_use_real_llm:
            try:
                llm_response = self._run_llm(prompt=prompt, execution_context=execution_context)
                raw_result = self.client.parse_json_object(llm_response["text"])
                return {
                    "result": ensure_judge_result(raw_result, knowledge_context, prompt),
                    "debug": llm_response["debug"],
                    "prompt": prompt,
                    "raw_text": llm_response["text"],
                }
            except BusinessException as exc:
                fallback_result = self._build_fallback_result(tender_fields, knowledge_context)
                return {
                    "result": ensure_judge_result(fallback_result, knowledge_context, prompt),
                    "debug": {
                        "provider": "fallback-rule",
                        "agent_id": settings.openclaw_agent_judge,
                        "used_fallback": True,
                        "failure_reason": exc.message,
                        "session_key": execution_context.get("session_key", ""),
                        "run_id": execution_context.get("run_id", ""),
                        "idempotency_key": execution_context.get("idempotency_key", ""),
                    },
                    "prompt": prompt,
                    "raw_text": json.dumps(fallback_result, ensure_ascii=False, indent=2),
                }

        fallback_result = self._build_fallback_result(tender_fields, knowledge_context)
        return {
            "result": ensure_judge_result(fallback_result, knowledge_context, prompt),
            "debug": {
                "provider": "fallback-rule",
                "agent_id": settings.openclaw_agent_judge,
                "used_fallback": True,
                "failure_reason": "AGENT_USE_REAL_LLM is disabled.",
                "session_key": execution_context.get("session_key", ""),
                "run_id": execution_context.get("run_id", ""),
                "idempotency_key": execution_context.get("idempotency_key", ""),
            },
            "prompt": prompt,
            "raw_text": json.dumps(fallback_result, ensure_ascii=False, indent=2),
        }

    def _run_llm(self, *, prompt: str, execution_context: dict) -> dict:
        run_id = str(execution_context.get("run_id", "")).strip()
        common_kwargs = {
            "agent_id": settings.openclaw_agent_judge,
            "message": prompt,
            "session_key": execution_context["session_key"],
            "idempotency_key": execution_context["idempotency_key"],
        }
        if run_id:
            return self.client.wait_agent_run(run_id=run_id, **common_kwargs)
        return self.client.run_agent(**common_kwargs)

    def _build_fallback_result(self, tender_fields: dict, knowledge_context: dict) -> dict:
        knowledge_chunks = knowledge_context.get("chunks", [])
        qualification_hits = [
            chunk for chunk in knowledge_chunks if chunk.get("category") == "qualifications"
        ]
        case_hits = [
            chunk for chunk in knowledge_chunks if chunk.get("category") == "project_cases"
        ]

        risks: list[str] = []
        if not tender_fields.get("budget"):
            risks.append("预算金额不明确，项目投入产出比需要人工复核。")
        if not tender_fields.get("deadline"):
            risks.append("投标截止时间不明确，时间窗口存在不确定性。")
        if not qualification_hits:
            risks.append("知识库未命中可复用的资质材料，资质响应支撑不足。")
        if not case_hits:
            risks.append("知识库未命中类似项目案例，案例支撑不足。")
        if not tender_fields.get("qualification_requirements"):
            risks.append("招标文件中的资质要求提取不足，需要人工核验。")

        should_bid = len(risks) <= 2 and (bool(qualification_hits) or bool(case_hits))
        if should_bid:
            reason = "已命中可复用的企业资质或项目案例，且当前关键信息相对完整，建议继续推进投标评估。"
        else:
            reason = "知识支撑或关键信息仍不充分，建议先补齐资质材料与案例证据后再决定是否投标。"

        return {
            "should_bid": should_bid,
            "reason": reason,
            "risks": risks,
        }
