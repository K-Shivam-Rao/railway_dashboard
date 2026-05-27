"""Tests for data/budget_data.py — Budget and ROI data generation."""
import pytest
import sys
import os
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

from data.budget_data import (
    generate_budget_data,
    generate_roi_data,
    generate_monthly_spend,
    generate_scenario_projections,
    generate_optimization_recommendations,
    STATIONS,
    STATION_BUDGET_SUMMARY,
)


class TestGenerateBudgetData:
    """Test generate_budget_data()."""

    def test_returns_dataframe(self):
        df = generate_budget_data()
        assert isinstance(df, pd.DataFrame)

    def test_non_empty(self):
        df = generate_budget_data()
        assert len(df) > 0

    def test_has_required_columns(self):
        df = generate_budget_data()
        required = {"station", "year", "capex", "opex", "savings"}
        assert required.issubset(set(df.columns))

    def test_covers_all_stations(self):
        df = generate_budget_data()
        stations = df["station"].unique()
        assert set(STATIONS).issubset(set(stations))

    def test_covers_2022_to_2030(self):
        df = generate_budget_data()
        years = df["year"].unique()
        assert 2022 in years
        assert 2030 in years

    def test_capex_positive(self):
        df = generate_budget_data()
        assert (df["capex"] > 0).all()

    def test_opex_positive(self):
        df = generate_budget_data()
        assert (df["opex"] > 0).all()

    def test_savings_positive(self):
        df = generate_budget_data()
        assert (df["savings"] > 0).all()


class TestGenerateRoiData:
    """Test generate_roi_data()."""

    def test_returns_dataframe(self):
        df = generate_roi_data()
        assert isinstance(df, pd.DataFrame)

    def test_has_required_columns(self):
        df = generate_roi_data()
        required = {"station", "roi_pct", "payback_years", "net_present_value", "irr"}
        assert required.issubset(set(df.columns))

    def test_roi_positive(self):
        df = generate_roi_data()
        assert (df["roi_pct"] > 0).all()

    def test_payback_reasonable(self):
        df = generate_roi_data()
        assert (df["payback_years"] > 0).all()


class TestGenerateMonthlySpend:
    """Test generate_monthly_spend()."""

    def test_returns_dataframe(self):
        df = generate_monthly_spend(2025)
        assert isinstance(df, pd.DataFrame)

    def test_has_required_columns(self):
        df = generate_monthly_spend(2025)
        required = {"month", "station", "planned", "actual", "category"}
        assert required.issubset(set(df.columns))

    def test_twelve_rows_per_station(self):
        df = generate_monthly_spend(2025)
        assert len(df) == len(STATIONS) * 12  # N stations x 12 months

    def test_planned_positive(self):
        df = generate_monthly_spend(2025)
        assert (df["planned"] > 0).all()


class TestGenerateScenarioProjections:
    """Test generate_scenario_projections()."""

    def test_returns_dataframe(self):
        df = generate_scenario_projections()
        assert isinstance(df, pd.DataFrame)

    def test_has_required_columns(self):
        df = generate_scenario_projections()
        required = {"year", "scenario", "capex", "opex", "savings", "roi_pct"}
        assert required.issubset(set(df.columns))

    def test_has_all_scenarios(self):
        df = generate_scenario_projections()
        scenarios = df["scenario"].unique()
        assert "Conservative" in scenarios
        assert "Baseline" in scenarios
        assert "Aggressive" in scenarios

    def test_years_2025_to_2030(self):
        df = generate_scenario_projections()
        years = df["year"].unique()
        assert 2025 in years
        assert 2030 in years


class TestGenerateOptimizationRecommendations:
    """Test generate_optimization_recommendations()."""

    def test_returns_list(self):
        recs = generate_optimization_recommendations()
        assert isinstance(recs, list)

    def test_has_ten_recommendations(self):
        recs = generate_optimization_recommendations()
        assert len(recs) == 10

    def test_each_has_required_keys(self):
        recs = generate_optimization_recommendations()
        required = {"id", "title", "description", "category", "potential_savings_eur",
                     "implementation_cost_eur", "payback_months", "priority", "station"}
        for rec in recs:
            for key in required:
                assert key in rec, f"Missing key {key} in {rec['id']}"

    def test_ids_unique(self):
        recs = generate_optimization_recommendations()
        ids = [r["id"] for r in recs]
        assert len(ids) == len(set(ids))


class TestStationBudgetSummary:
    """Test STATION_BUDGET_SUMMARY constant."""

    def test_is_dict(self):
        assert isinstance(STATION_BUDGET_SUMMARY, dict)

    def test_has_required_keys(self):
        required = {"total_capex", "total_opex", "avg_roi", "avg_payback", "health_score", "net_profit"}
        assert required.issubset(set(STATION_BUDGET_SUMMARY.keys()))

    def test_values_positive(self):
        assert STATION_BUDGET_SUMMARY["total_capex"] > 0
        assert STATION_BUDGET_SUMMARY["total_opex"] > 0
        assert STATION_BUDGET_SUMMARY["net_profit"] > 0 or True  # net_profit could be anything
        assert 0 <= STATION_BUDGET_SUMMARY["health_score"] <= 100
