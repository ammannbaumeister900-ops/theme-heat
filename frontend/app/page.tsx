import { HeroOverview } from "@/components/hero-overview";
import { OverviewChart } from "@/components/overview-chart";
import { ThemeRankingTable } from "@/components/theme-ranking-table";
import { getRankings } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const rankings = await getRankings();

  return (
    <div className="space-y-6 py-4">
      <HeroOverview data={rankings} />
      <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <OverviewChart data={rankings} />
        <ThemeRankingTable data={rankings} />
      </div>
    </div>
  );
}
