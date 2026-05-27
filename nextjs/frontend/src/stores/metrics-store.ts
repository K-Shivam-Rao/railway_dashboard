"use client";

import { create } from "zustand";
import { StationMetrics } from "@/lib/types";

interface MetricsState {
  latestMetrics: StationMetrics | null;
  historicalMetrics: StationMetrics[];
  setLatestMetrics: (metrics: StationMetrics | null) => void;
  setHistoricalMetrics: (metrics: StationMetrics[]) => void;
}

export const useMetricsStore = create<MetricsState>((set) => ({
  latestMetrics: null,
  historicalMetrics: [],
  setLatestMetrics: (metrics) => set({ latestMetrics: metrics }),
  setHistoricalMetrics: (metrics) => set({ historicalMetrics: metrics }),
}));