"use client";

import {
  LineChart as RechartsLine,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface LineChartProps {
  data: { name: string; [key: string]: unknown }[];
  series: { key: string; color: string; label?: string }[];
  height?: number;
}

export function LineChart({ data, series, height = 300 }: LineChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsLine data={data}>
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
        <Tooltip
          content={(({ active, payload, label }: { active?: boolean; payload?: readonly { name: string; value: number; color: string }[]; label?: string }) =>
            active && payload?.length ? (
              <div className="rounded-lg border border-border-default bg-bg-surface px-3 py-2 shadow-lg">
                <p className="text-xs text-text-muted mb-1">{label}</p>
                {payload.map((p, i) => (
                  <p key={i} className="text-sm text-text-primary" style={{ color: p.color }}>
                    {p.name}: {p.value.toLocaleString()}
                  </p>
                ))}
              </div>
            ) : null
          ) as any}
        />
        {series.map((s) => (
          <Line
            key={s.key}
            type="monotone"
            dataKey={s.key}
            stroke={s.color}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        ))}
      </RechartsLine>
    </ResponsiveContainer>
  );
}