import { ThemeRankingItem } from "@/lib/types";

function averageScore(items: ThemeRankingItem[]) {
  const values = items.map((item) => item.latest_score).filter((value): value is number => value !== null);
  if (values.length === 0) return 0;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

export function HeroOverview({ data }: { data: ThemeRankingItem[] }) {
  const industryCount = data.filter((item) => item.theme_type === "industry").length;
  const conceptCount = data.filter((item) => item.theme_type === "concept").length;
  const hotCount = data.filter((item) => ["surging", "hot"].includes((item.latest_status || "").toLowerCase())).length;

  const stats = [
    { label: "主题总数", value: data.length.toString().padStart(2, "0"), detail: "行业 + 概念双维度追踪" },
    { label: "平均热度", value: averageScore(data).toFixed(1), detail: "本周全市场板块均值" },
    { label: "强势主题", value: hotCount.toString().padStart(2, "0"), detail: "处于 hot / surging 状态" }
  ];

  return (
    <section className="fade-rise grid gap-6 lg:grid-cols-[1.3fr_0.7fr]">
      <div className="glass-card rounded-[32px] p-8">
        <p className="text-xs uppercase tracking-[0.4em] text-emerald-200/70">A-Share Theme Pulse</p>
        <h1 className="mt-4 max-w-3xl font-display text-5xl leading-tight text-white sm:text-6xl">
          A股主题热度分析看板
        </h1>
        <p className="mt-5 max-w-2xl text-lg leading-8 text-slate-300">
          聚合行业板块与概念板块，按周计算资金强度、涨幅广度与持续强势程度，输出可追踪的主题热度评分。
        </p>
        <div className="mt-10 grid gap-4 sm:grid-cols-3">
          {stats.map((stat) => (
            <div key={stat.label} className="rounded-[24px] border border-white/10 bg-white/5 p-5">
              <p className="text-sm text-slate-400">{stat.label}</p>
              <p className="mt-3 font-display text-4xl text-white">{stat.value}</p>
              <p className="mt-2 text-sm text-slate-300">{stat.detail}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="glass-card rounded-[32px] p-8">
        <p className="text-xs uppercase tracking-[0.3em] text-sky-200/70">Coverage</p>
        <div className="mt-6 space-y-6">
          <div className="rounded-[24px] border border-white/10 bg-gradient-to-br from-cyan-300/10 to-cyan-100/5 p-5">
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-300">行业板块</span>
              <span className="font-display text-3xl text-white">{industryCount}</span>
            </div>
            <p className="mt-3 text-sm text-slate-400">跟踪板块轮动中的资金主线与机构偏好。</p>
          </div>
          <div className="rounded-[24px] border border-white/10 bg-gradient-to-br from-emerald-300/10 to-emerald-100/5 p-5">
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-300">概念板块</span>
              <span className="font-display text-3xl text-white">{conceptCount}</span>
            </div>
            <p className="mt-3 text-sm text-slate-400">识别市场题材发酵速度与主题持续性。</p>
          </div>
        </div>
      </div>
    </section>
  );
}

