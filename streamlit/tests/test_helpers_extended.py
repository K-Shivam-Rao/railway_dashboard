"""Extended tests for utils/helpers.py — covering edge cases for all
formatting functions: format_euro, format_compact, format_score,
format_full, smart_format, get_status_color, convert_to_csv,
format_breakeven."""

import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

from utils.helpers import (
    convert_to_csv,
    format_breakeven,
    format_compact,
    format_euro,
    format_full,
    format_score,
    get_status_color,
    show_loading_spinner,
    smart_format,
)


class TestFormatEuroExtended:
    def test_none(self):
        assert format_euro(None) == "—"

    def test_billions(self):
        result = format_euro(2_500_000_000)
        assert "B" in result

    def test_millions_exact(self):
        result = format_euro(1_000_000)
        assert "1.0M" in result

    def test_thousands_exact(self):
        result = format_euro(1_000)
        assert "1.0K" in result

    def test_zero(self):
        result = format_euro(0)
        assert "~€0" in result

    def test_negative(self):
        result = format_euro(-1500)
        assert "-" in result or "K" in result

    def test_small_value_no_notation(self):
        result = format_euro(500)
        assert "~€500" in result

    def test_boundary_999(self):
        result = format_euro(999)
        assert "~€999" in result

    def test_boundary_1000(self):
        result = format_euro(1000)
        assert "K" in result


class TestGetStatusColorExtended:
    def test_at_threshold_high(self):
        assert get_status_color(80, 80, 60) == "#10b981"

    def test_at_threshold_low(self):
        assert get_status_color(60, 80, 60) == "#f59e0b"

    def test_below_threshold_low(self):
        assert get_status_color(59, 80, 60) == "#ef4444"

    def test_equal_thresholds(self):
        assert get_status_color(50, 50, 50) == "#10b981"

    def test_negative_values(self):
        assert get_status_color(-10, 80, 60) == "#ef4444"

    def test_float_values(self):
        assert get_status_color(75.5, 80, 60) == "#f59e0b"


class TestSmartFormatExtended:
    def test_none(self):
        assert smart_format(None) == "—"

    def test_billions(self):
        assert "B" in smart_format(2_500_000_000)

    def test_millions(self):
        assert "M" in smart_format(5_000_000)

    def test_thousands(self):
        assert "K" in smart_format(2_500)

    def test_small_number(self):
        assert smart_format(842) == "842"

    def test_zero(self):
        assert smart_format(0) == "0"

    def test_negative(self):
        result = smart_format(-1234)
        assert "K" in result
        assert "-" in result

    def test_dict_input(self):
        result = smart_format({"a": 1000, "b": 500})
        assert isinstance(result, str)
        assert "K" in result or "a" in result

    def test_list_input(self):
        result = smart_format([1000, 500])
        assert isinstance(result, str)
        assert "K" in result

    def test_tuple_input(self):
        result = smart_format((1000, 2000))
        assert isinstance(result, str)

    def test_set_input(self):
        result = smart_format({1000, 2000})
        assert isinstance(result, str)

    def test_string_input(self):
        result = smart_format("hello")
        assert result == "hello"

    def test_bool_input(self):
        result = smart_format(True)
        assert result == "1" or isinstance(result, str)


class TestFormatCompactExtended:
    def test_none(self):
        assert format_compact(None) == "—"

    def test_billions(self):
        result = format_compact(1_500_000_000)
        assert "B" in result
        assert "~" not in result

    def test_millions(self):
        result = format_compact(3_000_000)
        assert "M" in result
        assert "~" not in result

    def test_thousands(self):
        result = format_compact(1_200)
        assert "K" in result

    def test_small(self):
        assert format_compact(500) == "500"

    def test_zero(self):
        assert format_compact(0) == "0"

    def test_negative(self):
        result = format_compact(-5000)
        assert result == "-5.0K"


class TestFormatFullExtended:
    def test_none(self):
        assert format_full(None) == "—"

    def test_large_number(self):
        assert format_full(1234567) == "1,234,567"

    def test_small_number(self):
        assert format_full(42) == "42"

    def test_zero(self):
        assert format_full(0) == "0"

    def test_negative(self):
        assert format_full(-1234) == "-1,234"

    def test_dict_input(self):
        result = format_full({"a": 1000})
        assert isinstance(result, str)

    def test_float(self):
        # format_full uses ,.0f so it rounds floats
        result = format_full(1234.7)
        assert "1,235" in result

    def test_string_non_numeric(self):
        result = format_full("hello")
        assert result == "hello"


class TestFormatScoreExtended:
    def test_rounds_to_nearest_int(self):
        assert format_score(7.2) == "7/10"

    def test_rounds_up(self):
        assert format_score(7.6) == "8/10"

    def test_zero(self):
        assert format_score(0) == "0/10"

    def test_max(self):
        assert format_score(10) == "10/10"

    def test_negative(self):
        assert format_score(-5) == "-5/10"

    def test_float_with_many_decimals(self):
        result = format_score(8.456)
        assert "8" in result  # int(round()) = 8


class TestConvertToCsvExtended:
    def test_empty_df(self):
        df = pd.DataFrame()
        result = convert_to_csv(df)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_single_column(self):
        df = pd.DataFrame({"Name": ["Alice"]})
        result = convert_to_csv(df)
        assert b"Name" in result

    def test_with_nulls(self):
        df = pd.DataFrame({"A": [1, None], "B": [None, "hello"]})
        result = convert_to_csv(df)
        assert isinstance(result, bytes)

    def test_encoding_utf8(self):
        df = pd.DataFrame({"name": ["München", "Köln"]})
        result = convert_to_csv(df)
        assert isinstance(result, bytes)
        # Should be valid UTF-8
        result.decode("utf-8")


class TestShowLoadingSpinner:
    """Test show_loading_spinner returns a context manager."""

    def test_returns_spinner(self):
        spinner = show_loading_spinner("Loading...")
        assert hasattr(spinner, "__enter__")
        assert hasattr(spinner, "__exit__")

    def test_default_text(self):
        spinner = show_loading_spinner()
        assert spinner is not None

    def test_custom_text(self):
        spinner = show_loading_spinner("Custom loading message")
        assert spinner is not None


class TestFormatBreakevenExtended:
    """Test format_breakeven from helpers.py."""

    def test_valid_month(self):
        result = format_breakeven(12)
        assert result == "Month 12"

    def test_nan_value(self):
        result = format_breakeven(float("nan"))
        assert result == "Not achieved"

    def test_zero(self):
        result = format_breakeven(0)
        assert result == "Month 0"

    def test_none_pd(self):
        result = format_breakeven(pd.NA)
        assert result == "Not achieved"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
