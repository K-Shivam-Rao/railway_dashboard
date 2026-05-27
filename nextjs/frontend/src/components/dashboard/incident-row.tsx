"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface IncidentRowProps {
  severity: "critical" | "warning" | "info";
  timestamp: string;
  station: string;
  category: string;
  description: string;
  resolved?: boolean;
}

const severityStyles = {
  critical: { border: "border-l-danger", bg: "bg-danger/5", dot: "bg-danger" },
  warning: { border: "border-l-warning", bg: "bg-warning/5", dot: "bg-warning" },
  info: { border: "border-l-secondary", bg: "bg-secondary/5", dot: "bg-secondary" },
};

export function IncidentRow({
  severity,
  timestamp,
  station,
  category,
  description,
  resolved = false,
}: IncidentRowProps) {
  const style = severityStyles[severity];

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      className={cn(
        "group flex items-start gap-4 border-l-2 pl-4 py-3 rounded-r-lg",
        "hover:bg-bg-elevated transition-all duration-200 hover:translate-x-0.5",
        style.border,
        style.bg
      )}
    >
      <div className={cn("w-2 h-2 rounded-full mt-1.5 shrink-0", style.dot)} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 text-xs text-text-muted mb-1">
          <time dateTime={timestamp}>{timestamp}</time>
          <span>•</span>
          <span>{station}</span>
          <span>•</span>
          <span className="font-medium">{category}</span>
          {resolved && (
            <span className="text-success text-xs">Resolved</span>
          )}
        </div>
        <p className="text-sm text-text-secondary truncate group-hover:text-text-primary transition-colors">
          {description}
        </p>
      </div>
    </motion.div>
  );
}