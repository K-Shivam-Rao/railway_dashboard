"""
Unit tests for helper functions defined in main.py
"""
import pytest
import pandas as pd
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

# Import from main.py (where these are defined)
from main import format_euro, get_status_color, format_number, format_score, convert_to_csv


class TestFormatEuro:
    """Test format_euro() from main.py."""

    def test_millions(self):
        """Test formatting millions."""
        result = format_euro(1_500_000)
        assert "M" in result
        assert "~" in result

    def test_thousands(self):
        """Test formatting thousands."""
        result = format_euro(2_500)
        assert "K" in result

    def test_small_value(self):
        """Test formatting small values."""
        result = format_euro(500)
        assert "~" in result
        assert "K" not in result

    def test_zero(self):
        """Test formatting zero."""
        result = format_euro(0)
        assert "~" in result

    def test_negative(self):
        """Test formatting negative value."""
        result = format_euro(-100)
        # Should handle gracefully
        assert isinstance(result, str)

    def test_very_large(self):
        """Test formatting very large values."""
        result = format_euro(1_000_000_000)
        assert "M" in result

    def test_one_million_exact(self):
        """Test formatting exactly 1 million."""
        result = format_euro(1_000_000)
        assert "M" in result


class TestGetStatusColor:
    """Test get_status_color() from main.py."""

    def test_high_value(self):
        """Test value >= threshold_high returns green."""
        result = get_status_color(90, 80, 60)
        assert result == "#10b981"

    def test_medium_value(self):
        """Test threshold_low <= value < threshold_high returns yellow."""
        result = get_status_color(70, 80, 60)
        assert result == "#f59e0b"

    def test_low_value(self):
        """Test value < threshold_low returns red."""
        result = get_status_color(50, 80, 60)
        assert result == "#ef4444"

    def test_boundary_high(self):
        """Test value exactly at high threshold."""
        result = get_status_color(80, 80, 60)
        assert result == "#10b981"

    def test_boundary_low(self):
        """Test value exactly at low threshold."""
        result = get_status_color(60, 80, 60)
        assert result == "#f59e0b"

    def test_below_low(self):
        """Test value just below low threshold."""
        result = get_status_color(59, 80, 60)
        assert result == "#ef4444"

    def test_negative_value(self):
        """Test negative value."""
        result = get_status_color(-10, 80, 60)
        assert result == "#ef4444"


class TestFormatNumber:
    """Test format_number() from main.py."""

    def test_thousands(self):
        """Test formatting thousands."""
        result = format_number(1500)
        assert "~" in result

    def test_exact_thousand(self):
        """Test formatting exactly 1000."""
        result = format_number(1000)
        assert "~" in result

    def test_small_number(self):
        """Test formatting small number."""
        result = format_number(500)
        assert "~" in result

    def test_zero(self):
        """Test formatting zero."""
        result = format_number(0)
        assert "~" in result

    def test_large_number(self):
        """Test formatting large number."""
        result = format_number(1_000_000)
        assert "~" in result


class TestFormatScore:
    """Test format_score() from main.py."""

    def test_normal_score(self):
        """Test formatting normal score."""
        result = format_score(8.5)
        assert "~" in result
        assert "/10" in result

    def test_zero_score(self):
        """Test formatting zero score."""
        result = format_score(0)
        assert isinstance(result, str)

    def test_full_score(self):
        """Test formatting score of 10."""
        result = format_score(10)
        assert "/10" in result

    def test_none_score(self):
        """Test formatting None score returns fallback."""
        result = format_score(None)
        # Should return a string (either 'N/A' or similar fallback)
        assert isinstance(result, str)


class TestConvertToCsv:
    """Test convert_to_csv() from main.py."""

    def test_normal_dataframe(self):
        """Test convert DataFrame to CSV bytes."""
        df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
        result = convert_to_csv(df)
        assert isinstance(result, bytes)
        assert b"A,B" in result

    def test_empty_dataframe(self):
        """Test convert empty DataFrame."""
        df = pd.DataFrame()
        result = convert_to_csv(df)
        assert isinstance(result, bytes)

    def test_single_row(self):
        """Test convert single row DataFrame."""
        df = pd.DataFrame({"A": [1]})
        result = convert_to_csv(df)
        assert isinstance(result, bytes)
        assert b"A" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
