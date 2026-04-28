import { AppShell } from "@/components/dashboard/dashboard-shell";
import { MainlineRadar } from "@/components/mainline/mainline-radar";
import { getDashboardOverview, getMainlineRadar } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function MainlineRadarPage() {
  const [overview, data] = await Promise.all([
    getDashboardOverview(),
    getMainlineRadar()
  ]);

  return (
    <AppShell activeHref="/mainline-radar" generatedAt={overview.generated_at}>
      <MainlineRadar data={data} />
    </AppShell>
  );
}
