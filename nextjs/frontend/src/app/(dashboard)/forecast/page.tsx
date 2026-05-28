"use client";

import { GaugeChart } from "@/components/charts/gauge-chart";
import { GlassPanel } from "@/components/dashboard/glass-panel";
import { KpiCard } from "@/components/dashboard/kpi-card";
import { SankeyChart } from "@/components/charts/sankey-chart";
import { AreaChart } from "@/components/charts/area-chart";
import { TrendingUp, Shield, Target, Wrench } from "lucide-react";

const forecastData = [
  { name: "Week 1", predicted: 120, low: 100, high: 140 },
  { name: "Week 2", predicted: 135, low: 110, high: 155 },
  { name: "Week 3", predicted: 128, low: 105, high: 148 },
  { name: "Week 4", predicted: 150, low: 125, high: 170 },
];

const flowNodes = [
  { name: "Berlin Hbf" },
  { name: "Hamburg" },
  { name: "Munich" },
  { name: "Frankfurt" },
];

const flowLinks = [
  { source: 0, target: 1, value: 3200 },
  { source: 0, target: 2, value: 2800 },
  { source: 0, target: 3, value: 1900 },
  { source: 1, target: 2, value: 1500 },
  { source: 2, target: 3, value: 1200 },
];

export default function ForecastPage() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard label="Risk Score" value={23} trend="down" trendValue="-3" icon={Shield} color="emerald" progress={77} />
        <KpiCard label="Confidence" value="87.3%" trend="up" trendValue="+2.1%" icon={TrendingUp} color="cyan" progress={87} />
        <KpiCard label="Prediction Accuracy" value="94.1%" trend="up" trendValue="+1.2%" icon={Target} color="fuchsia" progress={94} />
        <KpiCard label="Maintenance Due" value={12} trend="up" trendValue="+4" icon={Wrench} color="amber" progress={40} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <GlassPanel icon={Shield} title="Risk Assessment">
          <div className="flex items-center justify-center py-4">
            <GaugeChart value={23} label="Anomaly Risk Score" size={220} />
          </div>
        </GlassPanel>
        <GlassPanel icon={TrendingUp} title="Passenger Flow">
          <div className="flex justify-center">
            <SankeyChart nodes={flowNodes} links={flowLinks} height={300} />
          </div>
        </GlassPanel>
      </div>

      <GlassPanel icon={Target} title="Passenger Forecast with Confidence Bands">
        <AreaChart
          data={forecastData.map((d) => ({
            name: d.name,
            predicted: d.predicted,
            "lower bound": d.low,
            "upper bound": d.high,
          }))}
          series={[
            { key: "upper bound", color: "rgba(59,130,246,0.15)", label: "Upper" },
            { key: "predicted", color: "#3b82f6", label: "Predicted" },
            { key: "lower bound", color: "rgba(59,130,246,0.15)", label: "Lower" },
          ]}
          height={300}
        />
      </GlassPanel>
    </div>
  );
}