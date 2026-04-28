from datetime import datetime

from sqlalchemy import DateTime, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Theme(Base):
    __tablename__ = "themes"
    __table_args__ = (UniqueConstraint("name", "theme_type", name="uq_themes_name_type"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    code: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    theme_type: Mapped[str] = mapped_column(String(20), index=True)
    source: Mapped[str] = mapped_column(String(40), default="akshare")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    stocks = relationship("ThemeStock", back_populates="theme", cascade="all, delete-orphan")
    scores = relationship("ThemeScore", back_populates="theme", cascade="all, delete-orphan")

