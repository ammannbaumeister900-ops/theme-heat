import Link from "next/link";

import { StatusPill } from "@/components/status-pill";
import { ThemeRankingItem } from "@/lib/types";

function scoreTone(score: number | null) {
  if (score === null) return "text-slate-300";
  if (score >= 80) return "text-emerald-300";
  if (score >= 65) return "text-cyan-200";
  if (score >= 50) return "text-amber-200";
  return "text-rose-200";
}

export function ThemeRankingTable({ data }: { data: ThemeRankingItem[] }) {
  return (
    <div className="glass-card fade-rise overflow-hidden rounded-[28px]">
      <div className="border-b border-white/10 px-6 py-5">
        <div className="flex items-end justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.32em] text-sky-200/70">Weekly Ranking</p>
            <h2 className="mt-2 font-display text-2xl">主题热度排行榜</h2>
          </div>
          <p className="text-sm text-slate-300">行业与概念板块统一评分，按最新周度结果排序。</p>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-white/5 text-slate-300">
            <tr>
              <th className="px-6 py-4">主题</th>
              <th className="px-4 py-4">类型</th>
              <th className="px-4 py-4">评分</th>
              <th className="px-4 py-4">状态</th>
              <th className="px-4 py-4">成分股</th>
              <th className="px-4 py-4">周期</th>
            </tr>
          </thead>
          <tbody>
            {data.map((item) => (
              <tr key={item.id} className="border-t border-white/10 transition hover:bg-white/5">
                <td className="px-6 py-4">
                  <Link href={`/themes/${item.id}`} className="group inline-flex flex-col">
                    <span className="font-semibold text-white group-hover:text-emerald-200">{item.name}</span>
                    <span className="text-xs uppercase tracking-[0.24em] text-slate-400">{item.code || "N/A"}</span>
                  </Link>
                </td>
                <td className="px-4 py-4 capitalize text-slate-200">{item.theme_type}</td>
                <td className={`px-4 py-4 text-xl font-bold ${scoreTone(item.latest_score)}`}>
                  {item.latest_score?.toFixed(1) || "--"}
                </td>
                <td className="px-4 py-4">
                  <StatusPill status={item.latest_status} />
                </td>
                <td className="px-4 py-4 text-slate-200">{item.stock_count}</td>
                <td className="px-4 py-4 text-slate-300">
                  {item.week_start && item.week_end ? `${item.week_start} ~ ${item.week_end}` : "--"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

