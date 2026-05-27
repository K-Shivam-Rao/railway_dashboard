"use client";

import { motion } from "framer-motion";
import { GlassPanel } from "@/components/dashboard/glass-panel";
import { KpiCard } from "@/components/dashboard/kpi-card";
import { PieChart } from "@/components/charts/pie-chart";
import { BarChart } from "@/components/charts/bar-chart";
import { DollarSign, TrendingUp, TrendingDown, Users } from "lucide-react";

const segments = [
  { name: "High-Value", value: 12, color: "#f59e0b" },
  { name: "At Risk", value: 5, color: "#ef4444" },
  { name: "Growing", value: 8, color: "#10b981" },
  { name: "New (30d)", value: 3, color: "#06b6d4" },
];

const mrrBySegment = [
  { name: "High-Value", value: 185000 },
  { name: "Growing", value: 62000 },
  { name: "At Risk", value: 28000 },
  { name: "New", value: 9000 },
];

const contractHealth = [
  { name: "Healthy", value: 18, color: "#10b981" },
  { name: "Warning", value: 7, color: "#f59e0b" },
  { name: "Critical", value: 3, color: "#ef4444" },
];

const renewals = [
  { client: "Deutsche Bahn", value: 320000, date: "Jul 2026" },
  { client: "Swiss Rail", value: 180000, date: "Sep 2026" },
  { client: "ÖBB", value: 150000, date: "Nov 2026" },
  { client: "SNCF", value: 280000, date: "Jan 2027" },
  { client: "NS", value: 120000, date: "Mar 2027" },
];

export default function CustomerPage() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <KpiCard label="High-Value" value={12} trend="up" trendValue="+2" icon={TrendingUp} color="emerald" />
        <KpiCard label="At Risk" value={5} trend="down" trendValue="-1" icon={TrendingDown} color="amber" />
        <KpiCard label="Growing" value={8} trend="up" trendValue="+3" icon={TrendingUp} color="cyan" />
        <KpiCard label="New (30d)" value={3} trend="up" trendValue="+1" icon={Users} color="fuchsia" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <GlassPanel icon={DollarSign} title="MRR by Segment">
          <BarChart data={mrrBySegment} height={280} color="#f59e0b" />
        </GlassPanel>
        <GlassPanel icon={Users} title="Contract Health">
          <PieChart data={contractHealth} height={280} />
        </GlassPanel>
      </div>

      <GlassPanel icon={TrendingUp} title="Renewal Forecast">
        <div className="space-y-3">
          {renewals.map((r, i) => (
            <motion.div
              key={r.client}
              initial={{ width: 0 }}
              animate={{ width: "100%" }}
              transition={{ delay: i * 0.1 }}
              className="flex items-center gap-4"
            >
              <span className="w-28 text-sm text-text-primary font-medium shrink-0">{r.client}</span>
              <div className="flex-1 h-8 bg-bg-elevated rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${(r.value / 320000) * 100}%` }}
                  transition={{ delay: i * 0.15, duration: 0.6 }}
                  className="h-full bg-primary/40 rounded-full flex items-center px-3"
                >
                  <span className="text-xs text-white font-medium">€{(r.value / 1000).toFixed(0)}K</span>
                </motion.div>
              </div>
              <span className="w-20 text-xs text-text-muted text-right">{r.date}</span>
            </motion.div>
          ))}
        </div>
      </GlassPanel>
    </div>
  );
}