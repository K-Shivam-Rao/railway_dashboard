"use client";

import { Activity, Users, AlertCircle, BarChart3, Wifi } from "lucide-react";
import { KpiCard } from "@/components/dashboard/kpi-card";
import { GlassPanel } from "@/components/dashboard/glass-panel";
import { StatusBadge } from "@/components/dashboard/status-badge";
import { AreaChart } from "@/components/charts/area-chart";
import { LineChart } from "@/components/charts/line-chart";
import { BarChart } from "@/components/charts/bar-chart";
import { useAppStore } from "@/stores/app-store";

const syncData = [
  { name: "00:00", value: 95 }, { name: "04:00", value: 97 },
  { name: "08:00", value: 92 }, { name: "12:00", value: 94 },
  { name: "16:00", value: 96 }, { name: "20:00", value: 93 },
];

const psdUsage = [
  { name: "Mon", value: 1200 }, { name: "Tue", value: 1350 },
  { name: "Wed", value: 1100 }, { name: "Thu", value: 1400 },
  { name: "Fri", value: 1550 }, { name: "Sat", value: 980 },
  { name: "Sun", value: 720 },
];

const gateStatus = [
  { name: "Active", value: 42 }, { name: "Standby", value: 5 },
  { name: "Maintenance", value: 3 },
];

export default function OpsPage() {
  const { systemStatus } = useAppStore();

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <KpiCard label="Active Gates" value={42} trend="up" trendValue="+2%" icon={Activity} color="emerald" progress={84} />
        <KpiCard label="Sync Health" value="94.2%" trend="up" trendValue="+0.5%" icon={Wifi} color="cyan" progress={94} />
        <KpiCard label="Passengers" value="12.4K" trend="up" trendValue="+8%" icon={Users} color="fuchsia" progress={62} />
        <KpiCard label="Alerts" value={2} trend="down" trendValue="-1" icon={AlertCircle} color="amber" progress={20} />
        <KpiCard label="Avg Response" value="1.2s" trend="up" trendValue="-0.3s" icon={BarChart3} color="emerald" progress={88} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <GlassPanel icon={Activity} title="PSD Usage (7-day)" badge={<StatusBadge status={systemStatus} />}>
            <AreaChart data={psdUsage} height={280} />
          </GlassPanel>
        </div>
        <GlassPanel icon={BarChart3} title="Gate Status">
          <BarChart data={gateStatus} height={280} color="#f59e0b" />
        </GlassPanel>
      </div>

      <GlassPanel icon={Wifi} title="Sync Over Time">
        <LineChart
          data={syncData}
          series={[{ key: "value", color: "#06b6d4" }]}
          height={220}
        />
      </GlassPanel>
    </div>
  );
}