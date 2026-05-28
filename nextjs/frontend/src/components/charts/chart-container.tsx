"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

interface ChartContainerProps {
  title?: string;
  children: React.ReactNode;
  className?: string;
  isLoading?: boolean;
  isEmpty?: boolean;
  error?: string | null;
  height?: number;
}

export function ChartContainer({
  title,
  children,
  className,
  isLoading,
  isEmpty,
  error,
  height = 300,
}: ChartContainerProps) {
  if (error) {
    return (
      <div
        className={cn(
          "flex items-center justify-center rounded-lg border border-border-default bg-bg-surface",
          className
        )}
        style={{ height }}
      >
        <p className="text-sm text-danger">{error}</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className={cn("space-y-2", className)}>
        {title && <Skeleton className="h-4 w-32" />}
        <div style={{ height }}>
          <Skeleton className="rounded-lg h-full w-full" />
        </div>
      </div>
    );
  }

  if (isEmpty) {
    return (
      <div
        className={cn(
          "flex items-center justify-center rounded-lg border border-border-default bg-bg-surface",
          className
        )}
        style={{ height }}
      >
        <p className="text-sm text-text-muted">No data available</p>
      </div>
    );
  }

  return (
    <div className={cn("w-full", className)} style={{ height }}>
      {children}
    </div>
  );
}