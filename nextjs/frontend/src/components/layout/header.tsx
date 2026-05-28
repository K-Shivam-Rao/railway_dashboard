"use client";

import { useState, useEffect } from "react";
import { usePathname } from "next/navigation";
import { NAV_ITEMS } from "@/lib/constants";
import { StatusBadge } from "@/components/dashboard/status-badge";

export function Header() {
  const pathname = usePathname();
  const [time, setTime] = useState("");

  useEffect(() => {
    const update = () => setTime(new Date().toLocaleTimeString());
    update();
    const id = setInterval(update, 1000);
    return () => clearInterval(id);
  }, []);

  const currentPage = NAV_ITEMS.find((i) => i.href === pathname);

  return (
    <header className="h-16 bg-bg-surface/80 backdrop-blur-md border-b border-border-default flex items-center justify-between px-6">
      <div>
        <h2 className="text-lg font-semibold text-text-primary">
          {currentPage?.label || "Dashboard"}
        </h2>
      </div>

      <div className="flex items-center gap-4">
        <StatusBadge status="normal" />
        <span className="text-sm text-text-secondary tabular-nums">{time}</span>
      </div>
    </header>
  );
}