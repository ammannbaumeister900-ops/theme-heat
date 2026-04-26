import { notFound } from "next/navigation";

import { ThemeDetailPanels } from "@/components/theme-detail-panels";
import { getThemeDetail } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ThemeDetailPage({ params }: { params: { id: string } }) {
  try {
    const theme = await getThemeDetail(params.id);
    return <ThemeDetailPanels theme={theme} />;
  } catch {
    notFound();
  }
}
