"use client";

import { PieChart } from "@/components/charts/pie-chart";
import { AreaChart } from "@/components/charts/area-chart";
import { IncidentRow } from "@/components/dashboard/incident-row";
import { GlassPanel } from "@/components/dashboard/glass-panel";
import { AlertTriangle, Clock, Filter } from "lucide-react";

const severityData = [
  { name: "Critical", value: 12, color: "#ef4444" },
  { name: "Warning", value: 28, color: "#f59e0b" },
  { name: "Info", value: 45, color: "#06b6d4" },
];

const incidentsOverTime = [
  { name: "Mon", value: 5 }, { name: "Tue", value: 8 },
  { name: "Wed", value: 3 }, { name: "Thu", value: 6 },
  { name: "Fri", value: 10 }, { name: "Sat", value: 4 },
  { name: "Sun", value: 2 },
];

const recentIncidents = [
  { severity: "critical" as const, timestamp: "14:30", station: "Berlin Hbf", category: "PSD Malfunction", description: "Door 4B sensor timeout on platform 3", resolved: false },
  { severity: "warning" as const, timestamp: "14:15", station: "Hamburg", category: "Sync Degraded", description: "Gate 12 sync latency exceeding threshold (180ms)", resolved: false },
  { severity: "info" as const, timestamp: "13:45", station: "Munich", category: "Scheduled Maintenance", description: "Platform 2 PSD calibration scheduled for 22:00", resolved: false },
  { severity: "warning" as const, timestamp: "12:30", station: "Frankfurt", category: "Network Latency", description: "Backup link failover detected on segment B3", resolved: true },
  { severity: "critical" as const, timestamp: "11:00", station: "Cologne", category: "Power Fluctuation", description: "UPS activated for gate cluster 4-7", resolved: true },
];

export default function IncidentsPage() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <GlassPanel icon={AlertTriangle} title="Severity Distribution">
          <PieChart data={severityData} height={280} />
        </GlassPanel>
        <GlassPanel icon={Clock} title="Incidents Over Time">
          <AreaChart data={incidentsOverTime} height={280} />
        </GlassPanel>
      </div>

      <GlassPanel icon={Filter} title="Incident Log">
        <div className="space-y-1">
          {recentIncidents.map((incident, i) => (
            <IncidentRow key={i} {...incident} />
          ))}
        </div>
      </GlassPanel>
    </div>
  );
}