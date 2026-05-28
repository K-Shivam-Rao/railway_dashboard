"""
Unit tests for core/logic.py
"""
import os
import sys

import pandas as pd
import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

from core.logic import FinancialModel, SaaSModelConfig, run_simulation
from utils.exceptions import ConfigurationError


class TestSaaSModelConfig:
    """Test suite for SaaSModelConfig."""

    def test_valid_config(self):
        """Test valid configuration creation."""
        config = SaaSModelConfig(
            starting_customers=50,
            monthly_growth_rate=0.20,
            churn_rate=0.05,
            price_per_customer=100,
            fixed_costs=5000,
            variable_cost_per_customer=10,
        )
        assert config.customers == 50
        assert config.growth_rate == 0.20
        assert config.churn_rate == 0.05

    def test_invalid_customers(self):
        """Test negative customers raises error."""
        with pytest.raises(ConfigurationError):
            SaaSModelConfig(
                starting_customers=-1,
                monthly_growth_rate=0.20,
                churn_rate=0.05,
                price_per_customer=100,
                fixed_costs=5000,
                variable_cost_per_customer=10,
            )

    def test_invalid_growth_rate(self):
        """Test invalid growth rate raises error."""
        with pytest.raises(ConfigurationError):
            SaaSModelConfig(
                starting_customers=50,
                monthly_growth_rate=1.5,  # > 1
                churn_rate=0.05,
                price_per_customer=100,
                fixed_costs=5000,
                variable_cost_per_customer=10,
            )

    def test_invalid_churn_rate(self):
        """Test invalid churn rate raises error."""
        with pytest.raises(ConfigurationError):
            SaaSModelConfig(
                starting_customers=50,
                monthly_growth_rate=0.20,
                churn_rate=1.5,  # > 1
                price_per_customer=100,
                fixed_costs=5000,
                variable_cost_per_customer=10,
            )

    def test_repr(self):
        """Test string representation."""
        config = SaaSModelConfig(
            starting_customers=50,
            monthly_growth_rate=0.20,
            churn_rate=0.05,
            price_per_customer=100,
            fixed_costs=5000,
            variable_cost_per_customer=10,
        )
        repr_str = repr(config)
        assert "Start=50" in repr_str
        assert "Growth=20.0%" in repr_str


class TestRunSimulation:
    """Test suite for run_simulation."""

    def test_valid_simulation(self):
        """Test simulation with valid config."""
        config = SaaSModelConfig(
            starting_customers=10,
            monthly_growth_rate=0.10,
            churn_rate=0.05,
            price_per_customer=100,
            fixed_costs=1000,
            variable_cost_per_customer=10,
            cac_simplified=100,
        )
        df = run_simulation(config, months=12)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 12
        assert "Month" in df.columns
        assert "MRR" in df.columns
        assert "Total_Customers" in df.columns

    def test_simulation_months(self):
        """Test simulation for specified months."""
        config = SaaSModelConfig(
            starting_customers=10,
            monthly_growth_rate=0.10,
            churn_rate=0.05,
            price_per_customer=100,
            fixed_costs=1000,
            variable_cost_per_customer=10,
        )
        df = run_simulation(config, months=6)
        assert len(df) == 6


class TestFinancialModel:
    """Test suite for FinancialModel OOP class."""

    def test_run_simulation_wrapper(self):
        """Test FinancialModel.run_simulation static method."""
        config = SaaSModelConfig(
            starting_customers=10,
            monthly_growth_rate=0.10,
            churn_rate=0.05,
            price_per_customer=100,
            fixed_costs=1000,
            variable_cost_per_customer=10,
        )
        df = FinancialModel.run_simulation(config, months=12)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 12


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
