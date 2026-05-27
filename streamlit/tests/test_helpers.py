"""
Unit tests for utils/helpers.py
"""
import pytest
import sys
import os
import pandas as pd

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

from utils.helpers import format_euro, get_status_color, format_compact, format_score, convert_to_csv, smart_format, format_full


class TestHelpers:
    """Test suite for helper functions."""

    def test_format_euro_millions(self):
        """Test format_euro with millions."""
        result = format_euro(1_500_000)
        assert "M" in result

    def test_format_euro_thousands(self):
        """Test format_euro with thousands."""
        result = format_euro(2_500)
        assert "K" in result

    def test_format_euro_small(self):
        """Test format_euro with small values."""
        result = format_euro(500)
        assert "~" in result
        assert "K" not in result

    def test_get_status_color_high(self):
        """Test get_status_color for high value."""
        result = get_status_color(90, 80, 60)
        assert result == "#10b981"

    def test_get_status_color_medium(self):
        """Test get_status_color for medium value."""
        result = get_status_color(70, 80, 60)
        assert result == "#f59e0b"

    def test_get_status_color_low(self):
        """Test get_status_color for low value."""
        result = get_status_color(50, 80, 60)
        assert result == "#ef4444"

    def test_format_compact_thousands(self):
        """Test format_compact with thousands."""
        result = format_compact(1500)
        assert "k" in result.lower() or "K" in result

    def test_smart_format_numeric(self):
        """Test smart_format with numeric values."""
        result = smart_format(12345)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_smart_format_dict(self):
        """Test smart_format with dict (should handle defensively)."""
        result = smart_format({"a": 1, "b": 2})
        assert isinstance(result, str)

    def test_smart_format_list(self):
        """Test smart_format with list (should handle defensively)."""
        result = smart_format([1, 2, 3])
        assert isinstance(result, str)

    def test_format_full_numeric(self):
        """Test format_full with numeric values."""
        result = format_full(12345)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_format_full_dict(self):
        """Test format_full with dict (should handle defensively)."""
        result = format_full({"a": 1})
        assert isinstance(result, str)

    def test_format_full_none(self):
        """Test format_full with None."""
        result = format_full(None)
        assert result == "—"  # Em dash

    def test_format_score(self):
        """Test format_score."""
        result = format_score(8.5)
        # Python banker's rounding: round(8.5) -> 8
        assert result == "8/10"

    def test_convert_to_csv(self):
        """Test convert_to_csv returns valid CSV bytes."""
        df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
        result = convert_to_csv(df)
        assert isinstance(result, bytes)
        assert b"A,B" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
