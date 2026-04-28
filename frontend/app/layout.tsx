import type { Metadata } from "next";

import "@/app/globals.css";

export const metadata: Metadata = {
  title: "主题热度分析系统",
  description: "A 股主题热度、资金流向与市场情绪驾驶舱"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
