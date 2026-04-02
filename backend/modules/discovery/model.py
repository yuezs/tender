from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class ProjectDiscoveryRun(Base):
    __tablename__ = "project_discovery_runs"

    run_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    trigger_type: Mapped[str] = mapped_column(String(32), nullable=False, default="manual")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="running", index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    total_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_new: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_updated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    targeting_snapshot: Mapped[str] = mapped_column(Text, nullable=False, default="{}")


class ProjectLead(Base):
    __tablename__ = "project_leads"

    lead_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    source_notice_id: Mapped[str] = mapped_column(String(128), nullable=False, default="", index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    notice_type: Mapped[str] = mapped_column(String(128), nullable=False, default="", index=True)
    region: Mapped[str] = mapped_column(String(128), nullable=False, default="", index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    detail_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    canonical_url: Mapped[str] = mapped_column(String(512), nullable=False, default="", index=True)
    project_code: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    tender_unit: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    budget_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    deadline_text: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    detail_text_path: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    raw_snapshot_path: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    extract_result_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    match_result_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    targeting_match_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    profile_key: Mapped[str] = mapped_column(String(128), nullable=False, default="", index=True)
    profile_title: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    recommendation_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    recommendation_level: Mapped[str] = mapped_column(
        String(32), nullable=False, default="low", index=True
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
