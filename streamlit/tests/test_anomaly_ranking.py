"""
Unit tests for core/anomaly_ranking.py
"""
import os
import sys
from datetime import datetime, timedelta

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

from core.anomaly_ranking import (
    ANOMALY_RANKING_PRESETS,
    DEFAULT_ANOMALY_PRESET,
    generate_anomaly_narrative,
    get_anomaly_ranking_matrix,
    get_anomaly_severity_score,
    get_recency_score,
    get_recommended_action,
    get_station_importance_score,
    rank_anomalies,
)

# ── get_anomaly_severity_score ──

class TestGetAnomalySeverityScore:
    """Test get_anomaly_severity_score()."""

    def test_critical(self):
        assert get_anomaly_severity_score("CRITICAL") == 100.0

    def test_critical_lowercase(self):
        assert get_anomaly_severity_score("critical") == 100.0

    def test_warning(self):
        assert get_anomaly_severity_score("WARNING") == 60.0

    def test_monitor(self):
        assert get_anomaly_severity_score("MONITOR") == 30.0

    def test_optimal(self):
        assert get_anomaly_severity_score("OPTIMAL") == 5.0

    def test_unknown(self):
        assert get_anomaly_severity_score("UNKNOWN") == 10.0

    def test_empty_string(self):
        assert get_anomaly_severity_score("") == 10.0

    def test_whitespace(self):
        assert get_anomaly_severity_score("  CRITICAL  ") == 100.0

    def test_none_returns_10(self):
        assert get_anomaly_severity_score(None) == 10.0


# ── get_station_importance_score ──

class TestGetStationImportanceScore:
    """Test get_station_importance_score()."""

    def test_high_volume_high_value(self):
        score = get_station_importance_score("Berlin Hbf", 5000, 1_000_000)
        assert score == 100.0  # Both maxed

    def test_half_volume(self):
        score = get_station_importance_score("Mid Station", 2500, 0)
        # pax_score = 50, contract_score = 0 -> 25
        assert score == pytest.approx(25.0)

    def test_zero_defaults(self):
        score = get_station_importance_score("Small Station")
        assert score == 0.0

    def test_contract_only(self):
        score = get_station_importance_score("Test", 0, 500_000)
        # pax_score = 0, contract_score = 50 -> 25
        assert score == pytest.approx(25.0)

    def test_caps_at_100(self):
        score = get_station_importance_score("Big", 10000, 5_000_000)
        assert score == 100.0


# ── get_recency_score ──

class TestGetRecencyScore:
    """Test get_recency_score()."""

    def test_just_now_high_score(self):
        now = datetime(2025, 1, 1, 12, 0, 0)
        ts = datetime(2025, 1, 1, 12, 0, 0)
        score = get_recency_score(ts, now)
        assert score > 99.0

    def test_one_hour_ago(self):
        now = datetime(2025, 1, 1, 13, 0, 0)
        ts = datetime(2025, 1, 1, 12, 0, 0)
        score = get_recency_score(ts, now)
        # 100 * 0.5^(60/60) = 50
        assert score == pytest.approx(50.0, rel=0.1)

    def test_two_hours_ago(self):
        now = datetime(2025, 1, 1, 14, 0, 0)
        ts = datetime(2025, 1, 1, 12, 0, 0)
        score = get_recency_score(ts, now)
        # 100 * 0.5^(120/60) = 25
        assert score == pytest.approx(25.0, rel=0.1)

    def test_iso_string_input(self):
        now = datetime(2025, 1, 1, 12, 0, 0)
        score = get_recency_score("2025-01-01T12:00:00", now)
        assert score > 99.0

    def test_invalid_string_returns_50(self):
        score = get_recency_score("not-a-date", datetime.now())
        assert score == 50.0

    def test_none_returns_50(self):
        score = get_recency_score(None, datetime.now())
        assert score == 50.0

    def test_old_event_low_score(self):
        now = datetime(2025, 1, 10, 12, 0, 0)
        ts = datetime(2025, 1, 1, 12, 0, 0)
        score = get_recency_score(ts, now)
        assert score < 2.0


# ── generate_anomaly_narrative ──

class TestGenerateAnomalyNarrative:
    """Test generate_anomaly_narrative()."""

    def test_critical_severity(self):
        row = {"station": "Berlin Hbf", "gate_id": "G01", "severity": "CRITICAL", "sensor_temp": 50, "sensor_vib": 4.0}
        narrative = generate_anomaly_narrative(row, 100.0, 90.0, 33.3, risk_score_val=80, recurrence_count=3)
        assert "CRITICAL" in narrative
        assert "G01" in narrative
        assert "Berlin Hbf" in narrative

    def test_warning_severity(self):
        row = {"station": "Munich", "gate_id": "G02", "sensor_temp": 30, "sensor_vib": 1.5}
        narrative = generate_anomaly_narrative(row, 60.0, 50.0, 0.0)
        assert "Warning" in narrative
        assert "G02" in narrative
        assert "Munich" in narrative

    def test_high_temperature_message(self):
        row = {"station": "Test", "gate_id": "G03", "sensor_temp": 50, "sensor_vib": 1.0}
        narrative = generate_anomaly_narrative(row, 60.0, 50.0, 0.0)
        assert "critically high" in narrative.lower()

    def test_elevated_temperature(self):
        row = {"station": "Test", "gate_id": "G04", "sensor_temp": 38, "sensor_vib": 1.0}
        narrative = generate_anomaly_narrative(row, 60.0, 50.0, 0.0)
        assert "elevated" in narrative.lower()

    def test_high_vibration(self):
        row = {"station": "Test", "gate_id": "G05", "sensor_temp": 25, "sensor_vib": 3.5}
        narrative = generate_anomaly_narrative(row, 60.0, 50.0, 0.0)
        assert "critically high" in narrative.lower()

    def test_high_risk_score(self):
        row = {"station": "Test", "gate_id": "G06", "sensor_temp": 25, "sensor_vib": 1.0}
        narrative = generate_anomaly_narrative(row, 60.0, 50.0, 0.0, risk_score_val=85)
        assert "critically high" in narrative.lower()

    def test_recurrence_3_or_more(self):
        row = {"station": "Test", "gate_id": "G07", "sensor_temp": 25, "sensor_vib": 1.0}
        narrative = generate_anomaly_narrative(row, 60.0, 50.0, 0.0, recurrence_count=3)
        assert "failure pattern likely" in narrative.lower()

    def test_recurrence_2(self):
        row = {"station": "Test", "gate_id": "G08", "sensor_temp": 25, "sensor_vib": 1.0}
        narrative = generate_anomaly_narrative(row, 60.0, 50.0, 0.0, recurrence_count=2)
        assert "preventive action" in narrative.lower()

    def test_high_recency(self):
        row = {"station": "Test", "gate_id": "G09", "sensor_temp": 25, "sensor_vib": 1.0}
        narrative = generate_anomaly_narrative(row, 60.0, 90.0, 0.0)
        assert "immediate response" in narrative.lower()

    def test_sensor_correlation(self):
        row = {"station": "Test", "gate_id": "G10", "sensor_temp": 25, "sensor_vib": 1.0}
        narrative = generate_anomaly_narrative(row, 60.0, 50.0, 66.0)
        assert "cascading" in narrative.lower()

    def test_fallback_keys_gate(self):
        row = {"station": "Test", "gate": "ALT", "sensor_temp": 25, "sensor_vib": 1.0}
        narrative = generate_anomaly_narrative(row, 60.0, 50.0, 0.0)
        assert "ALT" in narrative

    def test_fallback_keys_temp_vib(self):
        row = {"station": "Test", "gate_id": "G11", "temp": 48, "vib": 3.0}
        narrative = generate_anomaly_narrative(row, 100.0, 90.0, 33.3)
        assert "critically high" in narrative.lower()


# ── get_recommended_action ──

class TestGetRecommendedAction:
    """Test get_recommended_action()."""

    def test_critical_high_temp(self):
        row = {"severity": "CRITICAL", "sensor_temp": 50, "sensor_vib": 1.0}
        action = get_recommended_action(row)
        assert "thermal" in action.lower()

    def test_critical_high_vib(self):
        row = {"severity": "CRITICAL", "sensor_temp": 25, "sensor_vib": 4.0}
        action = get_recommended_action(row)
        assert "mechanical" in action.lower()

    def test_critical_generic(self):
        row = {"severity": "CRITICAL", "sensor_temp": 25, "sensor_vib": 1.0}
        action = get_recommended_action(row)
        assert "supervisor" in action.lower()

    def test_warning_elevated_temp(self):
        row = {"severity": "WARNING", "sensor_temp": 38, "sensor_vib": 1.0}
        action = get_recommended_action(row)
        assert "thermal" in action.lower()

    def test_warning_elevated_vib(self):
        row = {"severity": "WARNING", "sensor_temp": 25, "sensor_vib": 2.5}
        action = get_recommended_action(row)
        assert "vibration" in action.lower()

    def test_warning_generic(self):
        row = {"severity": "WARNING", "sensor_temp": 25, "sensor_vib": 1.0}
        action = get_recommended_action(row)
        assert "watch list" in action.lower()

    def test_routine_monitoring(self):
        row = {"severity": "OPTIMAL", "sensor_temp": 25, "sensor_vib": 1.0}
        action = get_recommended_action(row)
        assert "routine" in action.lower()

    def test_fallback_maintenance_status(self):
        row = {"maintenance_status": "CRITICAL", "sensor_temp": 25, "sensor_vib": 1.0}
        action = get_recommended_action(row)
        assert "supervisor" in action.lower()


# ── rank_anomalies ──

class TestRankAnomalies:
    """Test rank_anomalies()."""

    def test_none_input_returns_empty_list(self):
        result = rank_anomalies(None)
        assert result == []

    def test_empty_dataframe_returns_empty_list(self):
        df = pd.DataFrame()
        result = rank_anomalies(df)
        assert result == []

    def test_single_anomaly_returns_list(self):
        df = pd.DataFrame([{
            "station": "Berlin Hbf",
            "gate_id": "G01",
            "severity": "CRITICAL",
            "sensor_temp": 50,
            "sensor_vib": 4.0,
            "risk_score": 85,
            "timestamp": datetime.now().isoformat(),
            "passenger_count": 5000,
            "contract_value": 1_000_000,
            "recurrence_count": 3,
        }])
        result = rank_anomalies(df)
        assert isinstance(result, list)
        assert len(result) == 1

    def test_ranked_has_expected_keys(self):
        df = pd.DataFrame([{
            "station": "Berlin Hbf",
            "gate_id": "G01",
            "severity": "CRITICAL",
            "sensor_temp": 50,
            "sensor_vib": 4.0,
            "risk_score": 85,
            "timestamp": datetime.now().isoformat(),
            "passenger_count": 5000,
            "contract_value": 1_000_000,
            "recurrence_count": 3,
        }])
        result = rank_anomalies(df)
        item = result[0]
        expected_keys = {"station", "gate", "severity", "composite_score", "narrative",
                         "recommended_action", "severity_score", "station_importance",
                         "recency_score", "sensor_correlation", "temp", "vib",
                         "risk", "recurrence_count", "timestamp"}
        assert expected_keys.issubset(set(item.keys())), f"Missing: {expected_keys - set(item.keys())}"

    def test_sorts_by_composite_score_descending(self):
        rows = [
            {"station": "A", "gate_id": "G1", "severity": "CRITICAL", "sensor_temp": 50, "sensor_vib": 4.0, "risk_score": 90, "timestamp": datetime.now().isoformat(), "passenger_count": 5000, "contract_value": 1_000_000, "recurrence_count": 5},
            {"station": "B", "gate_id": "G2", "severity": "WARNING", "sensor_temp": 25, "sensor_vib": 1.0, "risk_score": 10, "timestamp": (datetime.now() - timedelta(hours=24)).isoformat(), "passenger_count": 0, "contract_value": 0, "recurrence_count": 0},
        ]
        df = pd.DataFrame(rows)
        result = rank_anomalies(df)
        assert len(result) == 2
        assert result[0]["composite_score"] >= result[1]["composite_score"]

    def test_custom_preset(self):
        df = pd.DataFrame([{
            "station": "Test", "gate_id": "G01", "severity": "WARNING",
            "sensor_temp": 30, "sensor_vib": 1.0, "risk_score": 50,
            "timestamp": datetime.now().isoformat(), "passenger_count": 100, "contract_value": 0,
        }])
        result = rank_anomalies(df, preset_name="safety_first")
        assert len(result) == 1
        assert result[0]["severity"] == "WARNING"

    def test_business_impact_preset(self):
        df = pd.DataFrame([{
            "station": "Test", "gate_id": "G01", "severity": "WARNING",
            "sensor_temp": 30, "sensor_vib": 1.0, "risk_score": 50,
            "timestamp": datetime.now().isoformat(), "passenger_count": 100, "contract_value": 0,
        }])
        result = rank_anomalies(df, preset_name="business_impact")
        assert len(result) == 1

    def test_custom_weights(self):
        df = pd.DataFrame([{
            "station": "Test", "gate_id": "G01", "severity": "WARNING",
            "sensor_temp": 30, "sensor_vib": 1.0, "risk_score": 50,
            "timestamp": datetime.now().isoformat(), "passenger_count": 100, "contract_value": 0,
        }])
        custom_weights = {"severity": 5.0, "station_importance": 0.0, "recency": 0.0, "recurrence": 0.0, "sensor_correlation": 0.0}
        result = rank_anomalies(df, preset_name="balanced", custom_weights=custom_weights)
        assert len(result) == 1

    def test_fallback_keys_in_row(self):
        df = pd.DataFrame([{
            "station": "Test", "gate": "G99", "maintenance_status": "CRITICAL",
            "temp": 45, "vib": 3.0, "risk": 90, "Timestamp": datetime.now().isoformat(),
            "people": 5000, "recurrence_count": 2,
        }])
        result = rank_anomalies(df)
        assert len(result) == 1
        assert result[0]["gate"] == "G99"

    def test_invalid_preset_falls_back_to_balanced(self):
        df = pd.DataFrame([{
            "station": "Test", "gate_id": "G01", "severity": "CRITICAL",
            "sensor_temp": 30, "sensor_vib": 1.0, "risk_score": 50,
            "timestamp": datetime.now().isoformat(), "passenger_count": 100, "contract_value": 0,
        }])
        result = rank_anomalies(df, preset_name="nonexistent")
        assert len(result) == 1


# ── get_anomaly_ranking_matrix ──

class TestGetAnomalyRankingMatrix:
    """Test get_anomaly_ranking_matrix()."""

    def test_returns_dict(self):
        matrix = get_anomaly_ranking_matrix()
        assert isinstance(matrix, dict)

    def test_has_presets(self):
        matrix = get_anomaly_ranking_matrix()
        assert "presets" in matrix
        assert isinstance(matrix["presets"], dict)

    def test_has_active_preset(self):
        matrix = get_anomaly_ranking_matrix()
        assert matrix["active_preset"] == "balanced"

    def test_has_factors_list(self):
        matrix = get_anomaly_ranking_matrix()
        assert "factors" in matrix
        assert isinstance(matrix["factors"], list)
        assert len(matrix["factors"]) == 5

    def test_factors_have_required_keys(self):
        matrix = get_anomaly_ranking_matrix()
        for factor in matrix["factors"]:
            assert "key" in factor
            assert "label" in factor
            assert "min" in factor
            assert "max" in factor

    def test_presets_match_constants(self):
        matrix = get_anomaly_ranking_matrix()
        assert matrix["presets"] == ANOMALY_RANKING_PRESETS
        assert DEFAULT_ANOMALY_PRESET == "balanced"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
