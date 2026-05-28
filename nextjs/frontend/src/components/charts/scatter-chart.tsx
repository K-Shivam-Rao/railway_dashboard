"use client";

import {
  ScatterChart as RechartsScatter,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface ScatterChartProps {
  data: { x: number; y: number; z?: number; name?: string }[];
  height?: number;
  color?: string;
}

export function ScatterChart({
  data,
  height = 300,
  color = "#f59e0b",
}: ScatterChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsScatter>
        <CartesianGrid
          strokeDasharray="3 3"
          stroke="rgba(241,240,245,0.05)"
        />
        <XAxis
          dataKey="x"
          stroke="#7a7891"
          fontSize={11}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          dataKey="y"
          stroke="#7a7891"
          fontSize={11}
          tickLine={false}
          axisLine={false}
          width={50}
        />
        <ZAxis dataKey="z" range={[40, 200]} />
          <Tooltip
            content={(({ active, payload }: { active?: boolean; payload?: readonly { payload: { x: number; y: number; name?: string } }[] }) =>
              active && payload?.length ? (
                <div className="rounded-lg border border-border-default bg-bg-surface px-3 py-2 shadow-lg">
                  <p className="text-sm text-text-primary">
                    x: {payload[0].payload.x.toLocaleString()}
                  </p>
                  <p className="text-sm text-text-primary">
                    y: {payload[0].payload.y.toLocaleString()}
                  </p>
                  {payload[0].payload.name && (
                    <p className="text-xs text-text-muted">{payload[0].payload.name}</p>
                  )}
                </div>
              ) : null
            ) as any}
          />
        <Scatter data={data} fill={color} opacity={0.7} />
      </RechartsScatter>
    </ResponsiveContainer>
  );
}