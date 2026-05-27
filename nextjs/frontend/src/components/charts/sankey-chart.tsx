"use client";

import { motion } from "framer-motion";

interface SankeyNode {
  name: string;
  x: number;
  y: number;
  height: number;
  color: string;
}

interface SankeyLink {
  source: number;
  target: number;
  value: number;
}

interface SankeyChartProps {
  nodes: { name: string; color?: string }[];
  links: { source: number; target: number; value: number }[];
  height?: number;
}

export function SankeyChart({
  nodes: rawNodes,
  links,
  height = 400,
}: SankeyChartProps) {
  const width = 600;
  const pad = 20;
  const nodeW = 20;
  const nodeColors = rawNodes.map(
    (n) => n.color || "#f59e0b"
  );

  const maxVal = Math.max(...links.map((l) => l.value));
  const totalHeight = height - pad * 2;
  const colCount = 2;
  const colW = (width - pad * 2 - nodeW) / (colCount - 1);

  const col0Nodes = rawNodes.filter((_, i) => links.some((l) => l.source === i));
  const col1Nodes = rawNodes.filter((_, i) => links.some((l) => l.target === i));

  const col0H = totalHeight / col0Nodes.length;
  const col1H = totalHeight / col1Nodes.length;

  const positionedNodes: SankeyNode[] = rawNodes.map((n, i) => {
    const isSource = links.some((l) => l.source === i);
    const isTarget = links.some((l) => l.target === i);
    if (!isSource && !isTarget) return { name: n.name, x: 0, y: 0, height: 0, color: nodeColors[i] };

    const col = isSource ? 0 : 1;
    const colNodes = isSource ? col0Nodes : col1Nodes;
    const colH = isSource ? col0H : col1H;
    const idx = colNodes.findIndex((cn) => cn.name === n.name);
    const colX = pad + col * colW;

    return {
      name: n.name,
      x: colX,
      y: pad + idx * colH + (colH - 20) / 2,
      height: 20,
      color: nodeColors[i],
    };
  });

  return (
    <svg width={width} height={height}>
      {positionedNodes.map(
        (node, i) =>
          node.height > 0 && (
            <motion.g key={i}>
              <rect
                x={node.x}
                y={node.y}
                width={nodeW}
                height={node.height}
                rx={3}
                fill={node.color}
              />
              <text
                x={node.x + nodeW + 4}
                y={node.y + node.height / 2 + 3}
                fill="#b8b6cc"
                fontSize={10}
              >
                {node.name}
              </text>
            </motion.g>
          )
      )}
      {links.map((link, i) => {
        const source = positionedNodes[link.source];
        const target = positionedNodes[link.target];
        if (!source.height || !target.height) return null;

        const thickness = (link.value / maxVal) * 20;
        const midX = (source.x + nodeW + target.x) / 2;

        return (
          <motion.path
            key={i}
            d={`M ${source.x + nodeW} ${source.y + source.height / 2}
                C ${midX} ${source.y + source.height / 2},
                  ${midX} ${target.y + target.height / 2},
                  ${target.x} ${target.y + target.height / 2}`}
            fill="none"
            stroke={source.color}
            strokeWidth={Math.max(2, thickness)}
            strokeOpacity={0.3}
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ delay: i * 0.05, duration: 0.5 }}
          />
        );
      })}
    </svg>
  );
}