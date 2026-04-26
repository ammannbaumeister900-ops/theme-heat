from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from statistics import median

from sqlalchemy import delete, desc, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import ComputeJob, DailyQuote, Theme, ThemeScore, ThemeStock
from app.schemas.compute import ComputeResponse
from app.services.akshare_service import AKShareService
from app.services.theme_service import ensure_theme_stock_relation, upsert_stock, upsert_theme


logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class ThemeWeekMetrics:
    theme: Theme
    week_start: date
    week_end: date
    average_return: float
    median_return: float
    advancing_ratio: float
    total_turnover: float
    stock_count: int


@dataclass
class ThemeCatalogItem:
    theme_type: str
    index: int
    name: str
    code: str | None
    source: str


class ComputeService:
    def __init__(self) -> None:
        self.ak_service = AKShareService()

    def compute(self, db: Session) -> ComputeResponse:
        catalog = self.build_theme_catalog()
        fetched_quotes_by_symbol: set[str] = set()
        synced_themes = 0
        for item in catalog:
            if self.sync_single_theme(db, item, fetched_quotes_by_symbol):
                synced_themes += 1
        score_count = self.compute_scores_only(db)
        return ComputeResponse(
            success=True,
            message="Computation completed",
            computed_at=datetime.utcnow(),
            theme_count=synced_themes,
            score_count=score_count,
        )

    def build_theme_catalog(self) -> list[ThemeCatalogItem]:
        catalog: list[ThemeCatalogItem] = []
        for theme_type in settings.theme_type_list:
            try:
                theme_list = self.ak_service.fetch_theme_list(theme_type)
            except Exception as exc:
                logger.warning("failed to fetch theme list for %s: %s", theme_type, exc)
                continue
            for index, theme_data in enumerate(theme_list):
                catalog.append(
                    ThemeCatalogItem(
                        theme_type=theme_type,
                        index=index,
                        name=theme_data["name"],
                        code=theme_data.get("code"),
                        source=theme_data["source"],
                    )
                )
        return catalog

    def build_theme_catalog_from_db(self, db: Session) -> list[ThemeCatalogItem]:
        themes = db.scalars(select(Theme).order_by(Theme.theme_type, Theme.name)).all()
        catalog: list[ThemeCatalogItem] = []
        type_indexes: dict[str, int] = {}
        for theme in themes:
            current_index = type_indexes.get(theme.theme_type, 0)
            catalog.append(
                ThemeCatalogItem(
                    theme_type=theme.theme_type,
                    index=current_index,
                    name=theme.name,
                    code=theme.code,
                    source=theme.source,
                )
            )
            type_indexes[theme.theme_type] = current_index + 1
        return catalog

    def sync_single_theme(
        self,
        db: Session,
        item: ThemeCatalogItem,
        fetched_quotes_by_symbol: set[str] | None = None,
    ) -> bool:
        fetched_quotes_by_symbol = fetched_quotes_by_symbol or set()
        start_date, end_date = self.ak_service.get_quote_window()

        theme = upsert_theme(
            db,
            name=item.name,
            code=item.code,
            theme_type=item.theme_type,
            source=item.source,
        )
        try:
            members = self.ak_service.fetch_theme_stocks(item.theme_type, theme.name, theme.code)
        except Exception as exc:
            logger.warning("failed to fetch members for %s/%s: %s", item.theme_type, theme.name, exc)
            db.rollback()
            return False

        db.execute(delete(ThemeStock).where(ThemeStock.theme_id == theme.id))
        db.flush()

        for member in members:
            stock = upsert_stock(db, symbol=member["symbol"], name=member["name"])
            ensure_theme_stock_relation(db, theme_id=theme.id, stock_id=stock.id)

            snapshot_available = all(
                member.get(field) is not None for field in ("close_price", "pct_change", "turnover_amount")
            )
            if snapshot_available:
                self.upsert_quote(
                    db,
                    stock_id=stock.id,
                    trade_date=end_date,
                    close_price=member["close_price"],
                    pct_change=member["pct_change"],
                    turnover_amount=member["turnover_amount"],
                )
                fetched_quotes_by_symbol.add(stock.symbol)
                continue

            if stock.symbol not in fetched_quotes_by_symbol:
                for quote in self.ak_service.fetch_stock_quotes(stock.symbol, start_date, end_date):
                    self.upsert_quote(
                        db,
                        stock_id=stock.id,
                        trade_date=quote["trade_date"],
                        close_price=quote["close_price"],
                        pct_change=quote["pct_change"],
                        turnover_amount=quote["turnover_amount"],
                    )
                fetched_quotes_by_symbol.add(stock.symbol)

        db.commit()
        return True

    def upsert_quote(
        self,
        db: Session,
        *,
        stock_id: int,
        trade_date: date,
        close_price: float,
        pct_change: float,
        turnover_amount: float,
    ) -> None:
        existing = db.scalar(
            select(DailyQuote).where(
                DailyQuote.stock_id == stock_id,
                DailyQuote.trade_date == trade_date,
            )
        )
        if existing is None:
            db.add(
                DailyQuote(
                    stock_id=stock_id,
                    trade_date=trade_date,
                    close_price=close_price,
                    pct_change=pct_change,
                    turnover_amount=turnover_amount,
                )
            )
            return
        existing.close_price = close_price
        existing.pct_change = pct_change
        existing.turnover_amount = turnover_amount

    def compute_scores_only(self, db: Session) -> int:
        week_start, week_end = self._get_current_week()
        metrics_list = self._collect_metrics(db, week_start, week_end)
        return self._persist_scores(db, metrics_list, week_start, week_end)

    def _persist_scores(self, db: Session, metrics_list: list[ThemeWeekMetrics], week_start: date, week_end: date) -> int:
        total_turnover_market = sum(item.total_turnover for item in metrics_list) or 1.0
        max_abs_return = max((max(abs(item.average_return), abs(item.median_return)) for item in metrics_list), default=1.0)
        max_strong_weeks = 8
        score_count = 0

        for metrics in metrics_list:
            turnover_ratio = metrics.total_turnover / total_turnover_market
            avg_component = ((metrics.average_return + metrics.median_return) / 2.0 + max_abs_return) / (2 * max_abs_return)
            avg_component = max(0.0, min(1.0, avg_component))
            advancing_ratio = max(0.0, min(1.0, metrics.advancing_ratio))
            strong_weeks = self._get_consecutive_strong_weeks(db, metrics.theme.id, week_end)
            streak_component = min(strong_weeks / max_strong_weeks, 1.0)

            turnover_ratio_score = turnover_ratio * 100
            average_return_score = avg_component * 100
            advancing_ratio_score = advancing_ratio * 100
            strength_streak_score = streak_component * 100
            overall_score = (
                turnover_ratio_score * 0.30
                + average_return_score * 0.30
                + advancing_ratio_score * 0.20
                + strength_streak_score * 0.20
            )

            status = "cold"
            if overall_score >= 80:
                status = "surging"
            elif overall_score >= 65:
                status = "hot"
            elif overall_score >= 50:
                status = "warm"

            score = db.scalar(
                select(ThemeScore).where(
                    ThemeScore.theme_id == metrics.theme.id,
                    ThemeScore.week_start == week_start,
                    ThemeScore.week_end == week_end,
                )
            )
            payload = dict(
                overall_score=round(overall_score, 2),
                status=status,
                turnover_ratio_score=round(turnover_ratio_score, 2),
                average_return_score=round(average_return_score, 2),
                advancing_ratio_score=round(advancing_ratio_score, 2),
                strength_streak_score=round(strength_streak_score, 2),
                average_return=round(metrics.average_return, 2),
                median_return=round(metrics.median_return, 2),
                advancing_ratio=round(metrics.advancing_ratio, 4),
                turnover_ratio=round(turnover_ratio, 6),
                strong_weeks=strong_weeks,
                sample_size=metrics.stock_count,
                total_turnover=round(metrics.total_turnover, 2),
            )

            if score is None:
                db.add(ThemeScore(theme_id=metrics.theme.id, week_start=week_start, week_end=week_end, **payload))
            else:
                for key, value in payload.items():
                    setattr(score, key, value)
            score_count += 1

        db.commit()
        return score_count

    def get_resume_start_position(self, db: Session, job: ComputeJob, catalog: list[ThemeCatalogItem]) -> int:
        if not catalog:
            return 0
        if not job.current_theme_type:
            return 0
        for position, item in enumerate(catalog):
            if item.theme_type == job.current_theme_type and item.index == job.current_theme_index:
                return position
        return min(job.processed_theme_count, len(catalog))

    def _collect_metrics(self, db: Session, week_start: date, week_end: date) -> list[ThemeWeekMetrics]:
        themes = db.scalars(select(Theme).order_by(Theme.theme_type, Theme.name)).all()
        metrics_list: list[ThemeWeekMetrics] = []

        for theme in themes:
            relations = db.scalars(select(ThemeStock).where(ThemeStock.theme_id == theme.id)).all()
            pct_changes: list[float] = []
            turnovers: list[float] = []
            advancing = 0

            for relation in relations:
                quote = db.scalar(
                    select(DailyQuote)
                    .where(
                        DailyQuote.stock_id == relation.stock_id,
                        DailyQuote.trade_date >= week_start,
                        DailyQuote.trade_date <= week_end,
                    )
                    .order_by(desc(DailyQuote.trade_date))
                )
                if quote is None:
                    continue
                pct_changes.append(float(quote.pct_change))
                turnovers.append(float(quote.turnover_amount))
                if quote.pct_change > 0:
                    advancing += 1

            stock_count = len(pct_changes)
            if stock_count == 0:
                continue

            metrics_list.append(
                ThemeWeekMetrics(
                    theme=theme,
                    week_start=week_start,
                    week_end=week_end,
                    average_return=sum(pct_changes) / stock_count,
                    median_return=median(pct_changes),
                    advancing_ratio=advancing / stock_count,
                    total_turnover=sum(turnovers),
                    stock_count=stock_count,
                )
            )
        return metrics_list

    def _get_current_week(self) -> tuple[date, date]:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        return week_start, week_end

    def _get_consecutive_strong_weeks(self, db: Session, theme_id: int, current_week_end: date) -> int:
        history = db.scalars(
            select(ThemeScore)
            .where(ThemeScore.theme_id == theme_id, ThemeScore.week_end < current_week_end)
            .order_by(desc(ThemeScore.week_end))
        ).all()

        streak = 0
        for item in history:
            if item.overall_score >= settings.strong_score_threshold:
                streak += 1
                continue
            break
        return streak
