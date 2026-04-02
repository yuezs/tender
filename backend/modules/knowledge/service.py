from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from core.exceptions import BusinessException
from modules.files.parser import blocks_to_text, parse_file_to_blocks
from modules.knowledge.chunker import split_text_into_chunks
from modules.knowledge.parser import (
    SUPPORTED_KNOWLEDGE_CATEGORIES,
    expand_csv_values,
    normalize_csv_input,
    normalize_parsed_text,
    parse_knowledge_file,
    save_knowledge_upload,
)
from modules.knowledge.repository import KnowledgeRepository
from modules.knowledge.retriever import normalize_retrieve_filters


class KnowledgeService:
    def __init__(self) -> None:
        self.repository = KnowledgeRepository()

    def get_module_status(self) -> dict:
        return {
            "module": "knowledge",
            "status": "ready",
            "message": "knowledge module is ready for MVP flow",
            "mock": False,
            "available_routes": [
                "/api/knowledge/status",
                "/api/knowledge/documents/upload",
                "/api/knowledge/documents",
                "/api/knowledge/documents/{document_id}/process",
                "/api/knowledge/documents/{document_id}/content",
                "/api/knowledge/documents/{document_id}/download",
                "/api/knowledge/documents/{document_id}",
                "/api/knowledge/retrieve",
            ],
            "supported_categories": list(SUPPORTED_KNOWLEDGE_CATEGORIES),
            "repository_ready": self.repository.is_ready(),
        }

    async def upload_document(
        self,
        db: Session,
        *,
        upload_file: UploadFile,
        title: str,
        category: str,
        tags: str | None,
        industry: str | None,
    ) -> dict:
        if not title.strip():
            raise BusinessException("上传失败：title 不能为空。")
        if category not in SUPPORTED_KNOWLEDGE_CATEGORIES:
            raise BusinessException("上传失败：category 不在允许范围内。")

        saved_file = await save_knowledge_upload(upload_file, category)
        document = self.repository.create_document(
            db,
            {
                "document_id": saved_file["document_id"],
                "title": title.strip(),
                "category": category,
                "file_name": saved_file["file_name"],
                "extension": saved_file["extension"],
                "tags": normalize_csv_input(tags),
                "industry": normalize_csv_input(industry),
                "storage_path": saved_file["storage_path"],
                "parsed_text_path": "",
                "status": "uploaded",
                "error_message": "",
                "chunk_count": 0,
                "content_length": 0,
            },
        )

        return {
            "document_id": document.document_id,
            "title": document.title,
            "category": document.category,
        }

    def list_documents(self, db: Session, category: str | None, status: str | None) -> dict:
        documents = self.repository.list_documents(db, category=category, status=status)
        items = []
        for document in documents:
            items.append(
                {
                    "document_id": document.document_id,
                    "title": document.title,
                    "category": document.category,
                    "file_name": document.file_name,
                    "tags": expand_csv_values(document.tags),
                    "industry": expand_csv_values(document.industry),
                    "status": document.status,
                    "chunk_count": document.chunk_count,
                    "content_length": document.content_length,
                    "error_message": document.error_message,
                    "created_at": document.created_at.isoformat(),
                    "updated_at": document.updated_at.isoformat(),
                }
            )
        return {"items": items}

    def process_document(self, db: Session, document_id: str) -> dict:
        document = self.repository.get_document(db, document_id)
        try:
            parsed_result = parse_knowledge_file(document.storage_path, document.document_id, document.category)
            chunks = split_text_into_chunks(
                parsed_result["text"],
                blocks=parsed_result["blocks"],
                category=document.category,
            )
            if not chunks:
                raise BusinessException("处理失败：文档中未提取到可切块内容。")

            warnings = list(parsed_result["warnings"])
            key_points = list(parsed_result["key_points"])
            if len(chunks) == 1 and document.category in {"project_cases", "qualifications"}:
                warnings.append("Only one chunk was generated for this category; review the source structure.")
            if document.category == "company_profile" and not key_points:
                warnings.append("No clear company profile key points were extracted; review the source structure.")

            chunk_records = []
            for chunk in chunks:
                chunk_records.append(
                    {
                        "chunk_id": uuid4().hex,
                        "section_title": chunk["section_title"],
                        "content": chunk["content"],
                        "chunk_index": chunk["chunk_index"],
                    }
                )

            self.repository.replace_chunks(db, document, chunk_records)
            updated = self.repository.update_document(
                db,
                document_id,
                {
                    "parsed_text_path": parsed_result["parsed_text_path"],
                    "status": "processed",
                    "error_message": "",
                    "chunk_count": len(chunk_records),
                    "content_length": len(parsed_result["text"]),
                },
            )
            return {
                "document_id": updated.document_id,
                "chunk_count": updated.chunk_count,
                "status": updated.status,
                "content_length": updated.content_length,
                "parse_summary": parsed_result["parse_summary"],
                "warnings": warnings,
                "key_points": key_points,
                "chunk_preview": [
                    {
                        "section_title": chunk["section_title"],
                        "content_preview": chunk["content"][:180],
                        "char_count": chunk["char_count"],
                    }
                    for chunk in chunks[:3]
                ],
            }
        except BusinessException as exc:
            self.repository.update_document(
                db,
                document_id,
                {
                    "status": "error",
                    "error_message": exc.message,
                },
            )
            raise exc

    def get_document_content(self, db: Session, document_id: str) -> dict:
        document = self.repository.get_document(db, document_id)
        parsed_text_path = Path(document.parsed_text_path) if document.parsed_text_path else None

        if parsed_text_path and parsed_text_path.exists():
            content = normalize_parsed_text(parsed_text_path.read_text(encoding="utf-8"))
            source = "parsed_text"
        else:
            storage_path = Path(document.storage_path)
            if not storage_path.exists():
                raise BusinessException("查看失败：原始知识文档不存在。", status_code=404)
            content = normalize_parsed_text(blocks_to_text(parse_file_to_blocks(storage_path)))
            source = "raw_file"

        if not content:
            raise BusinessException("查看失败：当前文档没有可展示的文本内容。")

        return {
            "document_id": document.document_id,
            "title": document.title,
            "category": document.category,
            "status": document.status,
            "source": source,
            "content": content,
        }

    def get_document_download(self, db: Session, document_id: str) -> dict:
        document = self.repository.get_document(db, document_id)
        file_path = Path(document.storage_path)
        if not file_path.exists():
            raise BusinessException("下载失败：原始知识文档不存在。", status_code=404)

        media_type = "text/plain; charset=utf-8"
        if document.extension == ".docx":
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

        return {
            "file_path": str(file_path),
            "file_name": document.file_name,
            "media_type": media_type,
        }

    def delete_document(self, db: Session, document_id: str) -> dict:
        document = self.repository.get_document(db, document_id)
        raw_file_path = Path(document.storage_path)
        parsed_text_path = Path(document.parsed_text_path) if document.parsed_text_path else None
        title = document.title

        self.repository.delete_document(db, document_id)

        if raw_file_path.exists():
            raw_file_path.unlink()
        if parsed_text_path and parsed_text_path.exists():
            parsed_text_path.unlink()

        return {
            "document_id": document_id,
            "title": title,
        }

    def retrieve(self, db: Session, payload: dict) -> dict:
        filters = normalize_retrieve_filters(
            category=payload.get("category"),
            query=payload.get("query"),
            tags=payload.get("tags"),
            industry=payload.get("industry"),
            limit=payload.get("limit"),
        )
        chunks = self.repository.retrieve_chunks(
            db,
            category=filters["category"],
            query=filters["query"],
            tags=filters["tags"],
            industry=filters["industry"],
            limit=filters["limit"],
        )

        return {
            "chunks": [
                {
                    "id": chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "category": chunk.category,
                    "document_title": chunk.document_title,
                    "section_title": chunk.section_title,
                    "content": chunk.content,
                }
                for chunk in chunks
            ]
        }
