from core.config import settings
from modules.agent.collect_agent import CollectAgent
from modules.agent.extract_agent import ExtractAgent
from modules.agent.orchestrator import AgentOrchestrator


class AgentService:
    def __init__(self) -> None:
        self.orchestrator = AgentOrchestrator()
        self.collect_agent = CollectAgent()
        self.extract_agent = ExtractAgent()

    def ping(self) -> dict:
        if settings.agent_use_real_llm and settings.discovery_collect_use_openclaw_agent:
            collect_mode = "openclaw-agent"
        else:
            collect_mode = "disabled"
        return {
            "module": "agent",
            "status": "ready",
            "mock": False,
            "collect_mode": collect_mode,
            "available_tasks": ["collect", "extract", "judge", "generate"],
        }

    def prepare_collect(self, *, source: str) -> dict:
        return {
            "agent_id": settings.openclaw_agent_collect,
            "source": source,
            "prompt": self.collect_agent.build_prompt(source),
        }

    def run_collect(self, prepared: dict, *, execution_context: dict | None = None) -> dict:
        return self.collect_agent.run(
            source=prepared["source"],
            prompt=prepared["prompt"],
            execution_context=execution_context,
        )

    def prepare_extract(self, *, parsed_text: str, fallback_result: dict) -> dict:
        return {
            "agent_id": settings.openclaw_agent_extract,
            "parsed_text": parsed_text,
            "fallback_result": fallback_result,
            "prompt": self.extract_agent.build_prompt(parsed_text),
        }

    def run_extract(self, prepared: dict, *, execution_context: dict | None = None) -> dict:
        return self.extract_agent.run(
            parsed_text=prepared["parsed_text"],
            fallback_result=prepared["fallback_result"],
            prompt=prepared["prompt"],
            execution_context=execution_context,
        )

    def prepare_judge(self, db, tender_record: dict) -> dict:
        prepared = self.orchestrator.prepare_judge(db, tender_record)
        prepared["agent_id"] = settings.openclaw_agent_judge
        return prepared

    def run_judge(self, prepared: dict, *, execution_context: dict | None = None) -> dict:
        return self.orchestrator.run_judge_prepared(
            prepared,
            execution_context=execution_context,
        )

    def prepare_generate(self, db, tender_record: dict, judge_result: dict) -> dict:
        prepared = self.orchestrator.prepare_generate(db, tender_record, judge_result)
        prepared["agent_id"] = settings.openclaw_agent_generate
        return prepared

    def run_generate(self, prepared: dict, *, execution_context: dict | None = None) -> dict:
        return self.orchestrator.run_generate_prepared(
            prepared,
            execution_context=execution_context,
        )
