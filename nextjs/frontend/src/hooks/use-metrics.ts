"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export function useMetrics(station?: string) {
  return useQuery({
    queryKey: ["metrics", station],
    queryFn: () =>
      apiFetch(station ? `/metrics/${station}` : "/metrics"),
    staleTime: 10000,
  });
}

export function useMetricsSummary(station: string) {
  return useQuery({
    queryKey: ["metrics-summary", station],
    queryFn: () => apiFetch(`/metrics/${station}/summary`),
    staleTime: 10000,
  });
}