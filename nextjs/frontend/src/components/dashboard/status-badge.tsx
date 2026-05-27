"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface StatusBadgeProps {
  status: "normal" | "warning" | "critical";
  label?: string;
  className?: string;
}

const statusConfig = {
  normal: {
    dot: "bg-success",
    ring: "border-success",
    pulse: "animate-pulse-ring border-success",
    label: "Normal",
  },
  warning: {
    dot: "bg-warning",
    ring: "border-warning",
    pulse: "animate-pulse-ring border-warning",
    label: "Warning",
  },
  critical: {
    dot: "bg-danger",
    ring: "border-danger",
    pulse: "animate-pulse-ring border-danger",
    label: "Critical",
  },
};

export function StatusBadge({
  status,
  label,
  className,
}: StatusBadgeProps) {
  const config = statusConfig[status];

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div className="relative flex items-center justify-center w-3 h-3">
        <div
          className={cn(
            "absolute inset-0 rounded-full border-2",
            config.pulse
          )}
        />
        <div
          className={cn(
            "w-2 h-2 rounded-full",
            config.dot
          )}
        />
      </div>
      <span className="text-xs font-medium text-text-secondary">
        {label || config.label}
      </span>
    </div>
  );
}