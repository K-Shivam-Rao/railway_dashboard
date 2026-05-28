"use client";

import { GlassPanel } from "@/components/dashboard/glass-panel";
import { StatusBadge } from "@/components/dashboard/status-badge";
import { Network, Table2 } from "lucide-react";

const stations = [
  { name: "Berlin Hbf", gates: "48/50", sync: "97.2%", passengers: "12.4K", alerts: 0, status: "normal" as const },
  { name: "Hamburg", gates: "32/35", sync: "94.5%", passengers: "8.1K", alerts: 2, status: "warning" as const },
  { name: "Munich", gates: "28/30", sync: "98.1%", passengers: "6.8K", alerts: 0, status: "normal" as const },
  { name: "Frankfurt", gates: "22/25", sync: "91.3%", passengers: "5.2K", alerts: 1, status: "warning" as const },
  { name: "Cologne", gates: "18/20", sync: "88.7%", passengers: "4.0K", alerts: 3, status: "critical" as const },
  { name: "Stuttgart", gates: "15/15", sync: "99.5%", passengers: "3.1K", alerts: 0, status: "normal" as const },
  { name: "Düsseldorf", gates: "20/22", sync: "96.8%", passengers: "3.8K", alerts: 1, status: "normal" as const },
  { name: "Leipzig", gates: "10/12", sync: "95.2%", passengers: "2.5K", alerts: 0, status: "normal" as const },
];

export default function NetworkPage() {
  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-border-default bg-bg-surface p-6 flex items-center justify-center" style={{ height: 300 }}>
        <div className="text-center space-y-3">
          <Network className="w-12 h-12 text-text-muted mx-auto" />
          <p className="text-text-secondary">3D Germany Map (Three.js)</p>
          <p className="text-text-muted text-sm">50 station markers — height by traffic, color by health</p>
        </div>
      </div>

      <GlassPanel icon={Table2} title="Station Performance Matrix">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border-default">
                <th className="text-left py-3 px-2 text-text-muted font-medium">Station</th>
                <th className="text-left py-3 px-2 text-text-muted font-medium">Gates</th>
                <th className="text-left py-3 px-2 text-text-muted font-medium">Sync Health</th>
                <th className="text-left py-3 px-2 text-text-muted font-medium">Passengers</th>
                <th className="text-left py-3 px-2 text-text-muted font-medium">Alerts</th>
                <th className="text-left py-3 px-2 text-text-muted font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {stations.map((s) => (
                <tr key={s.name} className="border-b border-border-default/50 hover:bg-bg-elevated transition-colors">
                  <td className="py-3 px-2 text-text-primary font-medium">{s.name}</td>
                  <td className="py-3 px-2 text-text-secondary tabular-nums">{s.gates}</td>
                  <td className="py-3 px-2 text-text-secondary tabular-nums">{s.sync}</td>
                  <td className="py-3 px-2 text-text-secondary tabular-nums">{s.passengers}</td>
                  <td className="py-3 px-2 text-text-secondary tabular-nums">{s.alerts}</td>
                  <td className="py-3 px-2"><StatusBadge status={s.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </GlassPanel>
    </div>
  );
}