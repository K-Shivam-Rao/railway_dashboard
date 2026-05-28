"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

interface LoadingSkeletonProps {
  variant?: "card" | "chart" | "text" | "table" | "kpi-grid";
  count?: number;
  className?: string;
}

export function LoadingSkeleton({
  variant = "card",
  count = 1,
  className,
}: LoadingSkeletonProps) {
  if (variant === "kpi-grid") {
    return (
      <div className={cn("grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4", className)}>
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className="bg-bg-surface rounded-lg border border-border-default p-5 space-y-3">
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-8 w-24" />
            <Skeleton className="h-3 w-16" />
          </div>
        ))}
      </div>
    );
  }

  if (variant === "card") {
    return (
      <div className={cn("space-y-3", className)}>
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className="bg-bg-surface rounded-lg border border-border-default p-5">
            <Skeleton className="h-3 w-24 mb-3" />
            <Skeleton className="h-8 w-32 mb-2" />
            <Skeleton className="h-3 w-20" />
          </div>
        ))}
      </div>
    );
  }

  if (variant === "chart") {
    return (
      <div className={cn("bg-bg-surface rounded-lg border border-border-default p-5", className)}>
        <Skeleton className="h-4 w-32 mb-4" />
        <Skeleton className="h-[280px] w-full rounded-lg" />
      </div>
    );
  }

  if (variant === "table") {
    return (
      <div className={cn("bg-bg-surface rounded-lg border border-border-default p-5 space-y-3", className)}>
        <Skeleton className="h-4 w-48" />
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className="flex gap-4">
            <Skeleton className="h-4 flex-1" />
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-4 w-16" />
            <Skeleton className="h-4 w-24" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className={cn("space-y-2", className)}>
      {Array.from({ length: count }).map((_, i) => (
        <Skeleton key={i} className="h-4 w-full" />
      ))}
    </div>
  );
}