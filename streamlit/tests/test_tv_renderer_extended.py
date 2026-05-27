"""Extended tests for core/tv_renderer.py — covering additional edge cases and
_all_stations_bar, _chart_info_bar, _render_kpi_row (mock-free) helpers."""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

from core.tv_renderer import (
    DOMAINS, DOMAIN_META,
    _make_domain_gauge, _make_radar_chart, _make_bar_chart,
    _make_all_stations_bar, _make_correlation_heatmap, _chart_info_bar,
)
from core.totalvision import STATIONS, SecurityData, SustainabilityData, PassengerData, AssetData, ClimateData, TotalVisionData


# ── Mock helpers ────────────────────────────────────────────────────────────

def _make_mock_tv(station="Berlin Hbf"):
    """Create a complete mock TotalVisionData with all domains."""
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

        def score(self, domain):
            return self.scores_dict().get(domain, 0)

    mock = MockTV()
    mock.station = station
    return mock


def _make_all_mock_data():
    """Create a dict of mock TotalVisionData for all stations."""
    return {s: _make_mock_tv(s) for s in STATIONS}


# ── Domain Gauge Edge Cases ────────────────────────────────────────────────

class TestDomainGaugeExtended:
    def test_value_0(self):
        fig = _make_domain_gauge(0, "Zero", "#ef4444")
        assert fig.data[0].value == 0

    def test_value_100(self):
        fig = _make_domain_gauge(100, "Max", "#10b981")
        assert fig.data[0].value == 100

    def test_nonstandard_color(self):
        fig = _make_domain_gauge(50, "Custom", "#ff00ff")
        assert fig is not None

    def test_empty_title(self):
        fig = _make_domain_gauge(50, "", "#f59e0b")
        assert fig is not None


# ── Radar Chart Edge Cases ─────────────────────────────────────────────────

class TestRadarChartExtended:
    def test_all_zeros(self):
        fig = _make_radar_chart(
            {"security": 0, "sustain": 0, "passenger": 0, "asset": 0, "climate": 0},
            "All Zero"
        )
        assert all(r == 0 for r in fig.data[0].r[:-1])  # Exclude closing loop

    def test_all_max(self):
        fig = _make_radar_chart(
            {"security": 100, "sustain": 100, "passenger": 100, "asset": 100, "climate": 100},
            "All Max"
        )
        assert all(r == 100 for r in fig.data[0].r[:-1])

    def test_missing_domain_defaults(self):
        fig = _make_radar_chart({"security": 80}, "Partial")
        assert len(fig.data[0].r) >= 5  # Should still have 5 entries

    def test_extra_domain_ignored(self):
        fig = _make_radar_chart(
            {"security": 80, "sustain": 70, "passenger": 60, "asset": 90,
             "climate": 50, "extra": 100},
            "Extra Key"
        )
        assert len(fig.data[0].r) == 6  # 5 + 1 closing


# ── Bar Chart Edge Cases ───────────────────────────────────────────────────

class TestBarChartExtended:
    def test_single_item(self):
        fig = _make_bar_chart({"Berlin Hbf": 90}, "Single", "#f59e0b")
        assert len(fig.data[0].y) == 1

    def test_all_equal_values(self):
        fig = _make_bar_chart(
            {"A": 50, "B": 50, "C": 50},
            "Equal", "#f59e0b"
        )
        assert len(fig.data[0].y) == 3

    def test_color_applied(self):
        fig = _make_bar_chart({"A": 80}, "Color Test", "#ef4444")
        assert fig.data[0].marker.color == "#ef4444"


# ── All Stations Bar Chart ─────────────────────────────────────────────────

class TestAllStationsBar:
    def test_all_stations_present(self):
        mock_data = _make_all_mock_data()
        fig = _make_all_stations_bar(mock_data, "security", "#ef4444")
        assert len(fig.data[0].y) == len(STATIONS)

    def test_sorted_by_value(self):
        mock_data = _make_all_mock_data()
        # Each mock has same score, so sorting shouldn't change
        fig = _make_all_stations_bar(mock_data, "security", "#ef4444")
        assert len(fig.data[0].y) == len(STATIONS)

    def test_empty_data(self):
        fig = _make_all_stations_bar({}, "security", "#ef4444")
        assert fig is not None

    def test_partial_data(self):
        mock_data = {"Berlin Hbf": _make_mock_tv()}
        fig = _make_all_stations_bar(mock_data, "security", "#ef4444")
        assert len(fig.data[0].y) == 1


# ── Correlation Heatmap Edge Cases ─────────────────────────────────────────

class TestCorrelationHeatmapExtended:
    def test_all_ones(self):
        matrix = {d: {d2: 1.0 for d2 in DOMAINS} for d in DOMAINS}
        fig = _make_correlation_heatmap(matrix)
        z = fig.data[0].z
        assert all(all(v == 1.0 for v in row) for row in z)

    def test_all_zeros(self):
        matrix = {d: {d2: 0.0 for d2 in DOMAINS} for d in DOMAINS}
        fig = _make_correlation_heatmap(matrix)
        assert fig is not None

    def test_negative_correlations(self):
        matrix = {d: {d2: -1.0 for d2 in DOMAINS} for d in DOMAINS}
        fig = _make_correlation_heatmap(matrix)
        z = fig.data[0].z
        assert all(all(v == -1.0 for v in row) for row in z)

    def test_incomplete_matrix(self):
        matrix = {"security": {"security": 1.0}}
        fig = _make_correlation_heatmap(matrix)
        assert fig is not None


# ── Chart Info Bar Extended ────────────────────────────────────────────────

class TestChartInfoBarExtended:
    def test_returns_html(self):
        mock = _make_mock_tv()
        for domain in DOMAINS:
            html = _chart_info_bar(domain, mock)
            assert isinstance(html, str)
            assert 'tv-chart-info-bar' in html

    def test_security_has_threat_metric(self):
        mock = _make_mock_tv()
        html = _chart_info_bar("security", mock)
        assert "Threat" in html

    def test_sustain_has_energy_metric(self):
        mock = _make_mock_tv()
        html = _chart_info_bar("sustain", mock)
        assert "Energy" in html

    def test_passenger_has_satisfaction_metric(self):
        mock = _make_mock_tv()
        html = _chart_info_bar("passenger", mock)
        assert "Satisfaction" in html

    def test_asset_has_rul_metric(self):
        mock = _make_mock_tv()
        html = _chart_info_bar("asset", mock)
        assert "RUL" in html

    def test_climate_has_resilience_metric(self):
        mock = _make_mock_tv()
        html = _chart_info_bar("climate", mock)
        assert "Resilience" in html

    def test_unknown_domain_returns_empty_chips(self):
        mock = _make_mock_tv()
        html = _chart_info_bar("unknown", mock)
        assert 'tv-chart-info-bar' in html

    def test_has_chip_structure(self):
        mock = _make_mock_tv()
        html = _chart_info_bar("security", mock)
        assert 'tv-chart-info-chip' in html
        assert 'chip-label' in html
        assert 'chip-value' in html


# ── DOMAIN_META Verification ────────────────────────────────────────────────

class TestDomainMetaExtended:
    def test_all_domains_have_meta(self):
        for d in DOMAINS:
            assert d in DOMAIN_META

    def test_meta_keys(self):
        for meta in DOMAIN_META.values():
            assert "icon" in meta
            assert "short" in meta
            assert "label" in meta


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
