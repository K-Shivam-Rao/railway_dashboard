import { LoadingSkeleton } from "@/components/dashboard/loading-skeleton";

export default function DashboardLoading() {
  return (
    <div className="space-y-6">
      <LoadingSkeleton variant="kpi-grid" count={5} />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <LoadingSkeleton variant="chart" />
        </div>
        <LoadingSkeleton variant="chart" />
      </div>
    </div>
  );
}