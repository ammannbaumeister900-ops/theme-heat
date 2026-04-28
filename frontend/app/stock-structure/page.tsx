import { AppShell } from "@/components/dashboard/dashboard-shell";
import { StockStructureView } from "@/components/stock-structure/stock-structure-view";
import { getDashboardOverview, getStockStructure } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function StockStructurePage({
  searchParams
}: {
  searchParams: { themeId?: string; theme_id?: string };
}) {
  const themeId = searchParams.themeId || searchParams.theme_id;
  const [overview, structure] = await Promise.all([
    getDashboardOverview(),
    getStockStructure(themeId)
  ]);

  return (
    <AppShell activeHref="/stock-structure" generatedAt={overview.generated_at}>
      <StockStructureView initialData={structure} />
    </AppShell>
  );
}
