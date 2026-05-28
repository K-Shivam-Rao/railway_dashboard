"use client";

import {
  BarChart as RechartsBar,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

interface WaterfallChartProps {
  data: { name: string; value: number; isTotal?: boolean }[];
  height?: number;
  positiveColor?: string;
  negativeColor?: string;
  totalColor?: string;
}

export function WaterfallChart({
  data,
  height = 300,
  positiveColor = "#10b981",
  negativeColor = "#ef4444",
  totalColor = "#f59e0b",
}: WaterfallChartProps) {
  let cumulative = 0;
  const chartData = data.map((d) => {
    const start = cumulative;
    if (d.isTotal) {
      cumulative = 0;
      return { ...d, start: 0, end: d.value, fill: totalColor };
    }
    const end = start + d.value;
    cumulative = end;
    return {
      ...d,
      start: d.value >= 0 ? start : end,
      end: d.value >= 0 ? end : start,
      fill: d.value >= 0 ? positiveColor : negativeColor,
    };
  });

  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsBar data={chartData}>
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
          content={({ active, payload }: any) =>
            active && payload?.length ? (
              <div className="rounded-lg border border-border-default bg-bg-surface px-3 py-2 shadow-lg">
                <p className="text-xs text-text-muted">{payload[0].payload.name}</p>
                <p className="text-sm text-text-primary">
                  {payload[0].payload.value.toLocaleString()}
                </p>
              </div>
            ) : null
          }
        />
        <Bar dataKey="end" stackId="a" fill={positiveColor} radius={[2, 2, 0, 0]}>
          {chartData.map((entry, i) => (
            <Cell key={i} fill={entry.fill} />
          ))}
        </Bar>
        <Bar dataKey="start" stackId="a" fill="transparent" />
      </RechartsBar>
    </ResponsiveContainer>
  );
}