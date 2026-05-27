"use client";

import {
  BarChart as RechartsBar,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface BarChartProps {
  data: { name: string; [key: string]: unknown }[];
  height?: number;
  color?: string;
  horizontal?: boolean;
  stacked?: boolean;
  series?: { key: string; color: string }[];
}

export function BarChart({
  data,
  height = 300,
  color = "#f59e0b",
  horizontal,
  stacked,
  series,
}: BarChartProps) {
  const keys = series || [{ key: "value", color }];

  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsBar data={data} layout={horizontal ? "vertical" : "horizontal"}>
        <CartesianGrid
          strokeDasharray="3 3"
          stroke="rgba(241,240,245,0.05)"
          vertical={false}
        />
        <XAxis
          dataKey={horizontal ? "value" : "name"}
          type={horizontal ? "number" : "category"}
          stroke="#7a7891"
          fontSize={11}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          dataKey={horizontal ? "name" : "value"}
          type={horizontal ? "category" : "number"}
          stroke="#7a7891"
          fontSize={11}
          tickLine={false}
          axisLine={false}
          width={horizontal ? 100 : 50}
        />
        <Tooltip
          content={({ active, payload, label }: any) =>
            active && payload?.length ? (
              <div className="rounded-lg border border-border-default bg-bg-surface px-3 py-2 shadow-lg">
                <p className="text-xs text-text-muted mb-1">{label}</p>
                {payload.map((p: any, i: number) => (
                  <p key={i} className="text-sm text-text-primary" style={{ color: p.color }}>
                    {p.name}: {p.value.toLocaleString()}
                  </p>
                ))}
              </div>
            ) : null
          }
        />
        {keys.map((s) => (
          <Bar
            key={s.key}
            dataKey={s.key}
            fill={s.color}
            radius={[2, 2, 0, 0]}
            stackId={stacked ? "stack" : undefined}
          />
        ))}
      </RechartsBar>
    </ResponsiveContainer>
  );
}