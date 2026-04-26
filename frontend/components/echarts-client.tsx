"use client";

import ReactECharts from "echarts-for-react";

type Props = {
  option: Record<string, unknown>;
  height?: number;
};

export function EChartsClient({ option, height = 320 }: Props) {
  return <ReactECharts option={option} style={{ height }} opts={{ renderer: "svg" }} />;
}

