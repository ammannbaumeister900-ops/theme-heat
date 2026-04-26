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

