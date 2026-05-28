"use client";

import {
  PieChart as RechartsPie,
  Pie,
  Cell,
  ResponsiveContainer,
} from "recharts";

interface PieChartProps {
  data: { name: string; value: number; color?: string }[];
  height?: number;
  innerRadius?: number;
  outerRadius?: number;
}

const DEFAULT_COLORS = ["#f59e0b", "#d946ef", "#06b6d4", "#3b82f6", "#10b981", "#ef4444"];

export function PieChart({
  data,
  height = 300,
  innerRadius = 60,
  outerRadius = 90,
}: PieChartProps) {
  const total = data.reduce((sum, d) => sum + d.value, 0);

  return (
    <div className="relative">
      <ResponsiveContainer width="100%" height={height}>
        <RechartsPie>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={innerRadius}
            outerRadius={outerRadius}
            dataKey="value"
            stroke="none"
          >
            {data.map((entry, i) => (
              <Cell key={i} fill={entry.color || DEFAULT_COLORS[i % DEFAULT_COLORS.length]} />
            ))}
          </Pie>
        </RechartsPie>
      </ResponsiveContainer>
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div className="text-center">
          <p className="text-2xl font-bold text-text-primary">{total.toLocaleString()}</p>
          <p className="text-xs text-text-muted">Total</p>
        </div>
      </div>
    </div>
  );
}