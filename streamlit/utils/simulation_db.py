"""
Database utilities for Training Simulator persistence.
Stores simulation sessions, incidents, and user achievements.
"""
import sqlite3
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict
from contextlib import contextmanager

logger = logging.getLogger(__name__)
DB_PATH = "simulation_history.db"


@contextmanager
def get_db_connection():
    """Context manager for database connections with error handling."""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        yield conn
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


def init_simulation_db():
    """Initialize the simulation database with required tables."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS simulation_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL,
                ended_at TEXT,
                mode TEXT,
                weather TEXT,
                target_incidents INTEGER,
                total_incidents INTEGER DEFAULT 0,
                critical_count INTEGER DEFAULT 0,
                resolved_count INTEGER DEFAULT 0,
                failed_count INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0,
                avg_response_time REAL DEFAULT 0.0,
                duration_sec REAL DEFAULT 0.0,
                config_json TEXT,
                scenario_json TEXT
            )
        """)

        # Incidents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS simulation_incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                incident_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                station TEXT,
                incident_type TEXT,
                severity TEXT,
                description TEXT,
                assigned_persona TEXT,
                assigned_role TEXT,
                status TEXT,
                resolution_time_min REAL,
                annotation TEXT,
                FOREIGN KEY (session_id) REFERENCES simulation_sessions(session_id)
            )
        """)

        # Achievements table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                badge_id TEXT NOT NULL,
                badge_name TEXT NOT NULL,
                earned_at TEXT NOT NULL,
                UNIQUE(session_id, badge_id)
            )
        """)

        # Scenario templates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scenario_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                config_json TEXT NOT NULL,
                tags TEXT,
                is_custom INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT
            )
        """)

        # Competency scores table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS competency_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                persona_name TEXT NOT NULL,
                speed_score REAL DEFAULT 0.0,
                accuracy_score REAL DEFAULT 0.0,
                critical_score REAL DEFAULT 0.0,
                specialty_score REAL DEFAULT 0.0,
                escalation_score REAL DEFAULT 0.0,
                balance_score REAL DEFAULT 0.0,
                overall_score REAL DEFAULT 0.0,
                FOREIGN KEY (session_id) REFERENCES simulation_sessions(session_id)
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_session ON simulation_incidents(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_created ON simulation_sessions(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_competency_session ON competency_scores(session_id)")


def save_session(session_id: str, metrics: Dict, config: Dict) -> None:
    """Save a simulation session to the database."""
    try:
        init_simulation_db()
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO simulation_sessions
                (session_id, created_at, mode, weather, target_incidents, total_incidents,
                 critical_count, resolved_count, failed_count, success_rate, avg_response_time,
                 duration_sec, config_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                datetime.now().isoformat(),
                config.get("mode", "quick_drill"),
                config.get("weather", "normal"),
                config.get("target_incidents", 20),
                metrics.get("total_incidents", 0),
                metrics.get("critical", 0),
                metrics.get("resolved", 0),
                metrics.get("failed", 0),
                metrics.get("success_rate", 0.0),
                metrics.get("avg_response_time", 0.0),
                metrics.get("duration_sec", 0.0),
                json.dumps(config),
            ))
        logger.info(f"Session {session_id} saved successfully")
    except Exception as e:
        logger.error(f"Failed to save session {session_id}: {e}")


def save_incidents(session_id: str, incidents: List) -> None:
    """Save incident records to the database using batch insert."""
    try:
        init_simulation_db()
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            incident_rows = [
                (
                    session_id,
                    inc.get("id", ""),
                    inc.get("timestamp", ""),
                    inc.get("station", ""),
                    inc.get("incident_type", ""),
                    inc.get("severity", ""),
                    inc.get("description", ""),
                    inc.get("assigned_persona", ""),
                    inc.get("assigned_role", ""),
                    inc.get("status", ""),
                    inc.get("resolution_time_min", 0.0),
                )
                for inc in incidents
            ]
            cursor.executemany("""
                INSERT OR REPLACE INTO simulation_incidents
                (session_id, incident_id, timestamp, station, incident_type, severity,
                 description, assigned_persona, assigned_role, status, resolution_time_min)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, incident_rows)
        logger.info(f"Saved {len(incidents)} incidents for session {session_id}")
    except Exception as e:
        logger.error(f"Failed to save incidents for {session_id}: {e}")


def save_achievement(session_id: str, badge_id: str, badge_name: str) -> None:
    """Save an earned achievement."""
    try:
        init_simulation_db()
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO user_achievements
                (session_id, badge_id, badge_name, earned_at)
                VALUES (?, ?, ?, ?)
            """, (session_id, badge_id, badge_name, datetime.now().isoformat()))
        logger.info(f"Achievement {badge_id} saved for session {session_id}")
    except Exception as e:
        logger.error(f"Failed to save achievement {badge_id}: {e}")


def get_recent_sessions(limit: int = 10) -> List[Dict]:
    """Get recent simulation sessions."""
    init_simulation_db()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM simulation_sessions
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        
        return [dict(row) for row in cursor.fetchall()]


def get_session_summary(session_id: str) -> Optional[Dict]:
    """Get summary stats for a specific session."""
    init_simulation_db()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM simulation_sessions WHERE session_id = ?
        """, (session_id,))
        
        row = cursor.fetchone()
        return dict(row) if row else None


def get_session_incidents(session_id: str) -> List[Dict]:
    """Get all incidents for a session."""
    init_simulation_db()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM simulation_incidents
            WHERE session_id = ?
            ORDER BY timestamp ASC
        """, (session_id,))
        
        return [dict(row) for row in cursor.fetchall()]


def get_achievements(session_id: Optional[str] = None) -> List[Dict]:
    """Get earned achievements, optionally filtered by session."""
    init_simulation_db()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if session_id:
            cursor.execute("""
                SELECT * FROM user_achievements
                WHERE session_id = ?
                ORDER BY earned_at DESC
            """, (session_id,))
        else:
            cursor.execute("SELECT * FROM user_achievements ORDER BY earned_at DESC LIMIT 50")
        
        return [dict(row) for row in cursor.fetchall()]


def get_all_time_stats() -> Dict:
    """Get all-time statistics across all sessions."""
    init_simulation_db()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                COUNT(*) as total_sessions,
                SUM(total_incidents) as total_incidents,
                SUM(critical_count) as total_critical,
                SUM(resolved_count) as total_resolved,
                SUM(failed_count) as total_failed,
                AVG(success_rate) as avg_success_rate,
                AVG(avg_response_time) as avg_response_time
            FROM simulation_sessions
        """)

        row = cursor.fetchone()
        return dict(row) if row else {}


def save_scenario_template(name: str, config: Dict, description: str = "", tags: List[str] = None) -> bool:
    """Save a custom scenario template."""
    try:
        init_simulation_db()
        import json as json_module

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO scenario_templates
                (name, description, config_json, tags, is_custom, created_at, updated_at)
                VALUES (?, ?, ?, ?, 1, ?, ?)
            """, (
                name,
                description,
                json_module.dumps(config),
                ",".join(tags or []),
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            ))
        logger.info(f"Scenario template '{name}' saved")
        return True
    except Exception as e:
        logger.error(f"Failed to save scenario template: {e}")
        return False


def get_scenario_templates() -> List[Dict]:
    """Get all saved scenario templates."""
    init_simulation_db()
    import json as json_module

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM scenario_templates ORDER BY created_at DESC")
        rows = cursor.fetchall()
        result = []
        for row in rows:
            d = dict(row)
            try:
                d["config_json"] = json_module.loads(d.get("config_json", "{}"))
            except Exception:
                d["config_json"] = {}
            d["tags"] = d.get("tags", "").split(",") if d.get("tags") else []
            result.append(d)
        return result


def delete_scenario_template(name: str) -> bool:
    """Delete a scenario template."""
    try:
        init_simulation_db()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM scenario_templates WHERE name = ? AND is_custom = 1", (name,))
        return True
    except Exception as e:
        logger.error(f"Failed to delete scenario template: {e}")
        return False


def save_competency_scores(session_id: str, scores: List[Dict]) -> None:
    """Save competency scores for a session."""
    try:
        init_simulation_db()

        with get_db_connection() as conn:
            cursor = conn.cursor()
            rows = [
                (
                    session_id,
                    s["persona_name"],
                    s.get("speed_score", 0.0),
                    s.get("accuracy_score", 0.0),
                    s.get("critical_score", 0.0),
                    s.get("specialty_score", 0.0),
                    s.get("escalation_score", 0.0),
                    s.get("balance_score", 0.0),
                    s.get("overall_score", 0.0),
                )
                for s in scores
            ]
            cursor.executemany("""
                INSERT OR REPLACE INTO competency_scores
                (session_id, persona_name, speed_score, accuracy_score, critical_score,
                 specialty_score, escalation_score, balance_score, overall_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, rows)
        logger.info(f"Saved {len(scores)} competency scores for session {session_id}")
    except Exception as e:
        logger.error(f"Failed to save competency scores: {e}")


def get_session_competency_scores(session_id: str) -> List[Dict]:
    """Get competency scores for a specific session."""
    init_simulation_db()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM competency_scores WHERE session_id = ? ORDER BY overall_score DESC
        """, (session_id,))
        return [dict(row) for row in cursor.fetchall()]


# Initialize on import
init_simulation_db()