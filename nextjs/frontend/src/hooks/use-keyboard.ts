"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useUIStore } from "@/stores/ui-store";

const KEY_MAP: Record<string, string> = {
  "1": "/ops",
  "2": "/forecast",
  "3": "/incidents",
  "4": "/network",
  "5": "/financial",
  "6": "/customer",
  "7": "/kpi",
  "8": "/budget",
  "9": "/analytics",
  "0": "/company",
};

export function useKeyboard() {
  const router = useRouter();
  const toggleCommandPalette = useUIStore((s) => s.toggleCommandPalette);

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.metaKey || e.ctrlKey) {
        if (e.key === "k") {
          e.preventDefault();
          toggleCommandPalette();
          return;
        }
        if (e.key === "r") {
          e.preventDefault();
          window.location.reload();
          return;
        }
      }

      if (!e.metaKey && !e.ctrlKey && !e.altKey) {
        const route = KEY_MAP[e.key];
        if (route) {
          e.preventDefault();
          router.push(route);
          return;
        }
      }

      if (e.key === "?" && !e.metaKey) {
        e.preventDefault();
        toggleCommandPalette();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [router, toggleCommandPalette]);
}