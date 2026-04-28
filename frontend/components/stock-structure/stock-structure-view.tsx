"use client";

import { useState } from "react";

import { getStockStructure } from "@/lib/api";
import {
  StockStructureResponse,
  ThemeStockRole,
  ThemeStockStructureItem
} from "@/lib/types";

const roleOrder: ThemeStockRole[] = ["龙头", "中军", "弹性标的", "补涨", "风险后排"];

function roleClass(role: ThemeStockRole) {
  if (role === "龙头") return "border-red-500/30 bg-red-500/10 text-red-200";
  if (role === "中军") return "border-blue-500/30 bg-blue-500/10 text-blue-200";
  if (role === "弹性标的") return "border-cyan-500/30 bg-cyan-500/10 text-cyan-200";
  if (role === "补涨") return "border-emerald-500/30 bg-emerald-500/10 text-emerald-200";
  return "border-slate-600 bg-slate-800 text-slate-300";
}

function formatYi(value: number) {
  return `${(value / 100000000).toFixed(2)} 亿`;
}

function riskText(stock: ThemeStockStructureItem) {
  if (stock.role === "风险后排") return "高";
  if (stock.role === "弹性标的" || stock.maxDrawdown5d <= -10) return "中高";
  if (stock.role === "补涨") return "中";
  return "低";
}

function StockCard({ stock }: { stock: ThemeStockStructureItem }) {
  return (
    <article className="rounded-lg border border-slate-800 bg-slate-950/30 p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h4 className="truncate text-base font-semibold text-slate-100">{stock.stockName}</h4>
          <p className="mt-1 font-mono text-xs text-slate-600">{stock.stockCode}</p>
        </div>
        <span className={`shrink-0 rounded-full border px-2.5 py-1 text-xs font-medium ${roleClass(stock.role)}`}>
          {stock.role}
        </span>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
        <div>
          <p className="text-xs text-slate-500">主题内评分</p>
          <p className="mt-1 font-mono text-lg font-semibold text-white">{stock.stockScore.toFixed(1)}</p>
        </div>
        <div>
          <p className="text-xs text-slate-500">主题关联度</p>
          <p className="mt-1 font-mono text-lg font-semibold text-white">{stock.themeRelevance.toFixed(0)}</p>
        </div>
        <div>
          <p className="text-xs text-slate-500">成交额排名</p>
          <p className="mt-1 text-slate-300">#{stock.turnoverRankInTheme}</p>
        </div>
        <div>
          <p className="text-xs text-slate-500">10 日涨幅</p>
          <p className={stock.return10d >= 0 ? "mt-1 text-red-400" : "mt-1 text-emerald-400"}>
            {stock.return10d >= 0 ? "+" : ""}
            {stock.return10d.toFixed(2)}%
          </p>
        </div>
        <div>
          <p className="text-xs text-slate-500">成交额</p>
          <p className="mt-1 text-slate-300">{formatYi(stock.turnoverAmount)}</p>
        </div>
        <div>
          <p className="text-xs text-slate-500">位置风险</p>
          <p className="mt-1 text-slate-300">{riskText(stock)}</p>
        </div>
      </div>

      <div className="mt-4 rounded-md border border-slate-800 bg-slate-900/60 p-3">
        <p className="text-xs font-medium text-slate-500">系统原因</p>
        <ul className="mt-2 space-y-1 text-sm leading-5 text-slate-400">
          {stock.reasons.map((reason) => (
            <li key={reason}>- {reason}</li>
          ))}
        </ul>
      </div>
      <div className="mt-3 rounded-md border border-amber-500/20 bg-amber-500/10 p-3">
        <p className="text-xs font-medium text-amber-300">风险提示</p>
        <ul className="mt-2 space-y-1 text-sm leading-5 text-amber-100">
          {stock.risks.map((risk) => (
            <li key={risk}>- {risk}</li>
          ))}
        </ul>
      </div>
    </article>
  );
}

export function StockStructureView({ initialData }: { initialData: StockStructureResponse }) {
  const [data, setData] = useState(initialData);
  const [loading, setLoading] = useState(false);

  async function handleThemeChange(themeId: string) {
    setLoading(true);
    try {
      setData(await getStockStructure(themeId));
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="text-slate-100">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Constituent Structure</p>
          <h1 className="mt-1 text-2xl font-semibold text-white">成分股结构</h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
            基于主题成分关系和最新日线行情计算结构定位、归因和风险。该页面是研究分析工具，不构成交易建议。
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <select
            className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-200"
            value={data.theme.id}
            onChange={(event) => handleThemeChange(event.target.value)}
            disabled={loading}
          >
            {data.themes.map((theme) => (
              <option key={theme.id} value={theme.id}>
                {theme.name}
              </option>
            ))}
          </select>
          <span className={`rounded-lg border px-3 py-2 text-sm ${data.isTodayData ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-200" : "border-amber-500/30 bg-amber-500/10 text-amber-200"}`}>
            最新交易日 {data.latestTradeDate || "--"}
          </span>
        </div>
      </div>

      <div className="mb-4 grid gap-3 sm:grid-cols-3">
        <div className="terminal-panel p-4">
          <p className="text-sm text-slate-400">当前主题</p>
          <p className="mt-2 text-xl font-semibold text-white">{data.theme.name}</p>
        </div>
        <div className="terminal-panel p-4">
          <p className="text-sm text-slate-400">主题热度</p>
          <p className="mt-2 font-mono text-xl font-semibold text-white">{data.theme.latestScore?.toFixed(1) || "--"}</p>
        </div>
        <div className="terminal-panel p-4">
          <p className="text-sm text-slate-400">成分股覆盖</p>
          <p className="mt-2 font-mono text-xl font-semibold text-white">{data.stocks.length}</p>
        </div>
      </div>

      <div className="grid gap-4">
        {roleOrder.map((role) => {
          const stocks = data.stocks.filter((stock) => stock.role === role);
          return (
            <section key={role} className="terminal-panel p-4">
              <div className="mb-3 flex items-center gap-2">
                <span className={`rounded-full border px-2.5 py-1 text-xs font-medium ${roleClass(role)}`}>{role}组</span>
                <span className="text-sm text-slate-500">{stocks.length} 只</span>
              </div>
              <div className="grid gap-3 xl:grid-cols-2 2xl:grid-cols-3">
                {stocks.map((stock) => (
                  <StockCard key={stock.stockCode} stock={stock} />
                ))}
              </div>
            </section>
          );
        })}
      </div>
    </section>
  );
}
