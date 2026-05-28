"""
Unit tests for core/narrative_html.py
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

from core.narrative_html import (
    build_green_state_banner,
    build_kpi_ticker,
    build_mini_ranking,
    build_org_tree,
)

# ── build_green_state_banner ──

class TestBuildGreenStateBanner:
    """Test build_green_state_banner()."""

    def test_returns_string(self):
        html = build_green_state_banner()
        assert isinstance(html, str)

    def test_contains_green_state_class(self):
        html = build_green_state_banner()
        assert "green-state-banner" in html

    def test_contains_station_count(self):
        html = build_green_state_banner(station_count=42)
        assert "42" in html or "42" in html

    def test_contains_uptime_pct(self):
        html = build_green_state_banner(uptime_pct=99.9)
        assert "99.9" in html

    def test_contains_streak_days(self):
        html = build_green_state_banner(streak_days=30)
        assert "30" in html

    def test_contains_mtbi(self):
        html = build_green_state_banner(mtbi="96h")
        assert "96h" in html

    def test_contains_last_incident(self):
        html = build_green_state_banner(last_incident="2025-01-01")
        assert "2025-01-01" in html

    def test_svg_elements_present(self):
        html = build_green_state_banner()
        assert "<svg" in html
        assert "</svg>" in html

    def test_animations_present(self):
        html = build_green_state_banner()
        assert "fade-in" in html or "slide-down" in html or "scale-in" in html


# ── build_kpi_ticker ──

class TestBuildKpiTicker:
    """Test build_kpi_ticker()."""

    def test_empty_returns_strip_html(self):
        html = build_kpi_ticker()
        assert isinstance(html, str)
        assert "kpi-ticker-strip" in html

    def test_empty_shows_monitoring_active(self):
        html = build_kpi_ticker()
        assert "Monitoring active" in html

    def test_with_incidents_compact_format(self):
        incidents = [{
            "severity": "critical",
            "station": "Berlin Hbf",
            "gate": "G01",
            "description": "G01 | TEMP 48.2C | VIB 5.5 mm/s | RISK 100",
            "timestamp": "14:30",
            "temp": 48.2,
            "vib": 5.5,
            "risk": 100,
        }]
        html = build_kpi_ticker(incidents=incidents)
        assert "ticker-incident" in html
        assert "Berlin Hbf" in html
        assert "ticker-critical" in html

    def test_with_incidents_legacy_format(self):
        incidents = [{
            "severity": "warning",
            "station": "München Hbf",
            "description": "Some long description without sensor pipes",
            "timestamp": "15:00",
        }]
        html = build_kpi_ticker(incidents=incidents)
        assert "München Hbf" in html
        assert "ticker-warning" in html

    def test_with_kpi_items(self):
        kpi_items = [
            {"label": "Uptime", "value": "99.7%"},
            {"label": "Customers", "value": "127"},
        ]
        html = build_kpi_ticker(kpi_items=kpi_items)
        assert "Uptime" in html
        assert "99.7%" in html
        assert "Customers" in html

    def test_combined_incidents_and_kpis(self):
        incidents = [{"severity": "critical", "station": "A", "description": "desc", "timestamp": "12:00"}]
        kpi_items = [{"label": "Test", "value": "42"}]
        html = build_kpi_ticker(incidents=incidents, kpi_items=kpi_items)
        assert "ticker-incident" in html
        assert "ticker-kpi" in html or "Test" in html

    def test_deduped_content(self):
        incidents = [{"severity": "info", "station": "S", "description": "desc", "timestamp": "10:00"}]
        html = build_kpi_ticker(incidents=incidents)
        # content is duplicated for scrolling — count opening tag patterns
        opener = '<div class="ticker-item ticker-incident'
        count = html.count(opener)
        assert count >= 2, f"Expected at least 2 duplicates, got {count}"

    def test_live_badge(self):
        html = build_kpi_ticker()
        assert "LIVE" in html

    def test_compact_sensor_pills(self):
        incidents = [{
            "severity": "critical",
            "station": "Test",
            "gate": "G01",
            "description": "G01 | TEMP 48.2C | VIB 5.5 mm/s | RISK 100",
            "timestamp": "12:00",
            "temp": 48.2,
            "vib": 5.5,
            "risk": 100,
        }]
        html = build_kpi_ticker(incidents=incidents)
        assert "ticker-sensor-pill" in html
        assert "temp-pill" in html or "vib-pill" in html or "risk-pill" in html


# ── build_mini_ranking ──

class TestBuildMiniRanking:
    """Test build_mini_ranking()."""

    def test_empty_returns_empty_string(self):
        html = build_mini_ranking([])
        assert html == ""

    def test_none_returns_empty_string(self):
        html = build_mini_ranking(None)
        assert html == ""

    def test_single_anomaly(self):
        anomalies = [{"severity": "CRITICAL", "station": "Berlin Hbf", "gate": "G01", "composite_score": 85}]
        html = build_mini_ranking(anomalies)
        assert "mini-rank-card" in html
        assert "Berlin Hbf" in html
        assert "G01" in html

    def test_shows_count_in_header(self):
        anomalies = [
            {"severity": "CRITICAL", "station": "A", "gate": "G1", "composite_score": 90},
            {"severity": "WARNING", "station": "B", "gate": "G2", "composite_score": 50},
        ]
        html = build_mini_ranking(anomalies)
        assert "2" in html  # count

    def test_limits_to_3_items(self):
        anomalies = [
            {"severity": "CRITICAL", "station": f"S{i}", "gate": f"G{i}", "composite_score": 100 - i*5}
            for i in range(10)
        ]
        html = build_mini_ranking(anomalies)
        # Should only show 3 items
        assert html.count("mini-rank-item") == 3

    def test_critical_class_for_critical(self):
        anomalies = [{"severity": "CRITICAL", "station": "A", "gate": "G1", "composite_score": 100}]
        html = build_mini_ranking(anomalies)
        assert "critical" in html.lower()

    def test_has_svg_icon(self):
        anomalies = [{"severity": "WARNING", "station": "A", "gate": "G1", "composite_score": 50}]
        html = build_mini_ranking(anomalies)
        assert "<svg" in html or "polygon" in html


# ── build_org_tree ──

class TestBuildOrgTree:
    """Test build_org_tree()."""

    def test_empty_data_returns_empty_message(self):
        html = build_org_tree([])
        assert "No operator data available" in html

    def test_none_data_returns_empty_message(self):
        html = build_org_tree(None)
        assert "No operator data available" in html

    def test_single_customer_no_contracts(self):
        customers = [{
            "name": "DB Station&Service",
            "health_score": 85,
            "tier": "Platinum",
            "stations": [{"name": "Berlin Hbf", "status": "operational", "region": "Berlin"}],
            "contracts": [],
        }]
        html = build_org_tree(customers)
        assert "org-tree-container" in html
        assert "DB Station&Service" in html
        assert "Berlin Hbf" in html

    def test_customer_with_contracts(self):
        customers = [{
            "name": "Operator A",
            "health_score": 70,
            "stations": [],
            "contracts": [{
                "name": "Contract 1",
                "value": 500000,
                "stations": [{"name": "Station 1", "status": "operational", "region": "DE"}],
            }],
        }]
        html = build_org_tree(customers)
        assert "Operator A" in html
        assert "Contract 1" in html
        assert "Station 1" in html

    def test_health_classes_applied(self):
        customers = [{
            "name": "Healthy Corp",
            "health_score": 85,
            "stations": [{"name": "S1", "status": "operational", "region": "DE"}],
            "contracts": [],
        }]
        html = build_org_tree(customers)
        assert "org-tree-health" in html

    def test_search_query_filters(self):
        customers = [
            {"name": "Deutsche Bahn", "health_score": 90, "stations": [{"name": "Berlin Hbf", "status": "operational", "region": "Berlin"}], "contracts": []},
            {"name": "SBB Swiss", "health_score": 80, "stations": [{"name": "Zurich HB", "status": "operational", "region": "Zurich"}], "contracts": []},
        ]
        html = build_org_tree(customers, search_query="Deutsche")
        assert "Deutsche Bahn" in html
        assert "SBB Swiss" not in html

    def test_tier_badge_for_platinum(self):
        customers = [{
            "name": "Platinum Customer",
            "health_score": 95,
            "tier": "Platinum",
            "stations": [{"name": "S1", "status": "operational", "region": "DE"}],
            "contracts": [],
        }]
        html = build_org_tree(customers)
        assert "Platinum" in html

    def test_value_formatting(self):
        customers = [{
            "name": "Big Client",
            "health_score": 80,
            "stations": [],
            "contracts": [{
                "name": "Main Contract",
                "value": 1500000,
                "stations": [],
            }],
        }]
        html = build_org_tree(customers)
        # Should contain formatted value (€1,500,000)
        assert "1,500,000" in html or "1500000" in html

    def test_station_issues_displayed(self):
        customers = [{
            "name": "Test Co",
            "health_score": 60,
            "stations": [{"name": "S1", "status": "warning", "region": "DE", "maint_count": 3}],
            "contracts": [],
        }]
        html = build_org_tree(customers)
        assert "3 issues" in html

    def test_multiple_stations_under_customer(self):
        customers = [{
            "name": "Multi-Station",
            "health_score": 75,
            "stations": [
                {"name": "Station A", "status": "operational", "region": "Berlin"},
                {"name": "Station B", "status": "warning", "region": "Munich"},
            ],
            "contracts": [],
        }]
        html = build_org_tree(customers)
        assert "Station A" in html
        assert "Station B" in html

    def test_search_query_matches_station_name(self):
        customers = [{
            "name": "Test",
            "health_score": 70,
            "stations": [{"name": "Hauptbahnhof", "status": "operational", "region": "Berlin"}],
            "contracts": [],
        }]
        html = build_org_tree(customers, search_query="Haupt")
        assert "Hauptbahnhof" in html

    def test_search_query_matches_region(self):
        customers = [{
            "name": "Test",
            "health_score": 70,
            "stations": [{"name": "S1", "status": "operational", "region": "Munich"}],
            "contracts": [],
        }]
        html = build_org_tree(customers, search_query="Munich")
        assert "S1" in html


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
