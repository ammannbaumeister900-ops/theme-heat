import Link from "next/link";

import { EChartsClient } from "@/components/echarts-client";
import { StatusPill } from "@/components/status-pill";
import { ThemeDetail } from "@/lib/types";

function formatPct(value: number | null) {
  if (value === null) return "--";
  return `${value.toFixed(2)}%`;
}

function formatAmount(value: number | null) {
  if (value === null) return "--";
  if (value >= 100000000) return `${(value / 100000000).toFixed(2)} 亿`;
  if (value >= 10000) return `${(value / 10000).toFixed(2)} 万`;
  return value.toFixed(0);
}

export function ThemeDetailPanels({ theme }: { theme: ThemeDetail }) {
  const trendOption = {
    backgroundColor: "transparent",
    tooltip: { trigger: "axis" },
    grid: { left: 20, right: 20, top: 40, bottom: 24, containLabel: true },
    xAxis: {
      type: "category",
      data: theme.score_history.map((item) => item.week_end),
      axisLabel: { color: "#8ea5ca" }
    },
    yAxis: {
      type: "value",
      min: 0,
      max: 100,
      axisLabel: { color: "#8ea5ca" },
      splitLine: { lineStyle: { color: "rgba(154,180,255,0.10)" } }
    },
    series: [
      {
        type: "line",
        smooth: true,
        data: theme.score_history.map((item) => item.overall_score),
        lineStyle: { width: 4, color: "#3ccf91" },
        areaStyle: {
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: "rgba(60, 207, 145, 0.45)" },
              { offset: 1, color: "rgba(60, 207, 145, 0.02)" }
            ]
          }
        },
        symbolSize: 8,
        itemStyle: { color: "#7cf0be" }
      }
    ]
  };

  const stockOption = {
    backgroundColor: "transparent",
    tooltip: { trigger: "axis" },
    grid: { left: 20, right: 12, top: 30, bottom: 20, containLabel: true },
    xAxis: {
      type: "category",
      data: theme.stocks.slice(0, 12).map((item) => item.name),
      axisLabel: { color: "#8ea5ca", rotate: 25 }
    },
    yAxis: {
      type: "value",
      axisLabel: { color: "#8ea5ca" },
      splitLine: { lineStyle: { color: "rgba(154,180,255,0.10)" } }
    },
    series: [
      {
        type: "bar",
        data: theme.stocks.slice(0, 12).map((item) => item.latest_pct_change || 0),
        barMaxWidth: 26,
        itemStyle: {
          color: (params: { value: number }) => (params.value >= 0 ? "#3ccf91" : "#ff6a6a"),
          borderRadius: [8, 8, 0, 0]
        }
      }
    ]
  };

  const latest = theme.score_history[theme.score_history.length - 1];
  const cards = [
    { label: "综合评分", value: theme.latest_score?.toFixed(1) || "--", detail: "0-100 周度热度分" },
    { label: "平均涨幅", value: latest ? `${latest.average_return.toFixed(2)}%` : "--", detail: "本周成分股均值" },
    { label: "中位数涨幅", value: latest ? `${latest.median_return.toFixed(2)}%` : "--", detail: "去极值后的中枢表现" },
    { label: "上涨占比", value: latest ? `${(latest.advancing_ratio * 100).toFixed(1)}%` : "--", detail: "成分股广度" }
  ];

  return (
    <div className="space-y-6">
      <section className="fade-rise glass-card rounded-[32px] p-8">
        <Link href="/" className="text-sm text-emerald-200/90 hover:text-emerald-100">
          ← 返回首页
        </Link>
        <div className="mt-6 flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.32em] text-sky-200/70">{theme.theme_type}</p>
            <h1 className="mt-3 font-display text-5xl text-white">{theme.name}</h1>
            <p className="mt-4 max-w-2xl text-slate-300">
              基于 AKShare 板块成分与个股周度表现自动计算热度，追踪题材发酵速度、板块广度与资金聚焦强度。
            </p>
          </div>
          <div className="flex items-center gap-4">
            <StatusPill status={theme.latest_status} />
            <div className="rounded-[24px] border border-white/10 bg-white/5 px-5 py-4">
              <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Constituents</p>
              <p className="mt-2 font-display text-3xl">{theme.stock_count}</p>
            </div>
          </div>
        </div>

        <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {cards.map((card) => (
            <div key={card.label} className="rounded-[24px] border border-white/10 bg-white/5 p-5">
              <p className="text-sm text-slate-400">{card.label}</p>
              <p className="mt-3 font-display text-4xl text-white">{card.value}</p>
              <p className="mt-2 text-sm text-slate-300">{card.detail}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.35fr_0.65fr]">
        <div className="glass-card rounded-[28px] p-6">
          <div className="flex items-end justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.32em] text-sky-200/70">Score History</p>
              <h2 className="mt-2 font-display text-2xl">热度评分趋势</h2>
            </div>
            <p className="text-sm text-slate-300">展示最近 12 周评分变化。</p>
          </div>
          <div className="mt-6">
            <EChartsClient option={trendOption} height={360} />
          </div>
        </div>

        <div className="glass-card rounded-[28px] p-6">
          <p className="text-xs uppercase tracking-[0.32em] text-sky-200/70">Heat Signals</p>
          <div className="mt-5 space-y-4">
            {theme.score_history.slice(-3).reverse().map((item) => (
              <div key={item.week_end} className="rounded-[22px] border border-white/10 bg-white/5 p-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-300">{item.week_end}</span>
                  <span className="font-display text-2xl text-white">{item.overall_score.toFixed(1)}</span>
                </div>
                <div className="mt-3 flex items-center justify-between text-sm text-slate-400">
                  <span>上涨占比 {(item.advancing_ratio * 100).toFixed(1)}%</span>
                  <span>连续强势 {item.strong_weeks} 周</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="glass-card rounded-[28px] p-6">
          <div className="flex items-end justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.32em] text-sky-200/70">Constituent Moves</p>
              <h2 className="mt-2 font-display text-2xl">成分股涨跌表现</h2>
            </div>
            <p className="text-sm text-slate-300">默认展示前 12 只股票的最新涨跌幅。</p>
          </div>
          <div className="mt-6">
            <EChartsClient option={stockOption} height={340} />
          </div>
        </div>

        <div className="glass-card rounded-[28px] p-6">
          <div className="flex items-end justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.32em] text-sky-200/70">Constituent List</p>
              <h2 className="mt-2 font-display text-2xl">成分股列表</h2>
            </div>
            <p className="text-sm text-slate-300">最新日行情快照。</p>
          </div>
          <div className="mt-6 space-y-3">
            {theme.stocks.map((stock) => (
              <div key={stock.id} className="flex items-center justify-between rounded-[22px] border border-white/10 bg-white/5 px-4 py-4">
                <div>
                  <p className="font-semibold text-white">{stock.name}</p>
                  <p className="mt-1 text-xs uppercase tracking-[0.2em] text-slate-400">{stock.symbol}</p>
                </div>
                <div className="text-right">
                  <p className={`${(stock.latest_pct_change || 0) >= 0 ? "text-emerald-300" : "text-rose-300"} font-semibold`}>
                    {formatPct(stock.latest_pct_change)}
                  </p>
                  <p className="mt-1 text-sm text-slate-400">{formatAmount(stock.latest_turnover_amount)}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}

