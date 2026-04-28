import { AppShell } from "@/components/dashboard/dashboard-shell";
import { JobsMonitor } from "@/components/jobs/jobs-monitor";
import { getComputeJobs, getDashboardOverview } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function JobsPage() {
  const [overview, jobs] = await Promise.all([
    getDashboardOverview(),
    getComputeJobs(30)
  ]);

  return (
    <AppShell activeHref="/data/jobs" generatedAt={overview.generated_at}>
      <JobsMonitor initialJobs={jobs} />
    </AppShell>
  );
}
