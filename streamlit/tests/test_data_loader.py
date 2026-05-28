"""
Unit tests for data/loader.py
"""
import os
import sys

import pandas as pd
import polars as pl
import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

from data.loader import DataLoader, _validate_data
from utils.exceptions import DataLoadError, DataValidationError


class TestDataLoader:
    """Test suite for DataLoader class."""

    def test_parquet_path(self):
        """Test _get_parquet_path returns valid path."""
        path = DataLoader._get_parquet_path()
        assert isinstance(path, str)
        assert path.endswith("stations.parquet")

    def test_csv_path(self):
        """Test _get_csv_path returns valid path."""
        path = DataLoader._get_csv_path()
        assert isinstance(path, str)
        assert path.endswith("stations.csv")

    def test_load_data_polars_returns_dataframe(self):
        """Test load_data_polars returns a Polars DataFrame."""
        try:
            df = DataLoader.load_data_polars()
            assert isinstance(df, pl.DataFrame)
            assert len(df) > 0
            # Check required columns
            required = {"station", "platform", "gate_id", "door_state", "sensor_temp", "sensor_vib", "people"}
            assert required.issubset(set(df.columns))
        except DataLoadError:
            pytest.skip("Data loading failed, skipping test")

    def test_transform_data_fast_returns_dataframe(self):
        """Test transform_data_fast returns transformed DataFrame."""
        try:
            df_pl = DataLoader.load_data_polars()
            df_transformed = DataLoader.transform_data_fast(df_pl)
            assert isinstance(df_transformed, pl.DataFrame)
            # Check new columns were added
            expected_cols = {"sync_score", "maintenance_status", "risk_score", "congestion_score"}
            assert expected_cols.issubset(set(df_transformed.columns))
        except DataLoadError:
            pytest.skip("Data loading failed, skipping test")

    def test_validate_data_valid(self):
        """Test _validate_data with valid data."""
        df = pl.DataFrame({
            "station": ["Station A", "Station B"],
            "platform": ["1", "2"],
            "gate_id": ["G1", "G2"],
            "door_state": ["open", "closed"],
            "sensor_temp": [25.0, 26.0],
            "sensor_vib": [0.1, 0.2],
            "people": [100, 150],
        })
        # Should not raise any exception
        try:
            _validate_data(df)
        except DataValidationError:
            pytest.fail("_validate_data raised DataValidationError for valid data")

    def test_validate_data_missing_columns(self):
        """Test _validate_data raises DataValidationError for missing columns."""
        df = pl.DataFrame({
            "station": ["Station A"],
            # Missing required columns
        })
        with pytest.raises(DataValidationError):
            _validate_data(df)

    def test_load_and_transform_data_returns_pandas(self):
        """Test load_and_transform_data returns Pandas DataFrame."""
        try:
            df = DataLoader.load_and_transform_data()
            assert isinstance(df, pd.DataFrame)
            if len(df) == 0:
                pytest.skip("Data loading returned empty DataFrame, skipping test")
        except DataLoadError:
            pytest.skip("Data loading failed, skipping test")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
