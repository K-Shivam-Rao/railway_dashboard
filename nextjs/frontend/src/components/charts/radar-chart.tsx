"use client";

import {
  RadarChart as RechartsRadar,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from "recharts";

interface RadarChartProps {
  data: { subject: string; value: number; fullMark?: number }[];
  series?: { key: string; color: string }[];
  height?: number;
}

export function RadarChart({
  data,
  height = 300,
  series,
}: RadarChartProps) {
  const keys = series || [{ key: "value", color: "#f59e0b" }];

  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsRadar data={data}>
        <PolarGrid stroke="rgba(241,240,245,0.1)" />
        <PolarAngleAxis
          dataKey="subject"
          stroke="#7a7891"
          fontSize={11}
        />
        <PolarRadiusAxis
          angle={30}
          domain={[0, "auto"]}
          stroke="#7a7891"
          fontSize={10}
        />
        {keys.map((s) => (
          <Radar
            key={s.key}
            name={s.key}
            dataKey={s.key}
            stroke={s.color}
            fill={s.color}
            fillOpacity={0.2}
          />
        ))}
      </RechartsRadar>
    </ResponsiveContainer>
  );
}