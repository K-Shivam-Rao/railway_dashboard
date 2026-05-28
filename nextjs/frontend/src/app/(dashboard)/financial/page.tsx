"use client";

import { useState } from "react";
import { GlassPanel } from "@/components/dashboard/glass-panel";
import { KpiCard } from "@/components/dashboard/kpi-card";
import { AreaChart } from "@/components/charts/area-chart";
import { LineChart } from "@/components/charts/line-chart";
import { DollarSign, TrendingUp, TrendingDown, Briefcase } from "lucide-react";

const scenarios = [
  { label: "Base", value: "base" },
  { label: "Optimistic", value: "optimistic" },
  { label: "Pessimistic", value: "pessimistic" },
] as const;

const baseData = [
  { name: "Q1", revenue: 850, cost: 420 },
  { name: "Q2", revenue: 920, cost: 440 },
  { name: "Q3", revenue: 1050, cost: 460 },
  { name: "Q4", revenue: 1180, cost: 480 },
  { name: "Q1'26", revenue: 1300, cost: 500 },
  { name: "Q2'26", revenue: 1450, cost: 520 },
  { name: "Q3'26", revenue: 1600, cost: 540 },
  { name: "Q4'26", revenue: 1750, cost: 560 },
];

const scenarioComparison = [
  { name: "Q1", optimistic: 920, base: 850, pessimistic: 780 },
  { name: "Q2", optimistic: 1050, base: 920, pessimistic: 830 },
  { name: "Q3", optimistic: 1200, base: 1050, pessimistic: 900 },
  { name: "Q4", optimistic: 1350, base: 1180, pessimistic: 1000 },
];

export default function FinancialPage() {
  const [scenario, setScenario] = useState<string>("base");

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard label="MRR" value="€284K" trend="up" trendValue="+12%" icon={DollarSign} color="emerald" />
        <KpiCard label="ARR" value="€3.4M" trend="up" trendValue="+15%" icon={TrendingUp} color="cyan" />
        <KpiCard label="Burn Rate" value="€185K" trend="down" trendValue="-5%" icon={TrendingDown} color="amber" />
        <KpiCard label="Rev/Employee" value="€142K" trend="up" trendValue="+8%" icon={Briefcase} color="fuchsia" />
      </div>

      <div className="flex gap-2 mb-2">
        {scenarios.map((s) => (
          <button
            key={s.value}
            onClick={() => setScenario(s.value)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              scenario === s.value
                ? "bg-primary text-black"
                : "bg-bg-surface text-text-secondary hover:text-text-primary border border-border-default"
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <GlassPanel icon={TrendingUp} title={`Revenue Projection (${scenario})`}>
          <AreaChart
            data={baseData.map((d) => ({ name: d.name, revenue: d.revenue, cost: d.cost }))}
            series={[
              { key: "revenue", color: "#f59e0b", label: "Revenue" },
              { key: "cost", color: "#ef4444", label: "Cost" },
            ]}
            height={300}
          />
        </GlassPanel>
        <GlassPanel icon={TrendingUp} title="Scenario Comparison">
          <LineChart
            data={scenarioComparison}
            series={[
              { key: "optimistic", color: "#10b981" },
              { key: "base", color: "#f59e0b" },
              { key: "pessimistic", color: "#ef4444" },
            ]}
            height={300}
          />
        </GlassPanel>
      </div>
    </div>
  );
}