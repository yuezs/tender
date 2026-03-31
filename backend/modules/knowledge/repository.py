from datetime import datetime

from sqlalchemy import delete, desc, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from core.exceptions import BusinessException
from modules.knowledge.model import KnowledgeChunk, KnowledgeDocument


class KnowledgeRepository:
    def is_ready(self) -> bool:
        return True

    def create_document(self, db: Session, payload: dict) -> KnowledgeDocument:
        try:
            document = KnowledgeDocument(**payload)
            db.add(document)
            db.commit()
            db.refresh(document)
            return document
        except SQLAlchemyError as exc:
            db.rollback()
            raise BusinessException(f"知识文档入库失败：{exc.__class__.__name__}") from exc

    def list_documents(
        self,
        db: Session,
        category: str | None = None,
        status: str | None = None,
    ) -> list[KnowledgeDocument]:
        try:
            stmt = select(KnowledgeDocument).order_by(desc(KnowledgeDocument.created_at))
            if category:
                stmt = stmt.where(KnowledgeDocument.category == category)
            if status:
                stmt = stmt.where(KnowledgeDocument.status == status)
            return list(db.scalars(stmt).all())
        except SQLAlchemyError as exc:
            raise BusinessException(f"知识文档查询失败：{exc.__class__.__name__}") from exc

    def get_document(self, db: Session, document_id: str) -> KnowledgeDocument:
        try:
            document = db.get(KnowledgeDocument, document_id)
            if not document:
                raise BusinessException("未找到对应的知识文档。", status_code=404)
            return document
        except SQLAlchemyError as exc:
            raise BusinessException(f"知识文档读取失败：{exc.__class__.__name__}") from exc

    def update_document(self, db: Session, document_id: str, updates: dict) -> KnowledgeDocument:
        try:
            document = self.get_document(db, document_id)
            for key, value in updates.items():
                setattr(document, key, value)
            document.updated_at = datetime.utcnow()
            db.add(document)
            db.commit()
            db.refresh(document)
            return document
        except SQLAlchemyError as exc:
            db.rollback()
            raise BusinessException(f"知识文档更新失败：{exc.__class__.__name__}") from exc

    def replace_chunks(self, db: Session, document: KnowledgeDocument, chunks: list[dict]) -> list[KnowledgeChunk]:
        try:
            db.execute(delete(KnowledgeChunk).where(KnowledgeChunk.document_id == document.document_id))
            db.flush()

            records: list[KnowledgeChunk] = []
            for chunk in chunks:
                record = KnowledgeChunk(
                    chunk_id=chunk["chunk_id"],
                    document_id=document.document_id,
                    category=document.category,
                    document_title=document.title,
                    tags=document.tags,
                    industry=document.industry,
                    section_title=chunk["section_title"],
                    content=chunk["content"],
                    chunk_index=chunk["chunk_index"],
                )
                db.add(record)
                records.append(record)

            db.commit()
            return records
        except SQLAlchemyError as exc:
            db.rollback()
            raise BusinessException(f"知识切块写入失败：{exc.__class__.__name__}") from exc

    def retrieve_chunks(
        self,
        db: Session,
        *,
        category: str,
        query: str,
        tags: list[str],
        industry: list[str],
        limit: int,
    ) -> list[KnowledgeChunk]:
        try:
            stmt = select(KnowledgeChunk)

            if category:
                stmt = stmt.where(KnowledgeChunk.category == category)

            for tag in tags:
                stmt = stmt.where(KnowledgeChunk.tags.like(f"%{tag}%"))

            if industry:
                stmt = stmt.where(or_(*[KnowledgeChunk.industry.like(f"%{item}%") for item in industry]))

            if query:
                like_value = f"%{query}%"
                stmt = stmt.where(
                    or_(
                        KnowledgeChunk.content.like(like_value),
                        KnowledgeChunk.section_title.like(like_value),
                        KnowledgeChunk.document_title.like(like_value),
                    )
                )

            stmt = stmt.order_by(KnowledgeChunk.created_at.desc(), KnowledgeChunk.chunk_index.asc()).limit(limit)
            return list(db.scalars(stmt).all())
        except SQLAlchemyError as exc:
            raise BusinessException(f"知识检索失败：{exc.__class__.__name__}") from exc
