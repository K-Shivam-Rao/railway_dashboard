"""Tests for core/budget_tracker.py — Budget/ROI analysis classes and utilities."""
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

from core.budget_tracker import (
    BudgetForecast,
    ROICalculator,
    StationBudget,
    get_budget_overview,
    get_future_data,
    get_historical_data,
    get_present_data,
    get_station_comparison_table,
)


class TestROICalculator:
    """Test ROICalculator class."""

    @pytest.fixture
    def roi_df(self):
        return pd.DataFrame({
            "station": ["A", "B", "C"],
            "roi_pct": [10.0, 25.0, 15.0],
            "payback_years": [5.0, 3.5, 4.2],
            "npv": [100000, 200000, 150000],
            "irr": [12.0, 18.0, 14.5],
        })

    @pytest.fixture
    def budget_df(self):
        return pd.DataFrame({
            "station": ["A", "B", "C"],
            "year": [2025, 2025, 2025],
            "capex": [100000, 200000, 150000],
            "opex": [30000, 50000, 40000],
            "savings": [60000, 120000, 90000],
        })

    def test_init(self, roi_df, budget_df):
        calc = ROICalculator(budget_df, roi_df)
        assert calc.budget_df.equals(budget_df)
        assert calc.roi_df.equals(roi_df)

    def test_calc_roi_by_station_sorted(self, roi_df, budget_df):
        calc = ROICalculator(budget_df, roi_df)
        result = calc.calc_roi_by_station()
        assert result["roi_pct"].iloc[0] == 25.0  # Highest first

    def test_calc_roi_by_station_empty(self):
        calc = ROICalculator(pd.DataFrame(), pd.DataFrame())
        result = calc.calc_roi_by_station()
        assert result.empty

    def test_calc_aggregate_roi(self, roi_df, budget_df):
        calc = ROICalculator(budget_df, roi_df)
        agg = calc.calc_aggregate_roi()
        assert "avg_roi_pct" in agg
        assert "station_count" in agg
        assert agg["station_count"] == 3
        assert agg["avg_roi_pct"] == pytest.approx(16.67, 0.1)

    def test_calc_aggregate_roi_empty(self):
        calc = ROICalculator(pd.DataFrame(), pd.DataFrame())
        agg = calc.calc_aggregate_roi()
        assert agg["station_count"] == 0

    def test_static_payback_period(self):
        payback = ROICalculator.calc_payback_period(100000, 25000)
        assert payback == 4.0

    def test_static_payback_period_zero_savings(self):
        payback = ROICalculator.calc_payback_period(100000, 0)
        assert payback == float("inf")

    def test_static_payback_period_negative_savings(self):
        payback = ROICalculator.calc_payback_period(100000, -1000)
        assert payback == float("inf")


class TestStationBudget:
    """Test StationBudget class."""

    def test_init(self):
        df = pd.DataFrame({"station": ["A"], "year": [2025], "month": [1],
                           "capex": [100], "opex": [50], "savings": [80],
                           "planned_spend": [150], "actual_spend": [140]})
        sb = StationBudget("A", df)
        assert sb.station == "A"

    def test_get_yearly_breakdown(self):
        df = pd.DataFrame({"station": ["A", "A"], "year": [2024, 2025], "month": [1, 1],
                           "capex": [100, 200], "opex": [50, 60], "savings": [80, 100],
                           "planned_spend": [150, 260], "actual_spend": [140, 250]})
        sb = StationBudget("A", df)
        result = sb.get_yearly_breakdown()
        assert len(result) == 2
        assert "capex" in result.columns
        assert "opex" in result.columns

    def test_get_yearly_breakdown_empty_station(self):
        df = pd.DataFrame({"station": ["B"], "year": [2025], "month": [1],
                           "capex": [100], "opex": [50], "savings": [80],
                           "planned_spend": [150], "actual_spend": [140]})
        sb = StationBudget("A", df)  # Station A not in df
        result = sb.get_yearly_breakdown()
        assert result.empty

    def test_get_capex_opex_ratio(self):
        df = pd.DataFrame({"station": ["A"], "year": [2025], "month": [1],
                           "capex": [200], "opex": [100], "savings": [80],
                           "planned_spend": [150], "actual_spend": [140]})
        sb = StationBudget("A", df)
        ratio = sb.get_capex_opex_ratio()
        assert ratio == 2.0

    def test_get_total_spend(self):
        df = pd.DataFrame({"station": ["A", "A"], "year": [2025, 2025], "month": [1, 2],
                           "capex": [100, 200], "opex": [50, 60], "savings": [80, 100],
                           "planned_spend": [150, 260], "actual_spend": [140, 250]})
        sb = StationBudget("A", df)
        spend = sb.get_total_spend()
        assert "total_capex" in spend
        assert spend["total_capex"] == 300
        assert spend["total_savings"] == 180

    def test_get_budget_vs_actuals(self):
        df = pd.DataFrame({"station": ["A", "A"], "year": [2025, 2025], "month": [1, 2],
                           "capex": [100, 200], "opex": [50, 60], "savings": [80, 100],
                           "planned_spend": [150, 260], "actual_spend": [140, 250]})
        sb = StationBudget("A", df)
        result = sb.get_budget_vs_actuals(2025)
        assert len(result) == 2
        assert "variance" in result.columns
        assert result["variance"].iloc[0] == 10  # 150 - 140

    def test_get_budget_vs_actuals_no_year(self):
        df = pd.DataFrame({"station": ["A"], "year": [2024], "month": [1],
                           "capex": [100], "opex": [50], "savings": [80],
                           "planned_spend": [150], "actual_spend": [140]})
        sb = StationBudget("A", df)
        result = sb.get_budget_vs_actuals(2025)
        assert result.empty


class TestBudgetForecast:
    """Test BudgetForecast class."""

    @pytest.fixture
    def scenarios_df(self):
        return pd.DataFrame({
            "year": [2025, 2025, 2026, 2026],
            "scenario": ["best_case", "worst_case", "best_case", "worst_case"],
            "revenue": [500000, 300000, 550000, 320000],
            "costs": [200000, 250000, 210000, 260000],
            "roi_pct": [15.0, 5.0, 16.0, 5.5],
        })

    def test_init(self, scenarios_df):
        bf = BudgetForecast(scenarios_df)
        assert len(bf.scenarios_df) == 4

    def test_get_scenario_comparison(self, scenarios_df):
        bf = BudgetForecast(scenarios_df)
        comparison = bf.get_scenario_comparison()
        assert isinstance(comparison, pd.DataFrame)
        assert not comparison.empty

    def test_get_scenario_comparison_missing_column(self):
        df = pd.DataFrame({"year": [2025]})
        bf = BudgetForecast(df)
        result = bf.get_scenario_comparison()
        assert result.empty

    def test_get_best_case(self, scenarios_df):
        bf = BudgetForecast(scenarios_df)
        best = bf.get_best_case()
        assert "total_revenue" in best
        assert best["years"] == 2

    def test_get_worst_case(self, scenarios_df):
        bf = BudgetForecast(scenarios_df)
        worst = bf.get_worst_case()
        assert "total_costs" in worst
        assert worst["years"] == 2

    def test_get_projected_roi_trajectory(self, scenarios_df):
        bf = BudgetForecast(scenarios_df)
        traj = bf.get_projected_roi_trajectory()
        assert isinstance(traj, pd.DataFrame)
        assert "roi_pct" in traj.columns

    def test_empty_scenario_returns_default(self):
        bf = BudgetForecast(pd.DataFrame())
        best = bf.get_best_case()
        assert isinstance(best, dict)
        # Empty DataFrame means no scenarios, returns defaults
        assert best.get("total_revenue", 0) == 0


class TestBudgetOverview:
    """Test get_budget_overview()."""

    def test_returns_dict(self):
        overview = get_budget_overview()
        assert isinstance(overview, dict)

    def test_has_all_kpi_keys(self):
        overview = get_budget_overview()
        expected = {"total_capex", "avg_roi", "avg_payback", "health_score", "net_profit"}
        assert expected.issubset(set(overview.keys()))


class TestGetHistoricalData:
    """Test get_historical_data()."""

    def test_returns_dataframe(self):
        df = get_historical_data()
        assert isinstance(df, pd.DataFrame)


class TestGetPresentData:
    """Test get_present_data()."""

    def test_returns_dataframe(self):
        df = get_present_data()
        assert isinstance(df, pd.DataFrame)

    def test_current_year(self):
        df = get_present_data()
        if not df.empty and "year" in df.columns:
            assert (df["year"] == 2025).all()


class TestGetFutureData:
    """Test get_future_data()."""

    def test_returns_dataframe(self):
        df = get_future_data()
        assert isinstance(df, pd.DataFrame)


class TestGetStationComparisonTable:
    """Test get_station_comparison_table()."""

    def test_returns_dataframe(self):
        df = get_station_comparison_table()
        assert isinstance(df, pd.DataFrame)

    def test_has_required_columns(self):
        df = get_station_comparison_table()
        if not df.empty:
            assert "station" in df.columns
            assert "roi_pct" in df.columns or "roi_pct" in df.columns

    def test_sorted_by_roi_descending(self):
        df = get_station_comparison_table()
        if not df.empty and "roi_pct" in df.columns:
            assert df["roi_pct"].is_monotonic_decreasing
