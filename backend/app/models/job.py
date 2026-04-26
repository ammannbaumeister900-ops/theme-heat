from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class ComputeJob(Base):
    __tablename__ = "compute_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    stage: Mapped[str] = mapped_column(String(20), default="queued", index=True)
    current_theme_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    current_theme_index: Mapped[int] = mapped_column(Integer, default=0)
    total_theme_count: Mapped[int] = mapped_column(Integer, default=0)
    processed_theme_count: Mapped[int] = mapped_column(Integer, default=0)
    synced_theme_count: Mapped[int] = mapped_column(Integer, default=0)
    score_count: Mapped[int] = mapped_column(Integer, default=0)
    last_theme_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

