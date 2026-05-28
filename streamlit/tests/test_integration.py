"""
Integration tests for Railway Dashboard - simplified and corrected
"""
import os
import sys

import pandas as pd
import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

# Import from both sample_data and core.logic to verify consistency
from core.logic import (
    get_customer_business_insights,
    get_customer_data,
)
from core.logic import (
    get_engagement_timeline as logic_get_engagement_timeline,
)
from core.logic import (
    get_operator_history as logic_get_operator_history,
)
from core.logic import (
    get_operator_monthly_stats as logic_get_operator_monthly_stats,
)
from core.logic import (
    get_operator_profile as logic_get_operator_profile,
)
from core.logic import (
    get_support_tickets as logic_get_support_tickets,
)
from data.sample_data import (
    get_customer_df as sd_get_customer_df,
)
from data.sample_data import (
    get_customer_insights as sd_get_customer_insights,
)
from data.sample_data import (
    get_engagement_timeline as sd_get_engagement_timeline,
)
from data.sample_data import (
    get_operator_history as sd_get_operator_history,
)
from data.sample_data import (
    get_operator_monthly_stats as sd_get_operator_monthly_stats,
)
from data.sample_data import (
    get_operator_profile as sd_get_operator_profile,
)
from data.sample_data import (
    get_support_tickets as sd_get_support_tickets,
)


class TestCustomerDfConsistency:
    """Test customer DataFrame consistency between modules."""

    def test_sample_data_and_logic_return_dataframes(self):
        """Test both return DataFrames."""
        df1 = sd_get_customer_df()
        df2 = get_customer_data()
        assert isinstance(df1, pd.DataFrame)
        assert isinstance(df2, pd.DataFrame)

    def test_column_consistency_total_trains(self):
        """Test total_trains column exists in both."""
        df1 = sd_get_customer_df()
        df2 = get_customer_data()
        assert "total_trains" in df1.columns
        assert "total_trains" in df2.columns

    def test_column_consistency_operator_type(self):
        """Test operator_type column exists in both."""
        df1 = sd_get_customer_df()
        df2 = get_customer_data()
        assert "operator_type" in df1.columns
        assert "operator_type" in df2.columns


class TestCustomerInsightsConsistency:
    """Test customer insights consistency between modules."""

    def test_both_return_dicts(self):
        """Test both return dictionaries."""
        result1 = sd_get_customer_insights()
        result2 = get_customer_business_insights()
        assert isinstance(result1, dict)
        assert isinstance(result2, dict)

    def test_both_have_risk_rate(self):
        """Test both have risk_rate key."""
        result1 = sd_get_customer_insights()
        result2 = get_customer_business_insights()
        assert "risk_rate" in result1
        assert "risk_rate" in result2

    def test_both_have_recommendations(self):
        """Test both have recommendations key."""
        result1 = sd_get_customer_insights()
        result2 = get_customer_business_insights()
        assert "recommendations" in result1
        assert "recommendations" in result2


class TestOperatorProfileConsistency:
    """Test operator profile consistency."""

    def test_both_return_dicts(self):
        """Test both return dictionaries."""
        result1 = sd_get_operator_profile("OP001")
        result2 = logic_get_operator_profile("OP001")
        assert isinstance(result1, dict)
        assert isinstance(result2, dict)

    def test_both_have_customer_id(self):
        """Test both have operator_id/customer_id key."""
        result1 = sd_get_operator_profile("OP001")
        result2 = logic_get_operator_profile("OP001")
        # sd uses 'operator_id', logic uses 'operator_id' too
        assert "operator_id" in result1 or "customer_id" in result1
        assert "operator_id" in result2 or "customer_id" in result2

    def test_both_use_total_trains(self):
        """Test both use total_trains key."""
        result1 = sd_get_operator_profile("OP001")
        result2 = logic_get_operator_profile("OP001")
        assert "total_trains" in result1
        assert "total_trains" in result2


class TestSupportTicketsConsistency:
    """Test support tickets consistency."""

    def test_both_return_dataframes(self):
        """Test both return DataFrames."""
        result1 = sd_get_support_tickets("OP001")
        result2 = logic_get_support_tickets("OP001")
        assert isinstance(result1, pd.DataFrame)
        assert isinstance(result2, pd.DataFrame)

    def test_sample_data_has_created_date(self):
        """Test sample_data version has created_date column."""
        df = sd_get_support_tickets("OP001")
        if not df.empty:
            assert "created_date" in df.columns

    def test_logic_has_created_date(self):
        """Test logic version has created_date column."""
        df = logic_get_support_tickets("OP001")
        if not df.empty:
            assert "created_date" in df.columns


class TestEngagementTimelineConsistency:
    """Test engagement timeline consistency."""

    def test_both_return_dataframes(self):
        """Test both return DataFrames."""
        df1 = sd_get_engagement_timeline("OP001")
        df2 = logic_get_engagement_timeline("OP001")
        assert isinstance(df1, pd.DataFrame)
        assert isinstance(df2, pd.DataFrame)


class TestOperatorMonthlyStatsConsistency:
    """Test operator monthly stats consistency."""

    def test_both_return_dataframes(self):
        """Test both return DataFrames."""
        df1 = sd_get_operator_monthly_stats("OP001")
        df2 = logic_get_operator_monthly_stats("OP001")
        assert isinstance(df1, pd.DataFrame)
        assert isinstance(df2, pd.DataFrame)


class TestOperatorHistoryConsistency:
    """Test operator history consistency."""

    def test_both_return_dataframes(self):
        """Test both return DataFrames (not lists)."""
        result1 = sd_get_operator_history("OP001")
        result2 = logic_get_operator_history("OP001")
        assert isinstance(result1, pd.DataFrame)
        assert isinstance(result2, pd.DataFrame)


class TestEndToEndWorkflow:
    """Test end-to-end workflows."""

    def test_customer_to_insights_workflow(self):
        """Test customer_df -> customer_insights workflow."""
        customer_df = sd_get_customer_df()
        assert isinstance(customer_df, pd.DataFrame)
        insights = sd_get_customer_insights()
        assert isinstance(insights, dict)
        assert "risk_rate" in insights

    def test_operator_profile_to_history(self):
        """Test operator_profile -> history -> monthly_stats workflow."""
        profile = sd_get_operator_profile("OP001")
        assert isinstance(profile, dict)
        history = sd_get_operator_history("OP001")
        assert isinstance(history, pd.DataFrame)
        stats = sd_get_operator_monthly_stats("OP001")
        assert isinstance(stats, pd.DataFrame)

    def test_contract_health_workflow(self):
        """Test customer_df -> contract_health -> renewal_forecast workflow."""
        from data.sample_data import get_contract_health_df, get_renewal_forecast_df
        df = get_contract_health_df()
        assert isinstance(df, pd.DataFrame)
        assert "health_status" in df.columns
        forecast = get_renewal_forecast_df()
        assert isinstance(forecast, pd.DataFrame)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
