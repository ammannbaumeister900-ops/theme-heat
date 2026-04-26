import { EChartsClient } from "@/components/echarts-client";
import { ThemeRankingItem } from "@/lib/types";

export function OverviewChart({ data }: { data: ThemeRankingItem[] }) {
  const topItems = data.slice(0, 10);
  const option = {
    backgroundColor: "transparent",
    tooltip: { trigger: "axis" },
    grid: { left: 16, right: 12, top: 36, bottom: 18, containLabel: true },
    xAxis: {
      type: "value",
      axisLabel: { color: "#8ea5ca" },
      splitLine: { lineStyle: { color: "rgba(154,180,255,0.10)" } }
    },
    yAxis: {
      type: "category",
      data: topItems.map((item) => item.name),
      axisLabel: { color: "#edf3ff" },
      axisTick: { show: false }
    },
    series: [
      {
        type: "bar",
        data: topItems.map((item) => item.latest_score || 0),
        barWidth: 16,
        itemStyle: {
          borderRadius: [0, 10, 10, 0],
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 1,
            y2: 0,
            colorStops: [
              { offset: 0, color: "#0ea5e9" },
              { offset: 1, color: "#3ccf91" }
            ]
          }
        }
      }
    ]
  };

  return (
    <div className="glass-card fade-rise rounded-[28px] p-6">
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.32em] text-sky-200/70">Top Themes</p>
          <h2 className="mt-2 font-display text-2xl">头部主题热度分布</h2>
        </div>
        <p className="text-sm text-slate-300">按本周综合评分取前十，便于快速识别市场主线。</p>
      </div>
      <div className="mt-6">
        <EChartsClient option={option} height={360} />
      </div>
    </div>
  );
}

