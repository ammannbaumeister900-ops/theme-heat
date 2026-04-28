import {
  ComputeJobStatus,
  ComputeJobTriggerResponse,
  DashboardOverview,
  MainlineRadarResponse,
  StockStructureResponse,
  ThemeDetail,
  ThemeRankingItem
} from "@/lib/types";

const INTERNAL_API_BASE_URL =
  process.env.INTERNAL_API_BASE_URL || "http://backend:8000/api";
const PUBLIC_API_BASE_PATH = process.env.NEXT_PUBLIC_API_BASE_PATH || "/api";

function getApiBaseUrl(): string {
  return typeof window === "undefined" ? INTERNAL_API_BASE_URL : PUBLIC_API_BASE_PATH;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, { cache: "no-store", ...init });
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }
  return response.json();
}

export async function getRankings(): Promise<ThemeRankingItem[]> {
  return request<ThemeRankingItem[]>("/rankings");
}

export async function getThemeDetail(id: string): Promise<ThemeDetail> {
  return request<ThemeDetail>(`/themes/${id}`);
}

export async function getDashboardOverview(): Promise<DashboardOverview> {
  return request<DashboardOverview>("/dashboard/overview");
}

export async function getComputeJobs(limit = 20): Promise<ComputeJobStatus[]> {
  return request<ComputeJobStatus[]>(`/compute/jobs?limit=${limit}`);
}

export async function triggerDailyCompute(): Promise<ComputeJobTriggerResponse> {
  return request<ComputeJobTriggerResponse>("/compute/daily", { method: "POST" });
}

export async function triggerFullCompute(): Promise<ComputeJobTriggerResponse> {
  return request<ComputeJobTriggerResponse>("/compute", { method: "POST" });
}

export async function getMainlineRadar(): Promise<MainlineRadarResponse> {
  return request<MainlineRadarResponse>("/mainline-radar");
}

export async function getStockStructure(themeId?: string | number): Promise<StockStructureResponse> {
  const query = themeId ? `?theme_id=${themeId}` : "";
  return request<StockStructureResponse>(`/stock-structure${query}`);
}
