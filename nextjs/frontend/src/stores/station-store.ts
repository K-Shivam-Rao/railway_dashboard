"use client";

import { create } from "zustand";
import { StationMetrics } from "@/lib/types";

interface StationState {
  stations: string[];
  currentStation: string | null;
  stationMetrics: Record<string, StationMetrics>;
  setCurrentStation: (station: string | null) => void;
  setStations: (stations: string[]) => void;
  updateStationMetrics: (station: string, metrics: StationMetrics) => void;
}

export const useStationStore = create<StationState>((set) => ({
  stations: [],
  currentStation: null,
  stationMetrics: {},
  setCurrentStation: (station) => set({ currentStation: station }),
  setStations: (stations) => set({ stations }),
  updateStationMetrics: (station, metrics) =>
    set((state) => ({
      stationMetrics: {
        ...state.stationMetrics,
        [station]: metrics,
      },
    })),
}));