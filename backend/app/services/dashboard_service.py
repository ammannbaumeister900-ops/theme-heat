from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models import ComputeJob, DailyQuote, Stock, Theme, ThemeScore, ThemeStock
from app.schemas.dashboard import (
    DashboardDataQuality,
    DashboardDistributionItem,
    DashboardFlowItem,
    DashboardHeatmapItem,
    DashboardHotspotItem,
    DashboardJobSummary,
    DashboardMetric,
    DashboardNewsItem,
    DashboardOverview,
    DashboardRankingItem,
    DashboardTickerItem,
)
from app.services.akshare_service import AKShareService


logger = logging.getLogger(__name__)
ak_service = AKShareService()


def _round(value: float | None, digits: int = 2) -> float:
    return round(float(value or 0), digits)


def _format_duration(index: int) -> str:
    hours = 1 + (index % 4)
    minutes = 15 + (index * 17) % 45
    return f"{hours}h {minutes}m"


def _load_news() -> list[DashboardNewsItem]:
    try:
        return [DashboardNewsItem(**item) for item in ak_service.fetch_market_news(limit=8)]
    except Exception as exc:
        logger.warning("failed to load market news: %s", exc)
        return []


def get_dashboard_overview(db: Session) -> DashboardOverview:
    latest_week = db.scalar(select(func.max(ThemeScore.week_end)))
    latest_trade_date = db.scalar(select(func.max(DailyQuote.trade_date)))
    latest_job = db.scalar(select(ComputeJob).order_by(desc(ComputeJob.id)))

    score_rows = []
    if latest_week is not None:
        score_rows = db.execute(
            select(Theme, ThemeScore)
            .join(ThemeScore, ThemeScore.theme_id == Theme.id)
            .where(ThemeScore.week_end == latest_week)
            .order_by(desc(ThemeScore.overall_score), Theme.name)
        ).all()

    latest_quotes = []
    if latest_trade_date is not None:
        latest_quotes = db.scalars(
            select(DailyQuote).where(DailyQuote.trade_date == latest_trade_date)
        ).all()

    total_stock_count = db.scalar(select(func.count(Stock.id))) or 0
    latest_quote_stock_count = len({quote.stock_id for quote in latest_quotes})
    quote_coverage_ratio = latest_quote_stock_count / max(int(total_stock_count), 1)

    rising_count = sum(1 for quote in latest_quotes if quote.pct_change > 0)
    falling_count = sum(1 for quote in latest_quotes if quote.pct_change < 0)
    limit_up_count = sum(1 for quote in latest_quotes if quote.pct_change >= 9.8)
    limit_down_count = sum(1 for quote in latest_quotes if quote.pct_change <= -9.8)
    total_turnover = sum(float(quote.turnover_amount or 0) for quote in latest_quotes)
    positive_turnover = sum(float(quote.turnover_amount or 0) for quote in latest_quotes if quote.pct_change > 0)
    negative_turnover = sum(float(quote.turnover_amount or 0) for quote in latest_quotes if quote.pct_change < 0)

    score_values = [float(score.overall_score) for _, score in score_rows]
    average_heat = sum(score_values) / len(score_values) if score_values else 0
    breadth = rising_count / max(rising_count + falling_count, 1)
    sentiment_score = max(0, min(100, average_heat * 0.55 + breadth * 45))

    stock_counts = dict(
        db.execute(
            select(ThemeStock.theme_id, func.count(ThemeStock.id)).group_by(ThemeStock.theme_id)
        ).all()
    )

    history_by_theme: dict[int, list[float]] = {}
    theme_ids = [theme.id for theme, _ in score_rows[:10]]
    if theme_ids:
        history_rows = db.execute(
            select(ThemeScore.theme_id, ThemeScore.overall_score)
            .where(ThemeScore.theme_id.in_(theme_ids))
            .order_by(ThemeScore.theme_id, desc(ThemeScore.week_end))
        ).all()
        for theme_id, score in history_rows:
            history_by_theme.setdefault(theme_id, [])
            if len(history_by_theme[theme_id]) < 6:
                history_by_theme[theme_id].append(_round(score, 1))

    heatmap = [
        DashboardHeatmapItem(
            id=theme.id,
            name=theme.name,
            value=_round(score.overall_score, 1),
            change=_round(score.average_return, 2),
            stock_count=int(stock_counts.get(theme.id, 0)),
        )
        for theme, score in score_rows[:24]
    ]

    ranking = [
        DashboardRankingItem(
            id=theme.id,
            rank=index + 1,
            name=theme.name,
            heat=_round(score.overall_score, 1),
            change=_round(score.average_return, 2),
            trend=list(reversed(history_by_theme.get(theme.id, [_round(score.overall_score, 1)]))),
        )
        for index, (theme, score) in enumerate(score_rows[:10])
    ]

    distribution = [
        DashboardDistributionItem(label="涨停", value=limit_up_count, tone="up"),
        DashboardDistributionItem(label=">7%", value=sum(1 for quote in latest_quotes if quote.pct_change >= 7), tone="up"),
        DashboardDistributionItem(label="3-7%", value=sum(1 for quote in latest_quotes if 3 <= quote.pct_change < 7), tone="up"),
        DashboardDistributionItem(label="0-3%", value=sum(1 for quote in latest_quotes if 0 < quote.pct_change < 3), tone="up"),
        DashboardDistributionItem(label="0~-3%", value=sum(1 for quote in latest_quotes if -3 < quote.pct_change <= 0), tone="down"),
        DashboardDistributionItem(label="-3~-7%", value=sum(1 for quote in latest_quotes if -7 < quote.pct_change <= -3), tone="down"),
        DashboardDistributionItem(label="<-7%", value=sum(1 for quote in latest_quotes if -9.8 < quote.pct_change <= -7), tone="down"),
        DashboardDistributionItem(label="跌停", value=limit_down_count, tone="down"),
    ]

    estimated_net_flow = (positive_turnover - negative_turnover) * 0.08
    flows = [
        DashboardFlowItem(label="强势主题", value=_round(positive_turnover / 100000000, 2), tone="up"),
        DashboardFlowItem(label="弱势主题", value=_round(-negative_turnover / 100000000, 2), tone="down"),
        DashboardFlowItem(label="估算净流入", value=_round(estimated_net_flow / 100000000, 2), tone="up" if estimated_net_flow >= 0 else "down"),
        DashboardFlowItem(label="总成交额", value=_round(total_turnover / 100000000, 2), tone="neutral"),
    ]

    hotspots = [
        DashboardHotspotItem(
            rank=index + 1,
            title=f"{theme.name}热度升温",
            heat=_round(score.overall_score, 1),
            duration=_format_duration(index),
            tone="up" if score.average_return >= 0 else "down",
        )
        for index, (theme, score) in enumerate(score_rows[:6])
    ]

    news = _load_news()

    ticker = [
        DashboardTickerItem(time=datetime.now().strftime("%H:%M"), text=f"主题热度已更新，当前覆盖 {len(score_rows)} 个主题。"),
        DashboardTickerItem(time=datetime.now().strftime("%H:%M"), text=f"市场情绪指数 {sentiment_score:.0f}，上涨 {rising_count} 家，下跌 {falling_count} 家。"),
    ]
    if ranking:
        ticker.append(
            DashboardTickerItem(
                time=datetime.now().strftime("%H:%M"),
                text=f"{ranking[0].name} 位居主题热度第一，热度值 {ranking[0].heat:.1f}。",
            )
        )
    if news:
        ticker.append(
            DashboardTickerItem(
                time=news[0].published_at[:5] if news[0].published_at else datetime.now().strftime("%H:%M"),
                text=f"最新资讯：{news[0].title}",
            )
        )

    warnings: list[str] = []
    if latest_trade_date is None:
        warnings.append("暂无行情数据，请先触发一次计算任务。")
    if not score_rows:
        warnings.append("暂无主题评分数据，排行榜和热力图为空。")
    if latest_job and latest_job.status == "failed":
        warnings.append("最近一次计算失败，请查看任务错误信息。")
    if latest_job and latest_job.status in {"pending", "running"}:
        warnings.append("数据任务正在运行，当前页面可能显示上一轮结果。")
    if total_stock_count and quote_coverage_ratio < 0.5:
        warnings.append("最新交易日行情覆盖率偏低，部分统计可能失真。")

    if warnings:
        data_quality_status = "warning"
    elif quote_coverage_ratio >= 0.8 and score_rows:
        data_quality_status = "healthy"
    else:
        data_quality_status = "partial"

    job_summary = DashboardJobSummary()
    if latest_job is not None:
        job_summary = DashboardJobSummary(
            id=latest_job.id,
            status=latest_job.status,
            stage=latest_job.stage,
            message=latest_job.message,
            error_message=latest_job.error_message,
            processed_count=latest_job.processed_theme_count,
            total_count=latest_job.total_theme_count,
            score_count=latest_job.score_count,
            started_at=latest_job.started_at,
            heartbeat_at=latest_job.heartbeat_at,
            finished_at=latest_job.finished_at,
        )

    metrics = [
        DashboardMetric(label="上涨家数", value=rising_count, delta=_round(breadth * 100, 2), tone="up"),
        DashboardMetric(label="下跌家数", value=falling_count, delta=_round((1 - breadth) * 100, 2), tone="down"),
        DashboardMetric(label="涨停家数", value=limit_up_count, delta=None, tone="up"),
        DashboardMetric(label="成交额", value=_round(total_turnover / 100000000, 2), unit="亿", delta=None, tone="neutral"),
        DashboardMetric(label="估算净流入", value=_round(estimated_net_flow / 100000000, 2), unit="亿", delta=None, tone="up" if estimated_net_flow >= 0 else "down"),
        DashboardMetric(label="市场情绪", value=_round(sentiment_score, 0), delta=_round(average_heat, 1), tone="hot" if sentiment_score >= 70 else "neutral"),
    ]

    return DashboardOverview(
        generated_at=datetime.now(),
        latest_trade_date=latest_trade_date,
        job=job_summary,
        data_quality=DashboardDataQuality(
            status=data_quality_status,
            quote_coverage_ratio=_round(quote_coverage_ratio, 4),
            stock_count=int(total_stock_count),
            quote_count=latest_quote_stock_count,
            warnings=warnings,
        ),
        metrics=metrics,
        heatmap=heatmap,
        ranking=ranking,
        distribution=distribution,
        flows=flows,
        hotspots=hotspots,
        news=news,
        ticker=ticker,
    )
