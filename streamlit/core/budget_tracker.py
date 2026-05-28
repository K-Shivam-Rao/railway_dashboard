"""Budget & ROI tracking module for SicherGleis PSD monitoring dashboard."""

import logging

import numpy as np
import pandas as pd

from data.budget_data import (
    STATION_BUDGET_SUMMARY,
    generate_budget_data,
    generate_roi_data,
    generate_scenario_projections,
)

logger = logging.getLogger(__name__)


class ROICalculator:
    """Calculate ROI metrics per station and in aggregate."""

    def __init__(self, budget_df: pd.DataFrame, roi_df: pd.DataFrame):
        self.budget_df = budget_df
        self.roi_df = roi_df

    def calc_roi_by_station(self) -> pd.DataFrame:
        df = self.roi_df.copy()
        if df.empty or "station" not in df.columns:
            return pd.DataFrame()
        required = ["roi_pct", "payback_years", "npv", "irr"]
        for col in required:
            if col not in df.columns:
                df[col] = 0.0
        return df.sort_values("roi_pct", ascending=False).reset_index(drop=True)

    def calc_aggregate_roi(self) -> dict:
        if self.roi_df.empty:
            return {"avg_roi_pct": 0, "avg_payback_years": 0, "total_npv": 0, "avg_irr": 0, "station_count": 0}
        return {
            "avg_roi_pct": round(self.roi_df["roi_pct"].mean(), 2),
            "avg_payback_years": round(self.roi_df["payback_years"].mean(), 2),
            "total_npv": round(self.roi_df["npv"].sum(), 2),
            "avg_irr": round(self.roi_df["irr"].mean(), 2),
            "station_count": len(self.roi_df),
        }

    @staticmethod
    def calc_payback_period(capex: float, annual_savings: float) -> float:
        if annual_savings <= 0:
            return float("inf")
        return round(capex / annual_savings, 2)


class StationBudget:
    """Per-station budget analysis."""

    def __init__(self, station: str, budget_df: pd.DataFrame):
        self.station = station
        self.budget_df = budget_df
        self.station_df = budget_df[budget_df["station"] == station].copy()

    def get_yearly_breakdown(self) -> pd.DataFrame:
        if self.station_df.empty:
            return pd.DataFrame(columns=["year", "capex", "opex", "savings"])
        grouped = self.station_df.groupby("year").agg(
            capex=("capex", "sum"),
            opex=("opex", "sum"),
            savings=("savings", "sum"),
        ).reset_index()
        return grouped

    def get_capex_opex_ratio(self) -> float:
        total_capex = self.station_df["capex"].sum()
        total_opex = self.station_df["opex"].sum()
        if total_opex == 0:
            return float("inf") if total_capex > 0 else 0.0
        return round(total_capex / total_opex, 2)

    def get_total_spend(self) -> dict:
        return {
            "total_capex": round(self.station_df["capex"].sum(), 2),
            "total_opex": round(self.station_df["opex"].sum(), 2),
            "total_savings": round(self.station_df["savings"].sum(), 2),
        }

    def get_budget_vs_actuals(self, year: int) -> pd.DataFrame:
        yr_df = self.station_df[self.station_df["year"] == year].copy()
        if yr_df.empty:
            return pd.DataFrame(columns=["month", "planned", "actual", "variance"])
        result = yr_df.groupby("month").agg(
            planned=("planned_spend", "sum"),
            actual=("actual_spend", "sum"),
        ).reset_index()
        result["variance"] = result["planned"] - result["actual"]
        return result


class BudgetForecast:
    """Scenario-based budget forecasting."""

    def __init__(self, scenarios_df: pd.DataFrame):
        self.scenarios_df = scenarios_df

    def get_scenario_comparison(self) -> pd.DataFrame:
        required = ["year", "scenario", "revenue", "costs", "roi_pct"]
        for col in required:
            if col not in self.scenarios_df.columns:
                return pd.DataFrame()
        return self.scenarios_df.pivot_table(
            index="year",
            columns="scenario",
            values=["revenue", "costs", "roi_pct"],
            aggfunc="mean",
        ).round(2)

    def _by_scenario(self, scenario: str) -> dict:
        if self.scenarios_df.empty or "scenario" not in self.scenarios_df.columns:
            return {"total_revenue": 0, "total_costs": 0, "avg_roi_pct": 0, "years": 0}
        subset = self.scenarios_df[self.scenarios_df["scenario"] == scenario]
        return {
            "total_revenue": round(subset["revenue"].sum(), 2),
            "total_costs": round(subset["costs"].sum(), 2),
            "avg_roi_pct": round(subset["roi_pct"].mean(), 2),
            "years": len(subset),
        }

    def get_best_case(self) -> dict:
        return self._by_scenario("best_case")

    def get_worst_case(self) -> dict:
        return self._by_scenario("worst_case")

    def get_projected_roi_trajectory(self) -> pd.DataFrame:
        if self.scenarios_df.empty:
            return pd.DataFrame(columns=["year", "scenario", "roi_pct"])
        subset = self.scenarios_df[self.scenarios_df["scenario"] == "best_case"].copy()
        if subset.empty:
            subset = self.scenarios_df
        return subset[["year", "roi_pct"]].sort_values("year").reset_index(drop=True)


def get_budget_overview() -> dict:
    """Top-level KPI card values from STATION_BUDGET_SUMMARY."""
    return {
        "total_capex": STATION_BUDGET_SUMMARY.get("total_capex", 0),
        "avg_roi": STATION_BUDGET_SUMMARY.get("avg_roi", 0),
        "avg_payback": STATION_BUDGET_SUMMARY.get("avg_payback", 0),
        "health_score": STATION_BUDGET_SUMMARY.get("health_score", 0),
        "net_profit": STATION_BUDGET_SUMMARY.get("net_profit", 0),
    }


def get_historical_data() -> pd.DataFrame:
    """Budget data for 2022–2024."""
    df = generate_budget_data()
    historical_years = [2022, 2023, 2024]
    if "year" in df.columns:
        return df[df["year"].isin(historical_years)].reset_index(drop=True)
    return df.head(0)


def get_present_data() -> pd.DataFrame:
    """Current year (2025) budget vs actuals."""
    df = generate_budget_data()
    if "year" in df.columns:
        return df[df["year"] == 2025].reset_index(drop=True)
    return df.head(0)


def get_future_data() -> pd.DataFrame:
    """Projected budget data for 2026–2030."""
    df = generate_scenario_projections()
    future_years = [2026, 2027, 2028, 2029, 2030]
    if "year" in df.columns:
        return df[df["year"].isin(future_years)].reset_index(drop=True)
    return df.head(0)


def get_station_comparison_table() -> pd.DataFrame:
    """Station × KPI comparison matrix."""
    df = generate_roi_data()
    if df.empty:
        return pd.DataFrame(columns=[
            "station", "total_capex", "total_opex", "avg_roi",
            "payback_years", "npv", "irr", "savings_to_cost_ratio",
        ])
    budget_df = generate_budget_data()
    if not budget_df.empty and "station" in budget_df.columns:
        agg = budget_df.groupby("station").agg(
            total_capex=("capex", "sum"),
            total_opex=("opex", "sum"),
        ).reset_index()
        df = df.merge(agg, on="station", how="left")
    else:
        df["total_capex"] = 0.0
        df["total_opex"] = 0.0
    if "net_present_value" in df.columns and "npv" not in df.columns:
        df["npv"] = df["net_present_value"]
    df["savings_to_cost_ratio"] = np.where(
        (df["total_capex"] + df["total_opex"]) > 0,
        (df["total_capex"] + df["total_opex"]) / (df["total_capex"] + df["total_opex"]).max(),
        0.0,
    )
    cols = [
        "station", "total_capex", "total_opex", "roi_pct",
        "payback_years", "npv", "irr", "savings_to_cost_ratio",
    ]
    available = [c for c in cols if c in df.columns]
    return df[available].round(2).sort_values("roi_pct", ascending=False).reset_index(drop=True)
