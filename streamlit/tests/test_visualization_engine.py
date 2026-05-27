"""Tests for core/visualization_engine.py — Architecture hub, loopholes, recommendations."""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

from core.visualization_engine import (
    ArchitectureNode,
    Loophole,
    Recommendation,
    ARCHITECTURE_NODES,
    ARCHITECTURE_EDGES,
    TECHNICAL_LOOPHOLES,
    OPERATIONAL_LOOPHOLES,
    generate_live_metrics,
    build_architecture_flow_html,
    analyze_loopholes,
    generate_recommendations,
    get_station_vulnerability_scores,
)


class TestArchitectureNodes:
    """Test ArchitectureNode dataclass and constants."""

    def test_node_creation(self):
        node = ArchitectureNode("test", "Test", "🚉", "station")
        assert node.id == "test"
        assert node.label == "Test"
        assert node.type == "station"
        assert node.status == "operational"

    def test_node_with_connections(self):
        node = ArchitectureNode("test", "Test", "📡", "sensor", connections=["cloud_api"])
        assert "cloud_api" in node.connections

    def test_architecture_nodes_count(self):
        assert len(ARCHITECTURE_NODES) == 12

    def test_architecture_edges_count(self):
        assert len(ARCHITECTURE_EDGES) == 17

    def test_all_node_ids_unique(self):
        ids = [n.id for n in ARCHITECTURE_NODES]
        assert len(ids) == len(set(ids))


class TestGenerateLiveMetrics:
    """Test generate_live_metrics()."""

    def test_returns_dict(self):
        metrics = generate_live_metrics()
        assert isinstance(metrics, dict)

    def test_has_all_components(self):
        metrics = generate_live_metrics()
        expected = {"stations", "sensors", "cloud_api", "analytics", "database",
                    "dashboard", "team", "mobile_edge", "notifications", "ml_engine",
                    "compliance", "maintenance"}
        assert expected.issubset(set(metrics.keys()))

    def test_each_component_has_uptime(self):
        metrics = generate_live_metrics()
        for key, data in metrics.items():
            assert "uptime" in data, f"{key} missing uptime"

    def test_uptime_in_valid_range(self):
        metrics = generate_live_metrics()
        for key, data in metrics.items():
            assert 0 <= data["uptime"] <= 100, f"{key} uptime out of range"

    def test_stations_online_positive(self):
        metrics = generate_live_metrics()
        assert metrics["stations"]["online"] > 0


class TestBuildArchitectureFlowHtml:
    """Test build_architecture_flow_html()."""

    def test_returns_string(self):
        html = build_architecture_flow_html()
        assert isinstance(html, str)

    def test_contains_pipeline_markup(self):
        html = build_architecture_flow_html()
        assert "pipeline-flow" in html

    def test_contains_css_styles(self):
        html = build_architecture_flow_html()
        assert "pipeline-tier" in html

    def test_contains_live_indicator(self):
        html = build_architecture_flow_html()
        assert "live-indicator" in html


class TestLoopholeData:
    """Test Loophole dataclass and data constants."""

    def test_loophole_creation(self):
        l = Loophole("T001", "technical", "high", "Test", "Desc", "Impact", "Suggestion")
        assert l.id == "T001"
        assert l.type == "technical"

    def test_technical_loopholes_not_empty(self):
        assert len(TECHNICAL_LOOPHOLES) > 0

    def test_operational_loopholes_not_empty(self):
        assert len(OPERATIONAL_LOOPHOLES) > 0

    def test_all_loopholes_have_required_fields(self):
        for l in TECHNICAL_LOOPHOLES + OPERATIONAL_LOOPHOLES:
            assert l.id
            assert l.title
            assert l.description
            assert l.severity in ("critical", "high", "medium", "low")


class TestAnalyzeLoopholes:
    """Test analyze_loopholes()."""

    def test_returns_tuple(self):
        tech, oper = analyze_loopholes()
        assert isinstance(tech, list)
        assert isinstance(oper, list)

    def test_without_history_returns_base(self):
        tech, oper = analyze_loopholes()
        assert len(tech) == len(TECHNICAL_LOOPHOLES)
        assert len(oper) >= len(OPERATIONAL_LOOPHOLES)

    def test_with_history_slow_response_adds_loophole(self):
        history = {"metrics": {"avg_response_time": 6.0, "success_rate": 90, "escalated": 1, "total_incidents": 10}}
        tech, oper = analyze_loopholes(history)
        assert len(oper) > len(OPERATIONAL_LOOPHOLES)  # dynamic O007 added

    def test_with_history_low_success_adds_loophole(self):
        history = {"metrics": {"avg_response_time": 2.0, "success_rate": 60, "escalated": 1, "total_incidents": 10}}
        tech, oper = analyze_loopholes(history)
        assert len(oper) > len(OPERATIONAL_LOOPHOLES)

    def test_with_history_high_escalation_adds_loophole(self):
        history = {"metrics": {"avg_response_time": 2.0, "success_rate": 90, "escalated": 5, "total_incidents": 10}}
        tech, oper = analyze_loopholes(history)
        assert len(oper) > len(OPERATIONAL_LOOPHOLES)

    def test_empty_history_returns_base(self):
        history = {"metrics": {}}
        tech, oper = analyze_loopholes(history)
        assert len(tech) == len(TECHNICAL_LOOPHOLES)


class TestRecommendationEngine:
    """Test generate_recommendations()."""

    def test_returns_sorted_list(self):
        recs = generate_recommendations()
        assert isinstance(recs, list)
        assert all(isinstance(r, Recommendation) for r in recs)

    def test_has_base_recommendations(self):
        recs = generate_recommendations()
        assert len(recs) >= 7  # R001-R007

    def test_recommendations_sorted_by_priority(self):
        recs = generate_recommendations()
        priorities = [r.priority for r in recs]
        order = {"critical": 0, "high": 1, "medium": 2, "info": 3}
        for i in range(len(priorities) - 1):
            assert order[priorities[i]] <= order[priorities[i + 1]]

    def test_with_low_success_rate(self):
        recs = generate_recommendations(metrics={"success_rate": 70})
        priorities = [r.priority for r in recs]
        assert "critical" in priorities  # R008 added
    
    def test_with_root_causes(self):
        recs = generate_recommendations(root_causes={"gate_jam": 5, "temp_spike": 2})
        ids = [r.id for r in recs]
        assert "R010" in ids

    def test_recommendation_required_fields(self):
        recs = generate_recommendations()
        for r in recs:
            assert r.id
            assert r.title
            assert r.priority in ("critical", "high", "medium", "info")

    def test_with_personas(self):
        from core.visualization_engine import Recommendation
        class MockPersona:
            def __init__(self, name, role, success_rate_computed):
                self.name = name
                self.role = role
                self.success_rate_computed = success_rate_computed

        personas = [MockPersona("Test", "Engineer", 99), MockPersona("Weak", "Tech", 60)]
        recs = generate_recommendations(metrics={"success_rate": 85}, personas=personas)
        ids = [r.id for r in recs]
        assert "R011" in ids


class TestStationVulnerabilityScores:
    """Test get_station_vulnerability_scores()."""

    def test_returns_list(self):
        scores = get_station_vulnerability_scores()
        assert isinstance(scores, list)

    def test_all_stations_have_required_keys(self):
        scores = get_station_vulnerability_scores()
        for s in scores:
            assert "station" in s
            assert "score" in s
            assert "critical" in s
            assert "high" in s

    def test_scores_non_empty(self):
        scores = get_station_vulnerability_scores()
        assert len(scores) > 0

    def test_scores_are_non_negative(self):
        scores = get_station_vulnerability_scores()
        for s in scores:
            assert s["score"] >= 0
            assert s["critical"] >= 0

    def test_unique_stations(self):
        scores = get_station_vulnerability_scores()
        stations = [s["station"] for s in scores]
        assert len(stations) == len(set(stations))
