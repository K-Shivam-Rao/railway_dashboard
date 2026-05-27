"""
ANOMALY RANKING ENGINE — NARRATIVE INTELLIGENCE
================================================
Composite scoring with user-configurable weights for ranking anomalies.
Part of the Midnight Express v5 UI/UX upgrade.
"""

from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd

ANOMALY_RANKING_PRESETS = {
    "balanced": {
        "label": "Balanced",
        "description": "Equal weight across all factors",
        "weights": {
            "severity": 1.0,
            "station_importance": 1.0,
            "recency": 1.0,
            "recurrence": 1.0,
            "sensor_correlation": 1.0,
        },
    },
    "safety_first": {
        "label": "Safety-First",
        "description": "Prioritize severity — critical incidents jump to the top",
        "weights": {
            "severity": 3.0,
            "station_importance": 1.0,
            "recency": 1.5,
            "recurrence": 2.0,
            "sensor_correlation": 1.0,
        },
    },
    "business_impact": {
        "label": "Business-Impact",
        "description": "Weight stations by passenger volume and contract value",
        "weights": {
            "severity": 1.0,
            "station_importance": 3.0,
            "recency": 1.0,
            "recurrence": 1.5,
            "sensor_correlation": 1.0,
        },
    },
}

DEFAULT_ANOMALY_PRESET = "balanced"


def get_anomaly_severity_score(severity_str: str) -> float:
    """Convert severity label to numeric score."""
    mapping = {
        "CRITICAL": 100.0, "critical": 100.0,
        "WARNING": 60.0, "warning": 60.0,
        "MONITOR": 30.0, "monitor": 30.0,
        "OPTIMAL": 5.0, "optimal": 5.0,
    }
    return mapping.get(str(severity_str).strip(), 10.0)


def get_station_importance_score(
    station_name: str,
    passenger_volume: int = 0,
    contract_value: float = 0.0
) -> float:
    """Calculate station importance score based on passenger volume and contract value."""
    pax_score = min(100.0, (passenger_volume / 5000.0) * 100.0)
    contract_score = min(100.0, (contract_value / 1000000.0) * 100.0)
    return (pax_score * 0.5) + (contract_score * 0.5)


def get_recency_score(timestamp, now=None) -> float:
    """Score based on how recent the anomaly is. Newer = higher score."""
    if now is None:
        now = datetime.now()
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp)
        except (ValueError, TypeError):
            return 50.0
    if timestamp is None:
        return 50.0
    delta_minutes = (now - timestamp).total_seconds() / 60.0
    return max(1.0, 100.0 * (0.5 ** (delta_minutes / 60.0)))


def generate_anomaly_narrative(
    row, severity_score: float, recency_score: float, sensor_corr: float,
    risk_score_val: float = 0.0, recurrence_count: int = 0,
) -> str:
    """Generate plain-language narrative for an anomaly."""
    station = str(row.get("station", "Unknown"))
    gate = str(row.get("gate_id", row.get("gate", "Unknown")))
    temp = float(row.get("sensor_temp", row.get("temp", 25)))
    vib = float(row.get("sensor_vib", row.get("vib", 1.0)))
    sev = str(row.get("severity", row.get("maintenance_status", "WARNING")))

    parts = []

    if sev.upper() == "CRITICAL":
        parts.append(
            f"CRITICAL: {gate} at {station} requires immediate attention."
        )
    elif sev.upper() == "WARNING":
        parts.append(
            f"Warning: {gate} at {station} showing abnormal readings."
        )
    else:
        parts.append(f"{gate} at {station} may need monitoring.")

    if temp > 45:
        parts.append(
            f"Temperature is critically high at {temp:.1f}°C "
            f"— {temp-25:.1f}°C above baseline."
        )
    elif temp > 35:
        parts.append(
            f"Temperature elevated at {temp:.1f}°C ({temp-25:.1f}°C above normal)."
        )
    elif temp > 28:
        parts.append(f"Temperature slightly elevated at {temp:.1f}°C.")

    if vib > 3.0:
        parts.append(f"Vibration levels critically high at {vib:.1f} mm/s.")
    elif vib > 2.0:
        parts.append(f"Vibration above normal range at {vib:.1f} mm/s.")

    if risk_score_val >= 70:
        parts.append(f"Risk score critically high at {risk_score_val:.0f}/100.")
    elif risk_score_val >= 40:
        parts.append(f"Risk score elevated at {risk_score_val:.0f}/100.")

    if recurrence_count >= 3:
        parts.append(
            f"This is the {recurrence_count}th occurrence — failure pattern likely."
        )
    elif recurrence_count >= 2:
        parts.append(
            f"Recurring issue ({recurrence_count}x) — preventive action advised."
        )

    if recency_score > 80:
        parts.append("This just occurred — immediate response recommended.")
    elif recency_score > 50:
        parts.append("Occurred recently — investigation underway.")

    if sensor_corr > 50:
        parts.append(
            "Multiple sensors are reporting abnormal values — possible cascading issue."
        )

    return " ".join(parts)


def get_recommended_action(row) -> str:
    """Generate recommended action based on anomaly type."""
    sev = str(row.get("severity", row.get("maintenance_status", ""))).upper()
    temp = float(row.get("sensor_temp", row.get("temp", 25)))
    vib = float(row.get("sensor_vib", row.get("vib", 1.0)))

    if sev == "CRITICAL":
        if temp > 45:
            return "Dispatch maintenance team immediately — possible thermal overload"
        if vib > 3.0:
            return "Inspect mechanical linkage — schedule emergency maintenance window"
        return "Escalate to shift supervisor — assess within 15 minutes"
    elif sev == "WARNING":
        if temp > 35:
            return "Schedule thermal inspection within next maintenance window"
        if vib > 2.0:
            return "Add to next routine inspection — monitor vibration trend"
        return "Monitor — add to watch list for next 48 hours"
    return "Continue routine monitoring"


def rank_anomalies(
    anomalies_df,
    preset_name: str = "balanced",
    custom_weights: Optional[Dict] = None,
) -> List[Dict]:
    """
    Rank anomalies by composite score using configurable weights.

    Args:
        anomalies_df: DataFrame with columns [station, severity/gate_id/sensor_temp/
                      sensor_vib/risk_score/timestamp/people/contract_value]
        preset_name: Preset name from ANOMALY_RANKING_PRESETS
        custom_weights: Optional override dict with weight keys

    Returns:
        List of ranked anomalies with scores and narrative, sorted highest-first.
        Returns empty list if no anomalies.
    """
    if anomalies_df is None:
        return []
    if isinstance(anomalies_df, pd.DataFrame) and anomalies_df.empty:
        return []

    preset = ANOMALY_RANKING_PRESETS.get(
        preset_name, ANOMALY_RANKING_PRESETS["balanced"]
    )
    weights = custom_weights if custom_weights else preset["weights"]

    now = datetime.now()
    ranked = []

    for _, row in anomalies_df.iterrows():
        sev = get_anomaly_severity_score(
            row.get("severity", row.get("maintenance_status", "WARNING"))
        )

        pax = int(row.get("passenger_count", row.get("people", 0)))
        cv = float(row.get("contract_value", 0))
        station_imp = get_station_importance_score(
            str(row.get("station", "")), pax, cv
        )

        ts = row.get("timestamp", row.get("Timestamp", now))
        recency = get_recency_score(ts, now)

        recurrence = (
            100.0 if row.get("recurrence_count", 0) >= 3
            else (60.0 if row.get("recurrence_count", 0) >= 2 else 20.0)
        )

        temp = float(row.get("sensor_temp", row.get("temp", 25)))
        vib = float(row.get("sensor_vib", row.get("vib", 1.0)))
        risk = float(row.get("risk_score", row.get("risk", 0)))
        abnormal_sensors = sum([
            1 if temp > 35 else 0,
            1 if vib > 2.0 else 0,
            1 if risk >= 70 else 0,
        ])
        sensor_corr = min(100.0, abnormal_sensors * 33.3)

        w_sum = sum(weights.values()) or 1.0
        composite = (
            sev * weights.get("severity", 1.0)
            + station_imp * weights.get("station_importance", 1.0)
            + recency * weights.get("recency", 1.0)
            + recurrence * weights.get("recurrence", 1.0)
            + sensor_corr * weights.get("sensor_correlation", 1.0)
        ) / w_sum

        narrative = generate_anomaly_narrative(
            row, sev, recency, sensor_corr,
            risk_score_val=risk, recurrence_count=int(row.get("recurrence_count", 0)),
        )

        ranked.append({
            "station": str(row.get("station", "")),
            "gate": str(row.get("gate_id", row.get("gate", ""))),
            "severity": str(row.get("severity", row.get("maintenance_status", "WARNING"))),
            "composite_score": round(composite, 1),
            "severity_score": round(sev, 1),
            "station_importance": round(station_imp, 1),
            "recency_score": round(recency, 1),
            "sensor_correlation": round(sensor_corr, 1),
            "temp": temp,
            "vib": vib,
            "risk": risk,
            "recurrence_count": int(row.get("recurrence_count", 0)),
            "narrative": narrative,
            "recommended_action": get_recommended_action(row),
            "timestamp": str(ts),
        })

    ranked.sort(key=lambda x: x["composite_score"], reverse=True)
    return ranked


def get_anomaly_ranking_matrix() -> Dict:
    """Return the full ranking matrix configuration for the settings editor."""
    return {
        "presets": dict(ANOMALY_RANKING_PRESETS),
        "active_preset": DEFAULT_ANOMALY_PRESET,
        "factors": [
            {
                "key": "severity",
                "label": "Severity Level",
                "description": "How critical is the incident type (CRITICAL/WARNING/MONITOR)",
                "min": 0.0, "max": 5.0, "step": 0.1,
            },
            {
                "key": "station_importance",
                "label": "Station Importance",
                "description": "Weight based on passenger volume and contract value",
                "min": 0.0, "max": 5.0, "step": 0.1,
            },
            {
                "key": "recency",
                "label": "Recency",
                "description": "How recently did this anomaly occur (newer = higher)",
                "min": 0.0, "max": 5.0, "step": 0.1,
            },
            {
                "key": "recurrence",
                "label": "Recurrence",
                "description": "How many times has this station/gate appeared recently",
                "min": 0.0, "max": 5.0, "step": 0.1,
            },
            {
                "key": "sensor_correlation",
                "label": "Sensor Correlation",
                "description": "How many sensors are reporting abnormal values",
                "min": 0.0, "max": 5.0, "step": 0.1,
            },
        ],
    }
