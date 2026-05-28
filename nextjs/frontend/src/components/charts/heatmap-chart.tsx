"use client";

import { motion } from "framer-motion";

interface HeatmapChartProps {
  data: { x: string; y: string; value: number }[];
  height?: number;
  colorScale?: [string, string];
}

export function HeatmapChart({
  data,
  height = 300,
  colorScale = ["rgba(16,185,129,0.1)", "rgba(16,185,129,0.9)"],
}: HeatmapChartProps) {
  const xLabels = [...new Set(data.map((d) => d.x))];
  const yLabels = [...new Set(data.map((d) => d.y))];
  const maxVal = Math.max(...data.map((d) => d.value));
  const cellW = Math.max(40, 600 / xLabels.length);
  const cellH = Math.max(30, height / yLabels.length);
  const width = cellW * xLabels.length + 100;

  return (
    <svg width={width} height={height} className="overflow-visible">
      {data.map((d, i) => {
        const intensity = d.value / maxVal;
        const [r, g, b, a1] = colorScale[0].match(/[\d.]+/g)!.map(Number);
        const [r2, g2, b2, a2] = colorScale[1].match(/[\d.]+/g)!.map(Number);
        const fill = `rgba(${r + (r2 - r) * intensity}, ${g + (g2 - g) * intensity}, ${b + (b2 - b) * intensity}, ${a1 + (a2 - a1) * intensity})`;

        const xIdx = xLabels.indexOf(d.x);
        const yIdx = yLabels.indexOf(d.y);

        return (
          <motion.rect
            key={i}
            x={xIdx * cellW + 80}
            y={yIdx * cellH + 20}
            width={cellW - 4}
            height={cellH - 4}
            rx={4}
            fill={fill}
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.01 }}
            className="cursor-pointer hover:opacity-80"
          />
        );
      })}
      {xLabels.map((label, i) => (
        <text
          key={`x-${i}`}
          x={i * cellW + 80 + cellW / 2}
          y={height - 5}
          textAnchor="middle"
          fill="#7a7891"
          fontSize={10}
        >
          {label}
        </text>
      ))}
      {yLabels.map((label, i) => (
        <text
          key={`y-${i}`}
          x={75}
          y={i * cellH + 20 + cellH / 2 + 3}
          textAnchor="end"
          fill="#7a7891"
          fontSize={10}
        >
          {label}
        </text>
      ))}
    </svg>
  );
}