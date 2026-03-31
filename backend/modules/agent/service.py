from modules.agent.orchestrator import AgentOrchestrator


class AgentService:
    def __init__(self) -> None:
        self.orchestrator = AgentOrchestrator()

    def ping(self) -> dict:
        return {
            "module": "agent",
            "status": "ready",
            "mock": True,
            "available_tasks": ["judge", "generate"],
        }

    def run_judge(self, db, tender_record: dict) -> dict:
        return self.orchestrator.run_judge(db, tender_record)

    def run_generate(self, db, tender_record: dict, judge_result: dict) -> dict:
        return self.orchestrator.run_generate(db, tender_record, judge_result)
