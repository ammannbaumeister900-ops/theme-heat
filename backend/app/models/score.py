from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class ThemeScore(Base):
    __tablename__ = "theme_scores"
    __table_args__ = (UniqueConstraint("theme_id", "week_start", "week_end", name="uq_theme_score_week"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    theme_id: Mapped[int] = mapped_column(ForeignKey("themes.id", ondelete="CASCADE"), index=True)
    week_start: Mapped[date] = mapped_column(Date, index=True)
    week_end: Mapped[date] = mapped_column(Date, index=True)
    overall_score: Mapped[float] = mapped_column(Float, index=True)
    status: Mapped[str] = mapped_column(String(30), default="neutral")
    turnover_ratio_score: Mapped[float] = mapped_column(Float)
    average_return_score: Mapped[float] = mapped_column(Float)
    advancing_ratio_score: Mapped[float] = mapped_column(Float)
    strength_streak_score: Mapped[float] = mapped_column(Float)
    average_return: Mapped[float] = mapped_column(Float)
    median_return: Mapped[float] = mapped_column(Float)
    advancing_ratio: Mapped[float] = mapped_column(Float)
    turnover_ratio: Mapped[float] = mapped_column(Float)
    strong_weeks: Mapped[int] = mapped_column(Integer, default=0)
    sample_size: Mapped[int] = mapped_column(Integer, default=0)
    total_turnover: Mapped[float] = mapped_column(Numeric(20, 2), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    theme = relationship("Theme", back_populates="scores")

