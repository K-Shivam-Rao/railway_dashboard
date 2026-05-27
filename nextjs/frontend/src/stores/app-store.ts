"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AppState {
  systemStatus: "normal" | "warning" | "critical";
  selectedStation: string | null;
  timeRange: "24h" | "7d" | "30d";
  setSystemStatus: (status: "normal" | "warning" | "critical") => void;
  setSelectedStation: (station: string | null) => void;
  setTimeRange: (range: "24h" | "7d" | "30d") => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      systemStatus: "normal",
      selectedStation: null,
      timeRange: "24h",
      setSystemStatus: (status) => set({ systemStatus: status }),
      setSelectedStation: (station) => set({ selectedStation: station }),
      setTimeRange: (range) => set({ timeRange: range }),
    }),
    {
      name: "sicher-gleis-app-storage",
    }
  )
);