"use client";

import { motion } from "framer-motion";

interface GaugeChartProps {
  value: number;
  min?: number;
  max?: number;
  label?: string;
  size?: number;
  color?: string;
}

const colorZones = [
  { threshold: 33, color: "#10b981" },
  { threshold: 66, color: "#f59e0b" },
  { threshold: 100, color: "#ef4444" },
];

function getColor(value: number) {
  const zone = colorZones.find((z) => value <= z.threshold);
  return zone?.color || "#ef4444";
}

export function GaugeChart({
  value,
  min = 0,
  max = 100,
  label,
  size = 200,
  color,
}: GaugeChartProps) {
  const radius = size * 0.35;
  const circumference = 2 * Math.PI * radius;
  const normalized = ((value - min) / (max - min)) * 100;
  const strokeDashoffset = circumference * (1 - normalized / 100);
  const gaugeColor = color || getColor(normalized);

  return (
    <div className="flex flex-col items-center" style={{ width: size }}>
      <svg width={size} height={size * 0.6} viewBox={`0 0 ${size} ${size * 0.6}`}>
        <path
          d={`M ${size * 0.1} ${size * 0.55} A ${radius} ${radius} 0 0 1 ${size * 0.9} ${size * 0.55}`}
          fill="none"
          stroke="rgba(241,240,245,0.05)"
          strokeWidth={12}
          strokeLinecap="round"
        />
        <motion.path
          d={`M ${size * 0.1} ${size * 0.55} A ${radius} ${radius} 0 0 1 ${size * 0.9} ${size * 0.55}`}
          fill="none"
          stroke={gaugeColor}
          strokeWidth={12}
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset }}
          transition={{ duration: 1, ease: "easeOut" }}
        />
        <text
          x={size / 2}
          y={size * 0.38}
          textAnchor="middle"
          fill="#f1f0f5"
          fontSize={28}
          fontWeight="bold"
          fontFamily="JetBrains Mono"
        >
          {Math.round(normalized)}%
        </text>
      </svg>
      {label && (
        <p className="text-xs text-text-secondary mt-1">{label}</p>
      )}
    </div>
  );
}