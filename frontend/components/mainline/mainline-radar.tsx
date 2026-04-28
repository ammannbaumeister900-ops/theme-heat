"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { MainlineRadarResponse, ThemeDiagnosis } from "@/lib/types";

const scoreItems: Array<{
  key: keyof ThemeDiagnosis["score"];
  label: string;
  negative?: boolean;
}> = [
  { key: "fund", label: "资金" },
  { key: "returnStrength", label: "涨幅" },
  { key: "breadth", label: "扩散" },
  { key: "persistence", label: "持续" },
  { key: "catalyst", label: "催化" },
  { key: "crowdingPenalty", label: "拥挤扣分", negative: true }
];

function badgeClass(value: string) {
  if (["强主线", "高"].includes(value)) {
    return "border-red-500/30 bg-red-500/10 text-red-200";
  }
  if (["潜在主线", "确认期", "主升期", "中"].includes(value)) {
    return "border-blue-500/30 bg-blue-500/10 text-blue-200";
  }
  if (["低", "萌芽期"].includes(value)) {
    return "border-emerald-500/30 bg-emerald-500/10 text-emerald-200";
  }
  if (["高潮期", "退潮期"].includes(value)) {
    return "border-amber-500/30 bg-amber-500/10 text-amber-200";
  }
  return "border-slate-600 bg-slate-800 text-slate-300";
}

function ScoreBar({
  label,
  value,
  negative = false
}: {
  label: string;
  value: number;
  negative?: boolean;
}) {
  const width = Math.max(0, Math.min(100, value));
  return (
    <div>
      <div className="mb-1 flex justify-between text-xs text-slate-500">
        <span>{label}</span>
        <span>{value.toFixed(1)}</span>
      </div>
      <div className="h-2 overflow-hidden rounded bg-slate-800">
        <div
          className={`h-full rounded ${negative ? "bg-amber-500" : "bg-blue-500"}`}
          style={{ width: `${width}%` }}
        />
      </div>
    </div>
  );
}

function SummaryCard({
  label,
  value,
  tone
}: {
  label: string;
  value: string | number;
  tone?: string;
}) {
  return (
    <div className="terminal-panel p-4">
      <p className="text-sm text-slate-400">{label}</p>
      <p className={`mt-3 font-display text-3xl font-bold ${tone || "text-white"}`}>
        {value}
      </p>
    </div>
  );
}

function CompactScoreBar({
  value,
  negative = false
}: {
  value: number;
  negative?: boolean;
}) {
  return (
    <span className="flex min-w-[74px] items-center gap-2">
      <span className="h-1.5 flex-1 overflow-hidden rounded bg-slate-800">
        <span
          className={`block h-full ${negative ? "bg-amber-500" : "bg-blue-500"}`}
          style={{ width: `${Math.min(100, value)}%` }}
        />
      </span>
      <span className="w-9 text-right font-mono text-xs text-slate-400">{value.toFixed(0)}</span>
    </span>
  );
}

export function MainlineRadar({ data }: { data: MainlineRadarResponse }) {
  const [selectedId, setSelectedId] = useState(data.themes[0]?.themeId || "");
  const selected = useMemo(
    () => data.themes.find((item) => item.themeId === selectedId) || data.themes[0],
    [data.themes, selectedId]
  );

  return (
    <div className="text-slate-100">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Mainline Radar</p>
          <h1 className="text-2xl font-bold text-white">主线雷达</h1>
        </div>
        <div className="text-sm text-slate-500">
          生成时间{" "}
          {new Intl.DateTimeFormat("zh-CN", {
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
            hour12: false
          }).format(new Date(data.generatedAt))}
        </div>
      </div>

      <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <SummaryCard
          label="今日最强主线"
          value={data.marketSummary.strongestTheme?.themeName || "--"}
          tone="text-red-300"
        />
        <SummaryCard label="潜在主线数量" value={data.marketSummary.potentialCount} tone="text-blue-300" />
        <SummaryCard
          label="高拥挤风险主题"
          value={data.marketSummary.highCrowdingRiskCount}
          tone="text-amber-300"
        />
        <SummaryCard label="市场状态" value={data.marketSummary.marketStatus} tone="text-emerald-300" />
      </section>

      <section className="mt-3 grid gap-3 xl:grid-cols-[minmax(0,1fr)_420px]">
        <div className="terminal-panel overflow-hidden">
          <div className="grid grid-cols-[44px_minmax(120px,1fr)_repeat(6,minmax(74px,0.58fr))_72px_82px_82px_70px_70px] gap-3 border-b border-slate-800 px-4 py-3 text-xs text-slate-500">
            <span>排名</span>
            <span>主题</span>
            {scoreItems.map((scoreItem) => (
              <span key={scoreItem.key}>{scoreItem.label}</span>
            ))}
            <span>总分</span>
            <span>状态</span>
            <span>阶段</span>
            <span>健康</span>
            <span>风险</span>
          </div>
          <div className="divide-y divide-slate-800/80">
            {data.themes.map((item, index) => (
              <button
                key={item.themeId}
                className={`grid w-full grid-cols-[44px_minmax(120px,1fr)_repeat(6,minmax(74px,0.58fr))_72px_82px_82px_70px_70px] items-center gap-3 px-4 py-3 text-left text-sm transition hover:bg-slate-800/40 ${
                  selected?.themeId === item.themeId ? "bg-blue-500/10" : ""
                }`}
                onClick={() => setSelectedId(item.themeId)}
              >
                <span
                  className={`grid h-6 w-6 place-items-center rounded text-xs text-white ${
                    index < 3 ? "bg-orange-500" : "bg-slate-700"
                  }`}
                >
                  {index + 1}
                </span>
                <span className="min-w-0">
                  <span className="block truncate font-semibold text-slate-100">{item.themeName}</span>
                </span>
                {scoreItems.map((scoreItem) => (
                  <CompactScoreBar
                    key={scoreItem.key}
                    value={item.score[scoreItem.key]}
                    negative={scoreItem.negative}
                  />
                ))}
                <span className="font-mono text-xl font-bold text-white">{item.score.total.toFixed(1)}</span>
                <span className={`w-fit rounded border px-2 py-1 text-xs ${badgeClass(item.status)}`}>
                  {item.status}
                </span>
                <span className={`w-fit rounded border px-2 py-1 text-xs ${badgeClass(item.stage)}`}>
                  {item.stage}
                </span>
                <span className={`w-fit rounded border px-2 py-1 text-xs ${badgeClass(item.healthLevel)}`}>
                  {item.healthLevel}
                </span>
                <span className={`w-fit rounded border px-2 py-1 text-xs ${badgeClass(item.riskLevel)}`}>
                  {item.riskLevel}
                </span>
              </button>
            ))}
          </div>
        </div>

        {selected ? (
          <aside className="terminal-panel p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-[0.22em] text-slate-500">Theme Diagnosis</p>
                <h2 className="mt-2 text-xl font-bold text-white">{selected.themeName}</h2>
              </div>
              <div className="flex shrink-0 items-center gap-2">
                <span className={`rounded border px-2 py-1 text-xs ${badgeClass(selected.status)}`}>
                  {selected.status}
                </span>
                <Link
                  href={`/stock-structure?themeId=${selected.themeId}`}
                  className="rounded border border-blue-400/30 bg-blue-500/10 px-2 py-1 text-xs text-blue-200 hover:text-white"
                >
                  成分股结构
                </Link>
              </div>
            </div>

            <div className="mt-4 rounded-lg border border-slate-800 bg-slate-950/30 p-3">
              <p className="text-sm text-slate-400">主线结论</p>
              <p className="mt-2 text-sm leading-6 text-slate-200">
                当前处于 <b>{selected.stage}</b>，主线总分{" "}
                <b>{selected.score.total.toFixed(1)}</b>，健康度{" "}
                <b>{selected.healthLevel}</b>，拥挤风险{" "}
                <b>{selected.riskLevel}</b>。
              </p>
            </div>

            <div className="mt-4 space-y-3">
              {scoreItems.map((item) => (
                <ScoreBar
                  key={item.key}
                  label={item.label}
                  value={selected.score[item.key]}
                  negative={item.negative}
                />
              ))}
            </div>

            <div className="mt-5">
              <h3 className="text-sm font-semibold text-white">形成原因</h3>
              <ul className="mt-2 space-y-2 text-sm leading-6 text-slate-400">
                {selected.reasons.map((reason) => (
                  <li key={reason}>- {reason}</li>
                ))}
              </ul>
            </div>

            <div className="mt-5">
              <h3 className="text-sm font-semibold text-white">后续观察重点</h3>
              <ul className="mt-2 space-y-2 text-sm leading-6 text-slate-400">
                {selected.watchPoints.map((point) => (
                  <li key={point}>- {point}</li>
                ))}
              </ul>
            </div>

            <div className="mt-5 rounded-lg border border-amber-500/20 bg-amber-500/10 p-3 text-sm leading-6 text-amber-100">
              风险提示：主线雷达是规则化诊断工具，不构成投资建议；高拥挤风险主题需要重点观察分歧和承接。
            </div>
          </aside>
        ) : null}
      </section>
    </div>
  );
}
