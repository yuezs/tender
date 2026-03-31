import json

from core.config import settings
from core.exceptions import BusinessException
from modules.agent.openclaw_client import OpenClawClient
from modules.agent.output_parser import ensure_extract_result
from modules.agent.prompt_templates import build_extract_prompt


class ExtractAgent:
    def __init__(self) -> None:
        self.client = OpenClawClient()

    def build_prompt(self, parsed_text: str) -> str:
        return build_extract_prompt(parsed_text)

    def run(
        self,
        *,
        parsed_text: str,
        fallback_result: dict,
        execution_context: dict | None = None,
        prompt: str | None = None,
    ) -> dict:
        prompt = prompt or self.build_prompt(parsed_text)
        execution_context = execution_context or {}

        if settings.agent_use_real_llm:
            try:
                llm_response = self._run_llm(prompt=prompt, execution_context=execution_context)
                raw_result = self.client.parse_json_object(llm_response["text"])
                normalized_result = ensure_extract_result(raw_result)
                if self._is_empty_extract_result(normalized_result):
                    raise BusinessException("OpenClaw returned an empty extraction result.")
                return {
                    "result": normalized_result,
                    "debug": llm_response["debug"],
                    "prompt": prompt,
                    "raw_text": llm_response["text"],
                }
            except BusinessException as exc:
                normalized_fallback = ensure_extract_result(fallback_result)
                return {
                    "result": normalized_fallback,
                    "debug": {
                        "provider": "fallback-rule",
                        "agent_id": settings.openclaw_agent_extract,
                        "used_fallback": True,
                        "failure_reason": exc.message,
                        "session_key": execution_context.get("session_key", ""),
                        "run_id": execution_context.get("run_id", ""),
                        "idempotency_key": execution_context.get("idempotency_key", ""),
                    },
                    "prompt": prompt,
                    "raw_text": json.dumps(normalized_fallback, ensure_ascii=False, indent=2),
                }

        normalized_fallback = ensure_extract_result(fallback_result)
        return {
            "result": normalized_fallback,
            "debug": {
                "provider": "fallback-rule",
                "agent_id": settings.openclaw_agent_extract,
                "used_fallback": True,
                "failure_reason": "AGENT_USE_REAL_LLM is disabled.",
                "session_key": execution_context.get("session_key", ""),
                "run_id": execution_context.get("run_id", ""),
                "idempotency_key": execution_context.get("idempotency_key", ""),
            },
            "prompt": prompt,
            "raw_text": json.dumps(normalized_fallback, ensure_ascii=False, indent=2),
        }

    def _run_llm(self, *, prompt: str, execution_context: dict) -> dict:
        run_id = str(execution_context.get("run_id", "")).strip()
        common_kwargs = {
            "agent_id": settings.openclaw_agent_extract,
            "message": prompt,
            "session_key": execution_context["session_key"],
            "idempotency_key": execution_context["idempotency_key"],
        }
        if run_id:
            return self.client.wait_agent_run(run_id=run_id, **common_kwargs)
        return self.client.run_agent(**common_kwargs)

    def _is_empty_extract_result(self, result: dict) -> bool:
        return not any(
            [
                result.get("project_name"),
                result.get("tender_company"),
                result.get("budget"),
                result.get("deadline"),
                result.get("qualification_requirements"),
                result.get("delivery_requirements"),
                result.get("scoring_focus"),
            ]
        )
