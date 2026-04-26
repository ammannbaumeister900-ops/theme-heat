import { ThemeDetail, ThemeRankingItem } from "@/lib/types";

const INTERNAL_API_BASE_URL =
  process.env.INTERNAL_API_BASE_URL || "http://backend:8000/api";
const PUBLIC_API_BASE_PATH = process.env.NEXT_PUBLIC_API_BASE_PATH || "/api";

function getApiBaseUrl(): string {
  return typeof window === "undefined" ? INTERNAL_API_BASE_URL : PUBLIC_API_BASE_PATH;
}

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, { cache: "no-store" });
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
