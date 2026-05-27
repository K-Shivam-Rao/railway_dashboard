export interface APIResponse<T> {
  data: T;
  status: string;
  message?: string;
}

export interface PaginatedResult<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface StationMetrics {
  station: string;
  gatesTotal: number;
  gatesActive: number;
  passengersTotal: number;
  alerts: number;
  warnings: number;
  avgSync: number;
  status: "normal" | "warning" | "critical";
  timestamp: string;
}

export interface Incident {
  id: string;
  station: string;
  severity: "critical" | "warning" | "info";
  category: string;
  description: string;
  timestamp: string;
  resolved: boolean;
}

export interface FinancialData {
  mrr: number;
  arr: number;
  burnRate: number;
  revenuePerEmployee: number;
}

export interface Customer {
  id: string;
  name: string;
  segment: string;
  mrr: number;
  renewalDate: string;
  healthScore: number;
  contractValue: number;
}

export interface KPI {
  label: string;
  value: number;
  format: "number" | "currency" | "percentage";
  trend: "up" | "down" | "neutral";
  trendValue: string;
  color: "amber" | "cyan" | "fuchsia" | "emerald";
}