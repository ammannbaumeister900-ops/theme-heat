from __future__ import annotations

from datetime import date, datetime
from functools import reduce
from operator import mul

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models import DailyQuote, Stock, Theme, ThemeScore, ThemeStock
from app.schemas.stock_structure import (
    StockStructureResponse,
    StockStructureTheme,
    StockStructureThemeOption,
    ThemeStockStructureItem,
)


def _clamp(value: float, low: float = 0, high: float = 100) -> float:
    return max(low, min(high, value))


def _compound_return(quotes: list[DailyQuote], days: int) -> float:
    selected = quotes[-days:]
    if not selected:
        return 0.0
    multiplier = reduce(mul, ((1 + float(quote.pct_change) / 100) for quote in selected), 1.0)
    return (multiplier - 1) * 100


def _max_drawdown(quotes: list[DailyQuote], days: int) -> float:
    selected = quotes[-days:]
    if len(selected) < 2:
        return 0.0
    peak = float(selected[0].close_price)
    max_drawdown = 0.0
    for quote in selected:
        close = float(quote.close_price)
        peak = max(peak, close)
        if peak:
            max_drawdown = min(max_drawdown, (close - peak) / peak * 100)
    return max_drawdown


def _volume_ratio(quotes: list[DailyQuote]) -> float:
    if not quotes:
        return 0.0
    latest = float(quotes[-1].turnover_amount or 0)
    baseline = quotes[-6:-1] or quotes[:-1]
    if not baseline:
        return 1.0
    average = sum(float(quote.turnover_amount or 0) for quote in baseline) / len(baseline)
    return latest / average if average > 0 else 1.0


def _new_high_20d(quotes: list[DailyQuote]) -> bool:
    selected = quotes[-20:]
    if not selected:
        return False
    latest_close = float(selected[-1].close_price)
    return latest_close >= max(float(quote.close_price) for quote in selected)


def _limit_up_count(quotes: list[DailyQuote], days: int = 10) -> int:
    return sum(1 for quote in quotes[-days:] if float(quote.pct_change) >= 9.8)


def _role(
    *,
    turnover_rank: int,
    return_rank: int,
    stock_count: int,
    market_cap_rank: int,
    return5d: float,
    return10d: float,
    return20d: float,
    max_drawdown5d: float,
    volume_ratio: float,
    new_high20d: bool,
    theme_relevance: float,
) -> str:
    top_turnover_cutoff = max(3, round(stock_count * 0.2))
    top_return_cutoff = max(3, round(stock_count * 0.25))
    middle_turnover_cutoff = max(5, round(stock_count * 0.45))

    if (
        theme_relevance >= 78
        and turnover_rank <= top_turnover_cutoff
        and return_rank <= top_return_cutoff
        and new_high20d
    ):
        return "龙头"
    if (
        market_cap_rank <= top_turnover_cutoff
        and turnover_rank <= middle_turnover_cutoff
        and max_drawdown5d > -6
    ):
        return "中军"
    if market_cap_rank > stock_count * 0.45 and return10d >= 8 and volume_ratio >= 1.6 and max_drawdown5d <= -6:
        return "弹性标的"
    if return20d <= 5 and return5d > 0 and turnover_rank > top_turnover_cutoff:
        return "补涨"
    if theme_relevance < 55 or (turnover_rank > stock_count * 0.65 and return10d <= 3):
        return "风险后排"
    return "补涨"


def _reasons(role: str) -> list[str]:
    if role == "龙头":
        return ["主题关联度高，成交额排名靠前。", "涨幅排名靠前，率先创 20 日新高。", "资金共识核心锚点。"]
    if role == "中军":
        return ["成交额和流动性排名靠前。", "走势相对稳健，短期回撤较小。", "主题持续性的核心观察标的。"]
    if role == "弹性标的":
        return ["短期涨幅高，放量明显。", "波动较大，弹性高但风险高。"]
    if role == "补涨":
        return ["前期涨幅相对落后，近期开始跟涨。", "成交额排名中后，需要观察持续性。"]
    return ["主题关联度较弱或成交额不足。", "跟风属性强，回撤风险高。"]


def _risks(role: str, max_drawdown5d: float, volume_ratio: float) -> list[str]:
    risks: list[str] = []
    if role in {"弹性标的", "风险后排"}:
        risks.append("波动放大后容易出现快速回撤。")
    if max_drawdown5d <= -8:
        risks.append("近 5 日最大回撤偏大，需要观察承接。")
    if volume_ratio >= 2.2:
        risks.append("放量较明显，若价格无法继续走强，可能形成高位分歧。")
    if not risks:
        risks.append("若主题热度回落，个股结构定位可能随之下修。")
    return risks


def _set_role(stock: ThemeStockStructureItem, role: str) -> None:
    stock.role = role  # type: ignore[assignment]
    stock.reasons = _reasons(role)
    stock.risks = _risks(role, stock.maxDrawdown5d, stock.volumeRatio)


def _ensure_role_coverage(stocks: list[ThemeStockStructureItem]) -> None:
    if len(stocks) < 5:
        return

    def counts() -> dict[str, int]:
        return {role: sum(1 for stock in stocks if stock.role == role) for role in ["龙头", "中军", "弹性标的", "补涨", "风险后排"]}

    def can_move(stock: ThemeStockStructureItem) -> bool:
        return counts().get(stock.role, 0) > 1

    role_candidates = {
        "龙头": lambda: sorted(stocks, key=lambda item: item.stockScore, reverse=True),
        "中军": lambda: sorted(stocks, key=lambda item: (item.turnoverRankInTheme, abs(item.maxDrawdown5d))),
        "弹性标的": lambda: sorted(stocks, key=lambda item: (item.return10d, item.volumeRatio), reverse=True),
        "补涨": lambda: sorted(stocks, key=lambda item: (abs(item.return20d), -item.return5d)),
        "风险后排": lambda: sorted(stocks, key=lambda item: (item.stockScore, item.themeRelevance)),
    }

    for role, candidates_factory in role_candidates.items():
        if counts().get(role, 0) > 0:
            continue
        for candidate in candidates_factory():
            if can_move(candidate):
                _set_role(candidate, role)
                break


def _theme_options(db: Session) -> list[StockStructureThemeOption]:
    latest_week = db.scalar(select(func.max(ThemeScore.week_end)))
    rows = db.execute(
        select(Theme, ThemeScore)
        .join(ThemeScore, ThemeScore.theme_id == Theme.id, isouter=True)
        .where(ThemeScore.week_end == latest_week if latest_week else True)
        .order_by(desc(ThemeScore.overall_score), Theme.name)
        .limit(80)
    ).all()
    options: list[StockStructureThemeOption] = []
    for theme, score in rows:
        stock_count = db.scalar(select(func.count(ThemeStock.id)).where(ThemeStock.theme_id == theme.id)) or 0
        if stock_count == 0:
            continue
        options.append(
            StockStructureThemeOption(
                id=theme.id,
                name=theme.name,
                latestScore=round(float(score.overall_score), 2) if score else None,
                stockCount=stock_count,
            )
        )
    return options


def _default_theme_id(db: Session) -> int | None:
    option = next(iter(_theme_options(db)), None)
    return option.id if option else None


def get_stock_structure(db: Session, theme_id: int | None = None) -> StockStructureResponse | None:
    selected_theme_id = theme_id or _default_theme_id(db)
    if selected_theme_id is None:
        return None

    theme = db.get(Theme, selected_theme_id)
    if theme is None:
        return None

    latest_trade_date = db.scalar(select(func.max(DailyQuote.trade_date)))
    if latest_trade_date is None:
        return None

    latest_score = db.scalar(
        select(ThemeScore)
        .where(ThemeScore.theme_id == theme.id)
        .order_by(desc(ThemeScore.week_end))
    )

    relations = db.execute(
        select(ThemeStock, Stock)
        .join(Stock, Stock.id == ThemeStock.stock_id)
        .where(ThemeStock.theme_id == theme.id)
        .order_by(Stock.symbol)
    ).all()

    stock_quote_rows: list[tuple[Stock, list[DailyQuote]]] = []
    for _, stock in relations:
        quotes = list(
            db.scalars(
                select(DailyQuote)
                .where(DailyQuote.stock_id == stock.id, DailyQuote.trade_date <= latest_trade_date)
                .order_by(desc(DailyQuote.trade_date))
                .limit(24)
            ).all()
        )
        quotes = list(reversed(quotes))
        if quotes:
            stock_quote_rows.append((stock, quotes))

    if not stock_quote_rows:
        return None

    turnover_ranked = sorted(
        stock_quote_rows,
        key=lambda row: float(row[1][-1].turnover_amount or 0),
        reverse=True,
    )
    turnover_ranks = {stock.id: index + 1 for index, (stock, _) in enumerate(turnover_ranked)}

    return_ranked = sorted(
        stock_quote_rows,
        key=lambda row: _compound_return(row[1], 10),
        reverse=True,
    )
    return_ranks = {stock.id: index + 1 for index, (stock, _) in enumerate(return_ranked)}

    # Market cap is not stored locally. Use turnover liquidity as the real-data proxy for rank.
    market_cap_ranks = turnover_ranks
    stock_count = len(stock_quote_rows)

    stocks: list[ThemeStockStructureItem] = []
    for stock, quotes in stock_quote_rows:
        latest_quote = quotes[-1]
        turnover_amount = float(latest_quote.turnover_amount or 0)
        turnover_rank = turnover_ranks[stock.id]
        return_rank = return_ranks[stock.id]
        return5d = _compound_return(quotes, 5)
        return10d = _compound_return(quotes, 10)
        return20d = _compound_return(quotes, 20)
        max_drawdown5d = _max_drawdown(quotes, 5)
        volume_ratio = _volume_ratio(quotes)
        new_high20d = _new_high_20d(quotes)
        limit_up_count10d = _limit_up_count(quotes)

        rank_score = (stock_count - turnover_rank + 1) / stock_count * 100
        return_score = (stock_count - return_rank + 1) / stock_count * 100
        theme_relevance = _clamp(
            40
            + rank_score * 0.24
            + return_score * 0.22
            + min(max(return20d, -10), 30) * 0.55
            + (10 if new_high20d else 0)
            + min(volume_ratio, 3) * 4
        )
        role = _role(
            turnover_rank=turnover_rank,
            return_rank=return_rank,
            stock_count=stock_count,
            market_cap_rank=market_cap_ranks[stock.id],
            return5d=return5d,
            return10d=return10d,
            return20d=return20d,
            max_drawdown5d=max_drawdown5d,
            volume_ratio=volume_ratio,
            new_high20d=new_high20d,
            theme_relevance=theme_relevance,
        )
        stock_score = _clamp(
            theme_relevance * 0.35
            + rank_score * 0.25
            + return_score * 0.20
            + (10 if new_high20d else 0)
            + min(limit_up_count10d * 4, 12)
            - max(abs(max_drawdown5d) - 6, 0) * 0.7
        )
        stocks.append(
            ThemeStockStructureItem(
                stockCode=stock.symbol,
                stockName=stock.name,
                themeId=str(theme.id),
                marketCap=0,
                turnoverAmount=round(turnover_amount, 2),
                turnoverRankInTheme=turnover_rank,
                return5d=round(return5d, 2),
                return10d=round(return10d, 2),
                return20d=round(return20d, 2),
                maxDrawdown5d=round(max_drawdown5d, 2),
                volumeRatio=round(volume_ratio, 2),
                newHigh20d=new_high20d,
                limitUpCount10d=limit_up_count10d,
                themeRelevance=round(theme_relevance, 1),
                stockScore=round(stock_score, 1),
                role=role,
                reasons=_reasons(role),
                risks=_risks(role, max_drawdown5d, volume_ratio),
            )
        )

    _ensure_role_coverage(stocks)
    role_order = {"龙头": 0, "中军": 1, "弹性标的": 2, "补涨": 3, "风险后排": 4}
    stocks.sort(key=lambda item: (role_order[item.role], -item.stockScore, item.turnoverRankInTheme))

    return StockStructureResponse(
        generatedAt=datetime.now(),
        latestTradeDate=latest_trade_date,
        isTodayData=latest_trade_date == date.today(),
        theme=StockStructureTheme(
            id=theme.id,
            name=theme.name,
            code=theme.code,
            themeType=theme.theme_type,
            latestScore=round(float(latest_score.overall_score), 2) if latest_score else None,
            stockCount=stock_count,
        ),
        themes=_theme_options(db),
        stocks=stocks,
    )
