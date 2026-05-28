export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const WS_BASE_URL =
  process.env.NEXT_PUBLIC_WS_URL || "http://localhost:8000";

export const STATUS_COLORS = {
  normal: "text-success bg-success/20",
  warning: "text-warning bg-warning/20",
  critical: "text-danger bg-danger/20",
} as const;

export const SEVERITY_COLORS = {
  critical: "bg-danger/20 text-danger border-danger/30",
  warning: "bg-warning/20 text-warning border-warning/30",
  info: "bg-secondary/20 text-secondary border-secondary/30",
} as const;

export const CHART_COLORS = [
  "#f59e0b",
  "#d946ef",
  "#06b6d4",
  "#3b82f6",
  "#10b981",
  "#ef4444",
];

export const NAV_ITEMS = [
  { href: "/ops", label: "Operations", icon: "Activity" },
  { href: "/forecast", label: "Forecast", icon: "TrendingUp" },
  { href: "/incidents", label: "Incidents", icon: "AlertTriangle" },
  { href: "/network", label: "Network", icon: "Network" },
  { href: "/financial", label: "Financial", icon: "DollarSign" },
  { href: "/customer", label: "Customers", icon: "Users" },
  { href: "/kpi", label: "KPIs", icon: "BarChart3" },
  { href: "/budget", label: "Budget", icon: "PieChart" },
  { href: "/analytics", label: "Analytics", icon: "Brain" },
  { href: "/viz", label: "Architecture", icon: "Layers" },
  { href: "/company", label: "Company", icon: "Building2" },
];