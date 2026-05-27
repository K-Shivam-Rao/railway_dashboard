"use client";

import { cn } from "@/lib/utils";

interface StatusDotProps {
  status: "normal" | "warning" | "critical";
  className?: string;
  pulse?: boolean;
}

export function StatusDot({ status, className, pulse = true }: StatusDotProps) {
  return (
    <span className={cn("relative inline-flex", className)}>
      <span
        className={cn(
          "w-2 h-2 rounded-full",
          status === "normal" && "bg-success",
          status === "warning" && "bg-warning",
          status === "critical" && "bg-danger",
        )}
      />
      {pulse && (
        <span
          className={cn(
            "absolute inset-0 rounded-full animate-ping opacity-75",
            status === "normal" && "bg-success",
            status === "warning" && "bg-warning",
            status === "critical" && "bg-danger",
          )}
        />
      )}
    </span>
  );
}