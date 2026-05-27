"use client";

import { GlassPanel } from "@/components/dashboard/glass-panel";
import { ScatterChart } from "@/components/charts/scatter-chart";
import { AreaChart } from "@/components/charts/area-chart";
import { HeatmapChart } from "@/components/charts/heatmap-chart";
import { Brain, Activity, Thermometer } from "lucide-react";

const anomalyData = [
  { x: 10, y: 25, z: 100 },
  { x: 15, y: 30, z: 120 },
  { x: 20, y: 22, z: 90 },
  { x: 25, y: 35, z: 150 },
  { x: 30, y: 28, z: 80 },
  { x: 35, y: 45, z: 200, name: "Anomaly" },
  { x: 40, y: 32, z: 110 },
  { x: 45, y: 55, z: 250, name: "Anomaly" },
  { x: 50, y: 38, z: 130 },
  { x: 55, y: 42, z: 140 },
  { x: 60, y: 65, z: 300, name: "Anomaly" },
];

const decompositionData = [
  { name: "Jan", trend: 100, seasonal: 95, residual: 102 },
  { name: "Feb", trend: 105, seasonal: 110, residual: 99 },
  { name: "Mar", trend: 110, seasonal: 105, residual: 106 },
  { name: "Apr", trend: 108, seasonal: 95, residual: 104 },
  { name: "May", trend: 115, seasonal: 120, residual: 97 },
  { name: "Jun", trend: 120, seasonal: 125, residual: 103 },
  { name: "Jul", trend: 125, seasonal: 130, residual: 99 },
  { name: "Aug", trend: 130, seasonal: 128, residual: 105 },
];

const correlationData = [
  { x: "PSD", y: "Gate 1", value: 95 },
  { x: "PSD", y: "Gate 2", value: 88 },
  { x: "PSD", y: "Gate 3", value: 92 },
  { x: "Sync", y: "Gate 1", value: 78 },
  { x: "Sync", y: "Gate 2", value: 85 },
  { x: "Sync", y: "Gate 3", value: 72 },
  { x: "Power", y: "Gate 1", value: 45 },
  { x: "Power", y: "Gate 2", value: 52 },
  { x: "Power", y: "Gate 3", value: 48 },
  { x: "Temp", y: "Gate 1", value: 35 },
  { x: "Temp", y: "Gate 2", value: 42 },
  { x: "Temp", y: "Gate 3", value: 38 },
];

export default function AnalyticsPage() {
  return (
    <div className="space-y-6">
      <div className="flex gap-2 mb-2">
        {["Isolation Forest", "Autoencoder", "LOF", "SVM"].map((method) => (
          <button
            key={method}
            className="px-4 py-2 rounded-lg text-sm font-medium bg-bg-surface text-text-secondary hover:text-text-primary border border-border-default hover:bg-bg-elevated transition-all"
          >
            {method}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <GlassPanel icon={Brain} title="Anomaly Detection">
          <ScatterChart data={anomalyData} height={300} />
          <div className="flex gap-3 mt-2">
            <span className="flex items-center gap-1 text-xs text-text-muted">
              <span className="w-2 h-2 rounded-full bg-primary" /> Normal
            </span>
            <span className="flex items-center gap-1 text-xs text-danger">
              <span className="w-2 h-2 rounded-full bg-danger" /> Anomaly
            </span>
          </div>
        </GlassPanel>
        <GlassPanel icon={Activity} title="Time-series Decomposition">
          <AreaChart
            data={decompositionData}
            series={[
              { key: "trend", color: "#f59e0b", label: "Trend" },
              { key: "seasonal", color: "#06b6d4", label: "Seasonal" },
              { key: "residual", color: "#d946ef", label: "Residual" },
            ]}
            height={300}
          />
        </GlassPanel>
      </div>

      <GlassPanel icon={Thermometer} title="Sensor Correlation Heatmap">
        <HeatmapChart data={correlationData} height={250} />
      </GlassPanel>
    </div>
  );
}