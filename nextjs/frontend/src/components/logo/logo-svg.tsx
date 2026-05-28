"use client";

interface LogoSvgProps {
  size?: number;
}

export function LogoSvg({ size = 40 }: LogoSvgProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" fill="none">
      <rect width="40" height="40" rx="8" fill="rgba(245,158,11,0.2)" />
      <path
        d="M12 20L18 14L24 20L18 26L12 20Z"
        stroke="#f59e0b"
        strokeWidth="2"
        strokeLinejoin="round"
        fill="none"
      />
      <circle cx="18" cy="20" r="2" fill="#f59e0b" />
      <path
        d="M24 20L28 16L32 20L28 24L24 20Z"
        stroke="#06b6d4"
        strokeWidth="1.5"
        strokeLinejoin="round"
        fill="none"
        opacity={0.6}
      />
    </svg>
  );
}