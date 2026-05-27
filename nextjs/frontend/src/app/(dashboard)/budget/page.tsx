"use client";

import { GlassPanel } from "@/components/dashboard/glass-panel";
import { KpiCard } from "@/components/dashboard/kpi-card";
import { WaterfallChart } from "@/components/charts/waterfall-chart";
import { AreaChart } from "@/components/charts/area-chart";
import { LineChart } from "@/components/charts/line-chart";
import { DollarSign, TrendingUp, PiggyBank, BarChart3 } from "lucide-react";

const budgetVariance = [
  { name: "Budget", value: 12000000, isTotal: true },
  { name: "Infrastructure", value: -3500000 },
  { name: "Operations", value: -2800000 },
  { name: "R&D", value: -1800000 },
  { name: "Personnel", value: -2200000 },
  { name: "Marketing", value: -600000 },
  { name: "Remaining", value: 1700000, isTotal: true },
];

const roiData = [
  { name: "2024", value: 2.1 },
  { name: "2025", value: 3.4 },
  { name: "2026", value: 5.2 },
  { name: "2027", value: 7.8 },
  { name: "2028", value: 11.3 },
];

const scenarioProjections = [
  { name: "2025", optimistic: 4.2, base: 3.4, pessimistic: 2.8 },
  { name: "2026", optimistic: 6.8, base: 5.2, pessimistic: 4.0 },
  { name: "2027", optimistic: 10.5, base: 7.8, pessimistic: 5.8 },
  { name: "2028", optimistic: 15.0, base: 11.3, pessimistic: 8.2 },
  { name: "2029", optimistic: 21.0, base: 15.5, pessimistic: 11.0 },
];

export default function BudgetPage() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard label="Total Budget" value="€12.0M" icon={DollarSign} color="emerald" />
        <KpiCard label="Spent" value="€10.3M" trend="up" trendValue="86%" icon={TrendingUp} color="amber" progress={86} />
        <KpiCard label="Remaining" value="€1.7M" trend="down" trendValue="14%" icon={PiggyBank} color="cyan" progress={14} />
        <KpiCard label="ROI (YTD)" value="3.4x" trend="up" trendValue="+62%" icon={BarChart3} color="fuchsia" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <GlassPanel icon={DollarSign} title="Budget vs Actual">
          <WaterfallChart data={budgetVariance} height={320} />
        </GlassPanel>
        <GlassPanel icon={TrendingUp} title="ROI Projection">
          <AreaChart
            data={roiData.map((d) => ({ name: d.name, value: d.value }))}
            height={320}
          />
        </GlassPanel>
      </div>

      <GlassPanel icon={BarChart3} title="Scenario Projections (ROI Multiples)">
        <LineChart
          data={scenarioProjections}
          series={[
            { key: "optimistic", color: "#10b981" },
            { key: "base", color: "#f59e0b" },
            { key: "pessimistic", color: "#ef4444" },
          ]}
          height={300}
        />
      </GlassPanel>
    </div>
  );
}