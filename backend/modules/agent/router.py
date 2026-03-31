from fastapi import APIRouter

from core.response import success_response
from modules.agent.service import AgentService

router = APIRouter(prefix="/agent", tags=["agent"])
service = AgentService()


@router.get("/status")
def get_agent_module_status():
    return success_response(service.ping())
