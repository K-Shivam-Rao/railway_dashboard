"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export function useStations() {
  return useQuery({
    queryKey: ["stations"],
    queryFn: () => apiFetch("/stations"),
  });
}

export function useStationDetail(station: string) {
  return useQuery({
    queryKey: ["station", station],
    queryFn: () => apiFetch(`/stations/${station}`),
    enabled: !!station,
  });
}