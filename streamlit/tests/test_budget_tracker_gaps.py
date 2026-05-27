"""Gap-filler tests for core/budget_tracker.py — cover edge cases and missing branches."""

import pytest
import pandas as pd
import numpy as np
from core.budget_tracker import (
    ROICalculator,
    StationBudget,
    BudgetForecast,
    ROICalculator,
    get_budget_overview,
    get_historical_data,
    get_present_data,
    get_future_data,
    get_station_comparison_table,
)


class TestROICalculatorGaps:
    """Cover calc_roi_by_station edge cases and calc_payback_period with 0 savings."""

    def test_calc_roi_empty_df(self):
        """Line 34: empty roi_df returns empty DataFrame."""
        calc = ROICalculator(pd.DataFrame(), pd.DataFrame())
        result = calc.calc_roi_by_station()
        assert result.empty

    def test_calc_roi_missing_station_col(self):
        """Line 34: roi_df without 'station' column returns empty."""
        df = pd.DataFrame({"roi_pct": [10.0], "npv": [500]})
        calc = ROICalculator(pd.DataFrame(), df)
        result = calc.calc_roi_by_station()
        assert result.empty

    def test_calc_roi_missing_required_cols(self):
        """Lines 36-38: missing required columns get filled with 0."""
        df = pd.DataFrame({"station": ["A", "B"], "roi_pct": [10.0, 20.0]})
        calc = ROICalculator(pd.DataFrame(), df)
        result = calc.calc_roi_by_station()
        assert "payback_years" in result.columns
        assert result["payback_years"].iloc[0] == 0.0

    def test_calc_aggregate_roi_empty(self):
        """Empty roi_df returns zero dict."""
        calc = ROICalculator(pd.DataFrame(), pd.DataFrame())
        result = calc.calc_aggregate_roi()
        assert result["station_count"] == 0

    def test_calc_payback_zero_savings(self):
        """Line 77: annual_savings <= 0 returns inf."""
        result = ROICalculator.calc_payback_period(1000, 0)
        assert result == float("inf")
        result2 = ROICalculator.calc_payback_period(1000, -5)
        assert result2 == float("inf")


class TestStationBudgetGaps:
    """Cover StationBudget edge cases."""

    def test_yearly_breakdown_empty(self):
        """get_yearly_breakdown with empty station_df."""
        sb = StationBudget("Unknown", pd.DataFrame(columns=["station", "year", "capex", "opex", "savings"]))
        result = sb.get_yearly_breakdown()
        assert result.empty
        assert list(result.columns) == ["year", "capex", "opex", "savings"]

    def test_capex_opex_ratio_zero_opex(self):
        """Lines 136-139: total_opex == 0, total_capex > 0 returns inf."""
        df = pd.DataFrame({"station": ["X", "X"], "year": [2024, 2024],
                           "capex": [100, 200], "opex": [0, 0], "savings": [10, 20]})
        sb = StationBudget("X", df)
        result = sb.get_capex_opex_ratio()
        assert result == float("inf")

    def test_capex_opex_ratio_both_zero(self):
        """Line 139: both zero returns 0.0."""
        df = pd.DataFrame({"station": ["X"], "year": [2024], "capex": [0], "opex": [0], "savings": [0]})
        sb = StationBudget("X", df)
        result = sb.get_capex_opex_ratio()
        assert result == 0.0

    def test_get_total_spend(self):
        """Basic total spend calculation."""
        df = pd.DataFrame({"station": ["X", "X"], "year": [2024, 2024],
                           "capex": [100, 200], "opex": [50, 50], "savings": [30, 40]})
        sb = StationBudget("X", df)
        result = sb.get_total_spend()
        assert result["total_capex"] == 300.0
        assert result["total_opex"] == 100.0
        assert result["total_savings"] == 70.0

    def test_budget_vs_actuals_empty(self):
        """get_budget_vs_actuals with empty year df."""
        sb = StationBudget("X", pd.DataFrame(columns=["station", "year", "month", "planned_spend", "actual_spend"]))
        result = sb.get_budget_vs_actuals(2025)
        assert result.empty


class TestBudgetForecastGaps:
    """Cover BudgetForecast edge cases and _by_scenario."""

    def test_scenario_comparison_missing_columns(self):
        """Missing required columns returns empty df."""
        bf = BudgetForecast(pd.DataFrame({"year": [2024]}))
        result = bf.get_scenario_comparison()
        assert result.empty

    def test_by_scenario_no_matching_scenario(self):
        """_by_scenario with empty df returns zeros."""
        bf = BudgetForecast(pd.DataFrame())
        result = bf._by_scenario("best_case")
        assert result["total_revenue"] == 0

    def test_best_case_delegation(self):
        """get_best_case calls _by_scenario correctly."""
        df = pd.DataFrame({"year": [2024], "scenario": ["best_case"],
                           "revenue": [100], "costs": [50], "roi_pct": [50]})
        bf = BudgetForecast(df)
        result = bf.get_best_case()
        assert result["total_revenue"] == 100

    def test_worst_case_delegation(self):
        """get_worst_case calls _by_scenario correctly."""
        df = pd.DataFrame({"year": [2024], "scenario": ["worst_case"],
                           "revenue": [80], "costs": [60], "roi_pct": [25]})
        bf = BudgetForecast(df)
        result = bf.get_worst_case()
        assert result["total_revenue"] == 80

    def test_projected_roi_trajectory_empty(self):
        """Empty df returns empty DataFrame with expected columns."""
        bf = BudgetForecast(pd.DataFrame())
        result = bf.get_projected_roi_trajectory()
        assert result.empty
        assert "year" in result.columns

    def test_projected_roi_fallback_no_best_case(self):
        """No best_case scenario falls back to all data."""
        df = pd.DataFrame({"year": [2024, 2025], "scenario": ["worst_case", "worst_case"],
                           "roi_pct": [10, 20]})
        bf = BudgetForecast(df)
        result = bf.get_projected_roi_trajectory()
        assert len(result) == 2


class TestBudgetModuleFunctions:
    """Cover module-level functions edge cases."""

    def test_get_budget_overview(self):
        """Returns dict with expected keys."""
        result = get_budget_overview()
        assert isinstance(result, dict)
        assert "total_capex" in result
        assert "avg_roi" in result
        assert "health_score" in result

    def test_get_historical_data(self):
        """Returns filtered 2022-2024 data."""
        result = get_historical_data()
        assert isinstance(result, pd.DataFrame)

    def test_get_present_data(self):
        """Returns 2025 data."""
        result = get_present_data()
        assert isinstance(result, pd.DataFrame)

    def test_get_future_data(self):
        """Returns 2026-2030 projections."""
        result = get_future_data()
        assert isinstance(result, pd.DataFrame)

    def test_get_station_comparison_table(self):
        """Returns sorted comparison table."""
        result = get_station_comparison_table()
        assert isinstance(result, pd.DataFrame)
        assert "station" in result.columns
        assert "roi_pct" in result.columns
        # Should be sorted descending by roi_pct
        if len(result) > 1:
            assert result["roi_pct"].iloc[0] >= result["roi_pct"].iloc[-1]
