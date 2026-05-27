"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export function useIncidents(station?: string, severity?: string, page = 1) {
  const params = new URLSearchParams();
  if (station) params.set("station", station);
  if (severity) params.set("severity", severity);
  params.set("page", String(page));

  return useQuery({
    queryKey: ["incidents", station, severity, page],
    queryFn: () => apiFetch(`/incidents?${params}`),
  });
}

export function useIncidentSummary() {
  return useQuery({
    queryKey: ["incidents-summary"],
    queryFn: () => apiFetch("/incidents/summary"),
  });
}