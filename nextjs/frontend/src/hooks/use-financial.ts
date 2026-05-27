"use client";

import { useQuery, useMutation } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export function useFinancialModel(scenario = "base") {
  return useQuery({
    queryKey: ["financial-model", scenario],
    queryFn: () => apiFetch(`/financial/model?scenario=${scenario}`),
  });
}

export function useFinancialSimulation() {
  return useMutation({
    mutationFn: (params: Record<string, number>) =>
      apiFetch("/financial/simulate", {
        method: "POST",
        body: JSON.stringify(params),
      }),
  });
}