from __future__ import annotations

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, selectinload

from app.models import DailyQuote, Stock, Theme, ThemeScore, ThemeStock
from app.schemas.theme import ThemeDetail, ThemeRankingItem, ThemeScorePoint, ThemeStockItem


def upsert_theme(db: Session, *, name: str, code: str | None, theme_type: str, source: str) -> Theme:
    theme = db.scalar(select(Theme).where(Theme.name == name, Theme.theme_type == theme_type))
    if theme is None:
        theme = Theme(name=name, code=code or None, theme_type=theme_type, source=source)
        db.add(theme)
        db.flush()
        return theme

    theme.code = code or theme.code
    theme.source = source
    db.flush()
    return theme


def upsert_stock(db: Session, *, symbol: str, name: str) -> Stock:
    stock = db.scalar(select(Stock).where(Stock.symbol == symbol))
    if stock is None:
        stock = Stock(symbol=symbol, name=name)
        db.add(stock)
        db.flush()
        return stock

    stock.name = name
    db.flush()
    return stock


def ensure_theme_stock_relation(db: Session, *, theme_id: int, stock_id: int) -> None:
    existing = db.scalar(
        select(ThemeStock).where(ThemeStock.theme_id == theme_id, ThemeStock.stock_id == stock_id)
    )
    if existing is None:
        db.add(ThemeStock(theme_id=theme_id, stock_id=stock_id))
        db.flush()


def get_theme_rankings(db: Session) -> list[ThemeRankingItem]:
    latest_week = db.scalar(select(func.max(ThemeScore.week_end)))
    stmt = (
        select(Theme, ThemeScore)
        .join(ThemeScore, ThemeScore.theme_id == Theme.id, isouter=True)
        .where(ThemeScore.week_end == latest_week if latest_week else True)
        .order_by(desc(ThemeScore.overall_score), Theme.name)
    )
    rows = db.execute(stmt).all()
    results: list[ThemeRankingItem] = []
    for theme, score in rows:
        stock_count = db.scalar(select(func.count(ThemeStock.id)).where(ThemeStock.theme_id == theme.id)) or 0
        results.append(
            ThemeRankingItem(
                id=theme.id,
                name=theme.name,
                code=theme.code,
                theme_type=theme.theme_type,
                source=theme.source,
                latest_score=round(score.overall_score, 2) if score else None,
                latest_status=score.status if score else None,
                week_start=score.week_start if score else None,
                week_end=score.week_end if score else None,
                stock_count=stock_count,
            )
        )
    return results


def get_theme_detail(db: Session, theme_id: int) -> ThemeDetail | None:
    theme = db.scalar(
        select(Theme)
        .where(Theme.id == theme_id)
        .options(
            selectinload(Theme.stocks).selectinload(ThemeStock.stock),
            selectinload(Theme.scores),
        )
    )
    if theme is None:
        return None

    latest_quote_by_stock: dict[int, DailyQuote] = {}
    stock_ids = [rel.stock_id for rel in theme.stocks]
    if stock_ids:
        quote_rows = db.execute(
            select(DailyQuote)
            .where(DailyQuote.stock_id.in_(stock_ids))
            .order_by(DailyQuote.stock_id, desc(DailyQuote.trade_date))
        ).scalars()
        for quote in quote_rows:
            latest_quote_by_stock.setdefault(quote.stock_id, quote)

    history = sorted(theme.scores, key=lambda item: item.week_end)
    stocks = []
    for relation in sorted(theme.stocks, key=lambda item: item.stock.symbol):
        stock = relation.stock
        latest_quote = latest_quote_by_stock.get(stock.id)
        stocks.append(
            ThemeStockItem(
                id=stock.id,
                symbol=stock.symbol,
                name=stock.name,
                latest_close_price=latest_quote.close_price if latest_quote else None,
                latest_pct_change=latest_quote.pct_change if latest_quote else None,
                latest_turnover_amount=float(latest_quote.turnover_amount) if latest_quote else None,
            )
        )

    latest_score = history[-1] if history else None
    return ThemeDetail(
        id=theme.id,
        name=theme.name,
        code=theme.code,
        theme_type=theme.theme_type,
        source=theme.source,
        latest_score=round(latest_score.overall_score, 2) if latest_score else None,
        latest_status=latest_score.status if latest_score else None,
        stock_count=len(stocks),
        score_history=[
            ThemeScorePoint.model_validate(item)
            for item in history[-12:]
        ],
        stocks=stocks,
    )

