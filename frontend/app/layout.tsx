import type { Metadata } from "next";

import "@/app/globals.css";

export const metadata: Metadata = {
  title: "A股主题热度分析",
  description: "行业与概念板块周度热度看板"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>
        <div className="dashboard-shell">
          <main className="mx-auto min-h-screen max-w-[1440px] px-4 py-6 sm:px-6 lg:px-8">{children}</main>
        </div>
      </body>
    </html>
  );
}

