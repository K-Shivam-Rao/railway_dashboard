"""
Extended unit tests for core/logic.py - simplified and corrected
"""
import pytest
import pandas as pd
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

from core.logic import (
    SaaSModelConfig, run_simulation, get_metrics, get_psd_analytics,
    get_network_summary, get_maintenance_forecast, get_passenger_heatmap,
    get_incident_log, get_leadership_data, get_tech_stack,
    get_financial_model_data, get_customer_data, get_rfm_analysis,
    get_high_value_customers, get_customer_business_insights,
    get_contract_health_score, get_renewal_forecast, get_at_risk_accounts,
    get_renewal_health_summary, get_operator_history,
    get_contract_amendments, get_support_tickets, get_engagement_timeline,
    get_operator_health_trend, get_support_ticket_trend,
    get_financial_projections, get_operator_comparison_benchmarks,
    get_operator_monthly_stats, get_business_map_data,
    StationAnalytics, FinancialModel
)
from utils.exceptions import ConfigurationError


class TestGetMetrics:
    """Test get_metrics() - returns tuple."""

    def test_returns_tuple(self):
        """Test returns a tuple using actual transformed data."""
        from data.loader import load_and_transform_data
        df = load_and_transform_data()
        if df.empty or "station" not in df.columns or "door_state" not in df.columns:
            pytest.skip("No valid transformed data available")
        station_name = df["station"].iloc[0]
        result = get_metrics(df, station_name)
        assert isinstance(result, tuple)
        assert len(result) == 7

    def test_nonexistent_station_returns_default(self):
        """Test nonexistent station returns (0,0,0,0,0,0, None)."""
        df = pd.DataFrame({"station": ["Berlin Hbf"]})
        result = get_metrics(df, "Nonexistent")
        assert result == (0, 0, 0, 0, 0, 0, None)


class TestGetPsdAnalytics:
    """Test get_psd_analytics() - returns tuple of DataFrames."""

    def test_returns_tuple(self):
        """Test returns a tuple of (cycles_df, temp_df)."""
        result = get_psd_analytics("Berlin Hbf")
        assert isinstance(result, tuple)
        assert len(result) == 2


class TestGetNetworkSummary:
    """Test get_network_summary() - returns dict."""

    def test_returns_dict(self):
        """Test returns a dictionary using actual transformed data."""
        from data.loader import load_and_transform_data
        df = load_and_transform_data()
        if df.empty or "people" not in df.columns:
            pytest.skip("No valid data with 'people' column")
        result = get_network_summary(df)
        assert isinstance(result, dict)


class TestGetMaintenanceForecast:
    """Test get_maintenance_forecast()."""

    def test_returns_dataframe(self):
        """Test returns a pandas DataFrame."""
        result = get_maintenance_forecast("Berlin Hbf")
        assert isinstance(result, pd.DataFrame)

    def test_non_empty(self):
        """Test returns non-empty DataFrame."""
        result = get_maintenance_forecast("Berlin Hbf")
        assert len(result) > 0


class TestGetPassengerHeatmap:
    """Test get_passenger_heatmap()."""

    def test_returns_dataframe(self):
        """Test returns a pandas DataFrame."""
        result = get_passenger_heatmap("Berlin Hbf")
        assert isinstance(result, pd.DataFrame)


class TestGetIncidentLog:
    """Test get_incident_log()."""

    def test_returns_dataframe(self):
        """Test returns a pandas DataFrame with required columns."""
        df = pd.DataFrame({
            "station": ["Berlin Hbf"] * 3,
            "platform": ["1", "2", "3"],
            "gate_id": ["G1", "G2", "G3"],
            "maintenance_status": ["OPTIMAL", "WARNING", "CRITICAL"],
            "door_state": ["open", "closed", "jammed"],
            "sensor_temp": [25.0, 30.0, 50.0],
            "sensor_vib": [0.1, 0.5, 5.0],
            "people": [100, 200, 500],
            "power_consumption": [15.0, 20.0, 60.0],
            "humidity": [50.0, 60.0, 90.0],
            "motor": [1.0, 2.0, 5.0],
            "sync_score": [90, 70, 40],
        })
        result = get_incident_log(df)
        assert isinstance(result, pd.DataFrame)


class TestGetLeadershipData:
    """Test get_leadership_data() from core.logic."""

    def test_returns_list(self):
        """Test returns a list."""
        result = get_leadership_data()
        assert isinstance(result, list)

    def test_has_member_details(self):
        """Test list items have required keys."""
        result = get_leadership_data()
        assert len(result) > 0
        required = {"name", "role", "experience", "education"}
        for key in required:
            assert key in result[0], f"Missing key: {key}"


class TestGetTechStack:
    """Test get_tech_stack() - returns list."""

    def test_returns_list(self):
        """Test returns a list."""
        result = get_tech_stack()
        assert isinstance(result, list)

    def test_list_items_have_layer(self):
        """Test list items have layer key."""
        result = get_tech_stack()
        assert "layer" in result[0]


class TestGetFinancialModelData:
    """Test get_financial_model_data()."""

    def test_returns_tuple(self):
        """Test returns a tuple (df_base, df_churn)."""
        result = get_financial_model_data(months=12)
        assert isinstance(result, tuple)
        assert len(result) == 2


class TestGetCustomerData:
    """Test get_customer_data()."""

    def test_returns_dataframe(self):
        """Test returns a pandas DataFrame."""
        result = get_customer_data()
        assert isinstance(result, pd.DataFrame)

    def test_has_total_trains_column(self):
        """Test has total_trains column."""
        result = get_customer_data()
        assert "total_trains" in result.columns


class TestGetRfmAnalysis:
    """Test get_rfm_analysis()."""

    def test_returns_dataframe(self):
        """Test returns a pandas DataFrame."""
        customer_df = get_customer_data()
        result = get_rfm_analysis(customer_df)
        assert isinstance(result, pd.DataFrame)


class TestGetHighValueCustomers:
    """Test get_high_value_customers()."""

    def test_returns_dataframe(self):
        """Test returns a pandas DataFrame."""
        customer_df = get_customer_data()
        result = get_high_value_customers(customer_df)
        assert isinstance(result, pd.DataFrame)


class TestGetCustomerBusinessInsights:
    """Test get_customer_business_insights()."""

    def test_returns_dict(self):
        """Test returns a dictionary."""
        customer_df = get_customer_data()
        result = get_customer_business_insights(customer_df)
        assert isinstance(result, dict)

    def test_has_risk_rate(self):
        """Test has risk_rate key."""
        customer_df = get_customer_data()
        result = get_customer_business_insights(customer_df)
        assert "risk_rate" in result

    def test_has_recommendations(self):
        """Test has recommendations key."""
        customer_df = get_customer_data()
        result = get_customer_business_insights(customer_df)
        assert "recommendations" in result


class TestGetContractHealthScore:
    """Test get_contract_health_score() - returns DataFrame."""

    def test_returns_dataframe(self):
        """Test returns a DataFrame."""
        customer_df = get_customer_data()
        result = get_contract_health_score(customer_df)
        assert isinstance(result, pd.DataFrame)


class TestRenewalHealthSummaryLogic:
    """Test get_renewal_health_summary() from core.logic."""

    def test_returns_dict(self):
        """Test returns a dictionary."""
        customer_df = get_customer_data()
        result = get_renewal_health_summary(customer_df)
        assert isinstance(result, dict)

    def test_has_healthy_count(self):
        """Test has healthy_count key."""
        customer_df = get_customer_data()
        result = get_renewal_health_summary(customer_df)
        assert "healthy_count" in result


class TestOperatorHistoryLogic:
    """Test get_operator_history() from core.logic - returns DataFrame."""

    def test_returns_dataframe(self):
        """Test returns a DataFrame."""
        result = get_operator_history("OP001")
        assert isinstance(result, pd.DataFrame)


class TestOperatorMonthlyStatsLogic:
    """Test get_operator_monthly_stats() from core.logic."""

    def test_returns_dataframe(self):
        """Test returns a pandas DataFrame."""
        result = get_operator_monthly_stats("OP001")
        assert isinstance(result, pd.DataFrame)


class TestStationAnalyticsClass:
    """Test StationAnalytics class - static methods."""

    def test_get_metrics_static(self):
        """Test get_metrics static method using actual data."""
        from data.loader import load_and_transform_data
        df = load_and_transform_data()
        if df.empty or "station" not in df.columns or "door_state" not in df.columns:
            pytest.skip("No valid data available")
        station_name = df["station"].iloc[0]
        result = StationAnalytics.get_metrics(df, station_name)
        assert isinstance(result, tuple)


class TestFinancialModelClass:
    """Test FinancialModel class."""

    def test_run_simulation_static(self):
        """Test static run_simulation method."""
        config = SaaSModelConfig(
            starting_customers=10, monthly_growth_rate=0.10,
            churn_rate=0.05, price_per_customer=100,
            fixed_costs=1000, variable_cost_per_customer=10
        )
        df = FinancialModel.run_simulation(config, months=12)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 12


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
