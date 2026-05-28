"use client";

import { motion } from "framer-motion";
import { Activity } from "lucide-react";
import { cn } from "@/lib/utils";

interface AnimatedLogoProps {
  status?: "normal" | "warning" | "critical";
  size?: "sm" | "md" | "lg";
}

const sizeMap = {
  sm: "w-8 h-8",
  md: "w-10 h-10",
  lg: "w-14 h-14",
};

const statusAnimations = {
  normal: { scale: [1, 1.05, 1], transition: { duration: 2, repeat: Infinity } },
  warning: { rotate: [0, 5, -5, 0], transition: { duration: 0.5, repeat: Infinity } },
  critical: { scale: [1, 1.1, 1], transition: { duration: 0.3, repeat: Infinity } },
};

export function AnimatedLogo({
  status = "normal",
  size = "md",
}: AnimatedLogoProps) {
  const bgColor = {
    normal: "bg-success/20",
    warning: "bg-warning/20",
    critical: "bg-danger/20",
  }[status];

  const iconColor = {
    normal: "text-success",
    warning: "text-warning",
    critical: "text-danger",
  }[status];

  return (
    <motion.div
      className={cn(
        "rounded-lg flex items-center justify-center",
        bgColor,
        sizeMap[size]
      )}
      animate={statusAnimations[status]}
    >
      <Activity className={cn("w-5 h-5", iconColor)} />
    </motion.div>
  );
}