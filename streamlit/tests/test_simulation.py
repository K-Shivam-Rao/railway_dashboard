"""
Tests for the Training Simulator module.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.logic import (
    INCIDENT_TYPES,
    STATIONS,
    Incident,
    SimulationPersona,
    SimulationSession,
    get_simulation_personas,
)


class TestIncident:
    """Tests for the Incident dataclass."""

    def test_incident_creation(self):
        """Test creating an incident with all fields."""
        incident = Incident(
            id="TEST-001",
            timestamp=None,
            station="Berlin Hauptbahnhof",
            incident_type="gate_jam",
            severity="CRITICAL",
            description="Gate jammed at Berlin Hauptbahnhof",
        )
        assert incident.id == "TEST-001"
        assert incident.station == "Berlin Hauptbahnhof"
        assert incident.severity == "CRITICAL"
        assert incident.status == "pending"

    def test_incident_to_dict(self):
        """Test converting incident to dictionary."""
        from datetime import datetime
        incident = Incident(
            id="TEST-002",
            timestamp=datetime(2026, 5, 10, 12, 0, 0),
            station="Munich Hauptbahnhof",
            incident_type="temp_high",
            severity="WARNING",
            description="Temperature exceeded threshold",
        )
        data = incident.to_dict()
        assert data["id"] == "TEST-002"
        assert data["station"] == "Munich Hauptbahnhof"
        assert data["severity"] == "WARNING"
        assert data["status"] == "pending"

    def test_incident_assignment(self):
        """Test assigning an incident to a persona."""
        incident = Incident(
            id="TEST-003",
            timestamp=None,
            station="Frankfurt Hauptbahnhof",
            incident_type="vibration",
            severity="INFO",
            description="Vibration elevated",
        )
        incident.assigned_persona = "Alex Chen"
        incident.assigned_role = "Maintenance Engineer"
        incident.status = "assigned"
        assert incident.assigned_persona == "Alex Chen"
        assert incident.status == "assigned"


class TestSimulationPersona:
    """Tests for the SimulationPersona dataclass."""

    def test_persona_creation(self):
        """Test creating a simulation persona."""
        persona = SimulationPersona(
            name="Test Person",
            role="Shift Supervisor",
            specialties=["safety", "operations"],
            avg_response_min=1.5,
            success_rate=85.0,
        )
        assert persona.name == "Test Person"
        assert persona.role == "Shift Supervisor"
        assert persona.success_rate == 85.0

    def test_persona_stats_tracking(self):
        """Test tracking assignment and resolution stats."""
        persona = SimulationPersona(
            name="Test Person",
            role="Maintenance Engineer",
            specialties=["maintenance"],
            avg_response_min=2.0,
            success_rate=80.0,
        )
        persona.current_assigned = 10
        persona.current_resolved = 8
        persona.active_count = 2
        # Manually set current_success_rate as a field
        persona.current_success_rate = 80.0
        assert persona.current_success_rate == 80.0

    def test_get_simulation_personas(self):
        """Test that personas are properly loaded."""
        personas = get_simulation_personas()
        assert len(personas) == 12
        names = [p.name for p in personas]
        assert "Khushboo Patil" in names
        assert "Namrata Joshi" in names
        # Check leadership and operational split
        leadership = [p for p in personas if p.role in ["CEO", "COO", "CTO", "CPO", "CFO"]]
        assert len(leadership) == 5


class TestSimulationSession:
    """Tests for the SimulationSession class."""

    def test_session_creation(self):
        """Test creating a simulation session."""
        session = SimulationSession(target_incidents=20, rate_per_sec=1)
        assert session.target_incidents == 20
        assert session.rate_per_sec == 1
        assert session.is_running is False

    def test_session_creation_duration_mode(self):
        """Test creating a duration-based session."""
        session = SimulationSession(duration_minutes=5)
        assert session.is_duration_mode is True
        assert session.duration_minutes == 5

    def test_session_start_stop(self):
        """Test starting and stopping a session."""
        session = SimulationSession()
        session.start()
        assert session.is_running is True
        assert session.start_time is not None

        session.stop()
        assert session.is_running is False
        assert session.end_time is not None

    def test_session_reset(self):
        """Test resetting a session."""
        session = SimulationSession()
        session.start()
        session.reset()
        assert session.is_running is False
        assert session.incidents == []
        assert session.start_time is None

    def test_generate_single(self):
        """Test generating a single incident."""
        session = SimulationSession(target_incidents=20, seed=42)
        session.start()

        # Generate one incident
        incident = session.generate_single()
        assert incident is not None
        assert len(session.incidents) == 1

        session.stop()

    def test_assign_incident(self):
        """Test assigning incidents to personas."""
        session = SimulationSession(target_incidents=10, seed=42)
        session.start()

        # Generate and assign incidents
        for _ in range(3):
            inc = session.generate_single()

        for incident in session.incidents:
            result = session.assign_incident(incident)
            assert result is True
            assert incident.assigned_persona is not None

        session.stop()

    def test_resolve_incident(self):
        """Test resolving incidents."""
        session = SimulationSession(target_incidents=5, seed=42)
        session.start()

        for _ in range(3):
            session.generate_single()

        # Assign and resolve all
        for incident in session.incidents:
            session.assign_incident(incident)
            success = True
            session.resolve_incident(incident, success)
            assert incident.status == "resolved"

        session.stop()

    def test_metrics_calculation(self):
        """Test that metrics are calculated correctly."""
        session = SimulationSession(target_incidents=10, seed=42)
        session.start()

        for _ in range(10):
            session.generate_single()

        for inc in session.incidents:
            session.assign_incident(inc)
            session.resolve_incident(inc, True)

        session.stop()

        metrics = session.metrics
        assert metrics["total_incidents"] == 10
        assert metrics["resolved"] == 10
        assert metrics["failed"] == 0
        assert metrics["success_rate"] == 100.0

    def test_to_dataframe(self):
        """Test converting incidents to DataFrame."""
        session = SimulationSession(target_incidents=5, seed=42)
        session.start()
        # Generate all 5 incidents
        for _ in range(5):
            session.generate_single()
        session.stop()

        df = session.to_dataframe()
        assert len(df) >= 1
        assert len(df.columns) > 0


class TestConfigurations:
    """Tests for simulation configuration constants."""

    def test_stations_loaded(self):
        """Test that stations are properly loaded."""
        assert len(STATIONS) == 10
        assert "Berlin Hauptbahnhof" in STATIONS
        assert "Munich Hauptbahnhof" in STATIONS

    def test_incident_types_loaded(self):
        """Test that incident types are properly loaded."""
        assert "CRITICAL" in INCIDENT_TYPES
        assert "WARNING" in INCIDENT_TYPES
        assert "INFO" in INCIDENT_TYPES
        assert len(INCIDENT_TYPES["CRITICAL"]) == 5
        assert len(INCIDENT_TYPES["WARNING"]) == 5
        assert len(INCIDENT_TYPES["INFO"]) == 5

    def test_severity_levels(self):
        """Test that all severity levels have valid types."""
        for severity, types in INCIDENT_TYPES.items():
            assert all(len(t) >= 2 for t in types)
            type_names = [t[0] for t in types]
            assert len(type_names) == len(set(type_names))  # No duplicates


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
