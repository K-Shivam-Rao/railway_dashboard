"use client";

import { useQuery, useMutation } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export function useAnomalyDetection() {
  return useMutation({
    mutationFn: (params: { method?: string; threshold?: number; station?: string }) =>
      apiFetch("/analytics/anomaly-detection", {
        method: "POST",
        body: JSON.stringify(params),
      }),
  });
}

export function useDecomposition() {
  return useQuery({
    queryKey: ["decomposition"],
    queryFn: () => apiFetch("/analytics/decomposition"),
  });
}

export function useCorrelations() {
  return useQuery({
    queryKey: ["correlations"],
    queryFn: () => apiFetch("/analytics/correlations"),
  });
}