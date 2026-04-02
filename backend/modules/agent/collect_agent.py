from core.config import settings
from core.exceptions import BusinessException
from modules.agent.openclaw_client import OpenClawClient
from modules.agent.output_parser import ensure_collect_result
from modules.agent.prompt_templates import build_collect_prompt


class CollectAgent:
    def __init__(self) -> None:
        self.client = OpenClawClient()

    def build_prompt(self, source: str) -> str:
        return build_collect_prompt(source)

    def run(
        self,
        *,
        source: str,
        execution_context: dict | None = None,
        prompt: str | None = None,
    ) -> dict:
        prompt = prompt or self.build_prompt(source)
        execution_context = execution_context or {}

        if not settings.agent_use_real_llm:
            raise BusinessException(
                "Discovery collect requires real OpenClaw. Set AGENT_USE_REAL_LLM=true and restart backend."
            )
        if not settings.discovery_collect_use_openclaw_agent:
            raise BusinessException(
                "Discovery collect requires DISCOVERY_COLLECT_USE_OPENCLAW_AGENT=true."
            )

        llm_response = self._run_llm(prompt=prompt, execution_context=execution_context)
        raw_result = self.client.parse_json_object(llm_response["text"])
        normalized_result = ensure_collect_result(raw_result)
        if not normalized_result["projects"]:
            raise BusinessException("OpenClaw collect agent returned no collectable projects.")
        return {
            "result": normalized_result,
            "debug": {
                **llm_response["debug"],
                "collect_mode": "openclaw-agent",
            },
            "prompt": prompt,
            "raw_text": llm_response["text"],
        }

    def _run_llm(self, *, prompt: str, execution_context: dict) -> dict:
        run_id = str(execution_context.get("run_id", "")).strip()
        common_kwargs = {
            "agent_id": settings.openclaw_agent_collect,
            "message": prompt,
            "session_key": execution_context["session_key"],
            "idempotency_key": execution_context["idempotency_key"],
        }
        if run_id:
            return self.client.wait_agent_run(run_id=run_id, **common_kwargs)
        return self.client.run_agent(**common_kwargs)
