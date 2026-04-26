from datetime import datetime, date

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Stock(Base):
    __tablename__ = "stocks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    symbol: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    market: Mapped[str] = mapped_column(String(20), default="A")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    themes = relationship("ThemeStock", back_populates="stock", cascade="all, delete-orphan")
    quotes = relationship("DailyQuote", back_populates="stock", cascade="all, delete-orphan")


class ThemeStock(Base):
    __tablename__ = "theme_stocks"
    __table_args__ = (UniqueConstraint("theme_id", "stock_id", name="uq_theme_stock"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    theme_id: Mapped[int] = mapped_column(ForeignKey("themes.id", ondelete="CASCADE"))
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    theme = relationship("Theme", back_populates="stocks")
    stock = relationship("Stock", back_populates="themes")


class DailyQuote(Base):
    __tablename__ = "daily_quotes"
    __table_args__ = (UniqueConstraint("stock_id", "trade_date", name="uq_stock_trade_date"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id", ondelete="CASCADE"), index=True)
    trade_date: Mapped[date] = mapped_column(Date, index=True)
    close_price: Mapped[float] = mapped_column(Float)
    pct_change: Mapped[float] = mapped_column(Float)
    turnover_amount: Mapped[float] = mapped_column(Numeric(18, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    stock = relationship("Stock", back_populates="quotes")

