from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel


StockRole = Literal["龙头", "中军", "弹性标的", "补涨", "风险后排"]


class StockStructureThemeOption(BaseModel):
    id: int
    name: str
    latestScore: float | None = None
    stockCount: int


class ThemeStockStructureItem(BaseModel):
    stockCode: str
    stockName: str
    themeId: str
    marketCap: float
    turnoverAmount: float
    turnoverRankInTheme: int
    return5d: float
    return10d: float
    return20d: float
    maxDrawdown5d: float
    volumeRatio: float
    newHigh20d: bool
    limitUpCount10d: int
    themeRelevance: float
    stockScore: float
    role: StockRole
    reasons: list[str]
    risks: list[str]


class StockStructureTheme(BaseModel):
    id: int
    name: str
    code: str | None = None
    themeType: str
    latestScore: float | None = None
    stockCount: int


class StockStructureResponse(BaseModel):
    generatedAt: datetime
    latestTradeDate: date | None
    isTodayData: bool
    theme: StockStructureTheme
    themes: list[StockStructureThemeOption]
    stocks: list[ThemeStockStructureItem]
