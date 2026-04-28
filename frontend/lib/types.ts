export type ThemeRankingItem = {
  id: number;
  name: string;
  code: string | null;
  theme_type: string;
  source: string;
  latest_score: number | null;
  latest_status: string | null;
  week_start: string | null;
  week_end: string | null;
  stock_count: number;
};

export type ThemeScorePoint = {
  week_start: string;
  week_end: string;
  overall_score: number;
  average_return: number;
  median_return: number;
  advancing_ratio: number;
  turnover_ratio: number;
  strong_weeks: number;
  status: string;
};

export type ThemeStockItem = {
  id: number;
  symbol: string;
  name: string;
  latest_close_price: number | null;
  latest_pct_change: number | null;
  latest_turnover_amount: number | null;
};

export type ThemeDetail = {
  id: number;
  name: string;
  code: string | null;
  theme_type: string;
  source: string;
  latest_score: number | null;
  latest_status: string | null;
  stock_count: number;
  score_history: ThemeScorePoint[];
  stocks: ThemeStockItem[];
};

export type ThemeStockRole =
  | "龙头"
  | "中军"
  | "弹性标的"
  | "补涨"
  | "风险后排";

export type ThemeStockStructureItem = {
  stockCode: string;
  stockName: string;
  themeId: string;
  marketCap: number;
  turnoverAmount: number;
  turnoverRankInTheme: number;
  return5d: number;
  return10d: number;
  return20d: number;
  maxDrawdown5d: number;
  volumeRatio: number;
  newHigh20d: boolean;
  limitUpCount10d: number;
  themeRelevance: number;
  stockScore: number;
  role: ThemeStockRole;
  reasons: string[];
  risks: string[];
};

export type StockStructureThemeOption = {
  id: number;
  name: string;
  latestScore: number | null;
  stockCount: number;
};

export type StockStructureResponse = {
  generatedAt: string;
  latestTradeDate: string | null;
  isTodayData: boolean;
  theme: {
    id: number;
    name: string;
    code: string | null;
    themeType: string;
    latestScore: number | null;
    stockCount: number;
  };
  themes: StockStructureThemeOption[];
  stocks: ThemeStockStructureItem[];
};

export type DashboardMetric = {
  label: string;
  value: number | string;
  unit: string | null;
  delta: number | null;
  tone: "up" | "down" | "hot" | "neutral" | string;
};

export type DashboardHeatmapItem = {
  id: number;
  name: string;
  value: number;
  change: number;
  stock_count: number;
};

export type DashboardRankingItem = {
  id: number;
  rank: number;
  name: string;
  heat: number;
  change: number;
  trend: number[];
};

export type DashboardDistributionItem = {
  label: string;
  value: number;
  tone: "up" | "down" | string;
};

export type DashboardFlowItem = {
  label: string;
  value: number;
  tone: "up" | "down" | "neutral" | string;
};

export type DashboardHotspotItem = {
  rank: number;
  title: string;
  heat: number;
  duration: string;
  tone: "up" | "down" | string;
};

export type DashboardTickerItem = {
  time: string;
  text: string;
};

export type DashboardNewsItem = {
  title: string;
  summary: string | null;
  published_at: string | null;
  source: string;
  url: string | null;
};

export type DashboardJobSummary = {
  id: number | null;
  status: string;
  stage: string;
  message: string | null;
  error_message: string | null;
  processed_count: number;
  total_count: number;
  score_count: number;
  started_at: string | null;
  heartbeat_at: string | null;
  finished_at: string | null;
};

export type DashboardDataQuality = {
  status: "healthy" | "partial" | "warning" | string;
  quote_coverage_ratio: number;
  stock_count: number;
  quote_count: number;
  warnings: string[];
};

export type DashboardOverview = {
  generated_at: string;
  latest_trade_date: string | null;
  job: DashboardJobSummary;
  data_quality: DashboardDataQuality;
  metrics: DashboardMetric[];
  heatmap: DashboardHeatmapItem[];
  ranking: DashboardRankingItem[];
  distribution: DashboardDistributionItem[];
  flows: DashboardFlowItem[];
  hotspots: DashboardHotspotItem[];
  news: DashboardNewsItem[];
  ticker: DashboardTickerItem[];
};

export type ComputeJobStatus = {
  id: number;
  status: string;
  stage: string;
  current_theme_type: string | null;
  current_theme_index: number;
  total_theme_count: number;
  processed_theme_count: number;
  synced_theme_count: number;
  score_count: number;
  last_theme_name: string | null;
  message: string | null;
  error_message: string | null;
  created_at: string;
  started_at: string | null;
  heartbeat_at: string | null;
  finished_at: string | null;
};

export type ComputeJobTriggerResponse = {
  success: boolean;
  message: string;
  job: ComputeJobStatus;
};

export type MainlineThemeScore = {
  total: number;
  fund: number;
  returnStrength: number;
  breadth: number;
  persistence: number;
  catalyst: number;
  crowdingPenalty: number;
};

export type ThemeDiagnosis = {
  themeId: string;
  themeName: string;
  score: MainlineThemeScore;
  status: "强主线" | "潜在主线" | "轮动热点" | "弱热点" | "噪音";
  stage: "萌芽期" | "确认期" | "主升期" | "高潮期" | "退潮期";
  healthLevel: "高" | "中" | "低";
  riskLevel: "低" | "中" | "高";
  reasons: string[];
  watchPoints: string[];
};

export type MainlineRadarResponse = {
  generatedAt: string;
  marketSummary: {
    strongestTheme: ThemeDiagnosis | null;
    potentialCount: number;
    highCrowdingRiskCount: number;
    marketStatus: "主线清晰" | "多线轮动" | "弱势混沌" | "退潮观察";
  };
  themes: ThemeDiagnosis[];
};

