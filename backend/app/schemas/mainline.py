from datetime import datetime
from typing import Literal

from pydantic import BaseModel


MainlineStatus = Literal["强主线", "潜在主线", "轮动热点", "弱热点", "噪音"]
MainlineStage = Literal["萌芽期", "确认期", "主升期", "高潮期", "退潮期"]
Level = Literal["高", "中", "低"]
MarketStatus = Literal["主线清晰", "多线轮动", "弱势混沌", "退潮观察"]


class MainlineThemeScore(BaseModel):
    total: float
    fund: float
    returnStrength: float
    breadth: float
    persistence: float
    catalyst: float
    crowdingPenalty: float


class ThemeDiagnosis(BaseModel):
    themeId: str
    themeName: str
    score: MainlineThemeScore
    status: MainlineStatus
    stage: MainlineStage
    healthLevel: Level
    riskLevel: Level
    reasons: list[str]
    watchPoints: list[str]


class MainlineMarketSummary(BaseModel):
    strongestTheme: ThemeDiagnosis | None
    potentialCount: int
    highCrowdingRiskCount: int
    marketStatus: MarketStatus


class MainlineRadarResponse(BaseModel):
    generatedAt: datetime
    marketSummary: MainlineMarketSummary
    themes: list[ThemeDiagnosis]
