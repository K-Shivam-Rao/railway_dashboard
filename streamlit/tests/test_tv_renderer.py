"""
Unit tests for core/tv_renderer.py — pure helper functions only.
The Streamlit-dependent render functions (_render_kpi_row, render_tv)
require mocking streamlit and are tested via integration tests.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

# Mock streamlit before importing tv_renderer


class TestTVRendererConstants:
    """Test DOMAIN constants."""

    def test_domains_list(self):
        from core.tv_renderer import DOMAINS
        assert isinstance(DOMAINS, list)
        assert len(DOMAINS) == 5
        assert "security" in DOMAINS
        assert "sustain" in DOMAINS
        assert "passenger" in DOMAINS
        assert "asset" in DOMAINS
        assert "climate" in DOMAINS

    def test_domain_meta_all_keys(self):
        from core.tv_renderer import DOMAIN_META, DOMAINS
        assert isinstance(DOMAIN_META, dict)
        for domain in DOMAINS:
            assert domain in DOMAIN_META
            meta = DOMAIN_META[domain]
            assert "icon" in meta
            assert "short" in meta
            assert "label" in meta

    def test_domain_meta_has_icons(self):
        from core.tv_renderer import DOMAIN_META
        for meta in DOMAIN_META.values():
            assert isinstance(meta["icon"], str)
            assert isinstance(meta["short"], str)
            assert isinstance(meta["label"], str)
            assert len(meta["short"]) > 0


class TestMakeDomainGauge:
    """Test tv_renderer._make_domain_gauge()."""

    def test_returns_figure(self):
        from core.tv_renderer import _make_domain_gauge
        fig = _make_domain_gauge(75.0, "Test Gauge", "#f59e0b")
        assert fig is not None
        assert len(fig.data) > 0

    def test_contains_indicator(self):
        from core.tv_renderer import _make_domain_gauge
        fig = _make_domain_gauge(75.0, "Test", "#f59e0b")
        assert fig.data[0].type == "indicator"
        # Check the reported value — gauge+number type uses go.Indicator
        assert hasattr(fig.data[0], "value")

    def test_value_0_to_100(self):
        from core.tv_renderer import _make_domain_gauge
        for val in [0, 25, 50, 75, 100]:
            fig = _make_domain_gauge(val, f"Val {val}", "#f59e0b")
            assert fig.data[0].type == "indicator"

    def test_layout_has_title(self):
        from core.tv_renderer import _make_domain_gauge
        fig = _make_domain_gauge(50.0, "Security", "#f59e0b")
        assert "Security" in str(fig.layout.title.text)

    def test_height_set(self):
        from core.tv_renderer import _make_domain_gauge
        fig = _make_domain_gauge(50.0, "Test", "#f59e0b")
        assert fig.layout.height == 140


class TestMakeRadarChart:
    """Test tv_renderer._make_radar_chart()."""

    def test_returns_figure(self):
        from core.tv_renderer import _make_radar_chart
        scores = {"security": 80, "sustain": 70, "passenger": 60, "asset": 90, "climate": 50}
        fig = _make_radar_chart(scores, "Test Radar")
        assert fig is not None
        assert len(fig.data) > 0

    def test_is_scatterpolar(self):
        from core.tv_renderer import _make_radar_chart
        scores = {"security": 80, "sustain": 70, "passenger": 60, "asset": 90, "climate": 50}
        fig = _make_radar_chart(scores, "Test")
        assert fig.data[0].type == "scatterpolar"

    def test_has_five_categories(self):
        from core.tv_renderer import _make_radar_chart
        scores = {"security": 80, "sustain": 70, "passenger": 60, "asset": 90, "climate": 50}
        fig = _make_radar_chart(scores, "Test")
        # Should have all 5 categories + closing loop
        assert len(fig.data[0].theta) >= 5

    def test_loop_closed(self):
        from core.tv_renderer import _make_radar_chart
        scores = {"security": 80, "sustain": 70, "passenger": 60, "asset": 90, "climate": 50}
        fig = _make_radar_chart(scores, "Test")
        # First and last theta should be same (loop closed)
        theta = list(fig.data[0].theta)
        assert theta[0] == theta[-1]


class TestMakeBarChart:
    """Test tv_renderer._make_bar_chart()."""

    def test_returns_figure(self):
        from core.tv_renderer import _make_bar_chart
        data = {"Berlin Hbf": 85, "München Hbf": 72, "Frankfurt": 65}
        fig = _make_bar_chart(data, "Test Bar", "#f59e0b")
        assert fig is not None
        assert len(fig.data) > 0

    def test_is_horizontal_bar(self):
        from core.tv_renderer import _make_bar_chart
        data = {"S1": 80, "S2": 70}
        fig = _make_bar_chart(data, "Test", "#f59e0b")
        assert fig.data[0].type == "bar"
        assert fig.data[0].orientation == "h"

    def test_sorted_by_value(self):
        from core.tv_renderer import _make_bar_chart
        data = {"A": 30, "B": 90, "C": 50}
        fig = _make_bar_chart(data, "Test", "#f59e0b")
        # Values should be sorted descending
        y_labels = list(fig.data[0].y)
        assert y_labels[0] == "B"  # Highest value

    def test_empty_data_still_returns_figure(self):
        from core.tv_renderer import _make_bar_chart
        fig = _make_bar_chart({}, "Empty", "#f59e0b")
        assert fig is not None


class TestMakeAllStationsBar:
    """Test tv_renderer._make_all_stations_bar()."""

    def test_returns_figure(self):
        from core.tv_renderer import STATIONS, _make_all_stations_bar
        # Create mock TotalVisionData objects
        all_data = {}
        for s in STATIONS[:3]:
            mock_data = type('MockTV', (), {'scores_dict': lambda self: {"security": 75},
                                            'security': type('MockSec', (), {'threat_level': 20, 'incidents_cyber': 3, 'avg_response_time': 2.5})()})()
            mock_data.score = lambda d, s=s: 75 if d == "security" else 65
            all_data[s] = mock_data

        fig = _make_all_stations_bar(all_data, "security", "#f59e0b")
        assert fig is not None


class TestMakeCorrelationHeatmap:
    """Test tv_renderer._make_correlation_heatmap()."""

    def test_returns_figure(self):
        from core.tv_renderer import _make_correlation_heatmap
        matrix = {
            "security": {"security": 1.0, "sustain": 0.3, "passenger": 0.5, "asset": 0.7, "climate": 0.2},
            "sustain": {"security": 0.3, "sustain": 1.0, "passenger": 0.4, "asset": 0.6, "climate": 0.8},
            "passenger": {"security": 0.5, "sustain": 0.4, "passenger": 1.0, "asset": 0.3, "climate": 0.1},
            "asset": {"security": 0.7, "sustain": 0.6, "passenger": 0.3, "asset": 1.0, "climate": 0.4},
            "climate": {"security": 0.2, "sustain": 0.8, "passenger": 0.1, "asset": 0.4, "climate": 1.0},
        }
        fig = _make_correlation_heatmap(matrix)
        assert fig is not None
        assert len(fig.data) > 0

    def test_is_heatmap(self):
        from core.tv_renderer import _make_correlation_heatmap
        matrix = {"security": {"security": 1.0, "sustain": 0.0, "passenger": 0.0, "asset": 0.0, "climate": 0.0},
                  "sustain": {"security": 0.0, "sustain": 1.0, "passenger": 0.0, "asset": 0.0, "climate": 0.0},
                  "passenger": {"security": 0.0, "sustain": 0.0, "passenger": 1.0, "asset": 0.0, "climate": 0.0},
                  "asset": {"security": 0.0, "sustain": 0.0, "passenger": 0.0, "asset": 1.0, "climate": 0.0},
                  "climate": {"security": 0.0, "sustain": 0.0, "passenger": 0.0, "asset": 0.0, "climate": 1.0}}
        fig = _make_correlation_heatmap(matrix)
        assert fig.data[0].type == "heatmap"

    def test_5x5_matrix(self):
        from core.tv_renderer import _make_correlation_heatmap
        matrix = {d: {d2: 1.0 if d == d2 else 0.0 for d2 in ["security", "sustain", "passenger", "asset", "climate"]}
                  for d in ["security", "sustain", "passenger", "asset", "climate"]}
        fig = _make_correlation_heatmap(matrix)
        z = fig.data[0].z
        assert len(z) == 5
        assert len(z[0]) == 5

    def test_colorscale_defined(self):
        from core.tv_renderer import _make_correlation_heatmap
        matrix = {"security": {"security": 1.0, "sustain": 0.5, "passenger": 0.0, "asset": -0.5, "climate": -1.0},
                  "sustain": {"security": 0.5, "sustain": 1.0, "passenger": 0.5, "asset": 0.0, "climate": -0.5},
                  "passenger": {"security": 0.0, "sustain": 0.5, "passenger": 1.0, "asset": 0.5, "climate": 0.0},
                  "asset": {"security": -0.5, "sustain": 0.0, "passenger": 0.5, "asset": 1.0, "climate": 0.5},
                  "climate": {"security": -1.0, "sustain": -0.5, "passenger": 0.0, "asset": 0.5, "climate": 1.0}}
        fig = _make_correlation_heatmap(matrix)
        assert fig.data[0].colorscale is not None


class TestChartInfoBar:
    """Test tv_renderer._chart_info_bar()."""

    def test_returns_string(self):
        from core.tv_renderer import _chart_info_bar
        mock_tv = _make_mock_tv_data()
        html = _chart_info_bar("security", mock_tv)
        assert isinstance(html, str)

    def test_security_domain_has_metrics(self):
        from core.tv_renderer import _chart_info_bar
        mock_tv = _make_mock_tv_data()
        html = _chart_info_bar("security", mock_tv)
        assert "tv-chart-info-bar" in html
        assert "Threat" in html

    def test_sustain_domain_has_energy(self):
        from core.tv_renderer import _chart_info_bar
        mock_tv = _make_mock_tv_data()
        html = _chart_info_bar("sustain", mock_tv)
        assert "Energy" in html or "Carbon" in html

    def test_passenger_domain_has_crowding(self):
        from core.tv_renderer import _chart_info_bar
        mock_tv = _make_mock_tv_data()
        html = _chart_info_bar("passenger", mock_tv)
        assert "Crowding" in html or "Satisfaction" in html

    def test_asset_domain_has_rul(self):
        from core.tv_renderer import _chart_info_bar
        mock_tv = _make_mock_tv_data()
        html = _chart_info_bar("asset", mock_tv)
        assert "RUL" in html or "Backlog" in html

    def test_climate_domain_has_resilience(self):
        from core.tv_renderer import _chart_info_bar
        mock_tv = _make_mock_tv_data()
        html = _chart_info_bar("climate", mock_tv)
        assert "Resilience" in html or "Flood" in html


def _make_mock_tv_data():
    """Helper to create a mock TotalVisionData object."""
    class MockDomain:
        threat_level = 20
        incidents_cyber = 3
        avg_response_time = 2.5
        energy_kwh = 4500
        carbon_tco2e = 1.2
        green_energy_pct = 65
        satisfaction_score = 82
        crowding_index = 45
        dwell_time_avg = 35
        fleet_rul_pct = 78
        backlog_total = 12
        sensor_healthy = 45
        gates_total = 48
        resilience_score = 70
        flood_risk = 25
        adaptation_readiness_pct = 60

    class MockTV:
        security = MockDomain()
        sustainability = MockDomain()
        passenger = MockDomain()
        asset = MockDomain()
        climate = MockDomain()

        def scores_dict(self):
            return {"security": 75, "sustain": 70, "passenger": 80, "asset": 65, "climate": 72}

    return MockTV()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
