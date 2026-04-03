from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from core.exceptions import BusinessException
from modules.discovery.model import ProjectDiscoveryRun, ProjectLead


class DiscoveryRepository:
    def is_ready(self) -> bool:
        return True

    def create_run(self, db: Session, payload: dict) -> ProjectDiscoveryRun:
        try:
            record = ProjectDiscoveryRun(**payload)
            db.add(record)
            db.commit()
            db.refresh(record)
            return record
        except SQLAlchemyError as exc:
            db.rollback()
            raise BusinessException(f"discovery run create failed: {exc.__class__.__name__}") from exc

    def update_run(self, db: Session, run_id: str, updates: dict) -> ProjectDiscoveryRun:
        try:
            record = self.get_run(db, run_id)
            for key, value in updates.items():
                setattr(record, key, value)
            db.add(record)
            db.commit()
            db.refresh(record)
            return record
        except SQLAlchemyError as exc:
            db.rollback()
            raise BusinessException(f"discovery run update failed: {exc.__class__.__name__}") from exc

    def get_run(self, db: Session, run_id: str) -> ProjectDiscoveryRun:
        try:
            record = db.get(ProjectDiscoveryRun, run_id)
            if not record:
                raise BusinessException("discovery run not found", status_code=404)
            return record
        except SQLAlchemyError as exc:
            raise BusinessException(f"discovery run read failed: {exc.__class__.__name__}") from exc

    def list_runs(self, db: Session, limit: int = 20) -> list[ProjectDiscoveryRun]:
        try:
            stmt = select(ProjectDiscoveryRun).order_by(ProjectDiscoveryRun.started_at.desc()).limit(limit)
            return list(db.scalars(stmt).all())
        except SQLAlchemyError as exc:
            raise BusinessException(f"discovery runs query failed: {exc.__class__.__name__}") from exc

    def create_lead(self, db: Session, payload: dict) -> ProjectLead:
        try:
            record = ProjectLead(**payload)
            db.add(record)
            db.commit()
            db.refresh(record)
            return record
        except SQLAlchemyError as exc:
            db.rollback()
            raise BusinessException(f"project lead create failed: {exc.__class__.__name__}") from exc

    def update_lead(self, db: Session, lead_id: str, updates: dict) -> ProjectLead:
        try:
            record = self.get_lead(db, lead_id)
            for key, value in updates.items():
                setattr(record, key, value)
            record.updated_at = datetime.utcnow()
            db.add(record)
            db.commit()
            db.refresh(record)
            return record
        except SQLAlchemyError as exc:
            db.rollback()
            raise BusinessException(f"project lead update failed: {exc.__class__.__name__}") from exc

    def get_lead(self, db: Session, lead_id: str) -> ProjectLead:
        try:
            record = db.get(ProjectLead, lead_id)
            if not record:
                raise BusinessException("project lead not found", status_code=404)
            return record
        except SQLAlchemyError as exc:
            raise BusinessException(f"project lead read failed: {exc.__class__.__name__}") from exc

    def find_existing_lead(
        self,
        db: Session,
        *,
        source: str,
        canonical_url: str,
        source_notice_id: str,
        title: str,
        published_at: datetime | None,
    ) -> ProjectLead | None:
        try:
            if canonical_url:
                existing = db.scalar(select(ProjectLead).where(ProjectLead.canonical_url == canonical_url))
                if existing:
                    return existing

            if source_notice_id:
                existing = db.scalar(
                    select(ProjectLead).where(
                        ProjectLead.source == source,
                        ProjectLead.source_notice_id == source_notice_id,
                    )
                )
                if existing:
                    return existing

            if title and published_at:
                existing = db.scalar(
                    select(ProjectLead).where(
                        ProjectLead.source == source,
                        ProjectLead.title == title,
                        ProjectLead.published_at == published_at,
                    )
                )
                if existing:
                    return existing
            return None
        except SQLAlchemyError as exc:
            raise BusinessException(f"project lead dedupe failed: {exc.__class__.__name__}") from exc

    def list_projects(
        self,
        db: Session,
        *,
        keyword: str,
        region: str,
        notice_type: str,
        recommendation_level: str,
        profile_key: str,
        recommended_only: bool,
        page: int,
        page_size: int,
    ) -> tuple[list[ProjectLead], int]:
        try:
            stmt = select(ProjectLead).where(ProjectLead.status == "active")

            if keyword:
                like_value = f"%{keyword}%"
                stmt = stmt.where(
                    or_(
                        ProjectLead.title.like(like_value),
                        ProjectLead.project_code.like(like_value),
                        ProjectLead.tender_unit.like(like_value),
                    )
                )
            if region:
                stmt = stmt.where(ProjectLead.region.like(f"%{region}%"))
            if notice_type:
                stmt = stmt.where(ProjectLead.notice_type.like(f"%{notice_type}%"))
            if recommendation_level:
                stmt = stmt.where(ProjectLead.recommendation_level == recommendation_level)
            if profile_key:
                stmt = stmt.where(ProjectLead.profile_key == profile_key)
            if recommended_only:
                stmt = stmt.where(ProjectLead.recommendation_score >= 60)

            total = int(db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)

            stmt = stmt.order_by(
                ProjectLead.recommendation_score.desc(),
                ProjectLead.targeting_match_score.desc(),
                ProjectLead.published_at.desc(),
                ProjectLead.updated_at.desc(),
            )
            stmt = stmt.offset((page - 1) * page_size).limit(page_size)
            return list(db.scalars(stmt).all()), total
        except SQLAlchemyError as exc:
            raise BusinessException(f"project leads query failed: {exc.__class__.__name__}") from exc
