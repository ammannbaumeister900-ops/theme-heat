from datetime import date

from pydantic import BaseModel, ConfigDict


class ThemeBase(BaseModel):
    id: int
    name: str
    code: str | None
    theme_type: str
    source: str

    model_config = ConfigDict(from_attributes=True)


class ThemeStockItem(BaseModel):
    id: int
    symbol: str
    name: str
    latest_close_price: float | None = None
    latest_pct_change: float | None = None
    latest_turnover_amount: float | None = None


class ThemeScorePoint(BaseModel):
    week_start: date
    week_end: date
    overall_score: float
    average_return: float
    median_return: float
    advancing_ratio: float
    turnover_ratio: float
    strong_weeks: int
    status: str

    model_config = ConfigDict(from_attributes=True)


class ThemeRankingItem(ThemeBase):
    latest_score: float | None = None
    latest_status: str | None = None
    week_start: date | None = None
    week_end: date | None = None
    stock_count: int = 0


class ThemeDetail(ThemeBase):
    latest_score: float | None = None
    latest_status: str | None = None
    stock_count: int
    score_history: list[ThemeScorePoint]
    stocks: list[ThemeStockItem]

