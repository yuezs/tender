from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from core.database import get_db
from core.response import success_response
from modules.knowledge.schema import KnowledgeRetrieveRequest
from modules.knowledge.service import KnowledgeService

router = APIRouter(prefix="/knowledge", tags=["knowledge"])
service = KnowledgeService()


@router.get("/status")
def get_knowledge_module_status():
    return success_response(service.get_module_status())


@router.post("/documents/upload")
async def upload_knowledge_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    category: str = Form(...),
    tags: str | None = Form(None),
    industry: str | None = Form(None),
    db: Session = Depends(get_db),
):
    result = await service.upload_document(
        db,
        upload_file=file,
        title=title,
        category=category,
        tags=tags,
        industry=industry,
    )
    return success_response(result, message="知识文档上传成功。")


@router.get("/documents")
def list_knowledge_documents(
    category: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    result = service.list_documents(db, category=category, status=status)
    return success_response(result, message="知识文档列表获取成功。")


@router.post("/documents/{document_id}/process")
def process_knowledge_document(document_id: str, db: Session = Depends(get_db)):
    result = service.process_document(db, document_id)
    return success_response(result, message="知识文档处理成功。")


@router.get("/documents/{document_id}/content")
def get_knowledge_document_content(document_id: str, db: Session = Depends(get_db)):
    result = service.get_document_content(db, document_id)
    return success_response(result, message="知识文档全文获取成功。")


@router.get("/documents/{document_id}/download")
def download_knowledge_document(document_id: str, db: Session = Depends(get_db)):
    result = service.get_document_download(db, document_id)
    return FileResponse(
        path=result["file_path"],
        filename=result["file_name"],
        media_type=result["media_type"],
    )


@router.delete("/documents/{document_id}")
def delete_knowledge_document(document_id: str, db: Session = Depends(get_db)):
    result = service.delete_document(db, document_id)
    return success_response(result, message="知识文档删除成功。")


@router.post("/retrieve")
def retrieve_knowledge_chunks(payload: KnowledgeRetrieveRequest, db: Session = Depends(get_db)):
    result = service.retrieve(db, payload.model_dump())
    return success_response(result, message="知识检索成功。")
