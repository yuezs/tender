from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class TenderRecord(Base):
    __tablename__ = "tender_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    file_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
