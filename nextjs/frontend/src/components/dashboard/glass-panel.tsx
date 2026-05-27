"use client";

import { cn } from "@/lib/utils";

interface GlassPanelProps {
  icon?: React.ElementType;
  title?: string;
  badge?: React.ReactNode;
  actions?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export function GlassPanel({
  icon: Icon,
  title,
  badge,
  actions,
  children,
  className,
}: GlassPanelProps) {
  return (
    <div
      className={cn(
        "group relative rounded-xl border border-border-default bg-bg-glass backdrop-blur-xl",
        "hover:border-border-strong transition-all duration-300",
        "before:pointer-events-none before:absolute before:inset-0 before:rounded-xl",
        "before:opacity-0 group-hover:before:opacity-100",
        "before:bg-gradient-to-b before:from-white/[0.03] before:to-transparent",
        className
      )}
    >
      {(Icon || title || badge || actions) && (
        <div className="flex items-center gap-3 px-5 py-4 border-b border-border-default">
          {Icon && <Icon className="w-4 h-4 text-text-secondary" />}
          {title && (
            <h3 className="text-sm font-semibold text-text-primary flex-1">
              {title}
            </h3>
          )}
          {badge && <div className="flex-shrink-0">{badge}</div>}
          {actions && <div className="flex-shrink-0">{actions}</div>}
        </div>
      )}
      <div className="p-5">{children}</div>
    </div>
  );
}