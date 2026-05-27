"""
Budget and ROI data for SicherGleis Railway Dashboard.
Contains sample budget data, ROI projections, and financial scenarios
for German railway station PSD (Platform Screen Door) monitoring.
"""

import pandas as pd
import numpy as np
from typing import List, Dict


STATIONS = [
    "Berlin Hbf",
    "München Hbf",
    "Hamburg Hbf",
    "Frankfurt Hbf",
    "Köln Hbf",
    "Stuttgart Hbf",
    "Düsseldorf Hbf",
    "Dortmund Hbf",
    "Essen Hbf",
    "Bremen Hbf",
    "Hannover Hbf",
    "Leipzig Hbf",
    "Nürnberg Hbf",
    "Berlin Südkreuz",
    "Frankfurt Flughafen",
]

_BASE_CAPEX: Dict[str, int] = {
    "Berlin Hbf": 28_000_000,
    "München Hbf": 24_000_000,
    "Hamburg Hbf": 22_000_000,
    "Frankfurt Hbf": 20_000_000,
    "Köln Hbf": 18_000_000,
    "Stuttgart Hbf": 15_000_000,
    "Düsseldorf Hbf": 14_000_000,
    "Dortmund Hbf": 12_000_000,
    "Essen Hbf": 10_000_000,
    "Bremen Hbf": 9_000_000,
    "Hannover Hbf": 8_000_000,
    "Leipzig Hbf": 8_000_000,
    "Nürnberg Hbf": 7_000_000,
    "Berlin Südkreuz": 6_000_000,
    "Frankfurt Flughafen": 5_000_000,
}


def generate_budget_data() -> pd.DataFrame:
    """Return budget DataFrame with columns: station, year, capex, opex, savings.

    Years 2022-2030. CapEx is front-loaded (infrastructure build-out decays to maintenance).
    OpEx is 15-25% of CapEx and grows ~2.5%/yr. Savings grow year-over-year.
    """
    rng = np.random.default_rng(42)
    rows = []
    for station in STATIONS:
        base = _BASE_CAPEX[station]
        for year in range(2022, 2031):
            idx = year - 2022
            decay = np.exp(-0.25 * idx)
            capex = int(base * (0.3 + 0.7 * decay))
            opex = int(base * 0.22 * (1.025 ** idx))
            savings = int(base * 0.35 * (1.22 ** idx) * rng.uniform(0.95, 1.05))
            rows.append({
                "station": station,
                "year": year,
                "capex": capex,
                "opex": opex,
                "savings": savings,
            })
    return pd.DataFrame(rows)


def generate_roi_data() -> pd.DataFrame:
    """Return ROI DataFrame with columns: station, roi_pct, payback_years, net_present_value, irr."""
    return pd.DataFrame([
        {"station": "Berlin Hbf",   "roi_pct": 22.4, "payback_years": 3.8, "net_present_value": 42_000_000, "irr": 25.3},
        {"station": "München Hbf",   "roi_pct": 25.1, "payback_years": 3.5, "net_present_value": 38_000_000, "irr": 28.0},
        {"station": "Hamburg Hbf",  "roi_pct": 28.6, "payback_years": 3.0, "net_present_value": 31_000_000, "irr": 32.1},
        {"station": "Frankfurt Hbf","roi_pct": 26.3, "payback_years": 3.3, "net_present_value": 28_000_000, "irr": 29.5},
        {"station": "Köln Hbf",  "roi_pct": 23.8, "payback_years": 3.7, "net_present_value": 22_000_000, "irr": 26.4},
        {"station": "Stuttgart Hbf","roi_pct": 30.1, "payback_years": 2.9, "net_present_value": 25_000_000, "irr": 33.2},
        {"station": "Düsseldorf Hbf","roi_pct": 27.5, "payback_years": 3.2, "net_present_value": 18_000_000, "irr": 30.8},
        {"station": "Dortmund Hbf",  "roi_pct": 24.2, "payback_years": 3.6, "net_present_value": 15_000_000, "irr": 27.1},
        {"station": "Essen Hbf",     "roi_pct": 29.8, "payback_years": 3.1, "net_present_value": 13_000_000, "irr": 31.5},
        {"station": "Bremen Hbf",    "roi_pct": 31.2, "payback_years": 2.8, "net_present_value": 12_000_000, "irr": 34.0},
        {"station": "Hannover Hbf",  "roi_pct": 26.8, "payback_years": 3.3, "net_present_value": 11_000_000, "irr": 29.0},
        {"station": "Leipzig Hbf",   "roi_pct": 28.3, "payback_years": 3.1, "net_present_value": 10_500_000, "irr": 31.0},
        {"station": "Nürnberg Hbf", "roi_pct": 32.5, "payback_years": 2.7, "net_present_value": 9_500_000, "irr": 35.1},
        {"station": "Berlin Südkreuz","roi_pct": 35.0, "payback_years": 2.5, "net_present_value": 8_000_000, "irr": 38.2},
        {"station": "Frankfurt Flughafen","roi_pct": 33.4, "payback_years": 2.6, "net_present_value": 7_000_000, "irr": 36.5},
    ])


_CATEGORIES = ["Maintenance", "Operations", "Upgrades", "Staff", "Energy"]
_CATEGORY_WEIGHTS = [0.30, 0.25, 0.15, 0.20, 0.10]


def generate_monthly_spend(year: int) -> pd.DataFrame:
    """Return monthly spend for a given year (len(STATIONS) x 12 rows).

    Columns: month, station, planned, actual, category.
    Actuals are +/-5-15% of planned with random variance.
    """
    budget_df = generate_budget_data()
    year_data = budget_df[budget_df["year"] == year]
    rng = np.random.default_rng(year)
    rows = []
    for _, row in year_data.iterrows():
        station = row["station"]
        annual_opex = row["opex"]
        station_idx = STATIONS.index(station)
        for month in range(1, 13):
            cat_idx = (station_idx + month - 1) % 5
            weight = _CATEGORY_WEIGHTS[cat_idx]
            planned = int(annual_opex / 12 * weight * rng.uniform(0.85, 1.15))
            actual = int(planned * rng.uniform(0.85, 1.15))
            rows.append({
                "month": month,
                "station": station,
                "planned": planned,
                "actual": actual,
                "category": _CATEGORIES[cat_idx],
            })
    return pd.DataFrame(rows)


def generate_scenario_projections() -> pd.DataFrame:
    """Return scenario projections for 2025-2030 under 3 growth scenarios.

    Columns: year, scenario, capex, opex, savings, roi_pct.
    Scenarios: Conservative (moderate growth), Baseline (current trajectory),
    Aggressive (accelerated adoption).
    """
    budget_df = generate_budget_data()
    base = budget_df[budget_df["year"] == 2025][["capex", "opex", "savings"]].sum()
    scenarios = {
        "Conservative": {"capex": 0.02, "opex": 0.020, "savings": 0.05},
        "Baseline":     {"capex": 0.04, "opex": 0.025, "savings": 0.12},
        "Aggressive":   {"capex": 0.07, "opex": 0.030, "savings": 0.20},
    }
    rows = []
    for scenario, rates in scenarios.items():
        for year in range(2025, 2031):
            idx = year - 2025
            capex = int(base["capex"] * (1 + rates["capex"]) ** idx)
            opex = int(base["opex"] * (1 + rates["opex"]) ** idx)
            savings = int(base["savings"] * (1 + rates["savings"]) ** idx)
            total_cost = capex + opex
            roi_pct = round((savings - total_cost) / total_cost * 100, 1)
            rows.append({
                "year": year,
                "scenario": scenario,
                "capex": capex,
                "opex": opex,
                "savings": savings,
                "roi_pct": roi_pct,
            })
    return pd.DataFrame(rows)


def generate_optimization_recommendations() -> List[Dict]:
    """Return list of 10 optimization recommendation dicts.

    Each has: id, title, description, category, potential_savings_eur,
    implementation_cost_eur, payback_months, priority, station.
    """
    return [
        {
            "id": "REC-001",
            "title": "Predictive Sensor Recalibration",
            "description": "Implement ML-based predictive recalibration for PSD gap sensors to reduce false positives and manual adjustments",
            "category": "Optimization",
            "potential_savings_eur": 180_000,
            "implementation_cost_eur": 45_000,
            "payback_months": 3,
            "priority": "High",
            "station": "Berlin Hbf",
        },
        {
            "id": "REC-002",
            "title": "LED Platform Lighting Retrofit",
            "description": "Replace existing platform lighting with energy-efficient LED systems with motion-based dimming",
            "category": "Energy",
            "potential_savings_eur": 95_000,
            "implementation_cost_eur": 120_000,
            "payback_months": 15,
            "priority": "Medium",
            "station": "München Hbf",
        },
        {
            "id": "REC-003",
            "title": "Automated Diagnostic Scheduling",
            "description": "Deploy automated diagnostic routines during off-peak hours to reduce manual inspection costs by 40%",
            "category": "Optimization",
            "potential_savings_eur": 210_000,
            "implementation_cost_eur": 85_000,
            "payback_months": 5,
            "priority": "High",
            "station": "Hamburg Hbf",
        },
        {
            "id": "REC-004",
            "title": "HVAC Efficiency Program",
            "description": "Upgrade station HVAC controls with smart zoning and predictive temperature management",
            "category": "Energy",
            "potential_savings_eur": 130_000,
            "implementation_cost_eur": 95_000,
            "payback_months": 9,
            "priority": "Medium",
            "station": "Frankfurt Hbf",
        },
        {
            "id": "REC-005",
            "title": "Proactive Door Seal Replacement",
            "description": "Replace PSD door seals on a predictive schedule to prevent air leakage and reduce motor strain",
            "category": "Maintenance",
            "potential_savings_eur": 65_000,
            "implementation_cost_eur": 28_000,
            "payback_months": 5,
            "priority": "High",
            "station": "Köln Hbf",
        },
        {
            "id": "REC-006",
            "title": "Edge Computing Infrastructure Upgrade",
            "description": "Deploy edge computing nodes for real-time PSD data processing, reducing cloud dependency and latency",
            "category": "Upgrade",
            "potential_savings_eur": 250_000,
            "implementation_cost_eur": 180_000,
            "payback_months": 9,
            "priority": "Medium",
            "station": "Berlin Hbf",
        },
        {
            "id": "REC-007",
            "title": "Solar Panel Canopy Installation",
            "description": "Install photovoltaic panels on station canopies to offset PSD system energy consumption by up to 30%",
            "category": "Energy",
            "potential_savings_eur": 75_000,
            "implementation_cost_eur": 150_000,
            "payback_months": 24,
            "priority": "Low",
            "station": "Stuttgart Hbf",
        },
        {
            "id": "REC-008",
            "title": "Smart Sensor Network Expansion",
            "description": "Expand IoT sensor mesh for granular platform occupancy, door cycle monitoring, and crowd flow analytics",
            "category": "Upgrade",
            "potential_savings_eur": 310_000,
            "implementation_cost_eur": 200_000,
            "payback_months": 8,
            "priority": "High",
            "station": "München Hbf",
        },
        {
            "id": "REC-009",
            "title": "Remote Monitoring Center Setup",
            "description": "Centralize PSD monitoring for all stations into a single remote operations center with AI-assisted alerting",
            "category": "Optimization",
            "potential_savings_eur": 420_000,
            "implementation_cost_eur": 350_000,
            "payback_months": 10,
            "priority": "Medium",
            "station": "Hamburg Hbf",
        },
        {
            "id": "REC-010",
            "title": "Predictive Bearing Replacement Program",
            "description": "Use vibration analysis to predict and replace PSD motor bearings before failure, reducing unplanned downtime",
            "category": "Maintenance",
            "potential_savings_eur": 88_000,
            "implementation_cost_eur": 32_000,
            "payback_months": 4,
            "priority": "High",
            "station": "Frankfurt Hbf",
        },
    ]


_BUDGET_DF = generate_budget_data()
_ROI_DF = generate_roi_data()

STATION_BUDGET_SUMMARY: Dict[str, float] = {
    "total_capex": int(_BUDGET_DF["capex"].sum()),
    "total_opex": int(_BUDGET_DF["opex"].sum()),
    "avg_roi": round(float(_ROI_DF["roi_pct"].mean()), 1),
    "avg_payback": round(float(_ROI_DF["payback_years"].mean()), 1),
    "health_score": 88,
    "net_profit": int(_BUDGET_DF["savings"].sum() - _BUDGET_DF["opex"].sum()),
}
