"use client";

import { cn } from "@/lib/utils";

interface CardProps {
  children: React.ReactNode;
  className?: string;
}

export function Card({ children, className }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-lg border border-border-default bg-bg-surface p-6",
        className
      )}
    >
      {children}
    </div>
  );
}