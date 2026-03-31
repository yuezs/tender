from fastapi import APIRouter

from core.response import success_response
from modules.files.service import FileService

router = APIRouter(prefix="/files", tags=["files"])
service = FileService()


@router.get("/status")
def get_file_module_status():
    return success_response(service.ping())
