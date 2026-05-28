"use client";

import { cn } from "@/lib/utils";

interface BadgeProps {
  variant?: "normal" | "warning" | "critical" | "success";
  children: React.ReactNode;
  className?: string;
}

const variantStyles = {
  normal: "bg-secondary/20 text-secondary border-secondary/30",
  warning: "bg-warning/20 text-warning border-warning/30",
  critical: "bg-danger/20 text-danger border-danger/30",
  success: "bg-success/20 text-success border-success/30",
};

export function Badge({ variant = "normal", children, className }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium border",
        variantStyles[variant],
        className
      )}
    >
      {children}
    </span>
  );
}