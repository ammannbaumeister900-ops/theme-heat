"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { EChartsClient } from "@/components/echarts-client";
import { StatusPill } from "@/components/status-pill";
import { StockStructureView } from "@/components/stock-structure/stock-structure-view";
import { getStockStructure } from "@/lib/api";
import { StockStructureResponse, ThemeDetail } from "@/lib/types";

function formatPct(value: number | null) {
  if (value === null) return "--";
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
}

function formatAmount(value: number | null) {
  if (value === null) return "--";
  if (value >= 100000000) return `${(value / 100000000).toFixed(2)} 亿`;
  if (value >= 10000) return `${(value / 10000).toFixed(2)} 万`;
  return value.toFixed(0);
}

function pctTone(value: number | null) {
  if ((value || 0) > 0) return "text-red-400";
  if ((value || 0) < 0) return "text-emerald-400";
  return "text-slate-300";
}

export function ThemeDetailPanels({ theme }: { theme: ThemeDetail }) {
  const [activeTab, setActiveTab] = useState<"overview" | "structure">("overview");
  const [structure, setStructure] = useState<StockStructureResponse | null>(null);
  const [structureLoading, setStructureLoading] = useState(false);
  const latest = theme.score_history[theme.score_history.length - 1];
  const sortedStocks = [...theme.stocks].sort((left, right) => (right.latest_pct_change || 0) - (left.latest_pct_change || 0));
  const risingCount = theme.stocks.filter((stock) => (stock.latest_pct_change || 0) > 0).length;
  const fallingCount = theme.stocks.filter((stock) => (stock.latest_pct_change || 0) < 0).length;
  const totalTurnover = theme.stocks.reduce((sum, stock) => sum + (stock.latest_turnover_amount || 0), 0);

  const trendOption = {
    backgroundColor: "transparent",
    tooltip: { trigger: "axis" },
    grid: { left: 16, right: 18, top: 30, bottom: 24, containLabel: true },
    xAxis: {
      type: "category",
      data: theme.score_history.map((item) => item.week_end),
      axisLabel: { color: "#71839f" },
      axisLine: { lineStyle: { color: "rgba(148, 163, 184, 0.25)" } }
    },
    yAxis: {
      type: "value",
      min: 0,
      max: 100,
      axisLabel: { color: "#71839f" },
      splitLine: { lineStyle: { color: "rgba(148, 163, 184, 0.12)" } }
    },
    series: [
      {
        type: "line",
        smooth: true,
        data: theme.score_history.map((item) => item.overall_score),
        lineStyle: { width: 3, color: "#2f8cff" },
        areaStyle: {
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: "rgba(47, 140, 255, 0.35)" },
              { offset: 1, color: "rgba(47, 140, 255, 0.02)" }
            ]
          }
        },
        symbolSize: 7,
        itemStyle: { color: "#8ec5ff" }
      }
    ]
  };

  const stockOption = {
    backgroundColor: "transparent",
    tooltip: { trigger: "axis" },
    grid: { left: 18, right: 12, top: 26, bottom: 24, containLabel: true },
    xAxis: {
      type: "category",
      data: sortedStocks.slice(0, 14).map((item) => item.name),
      axisLabel: { color: "#71839f", rotate: 30 },
      axisLine: { lineStyle: { color: "rgba(148, 163, 184, 0.25)" } }
    },
    yAxis: {
      type: "value",
      axisLabel: { color: "#71839f" },
      splitLine: { lineStyle: { color: "rgba(148, 163, 184, 0.12)" } }
    },
    series: [
      {
        type: "bar",
        data: sortedStocks.slice(0, 14).map((item) => ({
          value: item.latest_pct_change || 0,
          itemStyle: {
            color: (item.latest_pct_change || 0) >= 0 ? "#ef4444" : "#22c55e",
            borderRadius: [4, 4, 0, 0]
          }
        })),
        barMaxWidth: 28
      }
    ]
  };

  const cards = [
    { label: "综合热度", value: theme.latest_score?.toFixed(1) || "--", detail: "0-100 主题热度评分", tone: "text-blue-300" },
    { label: "平均涨跌", value: latest ? formatPct(latest.average_return) : "--", detail: "最新评分周期成分股均值", tone: pctTone(latest?.average_return || 0) },
    { label: "上涨占比", value: latest ? `${(latest.advancing_ratio * 100).toFixed(1)}%` : "--", detail: `上涨 ${risingCount} 家，下跌 ${fallingCount} 家`, tone: "text-slate-100" },
    { label: "成交额", value: formatAmount(totalTurnover), detail: `${theme.stock_count} 只成分股最新成交额`, tone: "text-violet-300" }
  ];

  return (
    <div className="min-h-screen bg-[#07111f] p-3 text-slate-100 lg:p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-3">
          <Link href="/" className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-300 hover:text-white">
            返回市场概览
          </Link>
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-slate-500">{theme.theme_type}</p>
            <h1 className="text-2xl font-bold text-white">{theme.name}</h1>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <StatusPill status={theme.latest_status} />
          <span className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-300">
            成分股 {theme.stock_count}
          </span>
        </div>
      </div>

      <div className="mb-3 flex gap-2 rounded-lg border border-slate-800 bg-slate-950/30 p-1">
        {[
          { key: "overview", label: "主题概览" },
          { key: "structure", label: "成分股结构" }
        ].map((tab) => (
          <button
            key={tab.key}
            className={`rounded-md px-4 py-2 text-sm transition ${
              activeTab === tab.key
                ? "bg-blue-500/20 text-blue-200"
                : "text-slate-500 hover:bg-slate-800/70 hover:text-slate-200"
            }`}
            onClick={async () => {
              const nextTab = tab.key as "overview" | "structure";
              setActiveTab(nextTab);
              if (nextTab === "structure" && structure === null && !structureLoading) {
                setStructureLoading(true);
                try {
                  setStructure(await getStockStructure(theme.id));
                } finally {
                  setStructureLoading(false);
                }
              }
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "overview" ? (
        <>
          <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {cards.map((card) => (
              <div key={card.label} className="terminal-panel p-4">
                <p className="text-sm text-slate-400">{card.label}</p>
                <p className={`mt-3 font-display text-3xl font-bold ${card.tone}`}>{card.value}</p>
                <p className="mt-2 text-xs text-slate-500">{card.detail}</p>
              </div>
            ))}
          </section>

          <section className="mt-3 grid gap-3 xl:grid-cols-[minmax(0,1.4fr)_360px]">
            <div className="terminal-panel p-4">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-white">热度评分趋势</h2>
                <span className="text-xs text-slate-500">最近 12 个评分周期</span>
              </div>
              <EChartsClient option={trendOption} height={330} />
            </div>

            <div className="terminal-panel p-4">
              <h2 className="text-lg font-semibold text-white">热度构成信号</h2>
              <div className="mt-4 space-y-3">
                {theme.score_history.slice(-4).reverse().map((item) => (
                  <div key={item.week_end} className="rounded-lg border border-slate-800 bg-slate-950/30 p-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-slate-400">{item.week_end}</span>
                      <span className="font-mono text-xl text-white">{item.overall_score.toFixed(1)}</span>
                    </div>
                    <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-slate-500">
                      <span>平均 {formatPct(item.average_return)}</span>
                      <span>中位 {formatPct(item.median_return)}</span>
                      <span>上涨占比 {(item.advancing_ratio * 100).toFixed(1)}%</span>
                      <span>强势 {item.strong_weeks} 周</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>

          <section className="mt-3 grid gap-3 xl:grid-cols-[minmax(0,1fr)_480px]">
            <div className="terminal-panel p-4">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-white">成分股涨跌排行</h2>
                <span className="text-xs text-slate-500">按最新涨跌幅排序</span>
              </div>
              <EChartsClient option={stockOption} height={330} />
            </div>

            <div className="terminal-panel overflow-hidden">
              <div className="border-b border-slate-800 px-4 py-3">
                <h2 className="text-lg font-semibold text-white">成分股列表</h2>
              </div>
              <div className="max-h-[390px] overflow-y-auto px-4 py-2">
                <div className="grid grid-cols-[minmax(0,1fr)_76px_96px] gap-3 py-2 text-xs text-slate-500">
                  <span>股票</span>
                  <span>涨跌幅</span>
                  <span className="text-right">成交额</span>
                </div>
                {sortedStocks.map((stock) => (
                  <div key={stock.id} className="grid grid-cols-[minmax(0,1fr)_76px_96px] items-center gap-3 border-t border-slate-800/80 py-2 text-sm">
                    <div className="min-w-0">
                      <p className="truncate text-slate-200">{stock.name}</p>
                      <p className="font-mono text-xs text-slate-600">{stock.symbol}</p>
                    </div>
                    <span className={pctTone(stock.latest_pct_change)}>{formatPct(stock.latest_pct_change)}</span>
                    <span className="text-right text-slate-400">{formatAmount(stock.latest_turnover_amount)}</span>
                  </div>
                ))}
              </div>
            </div>
          </section>
        </>
      ) : (
        structure ? (
          <StockStructureView initialData={structure} />
        ) : (
          <div className="rounded-xl bg-slate-100 p-5 text-sm text-slate-600">
            {structureLoading ? "正在加载真实成分股结构..." : "暂无成分股结构数据。"}
          </div>
        )
      )}
    </div>
  );
}
