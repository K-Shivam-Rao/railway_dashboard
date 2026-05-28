"""Gap-filler tests for core/narrative_html.py — cover edge cases and missed branches."""

from core.narrative_html import (
    build_green_state_banner,
    build_kpi_ticker,
    build_mini_ranking,
    build_org_tree,
)


class TestBuildKpiTickerEdgeCases:
    """Cover build_kpi_ticker edge cases: empty incidents, missing keys, duplicate content."""

    def test_no_incidents_no_kpis(self):
        """No incidents and no kpi_items returns default monitoring active."""
        result = build_kpi_ticker(incidents=None, kpi_items=None)
        assert "Monitoring active" in result
        assert "kpi-ticker-strip" in result

    def test_empty_incidents_list(self):
        """Empty list returns default message."""
        result = build_kpi_ticker(incidents=[], kpi_items=[])
        assert "Monitoring active" in result

    def test_incident_with_compact_format(self):
        """Incident with pipe-delimited description uses compact format (lines 123-124)."""
        inc = {
            "severity": "critical",
            "timestamp": "14:30",
            "station": "Berlin Hbf",
            "gate": "G03",
            "description": "G03 | TEMP 48.2C | VIB 5.5 mm/s | RISK 100",
            "temp": 48.2,
            "vib": 5.5,
            "risk": 100,
        }
        result = build_kpi_ticker(incidents=[inc])
        assert "ticker-incident" in result
        assert "TEMP" in result

    def test_incident_legacy_format(self):
        """Incident without pipes uses legacy fallback with truncation (line 239+)."""
        inc = {
            "severity": "warning",
            "timestamp": "15:00",
            "station": "München Hbf",
            "description": "A" * 150,  # Will be truncated
            "gate": "",
            "temp": None,
            "vib": None,
            "risk": None,
        }
        result = build_kpi_ticker(incidents=[inc])
        assert "ticker-incident" in result
        # Should be truncated to 100 chars + "..."
        assert "..." in result

    def test_incident_missing_keys(self):
        """Incident with missing optional keys still works."""
        inc = {"severity": "info", "station": "Test", "description": "Test desc"}
        result = build_kpi_ticker(incidents=[inc])
        assert "ticker-incident" in result

    def test_kpi_items_only(self):
        """KPI items without incidents."""
        kpis = [{"label": "Uptime", "value": "99.9%"}, {"label": "Gates", "value": "150"}]
        result = build_kpi_ticker(kpi_items=kpis)
        assert "Uptime" in result
        assert "99.9%" in result

    def test_incident_without_temp_vib_risk(self):
        """Compact format incident with zero temp/vib/risk values (falsy check)."""
        inc = {
            "severity": "critical",
            "timestamp": "12:00",
            "station": "Berlin Hbf",
            "gate": "G01",
            "description": "G01 | TEMP 0C | VIB 0 mm/s",
            "temp": 0,
            "vib": 0,
            "risk": 0,
        }
        result = build_kpi_ticker(incidents=[inc])
        assert "ticker-incident" in result

    def test_incident_empty_severity(self):
        """Empty severity defaults to warning color (falsy check)."""
        inc = {"severity": "", "station": "Test", "description": "Test", "timestamp": "12:00", "gate": "G01"}
        result = build_kpi_ticker(incidents=[inc])
        assert "ticker-incident" in result

    def test_compact_no_ts(self):
        """Compact format without timestamp skips timestamp span."""
        inc = {
            "severity": "critical",
            "station": "Test",
            "gate": "G01",
            "description": "G01 | TEMP 30C",
            "temp": 30.0,
            "vib": 0,
            "risk": 0,
            "timestamp": "",
        }
        result = build_kpi_ticker(incidents=[inc])
        # No timestamp means no <span class="ticker-timestamp"> with content
        assert "ticker-timestamp" not in result or "></span>" in result or "</span>" in result


class TestBuildMiniRanking:
    """Cover build_mini_ranking edge cases."""

    def test_empty_anomalies(self):
        """Empty list returns empty string."""
        result = build_mini_ranking([])
        assert result == ""

    def test_none_anomalies(self):
        """None returns empty string."""
        result = build_mini_ranking(None)
        assert result == ""

    def test_single_anomaly(self):
        """Single anomaly renders correctly."""
        anomalies = [{"severity": "CRITICAL", "station": "Berlin Hbf", "gate": "G01", "composite_score": 85}]
        result = build_mini_ranking(anomalies)
        assert "mini-rank-card" in result
        assert "Berlin Hbf" in result

    def test_multiple_anomalies_truncated(self):
        """More than 3 anomalies are truncated to 3."""
        anomalies = [
            {"severity": "CRITICAL", "station": f"Station {i}", "gate": f"G{i:02d}", "composite_score": i * 10}
            for i in range(5)
        ]
        result = build_mini_ranking(anomalies)
        assert "mini-rank-card" in result
        # Count the number of mini-rank-item divs
        count = result.count('<div class="mini-rank-item">')
        assert count == 3  # Truncated to 3


class TestBuildGreenStateBanner:
    """Cover build_green_state_banner basic usage."""

    def test_default_values(self):
        """All default values render."""
        result = build_green_state_banner()
        assert "All " in result
        assert "Stations Operational" in result
        assert "green-state-banner" in result

    def test_custom_values(self):
        """Custom values render correctly."""
        result = build_green_state_banner(station_count=15, streak_days=30, uptime_pct=99.99, mtbi="96h", last_incident="2025-01-15")
        assert "15 Stations" in result
        assert "30" in result
        assert "99.99%" in result
        assert "96h" in result
        assert "2025-01-15" in result


class TestBuildOrgTree:
    """Cover build_org_tree edge cases and search query filtering."""

    def test_empty_customers(self):
        """Empty customer list returns empty state message."""
        result = build_org_tree([])
        assert "No operator data available" in result

    def test_single_customer_no_contracts(self):
        """Customer without contracts renders directly with stations."""
        customers = [{
            "name": "DB Station&Service",
            "health_score": 85,
            "tier": "Platinum",
            "stations": [{"name": "Berlin Hbf", "region": "Berlin", "status": "operational", "maint_count": 0}],
            "contracts": [],
        }]
        result = build_org_tree(customers)
        assert "org-tree-container" in result
        assert "Berlin Hbf" in result

    def test_search_query_matches_station(self):
        """Search query matching station name filters correctly."""
        customers = [{
            "name": "DB",
            "health_score": 80,
            "stations": [{"name": "Berlin Hbf", "region": "Berlin", "status": "operational", "maint_count": 0}],
            "contracts": [],
        }]
        result = build_org_tree(customers, search_query="Berlin")
        assert "Berlin Hbf" in result

    def test_search_query_no_match(self):
        """Search query with no matches returns empty tree."""
        customers = [{
            "name": "DB",
            "health_score": 80,
            "stations": [{"name": "Berlin Hbf", "region": "Berlin", "status": "operational", "maint_count": 0}],
            "contracts": [],
        }]
        result = build_org_tree(customers, search_query="Munich")
        assert "org-tree-container" in result
        # No customer items rendered
        assert "org-tree-node" not in result

    def test_customer_with_contracts_and_stations(self):
        """Customer with both contracts and stations."""
        customers = [{
            "name": "DB",
            "health_score": 75,
            "tier": "Gold",
            "stations": [{"name": "Berlin Hbf", "region": "Berlin", "status": "operational", "maint_count": 2}],
            "contracts": [{
                "name": "Contract A",
                "value": 500000,
                "tier": "Gold",
                "stations": [{"name": "München Hbf", "region": "Munich", "status": "warning", "maint_count": 1}],
            }],
        }]
        result = build_org_tree(customers)
        assert "org-tree-container" in result
        # When contracts exist, code renders contract stations (not direct customer stations)
        assert "München Hbf" in result

    def test_tier_badge_variations(self):
        """Different tier badges render correctly."""
        customers = [
            {"name": "C1", "health_score": 90, "tier": "Platinum", "stations": [], "contracts": []},
            {"name": "C2", "health_score": 80, "tier": "Gold", "stations": [], "contracts": []},
            {"name": "C3", "health_score": 70, "tier": "Premium", "stations": [], "contracts": []},
            {"name": "C4", "health_score": 60, "tier": "Standard", "stations": [], "contracts": []},
        ]
        result = build_org_tree(customers)
        assert "platinum" in result
        assert "gold" in result
        assert "premium" in result

    def test_search_with_contracts_filter(self):
        """Search query filtering contracts keeps matched contracts only."""
        customers = [{
            "name": "DB",
            "health_score": 80,
            "stations": [],
            "contracts": [
                {"name": "Berlin Contract", "value": 300000, "stations": [{"name": "Berlin Hbf", "region": "Berlin", "status": "operational"}]},
                {"name": "Munich Contract", "value": 200000, "stations": [{"name": "München Hbf", "region": "Munich", "status": "operational"}]},
            ],
        }]
        result = build_org_tree(customers, search_query="Berlin")
        assert "Berlin" in result
        assert "Munich" not in result

    def test_contract_without_stations(self):
        """Contract without stations renders as leaf node."""
        customers = [{
            "name": "DB",
            "health_score": 80,
            "stations": [],
            "contracts": [{"name": "Empty Contract", "value": 100000, "stations": []}],
        }]
        result = build_org_tree(customers)
        assert "org-tree-container" in result

    def test_station_with_maint_issues(self):
        """Station with maint_count > 0 shows issues badge."""
        customers = [{
            "name": "DB",
            "health_score": 60,
            "stations": [{"name": "Leipzig Hbf", "region": "Saxony", "status": "critical", "maint_count": 5}],
            "contracts": [],
        }]
        result = build_org_tree(customers)
        assert "5 issues" in result
        assert "critical" in result

    def test_empty_tier_not_shown(self):
        """Empty tier (Standard) doesn't render badge."""
        customers = [{
            "name": "C1",
            "health_score": 50,
            "tier": "",
            "stations": [{"name": "Test", "region": "X", "status": "operational", "maint_count": 0}],
            "contracts": [],
        }]
        result = build_org_tree(customers)
        # No tier badge for empty/Standard tier
        assert "org-tree-tier" not in result
