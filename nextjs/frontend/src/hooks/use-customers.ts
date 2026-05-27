"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export function useCustomers() {
  return useQuery({
    queryKey: ["customers"],
    queryFn: () => apiFetch("/customers"),
  });
}

export function useCustomerDetail(id: string) {
  return useQuery({
    queryKey: ["customer", id],
    queryFn: () => apiFetch(`/customers/${id}`),
    enabled: !!id,
  });
}

export function useContractHealth() {
  return useQuery({
    queryKey: ["contract-health"],
    queryFn: () => apiFetch("/customers/contract-health"),
  });
}

export function useRenewalForecast() {
  return useQuery({
    queryKey: ["renewal-forecast"],
    queryFn: () => apiFetch("/customers/renewal-forecast"),
  });
}