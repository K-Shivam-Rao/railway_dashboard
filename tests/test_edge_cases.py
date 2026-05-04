"""
Edge case tests for Railway Dashboard
Tests for zero/empty data prevention and breakproofing - simplified and corrected
"""
import pytest
import pandas as pd
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

from data.sample_data import (
    get_customer_df, get_operator_profile, get_support_tickets,
    get_engagement_timeline, get_operator_monthly_stats,
    get_operator_history, get_contract_amendments,
    get_financial_projections, get_high_value_customers_df,
    get_at_risk_df, get_contract_health_df, get_renewal_forecast_df,
    get_customer_insights, get_renewal_health_summary,
)
from core.logic import (
    get_customer_data, get_customer_business_insights,
    get_operator_profile as logic_get_operator_profile,
    get_support_tickets as logic_get_support_tickets,
)


class TestDataFrameShapeValidation:
    """Test DataFrames are not empty where expected."""

    def test_customer_df_not_empty(self):
        """Test get_customer_df returns non-empty DataFrame."""
        df = get_customer_df()
        assert len(df) > 0, "customer_df should not be empty"

    def test_high_value_customers_not_empty(self):
        """Test get_high_value_customers_df returns non-empty DataFrame."""
        df = get_high_value_customers_df()
        assert len(df) > 0, "high_value_customers_df should not be empty"

    def test_at_risk_df_not_empty(self):
        """Test get_at_risk_df returns non-empty DataFrame."""
        df = get_at_risk_df()
        assert len(df) > 0, "at_risk_df should not be empty"

    def test_contract_health_df_not_empty(self):
        """Test get_contract_health_df returns non-empty DataFrame."""
        df = get_contract_health_df()
        assert len(df) > 0, "contract_health_df should not be empty"

    def test_renewal_forecast_df_not_empty(self):
        """Test get_renewal_forecast_df returns non-empty DataFrame."""
        df = get_renewal_forecast_df()
        assert len(df) > 0, "renewal_forecast_df should not be empty"


class TestColumnNameExactMatches:
    """Test DataFrame columns match what main.py expects."""

    def test_customer_df_has_total_trains(self):
        """Test customer_df has total_trains (not trains_covered)."""
        df = get_customer_df()
        assert "total_trains" in df.columns
        assert "trains_covered" not in df.columns

    def test_customer_df_has_operator_type(self):
        """Test customer_df has operator_type column."""
        df = get_customer_df()
        assert "operator_type" in df.columns

    def test_at_risk_df_has_required_columns(self):
        """Test at_risk_df has all required columns."""
        df = get_at_risk_df()
        required = {"operator_type", "satisfaction_score", "open_issues"}
        for col in required:
            assert col in df.columns, f"Missing column: {col}"

    def test_high_value_df_has_value_tier(self):
        """Test high_value_customers_df has value_tier column."""
        df = get_high_value_customers_df()
        assert "value_tier" in df.columns


class TestNumericValuesNonNegative:
    """Test numeric values are non-negative where expected."""

    def test_total_trains_positive(self):
        """Test total_trains values are positive."""
        df = get_customer_df()
        assert (df["total_trains"] > 0).all(), "total_trains should be positive"

    def test_satisfaction_scores_valid_range(self):
        """Test satisfaction_score values are between 0 and 10."""
        df = get_customer_df()
        if "satisfaction_score" in df.columns:
            assert (df["satisfaction_score"] >= 0).all()
            assert (df["satisfaction_score"] <= 10).all()

    def test_total_contract_value_positive(self):
        """Test total_contract_value_eur is positive."""
        df = get_customer_df()
        if "total_contract_value_eur" in df.columns:
            assert (df["total_contract_value_eur"] > 0).all()


class TestStringColumnsNoNulls:
    """Test string columns don't have nulls where required."""

    def test_customer_name_not_null(self):
        """Test customer_name values are not null."""
        df = get_customer_df()
        assert df["customer_name"].notna().all(), "customer_name should not have nulls"

    def test_customer_id_not_null(self):
        """Test customer_id values are not null."""
        df = get_customer_df()
        assert df["customer_id"].notna().all(), "customer_id should not have nulls"


class TestDictReturnsHaveRequiredKeys:
    """Test dict returns have required keys."""

    def test_customer_insights_has_required_keys(self):
        """Test customer_insights has all required keys."""
        result = get_customer_insights()
        required = {"risk_rate", "at_risk_count", "strategic_count", "recommendations"}
        for key in required:
            assert key in result, f"Missing key in insights: {key}"

    def test_renewal_health_summary_has_required_keys(self):
        """Test renewal_health_summary has required keys."""
        result = get_renewal_health_summary()
        required = {"avg_health_score", "healthy_count", "total_operators"}
        for key in required:
            assert key in result, f"Missing key in health summary: {key}"


class TestPandasOperationsDontFail:
    """Test pandas operations don't fail on returned DataFrames."""

    def test_customer_df_groupby_works(self):
        """Test groupby works on customer_df."""
        df = get_customer_df()
        result = df.groupby("tier").size()
        assert len(result) > 0

    def test_customer_df_sort_values_works(self):
        """Test sort_values works on customer_df."""
        df = get_customer_df()
        if "total_contract_value_eur" in df.columns:
            result = df.sort_values("total_contract_value_eur", ascending=False)
            assert len(result) == len(df)

    def test_at_risk_df_pandas_operations(self):
        """Test pandas operations on at_risk_df."""
        df = get_at_risk_df()
        assert isinstance(df, pd.DataFrame)
        _ = df.columns.tolist()
        rows, cols = df.shape
        assert rows > 0


class TestSupportTicketsReturnsDataFrame:
    """Test get_support_tickets returns DataFrame (not list)."""

    def test_sample_data_version_returns_dataframe(self):
        """Test returns DataFrame, not list."""
        result = get_support_tickets("OP001")
        assert isinstance(result, pd.DataFrame), "Should return DataFrame, not list"

    def test_logic_version_returns_dataframe(self):
        """Test core.logic version returns DataFrame."""
        result = logic_get_support_tickets("OP001")
        assert isinstance(result, pd.DataFrame), "Should return DataFrame, not list"

    def test_has_required_columns(self):
        """Test DataFrame has required columns."""
        df = get_support_tickets("OP001")
        required = {"created_date", "category", "priority", "status"}
        for col in required:
            assert col in df.columns, f"Missing column: {col}"


class TestOperatorProfileNoZeroValues:
    """Test operator profile has no zero values where inappropriate."""

    def test_total_trains_not_zero(self):
        """Test total_trains is not zero."""
        profile = get_operator_profile("OP001")
        if profile:  # May return empty dict for invalid ID
            assert profile.get("total_trains", 0) > 0, "total_trains should not be zero"

    def test_psd_units_not_zero(self):
        """Test psd_units is not zero."""
        profile = get_operator_profile("OP001")
        if profile:
            if "psd_units" in profile:
                assert profile["psd_units"] > 0, "psd_units should not be zero"

    def test_satisfaction_score_not_zero(self):
        """Test satisfaction_score is not zero."""
        profile = get_operator_profile("OP001")
        if profile:
            if "satisfaction_score" in profile:
                assert profile["satisfaction_score"] > 0, "satisfaction_score should not be zero"


class TestCustomerInsightsRecommendations:
    """Test customer_insights recommendations structure."""

    def test_recommendations_is_list(self):
        """Test recommendations is a list."""
        result = get_customer_insights()
        assert isinstance(result["recommendations"], list)

    def test_recommendations_items_have_category(self):
        """Test recommendation items have category key."""
        result = get_customer_insights()
        for rec in result["recommendations"]:
            assert "category" in rec, "Recommendation missing 'category' key"

    def test_recommendations_items_have_message(self):
        """Test recommendation items have message key."""
        result = get_customer_insights()
        for rec in result["recommendations"]:
            assert "message" in rec, "Recommendation missing 'message' key"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
