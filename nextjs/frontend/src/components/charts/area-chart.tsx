"use client";

import {
  AreaChart as RechartsArea,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface AreaChartProps {
  data: { name: string; [key: string]: unknown }[];
  series?: { key: string; color: string; label: string }[];
  height?: number;
}

const defaultTooltip = ({ active, payload, label }: { active?: boolean; payload?: readonly { name: string; value: number; color: string }[]; label?: string }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-border-default bg-bg-surface px-3 py-2 shadow-lg">
      <p className="text-xs text-text-muted mb-1">{label}</p>
      {payload.map((p, i) => (
        <p key={i} className="text-sm text-text-primary" style={{ color: p.color }}>
          {p.name}: {p.value.toLocaleString()}
        </p>
      ))}
    </div>
  );
};

export function AreaChart({ data, series, height = 300 }: AreaChartProps) {
  const keys = series || [{ key: "value", color: "#f59e0b", label: "Value" }];

  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsArea data={data}>
        <defs>
          {keys.map((s) => (
            <linearGradient key={s.key} id={`gradient-${s.key}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={s.color} stopOpacity={0.3} />
              <stop offset="95%" stopColor={s.color} stopOpacity={0} />
            </linearGradient>
          ))}
        </defs>
        <CartesianGrid
          strokeDasharray="3 3"
          stroke="rgba(241,240,245,0.05)"
          vertical={false}
        />
        <XAxis
          dataKey="name"
          stroke="#7a7891"
          fontSize={11}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          stroke="#7a7891"
          fontSize={11}
          tickLine={false}
          axisLine={false}
          width={50}
        />
        <Tooltip content={defaultTooltip as any} />
        {keys.map((s) => (
          <Area
            key={s.key}
            type="monotone"
            dataKey={s.key}
            stroke={s.color}
            strokeWidth={2}
            fill={`url(#gradient-${s.key})`}
          />
        ))}
      </RechartsArea>
    </ResponsiveContainer>
  );
}