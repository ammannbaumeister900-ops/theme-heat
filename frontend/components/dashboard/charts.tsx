"use client";

import { EChartsClient } from "@/components/echarts-client";
import {
  DashboardDistributionItem,
  DashboardFlowItem,
  DashboardHeatmapItem
} from "@/lib/types";

const chartText = "#d9e6ff";
const chartMuted = "#71839f";
const upColor = "#ef4444";
const downColor = "#22c55e";
const blueColor = "#2f8cff";
const amberColor = "#f59e0b";
const purpleColor = "#8b5cf6";

function interpolateHex(start: string, end: string, ratio: number) {
  const safeRatio = Math.max(0, Math.min(1, ratio));
  const startValue = Number.parseInt(start.slice(1), 16);
  const endValue = Number.parseInt(end.slice(1), 16);
  const startRgb = [(startValue >> 16) & 255, (startValue >> 8) & 255, startValue & 255];
  const endRgb = [(endValue >> 16) & 255, (endValue >> 8) & 255, endValue & 255];
  const rgb = startRgb.map((channel, index) =>
    Math.round(channel + (endRgb[index] - channel) * safeRatio)
  );
  return `#${rgb.map((channel) => channel.toString(16).padStart(2, "0")).join("")}`;
}

function heatColor(value: number, change: number, ratio: number) {
  if (change < 0) {
    return interpolateHex("#064e3b", "#22c55e", ratio);
  }
  return interpolateHex("#7f1d1d", "#ef4444", ratio);
}

export function HeatmapChart({ data }: { data: DashboardHeatmapItem[] }) {
  const heatValues = data.map((item) => item.value);
  const minHeat = Math.min(...heatValues);
  const maxHeat = Math.max(...heatValues);
  const heatRange = maxHeat - minHeat;
  const sortedByHeat = [...data].sort((left, right) => right.value - left.value);
  const rankRatio = new Map(
    sortedByHeat.map((item, index) => [
      item.id,
      sortedByHeat.length <= 1 ? 1 : 1 - index / (sortedByHeat.length - 1)
    ])
  );

  const option = {
    backgroundColor: "transparent",
    tooltip: { formatter: "{b}<br/>热度: {c}" },
    series: [
      {
        type: "treemap",
        roam: false,
        nodeClick: false,
        breadcrumb: { show: false },
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        label: {
          show: true,
          color: "#ffffff",
          formatter: "{b}\n{c}",
          fontSize: 15,
          lineHeight: 24
        },
        itemStyle: {
          borderColor: "#07111f",
          borderWidth: 2,
          gapWidth: 2
        },
        data: data.map((item) => ({
          name: item.name,
          value: Math.max(item.value, 1),
          itemStyle: {
            color: heatColor(
              item.value,
              item.change,
              heatRange >= 8 ? (item.value - minHeat) / heatRange : rankRatio.get(item.id) ?? 0
            )
          }
        }))
      }
    ]
  };

  return <EChartsClient option={option} height={360} />;
}

export function SentimentGauge({ value }: { value: number }) {
  const option = {
    backgroundColor: "transparent",
    series: [
      {
        type: "gauge",
        startAngle: 210,
        endAngle: -30,
        min: 0,
        max: 100,
        splitNumber: 4,
        radius: "95%",
        progress: { show: true, width: 12, itemStyle: { color: blueColor } },
        axisLine: {
          lineStyle: {
            width: 12,
            color: [
              [0.35, downColor],
              [0.7, amberColor],
              [1, upColor]
            ]
          }
        },
        axisTick: { show: false },
        splitLine: { length: 8, lineStyle: { color: chartMuted, width: 1 } },
        axisLabel: { color: chartMuted, distance: 18, fontSize: 10 },
        pointer: { show: false },
        detail: {
          valueAnimation: true,
          formatter: "{value}",
          color: chartText,
          fontSize: 34,
          offsetCenter: [0, "18%"]
        },
        title: {
          show: true,
          offsetCenter: [0, "48%"],
          color: "#a8ff60",
          fontSize: 14
        },
        data: [{ value, name: value >= 70 ? "贪婪" : value >= 45 ? "中性" : "谨慎" }]
      }
    ]
  };

  return <EChartsClient option={option} height={220} />;
}

export function FundFlowChart({ data }: { data: DashboardFlowItem[] }) {
  const option = {
    backgroundColor: "transparent",
    color: [blueColor, upColor, downColor, purpleColor],
    tooltip: { trigger: "item" },
    legend: {
      orient: "vertical",
      right: 0,
      top: "middle",
      textStyle: { color: chartText, fontSize: 11 }
    },
    series: [
      {
        type: "pie",
        radius: ["48%", "72%"],
        center: ["34%", "50%"],
        avoidLabelOverlap: true,
        label: { show: false },
        data: data.map((item) => ({
          name: item.label,
          value: Math.abs(item.value)
        }))
      }
    ]
  };

  return <EChartsClient option={option} height={220} />;
}

export function DistributionChart({ data }: { data: DashboardDistributionItem[] }) {
  const option = {
    backgroundColor: "transparent",
    grid: { left: 12, right: 12, top: 28, bottom: 28, containLabel: true },
    xAxis: {
      type: "category",
      data: data.map((item) => item.label),
      axisTick: { show: false },
      axisLine: { lineStyle: { color: "rgba(148, 163, 184, 0.25)" } },
      axisLabel: { color: chartMuted, fontSize: 11 }
    },
    yAxis: {
      type: "value",
      splitLine: { lineStyle: { color: "rgba(148, 163, 184, 0.12)" } },
      axisLabel: { color: chartMuted }
    },
    series: [
      {
        type: "bar",
        barWidth: 26,
        data: data.map((item) => ({
          value: item.value,
          itemStyle: {
            color: item.tone === "up" ? upColor : downColor,
            borderRadius: [4, 4, 0, 0]
          }
        })),
        label: {
          show: true,
          position: "top",
          color: chartText,
          fontSize: 11
        }
      }
    ]
  };

  return <EChartsClient option={option} height={250} />;
}

export function Sparkline({ data, tone }: { data: number[]; tone: "up" | "down" | string }) {
  const color = tone === "down" ? downColor : upColor;
  const option = {
    backgroundColor: "transparent",
    grid: { left: 0, right: 0, top: 4, bottom: 4 },
    xAxis: { type: "category", show: false, data: data.map((_, index) => index.toString()) },
    yAxis: { type: "value", show: false, min: "dataMin", max: "dataMax" },
    series: [
      {
        type: "line",
        data,
        smooth: true,
        symbol: "none",
        lineStyle: { color, width: 2 },
        areaStyle: { color: tone === "down" ? "rgba(34,197,94,0.12)" : "rgba(239,68,68,0.12)" }
      }
    ]
  };

  return <EChartsClient option={option} height={34} />;
}
