import Link from "next/link";
import type { ReactNode } from "react";

import {
  DistributionChart,
  FundFlowChart,
  HeatmapChart,
  SentimentGauge,
  Sparkline
} from "@/components/dashboard/charts";
import { DashboardMetric, DashboardOverview } from "@/lib/types";

const tradingEconomicsStocksUrl = "https://zh.tradingeconomics.com/stocks";

function metricToneClass(tone: string) {
  if (tone === "up") return "text-red-400";
  if (tone === "down") return "text-emerald-400";
  if (tone === "hot") return "text-violet-400";
  return "text-slate-100";
}

function signed(value: number) {
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
}

function formatGeneratedAt(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false
  }).format(new Date(value));
}

function MetricCard({ metric }: { metric: DashboardMetric }) {
  return (
    <div className="terminal-panel min-h-[116px] p-4">
      <p className="text-sm text-slate-400">{metric.label}</p>
      <div className="mt-3 flex items-end gap-1">
        <span className={`font-display text-3xl font-bold ${metricToneClass(metric.tone)}`}>{metric.value}</span>
        {metric.unit ? <span className="pb-1 text-sm text-slate-300">{metric.unit}</span> : null}
      </div>
      <p className="mt-3 text-xs text-slate-500">
        {metric.delta === null ? "基于最新交易日聚合" : `参考值 ${metric.delta.toFixed(2)}`}
      </p>
    </div>
  );
}

function formatJobMessage(data: DashboardOverview) {
  const rawMessage = data.job.error_message || data.job.message || "暂无任务记录";
  if (rawMessage.includes("ix_themes_name") || rawMessage.includes("uq_themes_name_type")) {
    return "最近任务失败：历史任务遇到主题名称重复，当前已改为按名称 + 类型唯一。";
  }
  if (rawMessage.length > 120) {
    return `${rawMessage.slice(0, 120)}...`;
  }
  return rawMessage;
}

function DataStatusBar({ data }: { data: DashboardOverview }) {
  const statusTone =
    data.data_quality.status === "healthy"
      ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-200"
      : data.data_quality.status === "warning"
        ? "border-amber-500/30 bg-amber-500/10 text-amber-200"
        : "border-blue-500/30 bg-blue-500/10 text-blue-200";
  const progress =
    data.job.total_count > 0
      ? Math.round((data.job.processed_count / data.job.total_count) * 100)
      : data.job.status === "completed"
        ? 100
        : 0;

  return (
    <section className={`terminal-panel mb-3 grid gap-3 p-4 xl:grid-cols-[1.1fr_0.9fr] ${statusTone}`}>
      <div>
        <div className="flex flex-wrap items-center gap-3">
          <span className="rounded bg-slate-950/40 px-2 py-1 text-xs">数据状态：{data.data_quality.status}</span>
          <span className="text-sm">最新交易日 {data.latest_trade_date || "--"}</span>
          <span className="text-sm">
            行情覆盖 {data.data_quality.quote_count}/{data.data_quality.stock_count}，
            {(data.data_quality.quote_coverage_ratio * 100).toFixed(1)}%
          </span>
          <Link href="/data/jobs" className="rounded border border-blue-400/30 bg-blue-500/10 px-2 py-1 text-xs text-blue-200 hover:text-white">
            查看任务监控
          </Link>
        </div>
        {data.data_quality.warnings.length > 0 ? (
          <div className="mt-2 space-y-1 text-sm">
            {data.data_quality.warnings.map((warning) => (
              <p key={warning}>{warning}</p>
            ))}
          </div>
        ) : (
          <p className="mt-2 text-sm text-slate-300">当前数据质量正常，派生资金流为估算指标，后续可替换为真实资金流数据源。</p>
        )}
      </div>
      <div className="rounded-lg border border-slate-700/60 bg-slate-950/30 p-3">
        <div className="flex items-center justify-between gap-3 text-sm">
          <span>最近任务 #{data.job.id || "--"}</span>
          <span className="rounded bg-slate-800 px-2 py-1 text-xs">{data.job.status} / {data.job.stage}</span>
        </div>
        <div className="mt-3 h-2 overflow-hidden rounded bg-slate-800">
          <div className="h-full rounded bg-blue-500" style={{ width: `${Math.min(progress, 100)}%` }} />
        </div>
        <div className="mt-2 flex min-w-0 items-center justify-between gap-3 text-xs text-slate-400">
          <span className="min-w-0 truncate" title={data.job.error_message || data.job.message || ""}>
            {formatJobMessage(data)}
          </span>
          <span>{progress}%</span>
        </div>
      </div>
    </section>
  );
}

function TopNav({ generatedAt, activeHref }: { generatedAt: string; activeHref: string }) {
  const navItems = [
    { label: "市场概览", href: "/" },
    { label: "主线雷达", href: "/mainline-radar" },
    { label: "成分股结构", href: "/stock-structure" },
    { label: "任务监控", href: "/data/jobs" }
  ];
  return (
    <header className="sticky top-0 z-20 border-b border-slate-800/80 bg-[#07111f]/95 backdrop-blur">
      <div className="flex min-h-16 items-center justify-between gap-6 px-4 lg:px-6">
        <div className="flex min-w-[260px] items-center gap-3">
          <div className="grid h-9 w-9 place-items-center rounded-lg border border-blue-400/30 bg-blue-500/15 text-blue-300">
            TH
          </div>
          <div>
            <h1 className="text-lg font-bold leading-5 text-white">主题热度分析系统</h1>
            <p className="text-xs text-slate-500">Theme Heat Analysis System</p>
          </div>
        </div>
        <nav className="hidden flex-1 items-center justify-center gap-2 xl:flex">
          {navItems.map((item) => {
            const active = item.href === activeHref;
            return (
            <Link
              key={item.label}
              href={item.href}
              className={`border-b-2 px-3 py-5 text-sm ${
                active
                  ? "border-blue-500 text-blue-300"
                  : "border-transparent text-slate-400 hover:text-slate-100"
              }`}
            >
              {item.label}
            </Link>
            );
          })}
        </nav>
        <div className="hidden items-center gap-4 text-sm text-slate-300 lg:flex">
          <span>{formatGeneratedAt(generatedAt)}</span>
          <span className="h-4 w-px bg-slate-700" />
          <span>admin</span>
        </div>
      </div>
    </header>
  );
}

function SideNav({ activeHref }: { activeHref: string }) {
  const groups = [
    { title: "市场概览", items: [{ label: "实时看板", href: "/" }] },
    { title: "主线雷达", items: [{ label: "主线评分", href: "/mainline-radar" }] },
    { title: "成分股结构", items: [{ label: "结构分组", href: "/stock-structure" }] },
    { title: "数据管理", items: [{ label: "任务监控", href: "/data/jobs" }] }
  ];

  return (
    <aside className="hidden w-[176px] shrink-0 border-r border-slate-800/80 bg-[#0a1728] px-4 py-4 lg:block">
      <div className="space-y-5">
        {groups.map((group) => (
          <div key={group.title}>
            <p className="mb-2 text-sm text-slate-400">{group.title}</p>
            <div className="space-y-1">
              {group.items.map((item) => {
                const active = item.href === activeHref;
                return (
                  <Link
                    key={item.label}
                    href={item.href}
                    className={`block rounded-lg px-3 py-2 text-sm ${
                      active
                        ? "bg-blue-500/20 text-blue-300"
                        : "text-slate-500 hover:bg-slate-800/70 hover:text-slate-200"
                    }`}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </div>
      <button className="mt-6 w-full rounded-lg bg-slate-800/80 px-3 py-2 text-sm text-slate-300">收起菜单</button>
    </aside>
  );
}

export function AppShell({
  activeHref,
  generatedAt,
  children
}: {
  activeHref: string;
  generatedAt: string;
  children: ReactNode;
}) {
  return (
    <div className="min-h-screen bg-[#07111f] text-slate-100">
      <TopNav generatedAt={generatedAt} activeHref={activeHref} />
      <div className="flex">
        <SideNav activeHref={activeHref} />
        <main className="min-w-0 flex-1 p-3 lg:p-4">{children}</main>
      </div>
    </div>
  );
}

export function DashboardShell({ data }: { data: DashboardOverview }) {
  const sentiment = Number(data.metrics.find((metric) => metric.label === "市场情绪")?.value || 0);
  const rising = data.metrics.find((metric) => metric.label === "上涨家数")?.value || 0;
  const falling = data.metrics.find((metric) => metric.label === "下跌家数")?.value || 0;

  return (
    <AppShell activeHref="/" generatedAt={data.generated_at}>
          <DataStatusBar data={data} />
          <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-6">
            {data.metrics.map((metric) => (
              <MetricCard key={metric.label} metric={metric} />
            ))}
          </section>
          <section className="mt-3 grid gap-3 2xl:grid-cols-[minmax(0,1fr)_430px]">
            <div className="terminal-panel p-4">
              <div className="mb-3 flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-white">主题热度地图</h2>
                  <p className="text-xs text-slate-500">块大小代表热度，颜色深浅代表同屏相对热度</p>
                </div>
                <div className="hidden items-center gap-2 text-xs text-slate-500 sm:flex">
                  <span>低</span>
                  <span className="h-2 w-36 rounded-full bg-gradient-to-r from-emerald-600 via-amber-500 to-red-600" />
                  <span>高</span>
                </div>
              </div>
              <HeatmapChart data={data.heatmap} />
            </div>
            <div className="terminal-panel overflow-hidden">
              <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3">
                <h2 className="text-lg font-semibold text-white">主题热度排行</h2>
                <span className="text-sm text-slate-500">更多 &gt;</span>
              </div>
              <div className="px-4 py-2">
                <div className="grid grid-cols-[44px_minmax(0,1fr)_72px_76px_86px] gap-2 py-2 text-xs text-slate-500">
                  <span>排名</span>
                  <span>主题</span>
                  <span>热度</span>
                  <span>涨跌幅</span>
                  <span>趋势</span>
                </div>
                {data.ranking.map((item) => (
                  <Link
                    key={item.id}
                    href={`/themes/${item.id}`}
                    className="grid grid-cols-[44px_minmax(0,1fr)_72px_76px_86px] items-center gap-2 border-t border-slate-800/80 py-2 text-sm hover:bg-slate-800/40"
                  >
                    <span className={`grid h-5 w-5 place-items-center rounded text-xs text-white ${item.rank <= 3 ? "bg-orange-500" : "bg-slate-700"}`}>
                      {item.rank}
                    </span>
                    <span className="truncate text-slate-200">{item.name}</span>
                    <span className="font-mono text-slate-100">{item.heat.toFixed(1)}</span>
                    <span className={item.change >= 0 ? "text-red-400" : "text-emerald-400"}>{signed(item.change)}</span>
                    <Sparkline data={item.trend} tone={item.change >= 0 ? "up" : "down"} />
                  </Link>
                ))}
              </div>
            </div>
          </section>
          <section className="mt-3 grid gap-3 xl:grid-cols-[280px_280px_minmax(0,1fr)_390px]">
            <div className="terminal-panel p-4">
              <h2 className="text-lg font-semibold text-white">市场情绪指数</h2>
              <SentimentGauge value={sentiment} />
              <p className="text-center text-sm text-slate-500">最新交易日 {data.latest_trade_date || "--"}</p>
            </div>
            <div className="terminal-panel p-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-white">资金流向</h2>
                <span className="text-xs text-slate-500">单位：亿元</span>
              </div>
              <FundFlowChart data={data.flows} />
            </div>
            <div className="terminal-panel p-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-white">涨跌分布</h2>
                <span className="text-sm text-slate-500">更多 &gt;</span>
              </div>
              <DistributionChart data={data.distribution} />
              <div className="mt-1 flex items-center justify-between text-sm">
                <span>上涨 <b className="text-red-400">{rising}</b> 家</span>
                <span>下跌 <b className="text-emerald-400">{falling}</b> 家</span>
              </div>
            </div>
            <div className="terminal-panel overflow-hidden">
              <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3">
                <h2 className="text-lg font-semibold text-white">实时热点</h2>
                <span className="text-sm text-slate-500">更多 &gt;</span>
              </div>
              <div className="px-4 py-3">
                <div className="grid grid-cols-[minmax(0,1fr)_64px_72px] gap-3 rounded bg-slate-900/60 px-3 py-2 text-xs text-slate-500">
                  <span>热点事件</span>
                  <span>热度</span>
                  <span>持续时间</span>
                </div>
                {data.hotspots.map((item) => (
                  <div key={item.rank} className="grid grid-cols-[minmax(0,1fr)_64px_72px] items-center gap-3 border-b border-slate-800/70 px-3 py-3 text-sm">
                    <span className="truncate">
                      <b className={`mr-2 rounded px-1.5 py-0.5 text-xs text-white ${item.rank <= 3 ? "bg-orange-500" : "bg-slate-700"}`}>{item.rank}</b>
                      {item.title}
                    </span>
                    <span className={item.tone === "up" ? "text-red-400" : "text-emerald-400"}>{item.heat.toFixed(1)}</span>
                    <span className="text-slate-400">{item.duration}</span>
                  </div>
                ))}
              </div>
            </div>
          </section>
          <section className="mt-3 grid gap-3 xl:grid-cols-[minmax(0,1fr)_390px]">
            <div className="terminal-panel overflow-hidden">
              <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3">
                <h2 className="text-lg font-semibold text-white">市场资讯</h2>
                <a href={tradingEconomicsStocksUrl} target="_blank" rel="noreferrer" className="text-sm text-blue-300 hover:text-blue-100">
                  全球股市行情 &gt;
                </a>
              </div>
              <div className="grid gap-0 md:grid-cols-2">
                {data.news.slice(0, 6).map((item, index) => {
                  const content = (
                    <article className="min-h-[118px] border-b border-slate-800/70 p-4 transition hover:bg-slate-800/30 md:border-r">
                      <div className="mb-2 flex items-center justify-between gap-3 text-xs text-slate-500">
                        <span>{item.source}</span>
                        <span>{item.published_at || "--"}</span>
                      </div>
                      <h3 className="line-clamp-2 text-sm font-semibold leading-6 text-slate-100">{item.title}</h3>
                      {item.summary ? <p className="mt-2 line-clamp-2 text-xs leading-5 text-slate-500">{item.summary}</p> : null}
                    </article>
                  );
                  return item.url ? (
                    <a key={`${item.title}-${index}`} href={item.url} target="_blank" rel="noreferrer">{content}</a>
                  ) : (
                    <div key={`${item.title}-${index}`}>{content}</div>
                  );
                })}
                {data.news.length === 0 ? <div className="p-4 text-sm text-slate-500">新闻源暂时不可用，主行情数据不受影响。</div> : null}
              </div>
            </div>
            <div className="terminal-panel p-4">
              <h2 className="text-lg font-semibold text-white">资讯说明</h2>
              <p className="mt-3 text-sm leading-6 text-slate-400">
                新闻模块用于辅助观察市场叙事，不参与当前主题热度评分。全球股市行情入口使用 Trading Economics 股票市场页面。
              </p>
              <a href={tradingEconomicsStocksUrl} target="_blank" rel="noreferrer" className="mt-3 inline-flex rounded-lg border border-blue-400/30 bg-blue-500/10 px-3 py-2 text-sm text-blue-200 hover:text-white">
                打开 Trading Economics
              </a>
              <div className="mt-4 rounded-lg border border-slate-800 bg-slate-950/30 p-3 text-xs leading-6 text-slate-500">
                当前评分仍基于成分股涨跌、成交额、上涨占比和强势持续性；新闻信号会作为下一阶段的可选增强因子。
              </div>
            </div>
          </section>
          <section className="mt-3 overflow-hidden rounded-lg border border-slate-800 bg-[#0a1728]">
            <div className="flex min-h-11 items-center gap-8 px-4 text-sm">
              <span className="shrink-0 text-blue-300">市场快讯</span>
              <div className="flex min-w-0 flex-1 gap-10 overflow-hidden text-slate-300">
                {data.ticker.map((item, index) => (
                  <span key={`${item.time}-${index}`} className="shrink-0">
                    <b className="mr-3 font-mono text-slate-500">{item.time}</b>
                    {item.text}
                  </span>
                ))}
              </div>
            </div>
          </section>
    </AppShell>
  );
}
