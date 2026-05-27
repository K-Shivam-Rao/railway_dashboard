"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { useTilt } from "@/hooks/use-tilt";

interface KpiCardProps {
  label: string;
  value: string | number;
  format?: "number" | "currency" | "percentage";
  trend?: "up" | "down" | "neutral";
  trendValue?: string;
  icon?: React.ElementType;
  color?: "emerald" | "amber" | "fuchsia" | "cyan";
  progress?: number;
  delay?: number;
  tilt?: boolean;
}

const colorStyles = {
  emerald: { bg: "bg-success/20", text: "text-success", bar: "bg-success" },
  amber: { bg: "bg-warning/20", text: "text-warning", bar: "bg-warning" },
  fuchsia: { bg: "bg-accent-fuchsia/20", text: "text-accent-fuchsia", bar: "bg-accent-fuchsia" },
  cyan: { bg: "bg-secondary/20", text: "text-secondary", bar: "bg-secondary" },
};

export function KpiCard({
  label,
  value,
  trend = "neutral",
  trendValue,
  icon: Icon,
  color = "emerald",
  progress,
  delay = 0,
  tilt = false,
}: KpiCardProps) {
  const styles = colorStyles[color];
  const tiltHook = useTilt();

  const tiltHandlers = tilt
    ? {
        ref: tiltHook.ref,
        onMouseMove: tiltHook.handleMouseMove,
        onMouseLeave: tiltHook.handleMouseLeave,
      }
    : {};

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.3 }}
      className="group relative overflow-hidden rounded-lg border border-border-default bg-bg-surface p-5 hover:border-border-strong transition-colors cursor-default"
      style={{ transformStyle: "preserve-3d", transition: "transform 0.2s ease-out" }}
      {...tiltHandlers}
    >
      {progress !== undefined && (
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-bg-elevated">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${Math.min(progress, 100)}%` }}
            transition={{ delay: delay + 0.3, duration: 0.6, ease: "easeOut" }}
            className={cn("h-full rounded-full", styles.bar)}
          />
        </div>
      )}

      <div className="flex items-start justify-between mb-3">
        <span className="text-xs font-medium text-text-secondary uppercase tracking-wider">
          {label}
        </span>
        {Icon && (
          <div className={cn("rounded-lg p-2", styles.bg)}>
            <Icon className={cn("w-4 h-4", styles.text)} />
          </div>
        )}
      </div>

      <div className="flex items-baseline gap-2">
        <span className="text-2xl font-bold text-text-primary tabular-nums">
          {value}
        </span>
        {trendValue && trend !== "neutral" && (
          <span
            className={cn(
              "text-xs font-medium",
              trend === "up" ? "text-success" : "text-danger"
            )}
          >
            {trend === "up" ? "▲" : "▼"} {trendValue}
          </span>
        )}
      </div>
    </motion.div>
  );
}