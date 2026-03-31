from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from core.database import get_db
from core.response import success_response
from modules.tender.schema import TenderProcessRequest
from modules.tender.service import TenderService

router = APIRouter(prefix="/tender", tags=["tender"])
service = TenderService()


@router.get("/status")
def get_tender_module_status():
    return success_response(service.get_module_status())


@router.post("/upload")
async def upload_tender_file(
    file: UploadFile = File(...),
    source_type: str = Form("upload"),
    source_url: str | None = Form(None),
):
    result = await service.upload_tender_file(
        upload_file=file,
        source_type=source_type,
        source_url=source_url,
    )
    return success_response(result, message="招标文件上传成功。")


@router.post("/parse")
def parse_tender_file(payload: TenderProcessRequest):
    return success_response(service.parse_tender(payload.file_id), message="招标文件解析成功。")


@router.post("/extract")
def extract_tender_fields(payload: TenderProcessRequest):
    return success_response(service.extract_tender(payload.file_id), message="核心字段抽取成功。")


@router.post("/judge")
def judge_tender(payload: TenderProcessRequest, db: Session = Depends(get_db)):
    return success_response(service.judge_tender(db, payload.file_id), message="投标建议生成成功。")


@router.post("/generate")
def generate_tender(payload: TenderProcessRequest, db: Session = Depends(get_db)):
    return success_response(service.generate_tender(db, payload.file_id), message="标书初稿生成成功。")
