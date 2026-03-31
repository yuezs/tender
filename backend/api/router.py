from fastapi import APIRouter

from core.response import success_response
from modules.knowledge.router import router as knowledge_router
from modules.tender.router import router as tender_router

api_router = APIRouter(prefix="/api")


@api_router.get("/health")
def health_check():
    return success_response({"status": "ok"})


api_router.include_router(tender_router)
api_router.include_router(knowledge_router)
