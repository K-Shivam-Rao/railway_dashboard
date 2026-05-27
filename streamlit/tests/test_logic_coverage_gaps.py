"""Gap-filler tests for core/logic.py — cover edge cases, error paths, lifecycle methods."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from unittest.mock import patch, MagicMock


# ── SaaSModelConfig validation ──

class TestSaaSModelConfigValidation:
    """Cover __init__ validation error paths."""

    def test_negative_starting_customers(self):
        from core.logic import SaaSModelConfig, ConfigurationError
        with pytest.raises(ConfigurationError, match="starting_customers"):
            SaaSModelConfig(-1, 0.1, 0.05, 100, 5000, 10)

    def test_invalid_growth_rate_too_high(self):
        from core.logic import SaaSModelConfig, ConfigurationError
        with pytest.raises(ConfigurationError, match="monthly_growth_rate"):
            SaaSModelConfig(50, 1.5, 0.05, 100, 5000, 10)

    def test_invalid_growth_rate_negative(self):
        from core.logic import SaaSModelConfig, ConfigurationError
        with pytest.raises(ConfigurationError, match="monthly_growth_rate"):
            SaaSModelConfig(50, -0.1, 0.05, 100, 5000, 10)

    def test_invalid_churn_rate(self):
        from core.logic import SaaSModelConfig, ConfigurationError
        with pytest.raises(ConfigurationError, match="churn_rate"):
            SaaSModelConfig(50, 0.1, 1.5, 100, 5000, 10)

    def test_negative_price(self):
        from core.logic import SaaSModelConfig, ConfigurationError
        with pytest.raises(ConfigurationError, match="price_per_customer"):
            SaaSModelConfig(50, 0.1, 0.05, -100, 5000, 10)

    def test_negative_fixed_costs(self):
        from core.logic import SaaSModelConfig, ConfigurationError
        with pytest.raises(ConfigurationError, match="fixed_costs"):
            SaaSModelConfig(50, 0.1, 0.05, 100, -5000, 10)

    def test_negative_variable_cost(self):
        from core.logic import SaaSModelConfig, ConfigurationError
        with pytest.raises(ConfigurationError, match="variable_cost_per_customer"):
            SaaSModelConfig(50, 0.1, 0.05, 100, 5000, -10)

    def test_valid_config(self):
        from core.logic import SaaSModelConfig
        config = SaaSModelConfig(50, 0.1, 0.05, 100, 5000, 10)
        assert config.customers == 50
        assert repr(config).startswith("SaaSConfig(")

    def test_zero_churn_rate_ltv(self):
        """run_simulation with churn_rate=0 — LTV division by zero returns 0."""
        from core.logic import SaaSModelConfig, run_simulation
        config = SaaSModelConfig(10, 0.05, 0.0, 100, 2000, 5)
        df = run_simulation(config, months=6)
        assert not df.empty
        # LTV = contribution_margin / churn_rate, with churn_rate=0 => returns 0
        assert df["LTV"].iloc[0] == 0


# ── SimulationSession lifecycle ──

class TestSimulationSessionLifecycle:
    """Cover SimulationSession lifecycle methods."""

    def test_reset_clears_all_state(self):
        from core.logic import SimulationSession
        session = SimulationSession(20, seed=42)
        session.start()
        session.pause()
        session.resume()
        inc = session.generate_single()
        assert inc is not None
        session.reset()
        assert not session.is_running
        assert len(session.incidents) == 0
        assert session.start_time is None
        assert session.end_time is None
        assert session._incident_counter == 0
        assert session.metrics == {}

    def test_pause_resume_generate(self):
        from core.logic import SimulationSession
        session = SimulationSession(20, seed=42)
        session.start()
        session.pause()
        # No incident generated while paused
        inc = session.generate_single()
        assert inc is None
        session.resume()
        inc = session.generate_single()
        assert inc is not None

    def test_stop_metrics_calculation(self):
        from core.logic import SimulationSession
        session = SimulationSession(20, seed=42)
        session.start()
        # Generate one incident
        session.generate_single()
        session.stop()
        assert not session.is_running
        assert session.end_time is not None
        assert "total_incidents" in session.metrics

    def test_duration_mode(self):
        from core.logic import SimulationSession
        session = SimulationSession(duration_minutes=1, seed=42)
        session.start()
        # is_duration_mode should be True
        assert session.is_duration_mode

    def test_properties_empty(self):
        from core.logic import SimulationSession
        session = SimulationSession(seed=42)
        session.start()
        assert isinstance(session.competency_scores, list)
        assert len(session.competency_scores) > 0
        assert isinstance(session.team_fatigue_summary, dict)
        assert isinstance(session.replay_timeline, list)

    def test_annotation_and_bookmarks(self):
        from core.logic import SimulationSession
        session = SimulationSession(20, seed=42)
        session.start()
        inc = session.generate_single()
        assert inc is not None
        session.add_annotation(inc.id, "Test annotation")
        assert session.annotations[inc.id] == "Test annotation"
        session.add_bookmark(inc.id, "Key moment")
        assert len(session.bookmarks) == 1

    def test_set_scenario(self):
        from core.logic import SimulationSession, Scenario
        scenario = Scenario.from_preset("quick_drill")
        assert scenario is not None
        session = SimulationSession(seed=42)
        session.set_scenario(scenario)
        assert session.target_incidents == scenario.base_incidents
        assert session.rate_per_sec == scenario.rate_per_sec

    def test_start_resets_personas(self):
        from core.logic import SimulationSession
        session = SimulationSession(20, seed=42)
        session.start()
        for p in session.personas:
            assert p.fatigue == 0.0
            assert p.stress_events == 0


# ── Scenario class methods ──

class TestScenarioMethods:
    """Cover Scenario class methods and edge cases."""

    def test_from_preset_invalid_name(self):
        from core.logic import Scenario
        result = Scenario.from_preset("nonexistent_preset")
        assert result is None

    def test_from_preset_valid(self):
        from core.logic import Scenario
        s = Scenario.from_preset("quick_drill")
        assert s is not None
        assert s.name == "quick_drill"
        assert len(s.steps) > 0

    def test_from_preset_critical_hours(self):
        from core.logic import Scenario
        s = Scenario.from_preset("critical_hours")
        assert s is not None
        assert s.name == "critical_hours"

    def test_to_dict_from_dict_roundtrip(self):
        from core.logic import Scenario
        s1 = Scenario.from_preset("quick_drill")
        assert s1 is not None
        d = s1.to_dict()
        s2 = Scenario.from_dict(d)
        assert s2.name == s1.name
        assert s2.description == s1.description
        assert len(s2.steps) == len(s1.steps)

    def test_get_active_step(self):
        from core.logic import Scenario
        s = Scenario.from_preset("quick_drill")
        assert s is not None
        # At 5 seconds, the first step (delay_sec=0) should be active
        step = s.get_active_step(5.0)
        assert step is not None
        assert step.step_type == "trigger"

    def test_get_active_step_no_steps(self):
        from core.logic import Scenario, ScenarioStep
        s = Scenario(name="empty", steps=[])
        step = s.get_active_step(10.0)
        assert step is None


# ── ScenarioStep ──

class TestScenarioStep:
    """Cover ScenarioStep from_dict and to_dict."""

    def test_from_dict(self):
        from core.logic import ScenarioStep
        data = {
            "step_id": "step_01",
            "step_type": "trigger",
            "delay_sec": 5.0,
            "severity_override": "CRITICAL",
            "config": {"custom": True},
        }
        step = ScenarioStep.from_dict(data)
        assert step.step_id == "step_01"
        assert step.step_type == "trigger"
        assert step.severity_override == "CRITICAL"
        assert step.config["custom"] is True

    def test_to_dict(self):
        from core.logic import ScenarioStep
        step = ScenarioStep(step_id="test", step_type="cascade", delay_sec=10.0)
        d = step.to_dict()
        assert d["step_id"] == "test"
        assert d["step_type"] == "cascade"


# ── SimulationPersona ──

class TestSimulationPersona:
    """Cover SimulationPersona properties and edge cases."""

    def test_needs_break_thresholds(self):
        from core.logic import SimulationPersona
        p = SimulationPersona("Test", "Engineer", ["Gate"], 2.0, 90.0)
        p.fatigue = 50.0
        assert not p.needs_break
        p.fatigue = 75.0
        assert p.needs_break

    def test_is_overloaded(self):
        from core.logic import SimulationPersona
        p = SimulationPersona("Test", "Engineer", ["Gate"], 2.0, 90.0)
        p.fatigue = 30.0
        p.active_count = 2
        assert not p.is_overloaded
        p.active_count = 4
        assert p.is_overloaded
        p.active_count = 2
        p.fatigue = 60.0
        assert p.is_overloaded

    def test_fatigue_level_all_ranges(self):
        from core.logic import SimulationPersona
        p = SimulationPersona("Test", "Engineer", ["Gate"], 2.0, 90.0)
        p.fatigue = 20
        assert p.fatigue_level == "fresh"
        p.fatigue = 40
        assert p.fatigue_level == "normal"
        p.fatigue = 60
        assert p.fatigue_level == "tired"
        p.fatigue = 80
        assert p.fatigue_level == "exhausted"
        p.fatigue = 90
        assert p.fatigue_level == "critical"

    def test_success_rate_computed_with_no_assigned(self):
        from core.logic import SimulationPersona
        p = SimulationPersona("Test", "Engineer", ["Gate"], 2.0, 90.0)
        p.current_assigned = 0
        assert p.success_rate_computed == p.success_rate

    def test_apply_fatigue_to_success_below_threshold(self):
        from core.logic import SimulationPersona
        p = SimulationPersona("Test", "Engineer", ["Gate"], 2.0, 90.0)
        p.fatigue = 20
        assert p.apply_fatigue_to_success(95.0) == 95.0

    def test_apply_fatigue_to_success_penalty(self):
        from core.logic import SimulationPersona
        p = SimulationPersona("Test", "Engineer", ["Gate"], 2.0, 90.0)
        p.fatigue = 80
        result = p.apply_fatigue_to_success(95.0)
        assert result < 95.0

    def test_apply_fatigue_to_response_below_threshold(self):
        from core.logic import SimulationPersona
        p = SimulationPersona("Test", "Engineer", ["Gate"], 2.0, 90.0)
        p.fatigue = 20
        assert p.apply_fatigue_to_response(2.0) == 2.0

    def test_apply_fatigue_to_response_penalty(self):
        from core.logic import SimulationPersona
        p = SimulationPersona("Test", "Engineer", ["Gate"], 2.0, 90.0)
        p.fatigue = 80
        result = p.apply_fatigue_to_response(2.0)
        assert result > 2.0

    def test_trigger_stress_event(self):
        from core.logic import SimulationPersona
        p = SimulationPersona("Test", "Engineer", ["Gate"], 2.0, 90.0)
        p.trigger_stress_event(20.0)
        assert p.stress_events == 1
        assert p.fatigue == 20.0

    def test_trigger_stress_event_fatigue_incident(self):
        from core.logic import SimulationPersona
        p = SimulationPersona("Test", "Engineer", ["Gate"], 2.0, 90.0)
        p.fatigue = 60.0
        p.trigger_stress_event(30.0)
        assert p.fatigue_incidents >= 1

    def test_add_incident_load(self):
        from core.logic import SimulationPersona
        p = SimulationPersona("Test", "Engineer", ["Gate"], 2.0, 90.0)
        p.fatigue = 10.0
        p.add_incident_load()
        assert p.fatigue == 15.0

    def test_recover(self):
        from core.logic import SimulationPersona
        p = SimulationPersona("Test", "Engineer", ["Gate"], 2.0, 90.0)
        p.fatigue = 80.0
        p.recover(30.0)
        assert p.fatigue == 50.0

    def test_rest_interval_recovery(self):
        from core.logic import SimulationPersona
        p = SimulationPersona("Test", "Engineer", ["Gate"], 2.0, 90.0)
        p.fatigue = 80.0
        p.rest_interval_recovery()
        assert p.fatigue == 65.0

    def test_record_assignment(self):
        from core.logic import SimulationPersona
        p = SimulationPersona("Test", "Engineer", ["Gate"], 2.0, 90.0)
        p.record_assignment()
        assert p.assigned_count == 1
        assert p.active_count == 1
        assert p.current_assigned == 1

    def test_record_resolution_success(self):
        from core.logic import SimulationPersona
        p = SimulationPersona("Test", "Engineer", ["Gate"], 2.0, 90.0)
        p.record_assignment()
        p.record_resolution(True, 3.0)
        assert p.active_count == 0
        assert p.resolved_count == 1

    def test_record_resolution_failure(self):
        from core.logic import SimulationPersona
        p = SimulationPersona("Test", "Engineer", ["Gate"], 2.0, 90.0)
        p.record_assignment()
        p.record_resolution(False, 3.0)
        assert p.resolved_count == 0

    def test_to_competency_score(self):
        from core.logic import SimulationPersona
        p = SimulationPersona("Test", "Engineer", ["Gate"], 2.0, 90.0)
        p.record_assignment()
        p.record_resolution(True, 2.0)
        score = p.to_competency_score({"speed": 2.0})
        assert score.persona_name == "Test"
        assert isinstance(score.overall_score, float)


# ── CompetencyScore methods ──

class TestCompetencyScore:
    """Cover CompetencyScore methods."""

    def test_to_radar_dict(self):
        from core.logic import CompetencyScore
        cs = CompetencyScore("Test", speed_score=80, accuracy_score=90,
                             critical_score=70, specialty_score=85,
                             escalation_score=60, balance_score=75)
        d = cs.to_radar_dict()
        assert "labels" in d
        assert "values" in d
        assert len(d["labels"]) == 6

    def test_get_weakest_area(self):
        from core.logic import CompetencyScore
        cs = CompetencyScore("Test", speed_score=80, accuracy_score=90,
                             critical_score=70, specialty_score=85,
                             escalation_score=30, balance_score=75)
        weakest = cs.get_weakest_area()
        assert weakest[0] == "Escalation Control"
        assert weakest[1] == 30.0

    def test_get_strengths(self):
        from core.logic import CompetencyScore
        cs = CompetencyScore("Test", speed_score=85, accuracy_score=90,
                             critical_score=75, specialty_score=80,
                             escalation_score=60, balance_score=95)
        strengths = cs.get_strengths()
        assert "Speed" in strengths
        assert "Accuracy" in strengths
        assert "Workload Balance" in strengths


# ── get_metrics / get_network_summary with missing columns ──

class TestMetricsEdgeCases:
    """Cover get_metrics and get_network_summary with edge cases."""

    def test_get_metrics_empty_station(self):
        from core.logic import get_metrics
        df = pd.DataFrame({"station": ["A"], "door_state": ["open"],
                           "people": [100], "maintenance_status": ["OPTIMAL"],
                           "sync_score": [90], "risk_score": [10]})
        result = get_metrics(df, "NonExistent")
        assert result == (0, 0, 0, 0, 0, 0, None)

    def test_get_metrics_with_congestion(self):
        from core.logic import get_metrics
        df = pd.DataFrame({"station": ["A", "A"],
                           "gate_id": ["G01", "G02"],
                           "door_state": ["open", "offline"],
                           "people": [100, 50],
                           "maintenance_status": ["OPTIMAL", "CRITICAL"],
                           "sync_score": [90, 50],
                           "risk_score": [10, 80],
                           "sensor_temp": [25, 48],
                           "sensor_vib": [1.0, 3.5],
                           "congestion_score": [30, 60],
                           "power_consumption": [15.0, 20.0]})
        gates_total, gates_active, people, critical, avg_sync, warning, metrics = get_metrics(df, "A")
        assert gates_total == 2
        assert gates_active == 1
        assert people == 150
        assert critical == 1
        assert metrics["high_risk_count"] == 1


# ── OOP Wrapper classes ──

class TestWrapperClasses:
    """Cover StationAnalytics, FinancialModel, CustomerSegmenter wrappers."""

    def test_station_analytics(self):
        from core.logic import StationAnalytics
        sa = StationAnalytics()
        df = pd.DataFrame({"station": ["A"], "door_state": ["open"],
                           "people": [100], "maintenance_status": ["OPTIMAL"],
                           "sync_score": [90], "risk_score": [10]})
        result = sa.get_metrics(df, "A")
        assert result[0] == 1

    def test_financial_model_simulation(self):
        from core.logic import FinancialModel, SaaSModelConfig
        fm = FinancialModel()
        config = SaaSModelConfig(10, 0.05, 0.02, 100, 2000, 5)
        df = fm.run_simulation(config, months=6)
        assert not df.empty

    def test_customer_segmenter_placeholders(self):
        from core.logic import CustomerSegmenter
        cs = CustomerSegmenter()
        assert cs.get_customer_data() == []
        assert cs.get_rfm_analysis() == {}
        assert cs.get_high_value_customers() == []
        assert cs.get_at_risk_accounts() == []


# ── get_financial_model_data ──

class TestFinancialModelData:
    """Cover get_financial_model_data variations."""

    def test_default_params(self):
        from core.logic import get_financial_model_data
        df_base, df_churn = get_financial_model_data(months=6)
        assert not df_base.empty
        assert not df_churn.empty

    def test_custom_churn_rate_high(self):
        from core.logic import get_financial_model_data
        df_base, df_churn = get_financial_model_data(
            months=6, churn_rate=0.03, churn_rate_high=0.10
        )
        assert not df_base.empty
        assert not df_churn.empty


# ── get_incident_log edge cases ──

class TestIncidentLogEdgeCases:
    """Cover get_incident_log edge cases."""

    def test_no_critical_or_warning(self):
        from core.logic import get_incident_log
        df = pd.DataFrame({"station": ["A"], "gate_id": ["G01"],
                           "platform": [1], "door_state": ["open"],
                           "maintenance_status": ["OPTIMAL"],
                           "sensor_temp": [25], "sensor_vib": [1.0],
                           "sync_score": [95]})
        result = get_incident_log(df)
        assert result.empty

    def test_jammed_door_desc(self):
        from core.logic import get_incident_log
        df = pd.DataFrame({"station": ["A"], "gate_id": ["G01"],
                           "platform": [1], "door_state": ["jammed"],
                           "maintenance_status": ["CRITICAL"],
                           "sensor_temp": [25], "sensor_vib": [1.0],
                           "sync_score": [50]})
        result = get_incident_log(df)
        assert not result.empty
        assert "jammed" in result["Description"].iloc[0]

    def test_high_temp_desc(self):
        from core.logic import get_incident_log
        df = pd.DataFrame({"station": ["A"], "gate_id": ["G01"],
                           "platform": [1], "door_state": ["open"],
                           "maintenance_status": ["CRITICAL"],
                           "sensor_temp": [50], "sensor_vib": [1.0],
                           "sync_score": [80]})
        result = get_incident_log(df)
        assert not result.empty
        assert "Thermal" in result["Description"].iloc[0]

    def test_low_sync_desc(self):
        from core.logic import get_incident_log
        df = pd.DataFrame({"station": ["A"], "gate_id": ["G01"],
                           "platform": [1], "door_state": ["open"],
                           "maintenance_status": ["WARNING"],
                           "sensor_temp": [25], "sensor_vib": [1.0],
                           "sync_score": [60]})
        result = get_incident_log(df)
        assert not result.empty
        assert "Sync" in result["Description"].iloc[0]


# ── get_network_summary with missing columns ──

class TestNetworkSummaryEdgeCases:
    """Cover get_network_summary with missing columns."""

    def test_no_operator_col(self):
        from core.logic import get_network_summary
        df = pd.DataFrame({"station": ["A", "B"],
                           "gate_id": ["G01", "G02"],
                           "door_state": ["open", "closed"],
                           "people": [100, 200],
                           "maintenance_status": ["OPTIMAL", "WARNING"],
                           "sync_score": [90, 70],
                           "risk_score": [10, 30],
                           "congestion_score": [30, 60]})
        result = get_network_summary(df)
        assert "operator_stats" in result
        assert result["operator_stats"].empty

    def test_no_power_consumption(self):
        from core.logic import get_network_summary
        df = pd.DataFrame({"station": ["A"],
                           "gate_id": ["G01"],
                           "door_state": ["open"],
                           "people": [100],
                           "maintenance_status": ["OPTIMAL"],
                           "sync_score": [90],
                           "risk_score": [10],
                           "congestion_score": [30]})
        result = get_network_summary(df)
        assert result["total_power_kw"] == 0

    def test_no_is_peak_hour(self):
        from core.logic import get_network_summary
        df = pd.DataFrame({"station": ["A"],
                           "gate_id": ["G01"],
                           "door_state": ["open"],
                           "people": [100],
                           "maintenance_status": ["OPTIMAL"],
                           "sync_score": [90],
                           "risk_score": [10],
                           "congestion_score": [30]})
        result = get_network_summary(df)
        assert result["peak_gates"] == 0


# ── get_simulation_personas ──

def test_get_simulation_personas_counts():
    from core.logic import get_simulation_personas
    personas = get_simulation_personas()
    assert len(personas) == 12


# ── SCENARIO_PRESETS constants ──

def test_scenario_presets_defined():
    from core.logic import SCENARIO_PRESETS, SCENARIO_MODES, INCIDENT_TYPES
    assert "quick_drill" in SCENARIO_PRESETS
    assert "shift_simulation" in SCENARIO_PRESETS
    assert "CRITICAL" in INCIDENT_TYPES
    assert len(INCIDENT_TYPES["CRITICAL"]) == 5


# ── get_psd_analytics ──

def test_get_psd_analytics():
    from core.logic import get_psd_analytics
    flow_df, temp_df = get_psd_analytics("Berlin Hbf")
    assert not flow_df.empty
    assert "Hour" in flow_df.columns
    assert not temp_df.empty


# ── get_maintenance_forecast ──

def test_get_maintenance_forecast():
    from core.logic import get_maintenance_forecast
    df = get_maintenance_forecast("Berlin Hbf")
    assert len(df) == 7
    assert "Date" in df.columns


# ── get_passenger_heatmap ──

def test_get_passenger_heatmap():
    from core.logic import get_passenger_heatmap
    df = get_passenger_heatmap("Berlin Hbf")
    assert not df.empty
    assert len(df.index) == 7  # 7 days


# ── get_leadership_data / get_tech_stack ──

def test_get_leadership_data():
    from core.logic import get_leadership_data
    data = get_leadership_data()
    assert len(data) == 5

def test_get_tech_stack():
    from core.logic import get_tech_stack
    stack = get_tech_stack()
    assert len(stack) == 6
