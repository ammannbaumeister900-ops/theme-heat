import { DashboardShell } from "@/components/dashboard/dashboard-shell";
import { getDashboardOverview } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const overview = await getDashboardOverview();

  return <DashboardShell data={overview} />;
}
