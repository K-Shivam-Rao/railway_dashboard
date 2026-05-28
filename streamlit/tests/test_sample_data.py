"""
Unit tests for data/sample_data.py
"""
import os
import sys

import pandas as pd
import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

from data.sample_data import (
    get_at_risk_df,
    get_business_map_data,
    get_contract_amendments,
    get_contract_health_df,
    get_customer_df,
    get_customer_insights,
    get_engagement_timeline,
    get_financial_projections,
    get_high_value_customers_df,
    get_leadership_data,
    get_operator_comparison_benchmarks,
    get_operator_health_trend,
    get_operator_history,
    get_operator_monthly_stats,
    get_operator_profile,
    get_renewal_forecast_df,
    get_renewal_health_summary,
    get_rfm_df,
    get_station_df,
    get_support_ticket_trend,
    get_support_tickets,
)


class TestGetStationDf:
    """Test get_station_df()."""

    def test_returns_dataframe(self):
        """Test returns a pandas DataFrame."""
        df = get_station_df()
        assert isinstance(df, pd.DataFrame)

    def test_non_empty(self):
        """Test returns non-empty DataFrame."""
        df = get_station_df()
        assert len(df) > 0

    def test_has_required_columns(self):
        """Test has required columns."""
        df = get_station_df()
        required = {"station", "lat", "lon", "status", "city", "state"}
        assert required.issubset(set(df.columns))


class TestGetCustomerDf:
    """Test get_customer_df()."""

    def test_returns_dataframe(self):
        """Test returns a pandas DataFrame."""
        df = get_customer_df()
        assert isinstance(df, pd.DataFrame)

    def test_has_total_trains_column(self):
        """Test has total_trains column (not trains_covered)."""
        df = get_customer_df()
        assert "total_trains" in df.columns
        assert "trains_covered" not in df.columns

    def test_has_operator_type_column(self):
        """Test has operator_type column."""
        df = get_customer_df()
        assert "operator_type" in df.columns

    def test_non_zero_trains(self):
        """Test total_trains values are non-zero."""
        df = get_customer_df()
        assert (df["total_trains"] > 0).all()

    def test_has_contract_status_column(self):
        """Test has contract_status column."""
        df = get_customer_df()
        assert "contract_status" in df.columns


class TestGetRfmDf:
    """Test get_rfm_df()."""

    def test_returns_dataframe(self):
        """Test returns a pandas DataFrame."""
        df = get_rfm_df()
        assert isinstance(df, pd.DataFrame)

    def test_has_rfm_columns(self):
        """Test has RFM columns."""
        df = get_rfm_df()
        required = {"recency_score", "frequency_score", "monetary_score"}
        assert required.issubset(set(df.columns))


class TestGetCustomerInsights:
    """Test get_customer_insights()."""

    def test_returns_dict(self):
        """Test returns a dictionary."""
        result = get_customer_insights()
        assert isinstance(result, dict)

    def test_has_total_customers(self):
        """Test has total_customers key."""
        result = get_customer_insights()
        assert "total_customers" in result

    def test_has_risk_rate(self):
        """Test has risk_rate key."""
        result = get_customer_insights()
        assert "risk_rate" in result

    def test_has_at_risk_count(self):
        """Test has at_risk_count key."""
        result = get_customer_insights()
        assert "at_risk_count" in result

    def test_has_strategic_count(self):
        """Test has strategic_count key."""
        result = get_customer_insights()
        assert "strategic_count" in result

    def test_has_recommendations(self):
        """Test has recommendations list with category/message keys."""
        result = get_customer_insights()
        assert "recommendations" in result
        assert len(result["recommendations"]) > 0
        assert "category" in result["recommendations"][0]
        assert "message" in result["recommendations"][0]


class TestGetOperatorProfile:
    """Test get_operator_profile()."""

    def test_valid_id_returns_dict(self):
        """Test valid customer_id returns dict."""
        result = get_operator_profile("OP001")
        assert isinstance(result, dict)

    def test_valid_id_has_required_keys(self):
        """Test returns dict with required keys."""
        result = get_operator_profile("OP001")
        required = {"operator_id", "operator_name", "tier", "total_trains"}
        for key in required:
            assert key in result, f"Missing key: {key}"

    def test_invalid_id_returns_empty_dict(self):
        """Test invalid customer_id returns empty dict."""
        result = get_operator_profile("INVALID")
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_uses_total_trains_not_trains_covered(self):
        """Test uses total_trains key."""
        result = get_operator_profile("OP001")
        assert "total_trains" in result
        assert "trains_covered" not in result


class TestGetContractHealthDf:
    """Test get_contract_health_df()."""

    def test_returns_dataframe(self):
        """Test returns a pandas DataFrame."""
        df = get_contract_health_df()
        assert isinstance(df, pd.DataFrame)

    def test_has_health_status_column(self):
        """Test has health_status column."""
        df = get_contract_health_df()
        assert "health_status" in df.columns

    def test_non_empty(self):
        """Test returns non-empty DataFrame."""
        df = get_contract_health_df()
        assert len(df) > 0


class TestGetRenewalForecastDf:
    """Test get_renewal_forecast_df()."""

    def test_returns_dataframe(self):
        """Test returns a pandas DataFrame."""
        df = get_renewal_forecast_df()
        assert isinstance(df, pd.DataFrame)

    def test_has_operator_type_column(self):
        """Test has operator_type column."""
        df = get_renewal_forecast_df()
        assert "operator_type" in df.columns

    def test_has_renewal_tier_column(self):
        """Test has renewal_tier column."""
        df = get_renewal_forecast_df()
        assert "renewal_tier" in df.columns

    def test_non_empty(self):
        """Test returns non-empty DataFrame."""
        df = get_renewal_forecast_df()
        assert len(df) > 0


class TestGetAtRiskDf:
    """Test get_at_risk_df()."""

    def test_returns_dataframe(self):
        """Test returns a pandas DataFrame."""
        df = get_at_risk_df()
        assert isinstance(df, pd.DataFrame)

    def test_has_operator_type_column(self):
        """Test has operator_type column."""
        df = get_at_risk_df()
        assert "operator_type" in df.columns

    def test_has_satisfaction_score_column(self):
        """Test has satisfaction_score column."""
        df = get_at_risk_df()
        assert "satisfaction_score" in df.columns

    def test_non_empty(self):
        """Test returns non-empty DataFrame."""
        df = get_at_risk_df()
        assert len(df) > 0


class TestGetRenewalHealthSummary:
    """Test get_renewal_health_summary()."""

    def test_returns_dict(self):
        """Test returns a dictionary."""
        result = get_renewal_health_summary()
        assert isinstance(result, dict)

    def test_has_avg_health_score(self):
        """Test has avg_health_score key."""
        result = get_renewal_health_summary()
        assert "avg_health_score" in result

    def test_has_healthy_count(self):
        """Test has healthy_count key."""
        result = get_renewal_health_summary()
        assert "healthy_count" in result

    def test_has_total_operators(self):
        """Test has total_operators key."""
        result = get_renewal_health_summary()
        assert "total_operators" in result

    def test_accepts_customer_df_parameter(self):
        """Test accepts optional customer_df parameter."""
        customer_df = get_customer_df()
        result = get_renewal_health_summary(customer_df=customer_df)
        assert isinstance(result, dict)


class TestGetHighValueCustomersDf:
    """Test get_high_value_customers_df()."""

    def test_returns_dataframe(self):
        """Test returns a pandas DataFrame."""
        df = get_high_value_customers_df()
        assert isinstance(df, pd.DataFrame)

    def test_has_operator_type_column(self):
        """Test has operator_type column."""
        df = get_high_value_customers_df()
        assert "operator_type" in df.columns

    def test_has_value_tier_column(self):
        """Test has value_tier column."""
        df = get_high_value_customers_df()
        assert "value_tier" in df.columns

    def test_has_psd_units_column(self):
        """Test has psd_units column."""
        df = get_high_value_customers_df()
        assert "psd_units" in df.columns

    def test_non_empty(self):
        """Test returns non-empty DataFrame."""
        df = get_high_value_customers_df()
        assert len(df) > 0


class TestGetOperatorHistory:
    """Test get_operator_history()."""

    def test_returns_dataframe(self):
        """Test returns a DataFrame (not list)."""
        result = get_operator_history("OP001")
        assert isinstance(result, pd.DataFrame)

    def test_dataframe_has_project_id_column(self):
        """Test DataFrame has project_id column."""
        df = get_operator_history("OP001")
        assert "project_id" in df.columns

    def test_invalid_id_returns_dataframe(self):
        """Test invalid ID still returns DataFrame (function doesn't filter by ID)."""
        result = get_operator_history("INVALID")
        assert isinstance(result, pd.DataFrame)


class TestGetSupportTickets:
    """Test get_support_tickets()."""

    def test_returns_dataframe(self):
        """Test returns a pandas DataFrame (not list)."""
        result = get_support_tickets("OP001")
        assert isinstance(result, pd.DataFrame)

    def test_has_required_columns(self):
        """Test has required columns."""
        df = get_support_tickets("OP001")
        required = {"created_date", "category", "priority", "status", "summary"}
        assert required.issubset(set(df.columns))

    def test_invalid_id_returns_dataframe(self):
        """Test invalid ID returns DataFrame."""
        result = get_support_tickets("INVALID")
        assert isinstance(result, pd.DataFrame)


class TestGetEngagementTimeline:
    """Test get_engagement_timeline()."""

    def test_returns_dataframe(self):
        """Test returns a pandas DataFrame."""
        df = get_engagement_timeline("OP001")
        assert isinstance(df, pd.DataFrame)

    def test_non_empty(self):
        """Test returns non-empty DataFrame."""
        df = get_engagement_timeline("OP001")
        assert len(df) > 0


class TestGetOperatorMonthlyStats:
    """Test get_operator_monthly_stats()."""

    def test_returns_dataframe(self):
        """Test returns a pandas DataFrame."""
        df = get_operator_monthly_stats("OP001")
        assert isinstance(df, pd.DataFrame)

    def test_non_empty(self):
        """Test returns non-empty DataFrame."""
        df = get_operator_monthly_stats("OP001")
        assert len(df) > 0


class TestGetContractAmendments:
    """Test get_contract_amendments()."""

    def test_returns_list(self):
        """Test returns a list."""
        result = get_contract_amendments("OP001")
        assert isinstance(result, list)


class TestGetFinancialProjections:
    """Test get_financial_projections()."""

    def test_returns_dataframe(self):
        """Test returns a pandas DataFrame."""
        df = get_financial_projections()
        assert isinstance(df, pd.DataFrame)

    def test_non_empty(self):
        """Test returns non-empty DataFrame."""
        df = get_financial_projections()
        assert len(df) > 0


class TestGetOperatorComparisonBenchmarks:
    """Test get_operator_comparison_benchmarks()."""

    def test_returns_dict(self):
        """Test returns a dictionary."""
        result = get_operator_comparison_benchmarks()
        assert isinstance(result, dict)


class TestGetSupportTicketTrend:
    """Test get_support_ticket_trend()."""

    def test_returns_dataframe(self):
        """Test returns a pandas DataFrame."""
        df = get_support_ticket_trend("OP001")
        assert isinstance(df, pd.DataFrame)


class TestGetBusinessMapData:
    """Test get_business_map_data()."""

    def test_returns_dataframe(self):
        """Test returns a DataFrame (not dict)."""
        result = get_business_map_data()
        assert isinstance(result, pd.DataFrame)

    def test_has_station_column(self):
        """Test has station column."""
        df = get_business_map_data()
        assert "station" in df.columns


class TestGetLeadershipData:
    """Test get_leadership_data()."""

    def test_returns_list(self):
        """Test returns a list."""
        result = get_leadership_data()
        assert isinstance(result, list)

    def test_list_items_have_required_keys(self):
        """Test list items have required keys."""
        result = get_leadership_data()
        assert len(result) > 0
        required = {"name", "role", "experience", "education", "specialization"}
        for key in required:
            assert key in result[0], f"Missing key: {key}"

    def test_has_achievements(self):
        """Test has achievements list (note: spelling 'achievements' not 'achievements')."""
        result = get_leadership_data()
        assert "achievements" in result[0]
        assert isinstance(result[0]["achievements"], list)

    def test_has_quote(self):
        """Test has quote key."""
        result = get_leadership_data()
        assert "quote" in result[0]


class TestGetOperatorHealthTrend:
    """Test get_operator_health_trend()."""

    def test_returns_dataframe(self):
        """Test returns a pandas DataFrame."""
        df = get_operator_health_trend("OP001")
        assert isinstance(df, pd.DataFrame)

    def test_non_empty(self):
        """Test returns non-empty DataFrame."""
        df = get_operator_health_trend("OP001")
        assert len(df) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
