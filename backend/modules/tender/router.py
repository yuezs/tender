from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from core.database import get_db
from core.response import success_response
from modules.tender.schema import TenderProcessRequest, TenderSectionGenerateRequest
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
    return success_response(service.generate_tender(db, payload.file_id), message="标书目录生成成功。")


@router.post("/generate/section")
def generate_tender_section(payload: TenderSectionGenerateRequest, db: Session = Depends(get_db)):
    return success_response(
        service.generate_tender_section(db, payload.file_id, payload.section_id),
        message="章节正文生成成功。",
    )


@router.post("/documents/fulltext")
def generate_full_text_document(payload: TenderProcessRequest, db: Session = Depends(get_db)):
    return success_response(
        service.generate_full_text_document(db, payload.file_id),
        message="全文 Word 已生成。",
    )


@router.get("/sections/{file_id}/{section_id}")
def get_tender_section_content(file_id: str, section_id: str):
    return success_response(
        service.get_tender_section_content(file_id, section_id),
        message="章节正文获取成功。",
    )


@router.get("/results/latest")
def get_latest_tender_result():
    return success_response(service.get_latest_result(), message="最近一次招标结果获取成功。")


@router.get("/results/{file_id}")
def get_tender_result(file_id: str):
    return success_response(service.get_tender_result(file_id), message="招标结果获取成功。")


@router.get("/documents/{document_id}/download")
def download_generated_tender_document(document_id: str):
    document = service.get_generated_document(document_id)
    return FileResponse(
        path=document["storage_path"],
        filename=document["file_name"],
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
