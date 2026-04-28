from datetime import date, datetime

from pydantic import BaseModel


class DashboardMetric(BaseModel):
    label: str
    value: float | int | str
    unit: str | None = None
    delta: float | None = None
    tone: str = "neutral"


class DashboardHeatmapItem(BaseModel):
    id: int
    name: str
    value: float
    change: float
    stock_count: int


class DashboardRankingItem(BaseModel):
    id: int
    rank: int
    name: str
    heat: float
    change: float
    trend: list[float]


class DashboardDistributionItem(BaseModel):
    label: str
    value: int
    tone: str


class DashboardFlowItem(BaseModel):
    label: str
    value: float
    tone: str


class DashboardHotspotItem(BaseModel):
    rank: int
    title: str
    heat: float
    duration: str
    tone: str


class DashboardTickerItem(BaseModel):
    time: str
    text: str


class DashboardNewsItem(BaseModel):
    title: str
    summary: str | None = None
    published_at: str | None = None
    source: str = "market"
    url: str | None = None


class DashboardJobSummary(BaseModel):
    id: int | None = None
    status: str = "unknown"
    stage: str = "unknown"
    message: str | None = None
    error_message: str | None = None
    processed_count: int = 0
    total_count: int = 0
    score_count: int = 0
    started_at: datetime | None = None
    heartbeat_at: datetime | None = None
    finished_at: datetime | None = None


class DashboardDataQuality(BaseModel):
    status: str
    quote_coverage_ratio: float
    stock_count: int
    quote_count: int
    warnings: list[str]


class DashboardOverview(BaseModel):
    generated_at: datetime
    latest_trade_date: date | None = None
    job: DashboardJobSummary
    data_quality: DashboardDataQuality
    metrics: list[DashboardMetric]
    heatmap: list[DashboardHeatmapItem]
    ranking: list[DashboardRankingItem]
    distribution: list[DashboardDistributionItem]
    flows: list[DashboardFlowItem]
    hotspots: list[DashboardHotspotItem]
    news: list[DashboardNewsItem]
    ticker: list[DashboardTickerItem]
