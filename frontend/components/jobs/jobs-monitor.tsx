"use client";

import { useMemo, useState, useTransition } from "react";

import {
  getComputeJobs,
  triggerDailyCompute,
  triggerFullCompute
} from "@/lib/api";
import { ComputeJobStatus } from "@/lib/types";

function formatDate(value: string | null) {
  if (!value) return "--";
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false
  }).format(new Date(value));
}

function progress(job: ComputeJobStatus) {
  if (job.total_theme_count > 0) {
    return Math.round((job.processed_theme_count / job.total_theme_count) * 100);
  }
  if (job.status === "completed") return 100;
  return 0;
}

function statusClass(status: string) {
  if (status === "completed") return "border-emerald-500/30 bg-emerald-500/10 text-emerald-200";
  if (status === "failed") return "border-red-500/30 bg-red-500/10 text-red-200";
  if (status === "running") return "border-blue-500/30 bg-blue-500/10 text-blue-200";
  return "border-slate-600 bg-slate-800 text-slate-300";
}

function shortMessage(job: ComputeJobStatus) {
  const message = job.error_message || job.message || "--";
  if (message.includes("ix_themes_name") || message.includes("uq_themes_name_type")) {
    return "历史任务遇到主题名称重复；当前唯一约束已修复。";
  }
  return message.length > 140 ? `${message.slice(0, 140)}...` : message;
}

export function JobsMonitor({ initialJobs }: { initialJobs: ComputeJobStatus[] }) {
  const [jobs, setJobs] = useState(initialJobs);
  const [notice, setNotice] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();
  const latest = jobs[0];
  const latestProgress = useMemo(() => (latest ? progress(latest) : 0), [latest]);

  async function refreshJobs() {
    const nextJobs = await getComputeJobs(30);
    setJobs(nextJobs);
  }

  function runAction(action: "daily" | "full") {
    setNotice(null);
    startTransition(async () => {
      try {
        const response = action === "daily" ? await triggerDailyCompute() : await triggerFullCompute();
        setNotice(response.message);
        await refreshJobs();
      } catch (error) {
        setNotice(error instanceof Error ? error.message : "任务触发失败");
      }
    });
  }

  return (
    <div className="text-slate-100">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Data Jobs</p>
          <h1 className="text-2xl font-bold text-white">任务监控</h1>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            className="rounded-lg border border-blue-400/40 bg-blue-500/15 px-3 py-2 text-sm text-blue-100 disabled:opacity-50"
            disabled={isPending}
            onClick={() => runAction("daily")}
          >
            触发日更刷新
          </button>
          <button
            className="rounded-lg border border-amber-400/40 bg-amber-500/15 px-3 py-2 text-sm text-amber-100 disabled:opacity-50"
            disabled={isPending}
            onClick={() => runAction("full")}
          >
            触发全量同步
          </button>
          <button
            className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-300 disabled:opacity-50"
            disabled={isPending}
            onClick={() => startTransition(refreshJobs)}
          >
            刷新状态
          </button>
        </div>
      </div>

      {notice ? (
        <div className="terminal-panel mb-3 border-blue-500/30 bg-blue-500/10 p-3 text-sm text-blue-100">{notice}</div>
      ) : null}

      <section className="grid gap-3 lg:grid-cols-[360px_minmax(0,1fr)]">
        <div className="terminal-panel p-4">
          <h2 className="text-lg font-semibold text-white">最近任务</h2>
          {latest ? (
            <div className="mt-4 space-y-4">
              <div className="flex items-center justify-between">
                <span className={`rounded border px-2 py-1 text-xs ${statusClass(latest.status)}`}>
                  {latest.status} / {latest.stage}
                </span>
                <span className="font-mono text-sm text-slate-400">#{latest.id}</span>
              </div>
              <div>
                <div className="mb-2 flex justify-between text-sm text-slate-400">
                  <span>进度</span>
                  <span>{latestProgress}%</span>
                </div>
                <div className="h-2 overflow-hidden rounded bg-slate-800">
                  <div className="h-full rounded bg-blue-500" style={{ width: `${Math.min(latestProgress, 100)}%` }} />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="rounded-lg border border-slate-800 bg-slate-950/30 p-3">
                  <p className="text-slate-500">已处理</p>
                  <p className="mt-1 font-mono text-xl text-white">{latest.processed_theme_count}</p>
                </div>
                <div className="rounded-lg border border-slate-800 bg-slate-950/30 p-3">
                  <p className="text-slate-500">评分数</p>
                  <p className="mt-1 font-mono text-xl text-white">{latest.score_count}</p>
                </div>
              </div>
              <p className="rounded-lg border border-slate-800 bg-slate-950/30 p-3 text-sm text-slate-300" title={latest.error_message || latest.message || ""}>
                {shortMessage(latest)}
              </p>
            </div>
          ) : (
            <p className="mt-4 text-sm text-slate-400">暂无任务记录。</p>
          )}
        </div>

        <div className="terminal-panel overflow-hidden">
          <div className="grid grid-cols-[72px_120px_100px_1fr_150px_150px] gap-3 border-b border-slate-800 px-4 py-3 text-xs text-slate-500">
            <span>ID</span>
            <span>状态</span>
            <span>进度</span>
            <span>信息</span>
            <span>开始时间</span>
            <span>完成时间</span>
          </div>
          <div className="divide-y divide-slate-800/80">
            {jobs.map((job) => (
              <div key={job.id} className="grid grid-cols-[72px_120px_100px_1fr_150px_150px] items-center gap-3 px-4 py-3 text-sm">
                <span className="font-mono text-slate-400">#{job.id}</span>
                <span className={`w-fit rounded border px-2 py-1 text-xs ${statusClass(job.status)}`}>
                  {job.status} / {job.stage}
                </span>
                <span className="text-slate-300">{progress(job)}%</span>
                <span className="truncate text-slate-400" title={job.error_message || job.message || ""}>
                  {shortMessage(job)}
                </span>
                <span className="text-slate-500">{formatDate(job.started_at)}</span>
                <span className="text-slate-500">{formatDate(job.finished_at)}</span>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
