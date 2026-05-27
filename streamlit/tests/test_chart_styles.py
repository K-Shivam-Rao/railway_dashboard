"""Tests for utils/chart_styles.py — Plotly chart styling utilities."""
import pytest
import sys
import os
import plotly.graph_objects as go

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

from utils.chart_styles import (
    style_chart,
    style_pie,
    style_indicator,
    style_df,
    COLOR_SCHEMES,
)


def _make_fig():
    return go.Figure(data=[go.Scatter(x=[1, 2, 3], y=[4, 5, 6])])


class TestStyleChart:
    """Test style_chart()."""

    def test_returns_figure(self):
        fig = style_chart(_make_fig())
        assert isinstance(fig, go.Figure)

    def test_sets_paper_bgcolor(self):
        fig = style_chart(_make_fig())
        assert fig.layout.paper_bgcolor == "rgba(0,0,0,0)"

    def test_accepts_kwargs(self):
        fig = style_chart(_make_fig(), height=400)
        assert fig.layout.height == 400

    def test_handles_legend_true(self):
        fig = style_chart(_make_fig(), legend=True)
        assert fig.layout.showlegend is True

    def test_handles_legend_false(self):
        fig = style_chart(_make_fig(), legend=False)
        assert fig.layout.showlegend is False

    def test_with_title_kwarg(self):
        fig = style_chart(_make_fig(), title="Test Chart")
        assert fig.layout.title.text == "Test Chart"


class TestStylePie:
    """Test style_pie()."""

    def test_returns_figure(self):
        fig = style_pie(_make_fig())
        assert isinstance(fig, go.Figure)

    def test_sets_dragmode_false(self):
        fig = style_pie(_make_fig())
        assert fig.layout.dragmode is False

    def test_with_title(self):
        fig = style_pie(_make_fig(), title="Pie Chart")
        assert fig.layout.annotations is not None

    def test_with_height(self):
        fig = style_pie(_make_fig(), height=300)
        assert fig.layout.height == 300


class TestStyleIndicator:
    """Test style_indicator()."""

    def test_returns_figure(self):
        fig = style_indicator(_make_fig())
        assert isinstance(fig, go.Figure)

    def test_sets_height(self):
        fig = style_indicator(_make_fig(), height=500)
        assert fig.layout.height == 500


class TestStyleDf:
    """Test style_df()."""

    def test_returns_styler_for_dataframe(self):
        import pandas as pd
        df = pd.DataFrame({"a": [1, 2]})
        result = style_df(df)
        # Should return a Styler or the df itself on error
        assert result is not None


class TestColorSchemes:
    """Test COLOR_SCHEMES constant."""

    def test_is_dict(self):
        assert isinstance(COLOR_SCHEMES, dict)

    def test_has_required_schemes(self):
        required = {"status_reverse", "blue", "teal", "amber", "fuchsia", "kpi", "aurora", "status_continuous"}
        assert required.issubset(set(COLOR_SCHEMES.keys()))

    def test_schemes_are_lists(self):
        for name, scheme in COLOR_SCHEMES.items():
            assert isinstance(scheme, list), f"{name} is not a list"

    def test_status_continuous_is_nested_list(self):
        scheme = COLOR_SCHEMES["status_continuous"]
        assert all(isinstance(item, list) for item in scheme)
        assert len(scheme) == 3
