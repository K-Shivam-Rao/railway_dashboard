"use client";

import { GlassPanel } from "@/components/dashboard/glass-panel";
import { KpiCard } from "@/components/dashboard/kpi-card";
import { RadarChart } from "@/components/charts/radar-chart";
import { Layers, Shield, Zap, Server, Cpu } from "lucide-react";

const systemNodes = [
  { id: "ingest", label: "Data Ingest", status: "healthy" as const, x: 50, y: 50 },
  { id: "process", label: "Stream Process", status: "healthy" as const, x: 200, y: 50 },
  { id: "store", label: "Time-Series DB", status: "healthy" as const, x: 350, y: 50 },
  { id: "analyze", label: "Analytics Engine", status: "healthy" as const, x: 500, y: 50 },
  { id: "alert", label: "Alert Manager", status: "warning" as const, x: 350, y: 180 },
  { id: "viz", label: "Visualization", status: "healthy" as const, x: 500, y: 180 },
  { id: "api", label: "API Gateway", status: "healthy" as const, x: 200, y: 180 },
];

const edges = [
  ["ingest", "process"],
  ["process", "store"],
  ["store", "analyze"],
  ["analyze", "viz"],
  ["analyze", "alert"],
  ["process", "api"],
  ["api", "viz"],
];

const vulnerabilityData = [
  { subject: "Network", value: 85 },
  { subject: "Auth", value: 72 },
  { subject: "Data", value: 90 },
  { subject: "API", value: 78 },
  { subject: "Physical", value: 65 },
  { subject: "Supply", value: 82 },
];

export default function VizPage() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard label="System Health" value="98.2%" trend="up" trendValue="+0.5%" icon={Shield} color="emerald" progress={98} />
        <KpiCard label="Active Services" value="7/7" icon={Server} color="cyan" />
        <KpiCard label="Data Throughput" value="2.4K/s" trend="up" trendValue="+12%" icon={Zap} color="fuchsia" />
        <KpiCard label="CPU Load" value="43%" trend="up" trendValue="+5%" icon={Cpu} color="amber" progress={43} />
      </div>

      <GlassPanel icon={Layers} title="System Architecture">
        <svg viewBox="0 0 600 240" className="w-full" style={{ height: 240 }}>
          {edges.map(([from, to]) => {
            const source = systemNodes.find((n) => n.id === from)!;
            const target = systemNodes.find((n) => n.id === to)!;
            return (
              <line
                key={`${from}-${to}`}
                x1={source.x}
                y1={source.y}
                x2={target.x}
                y2={target.y}
                stroke="rgba(241,240,245,0.1)"
                strokeWidth={2}
              />
            );
          })}
          {systemNodes.map((node) => (
            <g key={node.id}>
              <rect
                x={node.x - 60}
                y={node.y - 18}
                width={120}
                height={36}
                rx={8}
                fill={
                  node.status === "healthy"
                    ? "rgba(16,185,129,0.15)"
                    : "rgba(245,158,11,0.15)"
                }
                stroke={
                  node.status === "healthy"
                    ? "rgba(16,185,129,0.4)"
                    : "rgba(245,158,11,0.4)"
                }
                strokeWidth={1}
              />
              <text
                x={node.x}
                y={node.y + 4}
                textAnchor="middle"
                fill="#f1f0f5"
                fontSize={11}
              >
                {node.label}
              </text>
            </g>
          ))}
        </svg>
      </GlassPanel>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <GlassPanel icon={Shield} title="Vulnerability Assessment">
          <RadarChart
            data={vulnerabilityData}
            height={300}
            series={[{ key: "value", color: "#f59e0b" }]}
          />
        </GlassPanel>
        <GlassPanel icon={Zap} title="Simulation Results">
          <div className="space-y-3">
            {[
              { test: "DDoS Attack", result: "Mitigated", status: "success" as const },
              { test: "Sensor Failure", result: "Failover OK", status: "success" as const },
              { test: "Network Partition", result: "Degraded", status: "warning" as const },
              { test: "Power Outage", result: "UPS Active", status: "success" as const },
              { test: "Data Breach", result: "Blocked", status: "success" as const },
            ].map((s) => (
              <div key={s.test} className="flex items-center justify-between py-2 border-b border-border-default/50 last:border-0">
                <span className="text-sm text-text-primary">{s.test}</span>
                <span className={`text-xs font-medium px-2 py-1 rounded-full ${
                  s.status === "success" ? "bg-success/20 text-success" : "bg-warning/20 text-warning"
                }`}>
                  {s.result}
                </span>
              </div>
            ))}
          </div>
        </GlassPanel>
      </div>
    </div>
  );
}