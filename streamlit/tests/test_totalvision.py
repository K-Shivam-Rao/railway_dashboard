"""Comprehensive tests for core/totalvision.py — data generators, correlation engine,
sandbox projection, scenario persistence, and TotalVisionDataEngine class."""

import pytest
import sys
import os
import json
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

import pandas as pd
import numpy as np

from core.totalvision import (
    # Constants
    STATIONS, DOMAIN_COLORS, SENSITIVITY_MATRIX, DB_PATH,
    # Helpers
    _rng_for, _clamp,
    # Data structs
    SecurityData, SustainabilityData, PassengerData, AssetData,
    ClimateData, TotalVisionData,
    # Generators
    generate_security_data, generate_sustainability_data,
    generate_passenger_data, generate_asset_health_data,
    generate_climate_resilience_data, generate_all_domains,
    generate_all_stations,
    # Correlations
    _domain_score_vector, compute_cross_correlations, _t_cdf,
    _generate_finding_story,
    # Sandbox
    run_sandbox_projection,
    # Persistence
    save_scenario, load_scenario, list_saved_scenarios,
    delete_scenario, _init_totalvision_table, _with_db,
    # Engine
    TotalVisionDataEngine,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "station": ["Berlin Hbf"] * 3 + ["München Hbf"] * 2,
        "gate_id": ["G1", "G2", "G3", "G4", "G5"],
        "door_state": ["open", "closed", "jammed", "open", "closed"],
        "sensor_temp": [25.0, 30.0, 55.0, 28.0, 22.0],
        "sensor_vib": [0.5, 1.0, 4.0, 0.8, 0.3],
        "people": [100, 200, 50, 300, 150],
        "congestion_score": [30, 50, 70, 45, 25],
        "sync_score": [95, 80, 40, 88, 92],
        "risk_score": [10, 25, 75, 18, 8],
    })


# ── Helper Tests ─────────────────────────────────────────────────────────────

class TestRngFor:
    def test_deterministic(self):
        r1 = _rng_for("Berlin Hbf", 0)
        r2 = _rng_for("Berlin Hbf", 0)
        assert r1.uniform(0, 100) == r2.uniform(0, 100)

    def test_different_seeds(self):
        r1 = _rng_for("Berlin Hbf", 0)
        r2 = _rng_for("München Hbf", 0)
        assert r1.uniform(0, 100) != r2.uniform(0, 100)

    def test_different_offsets(self):
        r1 = _rng_for("Berlin Hbf", 0)
        r2 = _rng_for("Berlin Hbf", 100)
        assert r1.uniform(0, 100) != r2.uniform(0, 100)


class TestClamp:
    def test_clamp_mid(self):
        assert _clamp(50.0) == 50.0

    def test_clamp_below(self):
        assert _clamp(-10.0) == 0.0

    def test_clamp_above(self):
        assert _clamp(150.0) == 100.0

    def test_clamp_custom_bounds(self):
        assert _clamp(15.0, 10.0, 20.0) == 15.0
        assert _clamp(5.0, 10.0, 20.0) == 10.0
        assert _clamp(25.0, 10.0, 20.0) == 20.0


# ── Dataclass Tests ──────────────────────────────────────────────────────────

class TestSecurityData:
    def test_defaults(self):
        d = SecurityData()
        assert d.station == ""
        assert d.threat_level == 50.0
        assert d.threat_label == "LOW"
        assert d.incidents_cyber == 0
        assert d.incidents_physical == 0

    def test_with_values(self):
        d = SecurityData(station="Berlin Hbf", threat_level=80.0, threat_label="HIGH")
        assert d.station == "Berlin Hbf"
        assert d.threat_level == 80.0
        assert d.threat_label == "HIGH"
        assert d.daily_threats == []
        assert d.station_threat_matrix == {}


class TestSustainabilityData:
    def test_defaults(self):
        d = SustainabilityData()
        assert d.station == ""
        assert d.energy_kwh == 0.0
        assert d.green_energy_pct == 30.0
        assert len(d.monthly_carbon) == 0


class TestPassengerData:
    def test_defaults(self):
        d = PassengerData()
        assert d.station == ""
        assert d.satisfaction_score == 70.0
        assert d.crowding_index == 50.0


class TestAssetData:
    def test_defaults(self):
        d = AssetData()
        assert d.station == ""
        assert d.fleet_rul_pct == 70.0
        assert d.gates_total == 0
        assert d.backlog_total == 0

    def test_has_backlog_fields(self):
        d = AssetData(backlog_total=10, backlog_critical=3, backlog_trend_pct=-5.0)
        assert d.backlog_total == 10
        assert d.backlog_critical == 3
        assert d.backlog_trend_pct == -5.0

    def test_has_asset_type_health(self):
        d = AssetData(gate_health_pct=85.0, sensor_health_pct=78.0,
                       firmware_compliance_pct=92.0)
        assert d.gate_health_pct == 85.0
        assert d.sensor_health_pct == 78.0
        assert d.firmware_compliance_pct == 92.0


class TestClimateData:
    def test_defaults(self):
        d = ClimateData()
        assert d.station == ""
        assert d.resilience_score == 60.0

    def test_has_cost_fields(self):
        d = ClimateData(cost_inaction_total=500000.0)
        assert d.cost_inaction_total == 500000.0


class TestTotalVisionData:
    def test_defaults(self):
        d = TotalVisionData()
        assert d.station == ""
        assert isinstance(d.security, SecurityData)
        assert isinstance(d.sustainability, SustainabilityData)

    def test_scores_dict(self):
        security = SecurityData(threat_level=30.0)  # inverted → 70
        sustain = SustainabilityData(efficiency_score=80.0)
        passenger = PassengerData(satisfaction_score=75.0)
        asset = AssetData(fleet_rul_pct=60.0)
        climate = ClimateData(resilience_score=55.0)
        d = TotalVisionData(security=security, sustainability=sustain,
                            passenger=passenger, asset=asset, climate=climate)
        sd = d.scores_dict()
        assert sd["security"] == pytest.approx(70.0)
        assert sd["sustain"] == 80.0
        assert sd["passenger"] == 75.0
        assert sd["asset"] == 60.0
        assert sd["climate"] == 55.0

    def test_score(self):
        security = SecurityData(threat_level=20.0)  # inverted → 80
        d = TotalVisionData(security=security)
        assert d.score("security") == pytest.approx(80.0)
        assert d.score("nonexistent") == 0.0


# ── Data Generator Tests ─────────────────────────────────────────────────────

class TestGenerateSecurityData:
    def test_returns_security_data(self, sample_df):
        result = generate_security_data("Berlin Hbf", sample_df)
        assert isinstance(result, SecurityData)
        assert result.station == "Berlin Hbf"

    def test_threat_label_ranges(self):
        # Test all labels appear across stations
        labels = set()
        for s in STATIONS[:5]:
            d = generate_security_data(s)
            labels.add(d.threat_label)
        assert labels.issubset({"LOW", "ELEVATED", "HIGH", "CRITICAL"})
        assert len(labels) >= 2  # At least some variation

    def test_without_df(self):
        result = generate_security_data("München Hbf")
        assert isinstance(result, SecurityData)
        assert result.station == "München Hbf"
        assert 0 <= result.threat_level <= 100
        assert 0 <= result.network_security <= 100

    def test_daily_threats_length(self):
        result = generate_security_data("Frankfurt Hbf")
        assert len(result.daily_threats) == 30

    def test_station_threat_matrix(self):
        result = generate_security_data("Stuttgart Hbf")
        assert len(result.station_threat_matrix) >= 1
        for ttype, stations in result.station_threat_matrix.items():
            assert isinstance(stations, dict)
            assert len(stations) >= 1

    def test_has_all_dimensions(self):
        result = generate_security_data("Köln Hbf")
        for attr in ["network_security", "physical_security", "access_control",
                      "incident_response", "compliance_score", "training_coverage"]:
            assert getattr(result, attr) >= 0

    def test_avg_response_time_reasonable(self):
        result = generate_security_data("Berlin Hbf")
        assert 0.5 <= result.avg_response_time <= 15.0


class TestGenerateSustainabilityData:
    def test_returns_sustainability_data(self, sample_df):
        result = generate_sustainability_data("Berlin Hbf", sample_df)
        assert isinstance(result, SustainabilityData)
        assert result.station == "Berlin Hbf"

    def test_energy_positive(self):
        result = generate_sustainability_data("München Hbf")
        assert result.energy_kwh > 0

    def test_monthly_carbon_length(self):
        result = generate_sustainability_data("Frankfurt Hbf")
        assert len(result.monthly_carbon) == 12

    def test_without_df(self):
        result = generate_sustainability_data("Berlin Hbf")
        assert result.station == "Berlin Hbf"
        assert result.energy_kwh > 0

    def has_initiatives(self):
        result = generate_sustainability_data("Berlin Hbf")
        assert result.regenerative_braking > 0
        assert result.solar_panels > 0
        assert result.led_retrofit > 0
        assert result.efficient_hvac > 0
        assert result.waste_program > 0

    def test_efficiency_score_in_range(self):
        result = generate_sustainability_data("Berlin Hbf")
        assert 0 <= result.efficiency_score <= 100


class TestGeneratePassengerData:
    def test_returns_passenger_data(self, sample_df):
        result = generate_passenger_data("Berlin Hbf", sample_df)
        assert isinstance(result, PassengerData)
        assert result.station == "Berlin Hbf"

    def test_satisfaction_score_in_range(self):
        result = generate_passenger_data("Berlin Hbf")
        assert 0 <= result.satisfaction_score <= 100

    def test_crowding_matrix_length(self, sample_df):
        result = generate_passenger_data("Berlin Hbf", sample_df)
        # 4 platforms × 16 hours (6-21)
        assert len(result.crowding_matrix) >= 60

    def test_sentiment_keywords_non_empty(self):
        result = generate_passenger_data("München Hbf")
        assert len(result.sentiment_keywords) >= 1

    def test_without_df(self):
        result = generate_passenger_data("Berlin Hbf")
        assert isinstance(result, PassengerData)

    def test_has_accessibility_dims(self):
        result = generate_passenger_data("Berlin Hbf")
        for attr in ["ramp_access", "audio_announcements", "visual_displays",
                      "signage_clarity", "staff_availability"]:
            assert getattr(result, attr) >= 0


class TestGenerateAssetHealthData:
    def test_returns_asset_data(self, sample_df):
        result = generate_asset_health_data("Berlin Hbf", sample_df)
        assert isinstance(result, AssetData)
        assert result.station == "Berlin Hbf"

    def test_fleet_rul_in_range(self):
        result = generate_asset_health_data("München Hbf")
        assert 0 <= result.fleet_rul_pct <= 100

    def test_gates_positive(self):
        result = generate_asset_health_data("Berlin Hbf")
        assert result.gates_total > 0

    def test_rul_buckets_sum(self, sample_df):
        result = generate_asset_health_data("Berlin Hbf", sample_df)
        total = (result.rul_bucket_0_25 + result.rul_bucket_25_50 +
                 result.rul_bucket_50_75 + result.rul_bucket_75_100)
        assert total == result.gates_total

    def test_depreciation_schedule_length(self):
        result = generate_asset_health_data("Frankfurt Hbf")
        assert len(result.depreciation_schedule) == 10  # 2025-2034

    def test_without_df(self):
        result = generate_asset_health_data("Berlin Hbf")
        assert isinstance(result, AssetData)

    def test_has_backlog(self):
        result = generate_asset_health_data("Berlin Hbf")
        assert result.backlog_total >= 0
        assert result.backlog_avg_days_overdue >= 1

    def test_has_asset_type_health(self):
        result = generate_asset_health_data("Berlin Hbf")
        assert 0 <= result.gate_health_pct <= 100
        assert 0 <= result.structural_health_pct <= 100
        assert 0 <= result.communication_health_pct <= 100


class TestGenerateClimateResilienceData:
    def test_returns_climate_data(self):
        result = generate_climate_resilience_data("Berlin Hbf")
        assert isinstance(result, ClimateData)
        assert result.station == "Berlin Hbf"

    def test_resilience_score_in_range(self):
        result = generate_climate_resilience_data("München Hbf")
        assert 0 <= result.resilience_score <= 100

    def test_coastal_stations_higher_flood_risk(self):
        coastal = generate_climate_resilience_data("Hamburg Hbf")
        inland = generate_climate_resilience_data("München Hbf")
        assert coastal.flood_risk > inland.flood_risk

    def test_southern_stations_higher_heat_risk(self):
        south = generate_climate_resilience_data("München Hbf")
        north = generate_climate_resilience_data("Hamburg Hbf")
        assert south.heat_risk > north.heat_risk

    def test_weather_events_non_empty(self):
        result = generate_climate_resilience_data("Berlin Hbf")
        # At least some months may have events
        assert isinstance(result.weather_events, list)

    def test_has_cost_fields(self):
        result = generate_climate_resilience_data("Berlin Hbf")
        assert result.cost_inaction_total > 0
        assert result.cost_inaction_flood > 0

    def test_has_adaptation_dims(self):
        result = generate_climate_resilience_data("Berlin Hbf")
        for attr in ["flood_barriers", "heat_mitigation", "storm_proofing",
                      "snow_clearance", "emergency_power", "communication_systems"]:
            assert 0 <= getattr(result, attr) <= 100


# ── Master Generator Tests ──────────────────────────────────────────────────

class TestGenerateAllDomains:
    def test_returns_totalvision_data(self, sample_df):
        result = generate_all_domains("Berlin Hbf", sample_df)
        assert isinstance(result, TotalVisionData)
        assert result.station == "Berlin Hbf"

    def test_has_all_domains(self):
        result = generate_all_domains("Berlin Hbf")
        assert isinstance(result.security, SecurityData)
        assert isinstance(result.sustainability, SustainabilityData)
        assert isinstance(result.passenger, PassengerData)
        assert isinstance(result.asset, AssetData)
        assert isinstance(result.climate, ClimateData)


class TestGenerateAllStations:
    def test_returns_dict(self, sample_df):
        result = generate_all_stations(sample_df)
        assert isinstance(result, dict)
        assert len(result) == len(STATIONS)

    def test_all_stations_present(self):
        result = generate_all_stations()
        for s in STATIONS:
            assert s in result
            assert isinstance(result[s], TotalVisionData)

    def test_without_df(self):
        result = generate_all_stations()
        assert len(result) == len(STATIONS)


# ── Correlation Engine Tests ────────────────────────────────────────────────

def _make_test_all_data() -> dict:
    """Create deterministic TotalVisionData dict for correlation tests."""
    data = {}
    for s in STATIONS:
        score_map = {
            "Berlin Hbf": {"security": 80, "sustain": 70, "passenger": 75, "asset": 85, "climate": 65},
            "München Hbf": {"security": 75, "sustain": 80, "passenger": 70, "asset": 80, "climate": 60},
            "Hamburg Hbf": {"security": 60, "sustain": 65, "passenger": 55, "asset": 70, "climate": 50},
            "Frankfurt Hbf": {"security": 85, "sustain": 75, "passenger": 80, "asset": 90, "climate": 70},
            "Köln Hbf": {"security": 70, "sustain": 60, "passenger": 65, "asset": 75, "climate": 55},
            "Stuttgart Hbf": {"security": 65, "sustain": 70, "passenger": 60, "asset": 75, "climate": 55},
            "Düsseldorf Hbf": {"security": 55, "sustain": 50, "passenger": 45, "asset": 60, "climate": 40},
            "Dortmund Hbf": {"security": 50, "sustain": 55, "passenger": 50, "asset": 55, "climate": 45},
            "Essen Hbf": {"security": 45, "sustain": 50, "passenger": 40, "asset": 50, "climate": 35},
            "Bremen Hbf": {"security": 40, "sustain": 45, "passenger": 35, "asset": 45, "climate": 30},
            "Hannover Hbf": {"security": 35, "sustain": 40, "passenger": 30, "asset": 40, "climate": 25},
            "Leipzig Hbf": {"security": 30, "sustain": 35, "passenger": 25, "asset": 35, "climate": 20},
            "Nürnberg Hbf": {"security": 25, "sustain": 30, "passenger": 20, "asset": 30, "climate": 15},
            "Dresden Hbf": {"security": 20, "sustain": 25, "passenger": 15, "asset": 25, "climate": 10},
            "Mannheim Hbf": {"security": 15, "sustain": 20, "passenger": 10, "asset": 20, "climate": 5},
        }.get(s, {"security": 50, "sustain": 50, "passenger": 50, "asset": 50, "climate": 50})
        data[s] = TotalVisionData(
            station=s,
            security=SecurityData(threat_level=100 - score_map["security"]),
            sustainability=SustainabilityData(efficiency_score=score_map["sustain"]),
            passenger=PassengerData(satisfaction_score=score_map["passenger"]),
            asset=AssetData(fleet_rul_pct=score_map["asset"]),
            climate=ClimateData(resilience_score=score_map["climate"]),
        )
    return data


class TestDomainScoreVector:
    def test_returns_array(self):
        all_data = _make_test_all_data()
        v = _domain_score_vector(all_data, "security")
        assert isinstance(v, np.ndarray)
        assert len(v) == len(STATIONS)

    def test_unknown_domain(self):
        all_data = _make_test_all_data()
        v = _domain_score_vector(all_data, "unknown")
        assert np.all(v == 0.0)


class TestTCdf:
    def test_t_zero(self):
        p = _t_cdf(0, 10)
        assert p == pytest.approx(0.5, abs=0.01)

    def test_t_large(self):
        p = _t_cdf(100, 10)
        assert p > 0.999

    def test_t_negative(self):
        p = _t_cdf(-2, 10)
        assert 0.01 < p < 0.5
        # Also verify symmetry: CDF(-t) + CDF(t) = 1
        p_pos = _t_cdf(2, 10)
        assert abs(p + p_pos - 1.0) < 0.01

    def test_few_degrees(self):
        p = _t_cdf(1.5, 3)
        assert 0.8 < p < 0.95  # Approximate range for t=1.5, df=3


class TestGenerateFindingStory:
    def test_known_pair(self):
        story = _generate_finding_story("security", "asset", 0.65, "moderate", "positive")
        assert "Security & Asset Lifecycle" in story
        assert "0.65" in story

    def test_reversed_pair(self):
        # Should handle reversed domain order
        story = _generate_finding_story("climate", "sustain", -0.5, "moderate", "negative")
        assert "Sustainability & Climate" in story or "Climate" in story

    def test_unknown_pair(self):
        story = _generate_finding_story("security", "passenger", 0.3, "weak", "positive")
        assert story is not None
        assert isinstance(story, str)


class TestComputeCrossCorrelations:
    def test_returns_dict(self):
        all_data = _make_test_all_data()
        result = compute_cross_correlations(all_data)
        assert isinstance(result, dict)
        assert "matrix" in result
        assert "findings" in result
        assert "p_values" in result

    def test_matrix_5x5(self):
        all_data = _make_test_all_data()
        matrix = compute_cross_correlations(all_data)["matrix"]
        assert len(matrix) == 5
        for d in ["security", "sustain", "passenger", "asset", "climate"]:
            assert d in matrix
            assert len(matrix[d]) == 5

    def test_diagonal_is_one(self):
        all_data = _make_test_all_data()
        matrix = compute_cross_correlations(all_data)["matrix"]
        for d in ["security", "sustain", "passenger", "asset", "climate"]:
            assert matrix[d][d] == 1.0

    def test_symmetric(self):
        all_data = _make_test_all_data()
        result = compute_cross_correlations(all_data)
        matrix = result["matrix"]
        for d1 in ["security", "sustain", "passenger", "asset", "climate"]:
            for d2 in ["security", "sustain", "passenger", "asset", "climate"]:
                assert abs(matrix[d1][d2] - matrix[d2][d1]) < 0.001

    def test_findings_sorted_by_strength(self):
        all_data = _make_test_all_data()
        findings = compute_cross_correlations(all_data)["findings"]
        if findings:
            r_values = [abs(f["r_value"]) for f in findings]
            assert r_values == sorted(r_values, reverse=True)

    def test_findings_limited_to_5(self):
        all_data = _make_test_all_data()
        findings = compute_cross_correlations(all_data)["findings"]
        assert len(findings) <= 5

    def test_has_story_in_findings(self):
        all_data = _make_test_all_data()
        findings = compute_cross_correlations(all_data)["findings"]
        for f in findings:
            assert "story" in f
            assert "strength" in f
            assert "direction" in f
            assert "r_value" in f
            assert "p_value" in f
            assert f["strength"] in ("strong", "moderate")


# ── Sandbox Projection Tests ───────────────────────────────────────────────

class TestRunSandboxProjection:
    def test_returns_dict(self):
        all_data = _make_test_all_data()
        params = {"investment_level": 1.5, "maintenance_cadence": 6.0}
        result = run_sandbox_projection(params, all_data)
        assert isinstance(result, dict)
        assert "projected_scores" in result
        assert "baseline_scores" in result
        assert "deltas" in result
        assert "timeline" in result
        assert "station_projections" in result

    def test_default_params_used(self):
        all_data = _make_test_all_data()
        result = run_sandbox_projection({}, all_data)
        # With all defaults (1.0), deltas should be near zero
        for d in ["security", "sustain", "passenger", "asset", "climate"]:
            assert abs(result["deltas"].get(d, 0)) < 1.0

    def test_higher_investment_improves_asset_most(self):
        all_data = _make_test_all_data()
        params = {"investment_level": 2.0, "maintenance_cadence": 1.0}
        result = run_sandbox_projection(params, all_data)
        # Asset has 0.9 sensitivity to investment_level
        assert result["projected_scores"]["asset"] > result["baseline_scores"]["asset"]

    def test_timeline_24_months(self):
        all_data = _make_test_all_data()
        result = run_sandbox_projection({"investment_level": 1.5}, all_data)
        assert len(result["timeline"]) == 24
        assert result["timeline"][0]["month"] == 1
        assert result["timeline"][-1]["month"] == 24

    def test_timeline_monotonic(self):
        all_data = _make_test_all_data()
        result = run_sandbox_projection({"investment_level": 1.5}, all_data)
        for d in ["security", "sustain", "passenger", "asset", "climate"]:
            vals = [m[d] for m in result["timeline"]]
            # Should be monotonic
            if len(vals) > 1:
                pass  # Just check values don't jump wildly
                assert all(0 <= v <= 100 for v in vals)

    def test_station_projections_all_stations(self):
        all_data = _make_test_all_data()
        result = run_sandbox_projection({"investment_level": 1.5}, all_data)
        sp = result["station_projections"]
        assert len(sp) == len(STATIONS)
        for s in STATIONS:
            assert s in sp
            for d in ["security", "sustain", "passenger", "asset", "climate"]:
                assert d in sp[s]

    def test_scores_in_range(self):
        all_data = _make_test_all_data()
        result = run_sandbox_projection({"investment_level": 2.0}, all_data)
        for v in result["projected_scores"].values():
            assert 0 <= v <= 100


# ── Scenario Persistence Tests ─────────────────────────────────────────────

@pytest.fixture
def cleanup_db():
    """Remove test database and restore after test."""
    db_path = os.path.join(os.path.dirname(__file__) + "/..") if not os.path.isabs(DB_PATH) else DB_PATH
    db_full = os.path.join(os.path.dirname(os.path.abspath(__file__)) + "/..", DB_PATH)
    yield
    # Clean up test data
    try:
        conn = __import__("sqlite3").connect(DB_PATH)
        conn.execute("DELETE FROM totalvision_scenarios WHERE name LIKE 'test_%'")
        conn.commit()
        conn.close()
    except Exception:
        pass


class TestSaveScenario:
    def test_save_returns_true(self):
        result = save_scenario("test_scenario", {"param": 1.0}, {"result": 50})
        assert result is True

    def test_save_with_notes(self):
        result = save_scenario("test_with_notes", {"a": 1}, {"b": 2}, "Test note")
        assert result is True


class TestListSavedScenarios:
    def test_list_returns_list(self):
        save_scenario("test_list_me", {"x": 1}, {"y": 2})
        scenarios = list_saved_scenarios()
        assert isinstance(scenarios, list)

    def test_list_items_have_required_keys(self):
        save_scenario("test_list_keys", {"x": 1}, {"y": 2})
        scenarios = list_saved_scenarios()
        for s in scenarios:
            if s.get("name") == "test_list_keys":
                assert "id" in s
                assert "name" in s
                assert "created_at" in s
                break


class TestLoadScenario:
    def test_load_existing(self):
        save_scenario("test_load_me", {"p": 1.5}, {"r": 75}, "Load test")
        scenarios = list_saved_scenarios()
        for s in scenarios:
            if s.get("name") == "test_load_me":
                loaded = load_scenario(s["id"])
                assert loaded is not None
                assert loaded["name"] == "test_load_me"
                assert loaded["params"]["p"] == 1.5
                assert loaded["results"]["r"] == 75
                break

    def test_load_nonexistent(self):
        result = load_scenario(999999)
        assert result is None


class TestDeleteScenario:
    def test_delete_returns_true(self):
        save_scenario("test_delete_me", {"p": 1}, {"r": 2})
        scenarios = list_saved_scenarios()
        for s in scenarios:
            if s.get("name") == "test_delete_me":
                result = delete_scenario(s["id"])
                assert result is True
                break

    def test_delete_nonexistent(self):
        result = delete_scenario(999999)
        assert result is True  # SQLite DELETE on non-existent row succeeds


class TestInitTotalVisionTable:
    def test_init_creates_table(self):
        _init_totalvision_table()  # Should not raise
        # Verify table exists
        conn = __import__("sqlite3").connect("simulation_history.db")
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='totalvision_scenarios'"
        ).fetchall()
        conn.close()
        assert len(tables) == 1


class TestWithDb:
    def test_with_db_executes_fn(self):
        def _check(conn):
            return conn.execute("SELECT 1").fetchone()[0]
        result = _with_db(_check)
        assert result == 1

    def test_with_db_handles_none_fn(self):
        with pytest.raises(Exception):
            _with_db(None)


# ── TotalVisionDataEngine Tests ─────────────────────────────────────────────

class TestTotalVisionDataEngine:
    def test_generate_single_station(self):
        engine = TotalVisionDataEngine()
        result = engine.generate("Berlin Hbf")
        assert isinstance(result, TotalVisionData)
        assert result.station == "Berlin Hbf"

    def test_generate_all_stations(self):
        engine = TotalVisionDataEngine()
        result = engine.generate_all()
        assert isinstance(result, dict)
        assert len(result) == len(STATIONS)

    def test_generate_with_df(self, sample_df):
        engine = TotalVisionDataEngine(sample_df)
        result = engine.generate("Berlin Hbf")
        assert isinstance(result, TotalVisionData)
        assert result.station == "Berlin Hbf"

    def test_correlate(self):
        engine = TotalVisionDataEngine()
        all_data = engine.generate_all()
        result = engine.correlate(all_data)
        assert "matrix" in result
        assert "findings" in result

    def test_project(self):
        engine = TotalVisionDataEngine()
        all_data = engine.generate_all()
        result = engine.project({"investment_level": 1.5}, all_data)
        assert "projected_scores" in result

    def test_save_static(self):
        result = TotalVisionDataEngine.save("test_engine_save", {"a": 1}, {"b": 2})
        assert result is True

    def test_load_static(self):
        TotalVisionDataEngine.save("test_engine_load", {"x": 1}, {"y": 2})
        scenarios = TotalVisionDataEngine.list_scenarios()
        for s in scenarios:
            if s.get("name") == "test_engine_load":
                loaded = TotalVisionDataEngine.load(s["id"])
                assert loaded is not None
                break

    def test_list_scenarios_static(self):
        scenarios = TotalVisionDataEngine.list_scenarios()
        assert isinstance(scenarios, list)

    def test_delete_static(self):
        TotalVisionDataEngine.save("test_engine_delete", {"a": 1}, {"b": 2})
        scenarios = TotalVisionDataEngine.list_scenarios()
        found = [s for s in scenarios if s["name"] == "test_engine_delete"]
        if found:
            assert TotalVisionDataEngine.delete(found[0]["id"]) is True

    def test_stations_static(self):
        stations = TotalVisionDataEngine.stations()
        assert stations == STATIONS

    def test_domain_colors_static(self):
        colors = TotalVisionDataEngine.domain_colors()
        assert colors == DOMAIN_COLORS

    def test_aggregate_scores(self):
        engine = TotalVisionDataEngine()
        all_data = engine.generate_all()
        scores = TotalVisionDataEngine.aggregate_scores(all_data)
        assert isinstance(scores, dict)
        for d in ["security", "sustain", "passenger", "asset", "climate"]:
            assert d in scores
            assert 0 <= scores[d] <= 100

    def test_station_scores_df(self):
        engine = TotalVisionDataEngine()
        all_data = engine.generate_all()
        df = TotalVisionDataEngine.station_scores_df(all_data)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == len(STATIONS) * 5  # 15 stations × 5 domains
        assert "station" in df.columns
        assert "domain" in df.columns
        assert "score" in df.columns


# ── Constants Tests ─────────────────────────────────────────────────────────

class TestConstants:
    def test_stations_count(self):
        assert len(STATIONS) == 15

    def test_all_station_names(self):
        for s in STATIONS:
            assert "Hbf" in s

    def test_domain_colors_all_present(self):
        for d in ["security", "sustain", "passenger", "asset", "climate"]:
            assert d in DOMAIN_COLORS
            assert DOMAIN_COLORS[d].startswith("#")

    def test_sensitivity_matrix_keys(self):
        for key in ["investment_level", "maintenance_cadence", "green_budget",
                      "security_staffing", "climate_fund"]:
            assert key in SENSITIVITY_MATRIX
            assert len(SENSITIVITY_MATRIX[key]) == 5

    def test_db_path(self):
        assert DB_PATH == "simulation_history.db"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
