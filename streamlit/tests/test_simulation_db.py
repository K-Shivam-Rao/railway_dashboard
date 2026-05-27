"""Tests for utils/simulation_db.py — Simulation persistence database."""
import pytest
import sys
import os
import json
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

# Backup and set DB_PATH to a temp file
import utils.simulation_db as db_mod

ORIGINAL_DB_PATH = db_mod.DB_PATH


@pytest.fixture(autouse=True)
def _temp_db():
    """Use a temporary database file for each test."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    db_mod.DB_PATH = tmp.name
    # Reinitialize with temp db
    from utils.simulation_db import init_simulation_db
    if os.path.exists(tmp.name):
        os.unlink(tmp.name)
    init_simulation_db()
    yield
    # Cleanup
    if os.path.exists(tmp.name):
        os.unlink(tmp.name)
    db_mod.DB_PATH = ORIGINAL_DB_PATH


from utils.simulation_db import (
    get_db_connection,
    init_simulation_db,
    save_session,
    save_incidents,
    save_achievement,
    get_recent_sessions,
    get_session_summary,
    get_session_incidents,
    get_achievements,
    get_all_time_stats,
    save_scenario_template,
    get_scenario_templates,
    delete_scenario_template,
    save_competency_scores,
    get_session_competency_scores,
)


class TestDatabaseConnection:
    """Test get_db_connection()."""

    def test_connection_works(self):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            assert cursor.fetchone()[0] == 1

    def test_tables_exist(self):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row["name"] for row in cursor.fetchall()]
            assert "simulation_sessions" in tables
            assert "simulation_incidents" in tables


class TestSaveSession:
    """Test save_session()."""

    def test_saves_and_retrieves(self):
        save_session("test-session-1", {"total_incidents": 10, "resolved": 8, "success_rate": 80.0},
                     {"mode": "quick_drill", "target_incidents": 10})
        summary = get_session_summary("test-session-1")
        assert summary is not None
        assert summary["total_incidents"] == 10

    def test_recent_sessions(self):
        save_session("recent-test", {"total_incidents": 5}, {"mode": "drill"})
        recent = get_recent_sessions(limit=5)
        ids = [s["session_id"] for s in recent]
        assert "recent-test" in ids


class TestSaveIncidents:
    """Test save_incidents()."""

    def test_saves_and_retrieves(self):
        save_session("inc-test", {"total_incidents": 2}, {})
        save_incidents("inc-test", [
            {"id": "INC-001", "timestamp": "2026-01-01", "station": "Berlin Hbf",
             "incident_type": "gate_jam", "severity": "CRITICAL", "description": "test",
             "assigned_persona": "", "assigned_role": "", "status": "resolved", "resolution_time_min": 5.0},
            {"id": "INC-002", "timestamp": "2026-01-02", "station": "München Hbf",
             "incident_type": "temp_high", "severity": "WARNING", "description": "test2",
             "assigned_persona": "", "assigned_role": "", "status": "pending", "resolution_time_min": 0.0},
        ])
        incidents = get_session_incidents("inc-test")
        assert len(incidents) == 2
        assert incidents[0]["incident_id"] == "INC-001"


class TestAchievements:
    """Test save_achievement() and get_achievements()."""

    def test_save_and_retrieve(self):
        save_session("ach-test", {}, {})
        save_achievement("ach-test", "BADGE-1", "First Responder")
        achievements = get_achievements("ach-test")
        assert len(achievements) >= 1
        assert achievements[0]["badge_id"] == "BADGE-1"

    def test_all_achievements(self):
        save_session("ach-all", {}, {})
        save_achievement("ach-all", "B1", "One")
        save_achievement("ach-all", "B2", "Two")
        all_achs = get_achievements()
        assert len(all_achs) >= 2


class TestAllTimeStats:
    """Test get_all_time_stats()."""

    def test_returns_dict(self):
        stats = get_all_time_stats()
        assert isinstance(stats, dict)


class TestScenarioTemplates:
    """Test scenario template CRUD."""

    def test_save_and_retrieve(self):
        result = save_scenario_template("Test Scenario", {"param": 42}, "A test", ["tag1"])
        assert result is True
        templates = get_scenario_templates()
        names = [t["name"] for t in templates]
        assert "Test Scenario" in names

    def test_delete(self):
        save_scenario_template("Delete-Me", {"x": 1})
        result = delete_scenario_template("Delete-Me")
        assert result is True
        templates = get_scenario_templates()
        names = [t["name"] for t in templates]
        assert "Delete-Me" not in names


class TestCompetencyScores:
    """Test competency scores CRUD."""

    def test_save_and_retrieve(self):
        save_session("comp-test", {"total_incidents": 5}, {})
        save_competency_scores("comp-test", [
            {"persona_name": "Alice", "speed_score": 85.0, "accuracy_score": 90.0,
             "critical_score": 75.0, "specialty_score": 88.0, "escalation_score": 80.0,
             "balance_score": 82.0, "overall_score": 84.0},
        ])
        scores = get_session_competency_scores("comp-test")
        assert len(scores) == 1
        assert scores[0]["persona_name"] == "Alice"
        assert scores[0]["overall_score"] == 84.0
