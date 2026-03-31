from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class AgentRunRecord(Base):
    __tablename__ = "agent_run_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    agent_name: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
