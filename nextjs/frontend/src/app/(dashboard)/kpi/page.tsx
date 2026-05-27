"use client";

import { KpiCard } from "@/components/dashboard/kpi-card";
import { GlassPanel } from "@/components/dashboard/glass-panel";
import { BarChart } from "@/components/charts/bar-chart";
import {
  Activity, Users, Wifi, AlertTriangle, Shield, Clock,
  BarChart3, TrendingUp, Zap, Target, Thermometer, Database
} from "lucide-react";

const comparisonData = [
  { name: "Gates", current: 42, previous: 38 },
  { name: "Sync %", current: 94.2, previous: 91.5 },
  { name: "Passengers", current: 12400, previous: 11400 },
  { name: "Alerts", current: 2, previous: 5 },
  { name: "Uptime %", current: 99.97, previous: 99.92 },
  { name: "Response ms", current: 12, previous: 18 },
];

export default function KPIPage() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        <KpiCard label="Active Gates" value="42/50" trend="up" trendValue="+2%" icon={Activity} color="emerald" progress={84} />
        <KpiCard label="Sync Health" value="94.2%" trend="up" trendValue="+0.5%" icon={Wifi} color="cyan" progress={94} />
        <KpiCard label="Passengers" value="12.4K" trend="up" trendValue="+8%" icon={Users} color="fuchsia" progress={62} />
        <KpiCard label="Active Alerts" value={2} trend="down" trendValue="-3" icon={AlertTriangle} color="amber" progress={20} />
        <KpiCard label="Risk Level" value="Low" trend="neutral" icon={Shield} color="emerald" progress={85} />
        <KpiCard label="Uptime" value="99.97%" trend="up" trendValue="+0.05%" icon={Clock} color="cyan" progress={99} />
        <KpiCard label="Avg Response" value="1.2s" trend="up" trendValue="-0.3s" icon={Zap} color="fuchsia" progress={88} />
        <KpiCard label="Accuracy" value="98.4%" trend="up" trendValue="+0.7%" icon={Target} color="emerald" progress={98} />
        <KpiCard label="Throughput" value="2.4K/s" trend="up" trendValue="+12%" icon={BarChart3} color="cyan" progress={72} />
        <KpiCard label="Efficiency" value="87%" trend="up" trendValue="+3%" icon={TrendingUp} color="fuchsia" progress={87} />
        <KpiCard label="Temp Sensors" value="23.4°C" trend="neutral" icon={Thermometer} color="amber" progress={65} />
        <KpiCard label="Data Volume" value="4.2TB" trend="up" trendValue="+8%" icon={Database} color="emerald" progress={55} />
      </div>

      <GlassPanel icon={BarChart3} title="Current vs Previous Period">
        <BarChart
          data={comparisonData}
          height={320}
          stacked={false}
          series={[
            { key: "current", color: "#f59e0b" },
            { key: "previous", color: "rgba(245,158,11,0.3)" },
          ]}
        />
      </GlassPanel>
    </div>
  );
}