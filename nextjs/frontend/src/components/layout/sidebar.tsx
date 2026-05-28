"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { NAV_ITEMS } from "@/lib/constants";
import { cn } from "@/lib/utils";
import {
  Activity,
  TrendingUp,
  AlertTriangle,
  Network,
  DollarSign,
  Users,
  BarChart3,
  PieChart,
  Brain,
  Layers,
  Building2,
} from "lucide-react";

const iconMap: Record<string, React.ElementType> = {
  Activity,
  TrendingUp,
  AlertTriangle,
  Network,
  DollarSign,
  Users,
  BarChart3,
  PieChart,
  Brain,
  Layers,
  Building2,
};

export function Sidebar() {
  const pathname = usePathname();

  return (
    <motion.nav
      initial={{ x: -280 }}
      animate={{ x: 0 }}
      className="w-64 h-screen bg-bg-surface flex flex-col border-r border-border-default"
      role="navigation"
      aria-label="Main navigation"
    >
      <div className="p-6 border-b border-border-default">
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 bg-primary/20 rounded-lg flex items-center justify-center"
            aria-hidden="true"
          >
            <Activity className="w-6 h-6 text-primary" />
          </div>
          <div>
            <h1 className="font-bold text-lg text-text-primary">SicherGleis</h1>
            <p className="text-xs text-text-secondary">BahnSetu Pro</p>
          </div>
        </div>
      </div>

      <div className="flex-1 py-4 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map((item) => {
          const Icon = iconMap[item.icon];
          const isActive = pathname === item.href;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-6 py-2.5 text-sm transition-all duration-200",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:ring-inset",
                isActive
                  ? "text-primary bg-primary/10 border-r-2 border-primary"
                  : "text-text-secondary hover:text-text-primary hover:bg-bg-elevated"
              )}
              aria-current={isActive ? "page" : undefined}
            >
              <Icon className="w-5 h-5 shrink-0" aria-hidden="true" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </div>

      <div className="p-4 border-t border-border-default">
        <p className="text-xs text-text-muted">v3.0.0 &copy; 2026 SicherGleis</p>
      </div>
    </motion.nav>
  );
}