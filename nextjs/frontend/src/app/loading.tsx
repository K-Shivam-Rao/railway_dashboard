import { Skeleton } from "@/components/ui/skeleton";

export default function Loading() {
  return (
    <div className="space-y-6 p-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="bg-bg-surface rounded-lg border border-border-default p-5 space-y-3">
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-8 w-24" />
            <Skeleton className="h-3 w-16" />
          </div>
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-bg-surface rounded-lg border border-border-default p-5">
          <Skeleton className="h-4 w-32 mb-4" />
          <Skeleton className="h-[280px] w-full rounded-lg" />
        </div>
        <div className="bg-bg-surface rounded-lg border border-border-default p-5">
          <Skeleton className="h-4 w-24 mb-4" />
          <Skeleton className="h-[280px] w-full rounded-lg" />
        </div>
      </div>
    </div>
  );
}