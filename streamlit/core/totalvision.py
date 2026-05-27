"""
TotalVision — Cross-Domain Intelligence Hub Data Engine.

Generates synthetic data across 5 analytical domains (Security & Threat,
Sustainability & Energy, Passenger Experience & Sentiment, Asset Lifecycle
& IoT Health, Climate & Infrastructure Resilience), computes cross-domain
correlations, and powers the sandbox what-if simulation engine.

Data patterns match `core/logic.py` conventions: deterministic seeds per
station name, numpy/pandas for data generation, structured logging.
"""

import pandas as pd
import numpy as np
import logging
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────

STATIONS = [
    "Berlin Hbf", "München Hbf", "Hamburg Hbf", "Frankfurt Hbf",
    "Köln Hbf", "Stuttgart Hbf", "Düsseldorf Hbf", "Dortmund Hbf",
    "Essen Hbf", "Bremen Hbf", "Hannover Hbf", "Leipzig Hbf",
    "Nürnberg Hbf", "Dresden Hbf", "Mannheim Hbf",
]

# Domain color identities (matching spec §7.4)
DOMAIN_COLORS = {
    "security":    "#ef4444",  # red
    "sustain":     "#10b981",  # emerald
    "passenger":   "#8b5cf6",  # purple
    "asset":       "#3b82f6",  # blue
    "climate":     "#f59e0b",  # amber/gold
}

# Domain-sensitivity matrix for sandbox projection (spec §11.1)
SENSITIVITY_MATRIX = {
    "investment_level":      {"security": 0.8, "sustain": 0.7, "passenger": 0.5, "asset": 0.9, "climate": 0.6},
    "maintenance_cadence":   {"security": 0.3, "sustain": 0.1, "passenger": 0.4, "asset": 0.8, "climate": 0.2},
    "green_budget":          {"security": 0.1, "sustain": 0.9, "passenger": 0.2, "asset": 0.1, "climate": 0.5},
    "security_staffing":     {"security": 0.9, "sustain": 0.0, "passenger": 0.3, "asset": 0.1, "climate": 0.0},
    "climate_fund":          {"security": 0.0, "sustain": 0.3, "passenger": 0.1, "asset": 0.1, "climate": 0.9},
}

DB_PATH = "simulation_history.db"

# ── Helper ─────────────────────────────────────────────────────────────────


def _rng_for(station: str, offset: int = 0) -> np.random.RandomState:
    """Deterministic RNG seeded by station name + offset."""
    return np.random.RandomState(seed=sum(ord(c) for c in station) + offset)


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


# ── Dataclasses for domain data structures ─────────────────────────────────


@dataclass
class SecurityData:
    station: str = ""
    threat_level: float = 50.0
    threat_label: str = "LOW"
    incidents_cyber: int = 0
    incidents_physical: int = 0
    avg_response_time: float = 3.0
    network_security: float = 70.0
    physical_security: float = 70.0
    access_control: float = 70.0
    incident_response: float = 70.0
    compliance_score: float = 70.0
    training_coverage: float = 70.0
    daily_threats: List[Dict] = field(default_factory=list)
    station_threat_matrix: Dict[str, Dict[str, int]] = field(default_factory=dict)


@dataclass
class SustainabilityData:
    station: str = ""
    energy_kwh: float = 0.0
    energy_target_kwh: float = 0.0
    carbon_tco2e: float = 0.0
    carbon_target_tco2e: float = 0.0
    green_energy_pct: float = 30.0
    recycling_rate: float = 50.0
    efficiency_score: float = 60.0
    monthly_carbon: List[float] = field(default_factory=list)
    regenerative_braking: float = 0.0
    solar_panels: float = 0.0
    led_retrofit: float = 0.0
    efficient_hvac: float = 0.0
    waste_program: float = 0.0


@dataclass
class PassengerData:
    station: str = ""
    satisfaction_score: float = 70.0
    crowding_index: float = 50.0
    accessibility_score: float = 70.0
    dwell_time_avg: float = 45.0
    sentiment_keywords: List[Dict] = field(default_factory=list)
    crowding_matrix: List[Dict] = field(default_factory=list)
    ramp_access: float = 70.0
    audio_announcements: float = 70.0
    visual_displays: float = 70.0
    signage_clarity: float = 70.0
    staff_availability: float = 70.0


@dataclass
class AssetData:
    station: str = ""
    fleet_rul_pct: float = 70.0
    gates_healthy: int = 0
    gates_total: int = 0
    depreciation_remaining: float = 0.0
    rul_bucket_0_25: int = 0
    rul_bucket_25_50: int = 0
    rul_bucket_50_75: int = 0
    rul_bucket_75_100: int = 0
    sensor_healthy: int = 0
    sensor_degraded: int = 0
    sensor_failed: int = 0
    firmware_uptodate: int = 0
    firmware_pending: int = 0
    firmware_critical: int = 0
    depreciation_schedule: List[Dict] = field(default_factory=list)

    # Maintenance backlog (added for Ch5 rebuild)
    backlog_total: int = 0                    # Total overdue maintenance tasks
    backlog_critical: int = 0                  # Critical overdue tasks
    backlog_high: int = 0                      # High priority tasks
    backlog_medium: int = 0                    # Medium priority tasks
    backlog_avg_days_overdue: float = 0.0      # Average days overdue
    backlog_trend_pct: float = 0.0             # Month-over-month trend (% change)

    # Asset type health matrix (per-station breakdown)
    gate_health_pct: float = 0.0               # % of gates healthy
    sensor_health_pct: float = 0.0              # % of sensors healthy
    firmware_compliance_pct: float = 0.0        # % firmware up-to-date
    structural_health_pct: float = 0.0          # % structural components healthy
    power_system_health_pct: float = 0.0        # % power systems operational
    communication_health_pct: float = 0.0        # % comms systems operational


@dataclass
class ClimateData:
    station: str = ""
    resilience_score: float = 60.0
    flood_risk: float = 30.0
    heat_risk: float = 30.0
    storm_risk: float = 30.0
    snow_risk: float = 30.0
    adaptation_readiness_pct: float = 40.0
    weather_events: List[Dict] = field(default_factory=list)
    flood_barriers: float = 30.0
    heat_mitigation: float = 30.0
    storm_proofing: float = 30.0
    snow_clearance: float = 30.0
    emergency_power: float = 30.0
    communication_systems: float = 30.0
    cost_inaction_flood: float = 0.0
    cost_inaction_heat: float = 0.0
    cost_inaction_storm: float = 0.0
    cost_inaction_snow: float = 0.0
    cost_inaction_total: float = 0.0


# ── Master container ────────────────────────────────────────────────────────


@dataclass
class TotalVisionData:
    station: str = ""
    security: SecurityData = field(default_factory=SecurityData)
    sustainability: SustainabilityData = field(default_factory=SustainabilityData)
    passenger: PassengerData = field(default_factory=PassengerData)
    asset: AssetData = field(default_factory=AssetData)
    climate: ClimateData = field(default_factory=ClimateData)

    def scores_dict(self) -> Dict[str, float]:
        return {
            "security":      self.security.threat_level * -1 + 100,  # invert so higher = better
            "sustain":       self.sustainability.efficiency_score,
            "passenger":     float(self.passenger.satisfaction_score),
            "asset":         self.asset.fleet_rul_pct,
            "climate":       float(self.climate.resilience_score),
        }

    def score(self, domain: str) -> float:
        return self.scores_dict().get(domain, 0.0)


# ── Domain Data Generators ─────────────────────────────────────────────────


def generate_security_data(station: str, df: Optional[pd.DataFrame] = None) -> SecurityData:
    """
    Generate synthetic security & threat intelligence data for a station.

    Derives some metrics from existing gate data (sync anomalies → cyber
    indicators, tamper events → physical incidents).
    """
    rng = _rng_for(station, 100)
    gates = 0
    if df is not None and not df.empty:
        gates = int((df[df.get("station", "") == station]["gate_id"].nunique()
                      if "gate_id" in df.columns else 0))
    gates = max(gates, rng.randint(15, 45))

    # Threat level derived from station gate count + randomness
    base_threat = rng.uniform(15, 45)
    cyber_incidents = max(0, int(rng.poisson(2.5)))
    physical_incidents = max(0, int(rng.poisson(1.8)))
    threat_level = _clamp(base_threat + cyber_incidents * 5 + physical_incidents * 4)

    if threat_level < 30:
        label = "LOW"
    elif threat_level < 55:
        label = "ELEVATED"
    elif threat_level < 80:
        label = "HIGH"
    else:
        label = "CRITICAL"

    # Security dimensions (0-100)
    dims = {
        "network_security":    _clamp(rng.normal(72, 12)),
        "physical_security":   _clamp(rng.normal(68, 14)),
        "access_control":      _clamp(rng.normal(75, 10)),
        "incident_response":   _clamp(rng.normal(65, 15)),
        "compliance_score":    _clamp(rng.normal(70, 12)),
        "training_coverage":   _clamp(rng.normal(62, 16)),
    }

    # 30-day daily threat timeline
    daily_threats = []
    for d in range(30):
        cyber = max(0, int(rng.poisson(0.8 + (cyber_incidents / 30))))
        physical = max(0, int(rng.poisson(0.6 + (physical_incidents / 30))))
        daily_threats.append({"day": d + 1, "cyber": cyber, "physical": physical})

    # Station × threat type matrix
    threat_matrix = {}
    threat_types = ["cyber_attack", "physical_breach", "access_tamper", "door_tamper"]
    for ttype in threat_types:
        threat_matrix[ttype] = {
            s: int(rng.poisson(1.5)) for s in rng.choice(STATIONS, rng.randint(3, 8), replace=False)
        }

    # Average response time (minutes)
    avg_response = _clamp(rng.normal(3.5, 1.2), 0.5, 15.0)

    return SecurityData(
        station=station,
        threat_level=round(threat_level, 1),
        threat_label=label,
        incidents_cyber=cyber_incidents,
        incidents_physical=physical_incidents,
        avg_response_time=round(avg_response, 1),
        network_security=round(dims["network_security"], 1),
        physical_security=round(dims["physical_security"], 1),
        access_control=round(dims["access_control"], 1),
        incident_response=round(dims["incident_response"], 1),
        compliance_score=round(dims["compliance_score"], 1),
        training_coverage=round(dims["training_coverage"], 1),
        daily_threats=daily_threats,
        station_threat_matrix=threat_matrix,
    )


def generate_sustainability_data(station: str, df: Optional[pd.DataFrame] = None) -> SustainabilityData:
    """
    Generate synthetic sustainability & energy data for a station.

    Energy consumption is scaled by station size (gate count from df or seed).
    """
    rng = _rng_for(station, 200)
    gates = 0
    if df is not None and not df.empty:
        gates = int((df[df.get("station", "") == station]["gate_id"].nunique()
                      if "gate_id" in df.columns else 0))
    gates = max(gates, rng.randint(15, 45))

    scale = gates * rng.uniform(0.9, 1.1)
    energy_kwh = round(scale * rng.uniform(120, 280), 1)
    energy_target = round(energy_kwh * 0.85, 1)  # 15% reduction target
    carbon = round(energy_kwh * rng.uniform(0.18, 0.35) * 0.001, 2)  # tCO2e
    carbon_target = round(carbon * 0.78, 2)  # 22% reduction target

    green_pct = _clamp(rng.normal(35, 12))
    recycling = _clamp(rng.normal(52, 15))
    efficiency = _clamp(rng.normal(62, 10))

    # Monthly carbon (12 months)
    monthly_carbon = [
        round(carbon * rng.uniform(0.7, 1.3), 2) for _ in range(12)
    ]

    # Initiative breakdown (contribution tonnes CO2e saved per year)
    initiatives = {
        "regenerative_braking": round(rng.uniform(10, 80), 1),
        "solar_panels":         round(rng.uniform(5, 60), 1),
        "led_retrofit":         round(rng.uniform(15, 100), 1),
        "efficient_hvac":       round(rng.uniform(8, 70), 1),
        "waste_program":        round(rng.uniform(3, 30), 1),
    }

    return SustainabilityData(
        station=station,
        energy_kwh=energy_kwh,
        energy_target_kwh=energy_target,
        carbon_tco2e=carbon,
        carbon_target_tco2e=carbon_target,
        green_energy_pct=round(green_pct, 1),
        recycling_rate=round(recycling, 1),
        efficiency_score=round(efficiency, 1),
        monthly_carbon=monthly_carbon,
        **{k: v for k, v in initiatives.items()},
    )


def generate_passenger_data(station: str, df: Optional[pd.DataFrame] = None) -> PassengerData:
    """
    Generate synthetic passenger experience & sentiment data.

    Crowding is scaled by station gate count; satisfaction is influenced
    by congestion/risk scores if df is provided.
    """
    rng = _rng_for(station, 300)
    gates = 0
    avg_congestion = 50.0
    if df is not None and not df.empty:
        sdf = df[df.get("station", "") == station]
        if not sdf.empty:
            gates = int(sdf["gate_id"].nunique()) if "gate_id" in sdf.columns else 0
            if "congestion_score" in sdf.columns:
                avg_congestion = float(sdf["congestion_score"].mean())

    gates = max(gates, rng.randint(15, 45))

    # Satisfaction: influenced by congestion (higher congestion = lower satisfaction)
    base_sat = 75.0 - (avg_congestion / 100) * 15 + rng.normal(0, 5)
    satisfaction = _clamp(base_sat)

    crowding = _clamp(avg_congestion * rng.uniform(0.8, 1.2))
    accessibility = _clamp(rng.normal(72, 10))
    dwell_time = _clamp(rng.normal(48, 12), 15, 120)

    # Sentiment keywords
    all_keywords = [
        ("cleanliness", "pos"), ("punctuality", "pos"), ("staff_helpfulness", "pos"),
        ("signage", "pos"), ("safety", "pos"), ("crowding", "neg"), ("delays", "neg"),
        ("noise", "neg"), ("temperature", "neg"), ("maintenance", "neg"),
        ("accessibility", "pos"), ("lighting", "pos"), ("escalators", "neg"),
    ]
    rng.shuffle(all_keywords)
    sentiment_kws = []
    for word, sentiment in all_keywords[:rng.randint(5, 10)]:
        count = int(rng.poisson(8))
        sentiment_kws.append({"word": word, "count": count, "sentiment": sentiment})

    # Crowding matrix: 4 platforms × 12 hours
    crowding_matrix = []
    hours = list(range(6, 22))  # 06:00 to 21:00
    for platform in range(1, 5):
        for hour in hours:
            base_crowd = 30 + (30 if hour in (7, 8, 17, 18) else 0) + rng.normal(0, 8)
            crowding_matrix.append({
                "platform": platform,
                "hour": hour,
                "crowding_pct": round(_clamp(base_crowd), 1),
            })

    # Accessibility dimensions
    acc_dims = {
        "ramp_access":          _clamp(rng.normal(72, 14)),
        "audio_announcements":  _clamp(rng.normal(68, 16)),
        "visual_displays":      _clamp(rng.normal(75, 12)),
        "signage_clarity":      _clamp(rng.normal(65, 15)),
        "staff_availability":   _clamp(rng.normal(58, 18)),
    }

    return PassengerData(
        station=station,
        satisfaction_score=round(satisfaction, 1),
        crowding_index=round(crowding, 1),
        accessibility_score=round(accessibility, 1),
        dwell_time_avg=round(dwell_time, 1),
        sentiment_keywords=sentiment_kws,
        crowding_matrix=crowding_matrix,
        **{k: round(v, 1) for k, v in acc_dims.items()},
    )


def generate_asset_health_data(station: str, df: Optional[pd.DataFrame] = None) -> AssetData:
    """
    Generate synthetic asset lifecycle & IoT health data.

    Remaining useful life (RUL) is partly derived from existing sensor data
    (temperature, vibration) as degradation proxies.
    """
    rng = _rng_for(station, 400)
    gates = 0
    avg_temp = 30.0
    avg_vib = 5.0
    if df is not None and not df.empty:
        sdf = df[df.get("station", "") == station]
        if not sdf.empty:
            gates = int(sdf["gate_id"].nunique()) if "gate_id" in sdf.columns else 0
            if "sensor_temp" in sdf.columns:
                avg_temp = float(sdf["sensor_temp"].mean())
            if "sensor_vib" in sdf.columns:
                avg_vib = float(sdf["sensor_vib"].mean())

    gates = max(gates, rng.randint(15, 45))

    # RUL: higher temp/vib → lower RUL
    temp_penalty = max(0, (avg_temp - 30) * 1.5)
    vib_penalty = max(0, (avg_vib - 5) * 3)
    base_rul = 75 - temp_penalty - vib_penalty + rng.normal(0, 8)
    fleet_rul = _clamp(base_rul)

    # RUL distribution across gate population
    rul_buckets = {
        "0-25":  max(0, int(gates * (1 - fleet_rul / 100) * rng.uniform(0.3, 0.7))),
        "25-50": max(0, int(gates * rng.uniform(0.15, 0.35))),
        "50-75": max(0, int(gates * rng.uniform(0.20, 0.40))),
        "75-100": 0,
    }
    rul_buckets["75-100"] = max(0, gates - sum(rul_buckets.values()))

    # Sensor health
    sensor_healthy = int(gates * _clamp(rng.normal(0.78, 0.08)))
    sensor_degraded = int(gates * _clamp(rng.normal(0.15, 0.05)))
    sensor_failed = max(0, gates - sensor_healthy - sensor_degraded)

    # Firmware compliance
    fw_counts = {
        "up_to_date":     int(gates * _clamp(rng.normal(0.60, 0.10))),
        "pending_update": int(gates * _clamp(rng.normal(0.25, 0.08))),
        "critical_missing": 0,
    }
    fw_counts["critical_missing"] = max(0, gates - sum(fw_counts.values()))

    # Depreciation: gate value €50K avg, 10-year straight-line
    total_value = gates * rng.uniform(35, 65) * 1000  # €
    annual_depreciation = total_value / 10
    depreciation_schedule = []
    for year in range(2025, 2035):
        remaining = max(0, total_value - annual_depreciation * (year - 2025))
        depreciation_schedule.append({
            "year": year,
            "book_value": round(remaining, 0),
        })

    # ── Maintenance backlog (proportional to gate count & degradation) ──
    backlog_base = gates * _clamp(rng.normal(0.15, 0.04))
    backlog_total = int(backlog_base)
    backlog_priority_ratios = [0.20, 0.30, 0.50]  # critical/high/medium
    backlog_critical = max(0, int(backlog_total * backlog_priority_ratios[0] * (1 + sensor_failed / max(gates, 1) * 2)))
    backlog_high = max(0, int(backlog_total * backlog_priority_ratios[1]))
    backlog_medium = max(0, backlog_total - backlog_critical - backlog_high)
    backlog_avg_days = _clamp(rng.normal(14, 5), 1, 90)
    backlog_trend = _clamp(rng.normal(-3, 8), -30, 30)  # negative = improving

    # ── Asset type health percentages ──
    gate_health_pct = _clamp((sensor_healthy / max(gates, 1)) * 100)
    sensor_health_pct_val = _clamp(((sensor_healthy + sensor_degraded * 0.5) / max(gates, 1)) * 100)
    firmware_comp_pct = _clamp((fw_counts["up_to_date"] / max(gates, 1)) * 100)
    structural_health = _clamp(rng.normal(82, 8))
    power_health = _clamp(rng.normal(78, 10))
    comm_health = _clamp(rng.normal(85, 7))

    return AssetData(
        station=station,
        fleet_rul_pct=round(fleet_rul, 1),
        gates_healthy=sensor_healthy,
        gates_total=gates,
        depreciation_remaining=round(total_value * (fleet_rul / 100), 0),
        rul_bucket_0_25=rul_buckets["0-25"],
        rul_bucket_25_50=rul_buckets["25-50"],
        rul_bucket_50_75=rul_buckets["50-75"],
        rul_bucket_75_100=rul_buckets["75-100"],
        sensor_healthy=sensor_healthy,
        sensor_degraded=sensor_degraded,
        sensor_failed=sensor_failed,
        firmware_uptodate=fw_counts["up_to_date"],
        firmware_pending=fw_counts["pending_update"],
        firmware_critical=fw_counts["critical_missing"],
        depreciation_schedule=depreciation_schedule,
        backlog_total=backlog_total,
        backlog_critical=backlog_critical,
        backlog_high=backlog_high,
        backlog_medium=backlog_medium,
        backlog_avg_days_overdue=round(backlog_avg_days, 1),
        backlog_trend_pct=round(backlog_trend, 1),
        gate_health_pct=round(gate_health_pct, 1),
        sensor_health_pct=round(sensor_health_pct_val, 1),
        firmware_compliance_pct=round(firmware_comp_pct, 1),
        structural_health_pct=round(structural_health, 1),
        power_system_health_pct=round(power_health, 1),
        communication_health_pct=round(comm_health, 1),
    )


def generate_climate_resilience_data(station: str) -> ClimateData:
    """
    Generate synthetic climate & infrastructure resilience data.

    Coastal stations get higher flood/storm risk; southern stations get
    higher heat risk.
    """
    rng = _rng_for(station, 500)

    # Determine station geography for risk weighting
    coastal = any(city in station for city in ["Hamburg", "Bremen", "Kiel"])
    southern = any(city in station for city in ["Munich", "Stuttgart", "Nuremberg", "Mannheim"])

    flood_risk = _clamp(rng.normal(50 if coastal else 25, 15))
    heat_risk = _clamp(rng.normal(55 if southern else 30, 12))
    storm_risk = _clamp(rng.normal(45 if coastal else 28, 14))
    snow_risk = _clamp(rng.normal(40 if southern else 25, 12))

    # Overall resilience — inverse of weighted risks
    resilience = 100 - (
        flood_risk * 0.30 + heat_risk * 0.25 +
        storm_risk * 0.25 + snow_risk * 0.20
    ) + rng.normal(0, 5)
    resilience = _clamp(resilience)

    adaptation = _clamp(rng.normal(42, 12))

    # Adaptation dimensions
    adapt_dims = {
        "flood_barriers":        _clamp(rng.normal(35, 18)),
        "heat_mitigation":       _clamp(rng.normal(40, 15)),
        "storm_proofing":        _clamp(rng.normal(30, 16)),
        "snow_clearance":        _clamp(rng.normal(55, 14)),
        "emergency_power":       _clamp(rng.normal(45, 12)),
        "communication_systems": _clamp(rng.normal(60, 10)),
    }

    # Weather events over 12 months
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    event_types = ["storm", "heatwave", "flood", "snowfall", "wind"]
    weather_events = []
    for i, month in enumerate(months):
        if rng.random() < 0.35:  # ~35% chance of event per month
            event_type = rng.choice(event_types)
            base_sev = 20
            if event_type == "storm" and coastal:
                base_sev = 40
            elif event_type == "heatwave" and southern:
                base_sev = 45
            severity = _clamp(base_sev + rng.normal(0, 15))
            disruptions = int(rng.poisson(3))
            weather_events.append({
                "month": month,
                "event_type": event_type,
                "severity": round(severity, 1),
                "disruptions": disruptions,
            })

    # Cost of inaction (€K)
    costs = {
        "flood": round(rng.uniform(200, 3000), 0) if coastal else round(rng.uniform(50, 800), 0),
        "heat":  round(rng.uniform(100, 1500), 0),
        "storm": round(rng.uniform(150, 2500), 0) if coastal else round(rng.uniform(80, 1000), 0),
        "snow":  round(rng.uniform(50, 800), 0),
    }
    costs["total"] = sum(costs.values())

    return ClimateData(
        station=station,
        resilience_score=round(resilience, 1),
        flood_risk=round(flood_risk, 1),
        heat_risk=round(heat_risk, 1),
        storm_risk=round(storm_risk, 1),
        snow_risk=round(snow_risk, 1),
        adaptation_readiness_pct=round(adaptation, 1),
        weather_events=weather_events,
        **{k: round(v, 1) for k, v in adapt_dims.items()},
        cost_inaction_flood=costs["flood"],
        cost_inaction_heat=costs["heat"],
        cost_inaction_storm=costs["storm"],
        cost_inaction_snow=costs["snow"],
        cost_inaction_total=costs["total"],
    )


# ── Master Generator ───────────────────────────────────────────────────────


def generate_all_domains(station: str, df: Optional[pd.DataFrame] = None) -> TotalVisionData:
    """Generate all 5 domain data for a single station."""
    return TotalVisionData(
        station=station,
        security=generate_security_data(station, df),
        sustainability=generate_sustainability_data(station, df),
        passenger=generate_passenger_data(station, df),
        asset=generate_asset_health_data(station, df),
        climate=generate_climate_resilience_data(station),
    )


def generate_all_stations(df: Optional[pd.DataFrame] = None) -> Dict[str, TotalVisionData]:
    """Generate TotalVision data for all 15 stations."""
    return {s: generate_all_domains(s, df) for s in STATIONS}


# ── Correlation Engine ────────────────────────────────────────────────────


def _domain_score_vector(all_data: Dict[str, TotalVisionData], domain: str) -> np.ndarray:
    return np.array([d.score(domain) for d in all_data.values()])


def compute_cross_correlations(all_data: Dict[str, TotalVisionData]) -> Dict[str, Any]:
    """
    Compute Pearson correlation matrix across all 5 domains.

    Returns:
        {
            "matrix": {domain_a: {domain_b: r_value}},
            "findings": [{domain_a, domain_b, r_value, story, strength}],
            "p_values": {domain_a: {domain_b: p_value}},
        }
    """
    domains = ["security", "sustain", "passenger", "asset", "climate"]
    vectors = {d: _domain_score_vector(all_data, d) for d in domains}

    matrix = {}
    p_values = {}

    for d1 in domains:
        matrix[d1] = {}
        p_values[d1] = {}
        for d2 in domains:
            if d1 == d2:
                matrix[d1][d2] = 1.0
                p_values[d1][d2] = 0.0
            else:
                v1, v2 = vectors[d1], vectors[d2]
                if np.std(v1) > 0 and np.std(v2) > 0:
                    r = np.corrcoef(v1, v2)[0, 1]
                    # Approximate p-value using t-distribution
                    n = len(v1)
                    t_stat = r * np.sqrt((n - 2) / max(1 - r**2, 0.001))
                    p = 2 * (1 - _t_cdf(abs(t_stat), n - 2))
                    matrix[d1][d2] = round(r, 4)
                    p_values[d1][d2] = round(min(p, 1.0), 4)
                else:
                    matrix[d1][d2] = 0.0
                    p_values[d1][d2] = 1.0

    # Auto-discover surprising findings
    findings = []
    domain_labels = {
        "security": "Security & Threat",
        "sustain": "Sustainability & Energy",
        "passenger": "Passenger Experience",
        "asset": "Asset Lifecycle",
        "climate": "Climate Resilience",
    }
    for d1 in domains:
        for d2 in domains:
            if d1 < d2:
                r = matrix[d1][d2]
                p = p_values[d1][d2]
                if abs(r) > 0.3 and p < 0.1:
                    strength = "strong" if abs(r) > 0.7 else "moderate"
                    direction = "positive" if r > 0 else "negative"
                    story = _generate_finding_story(d1, d2, r, strength, direction)
                    findings.append({
                        "domain_a": d1,
                        "domain_b": d2,
                        "label_a": domain_labels[d1],
                        "label_b": domain_labels[d2],
                        "r_value": r,
                        "p_value": p,
                        "strength": strength,
                        "direction": direction,
                        "story": story,
                    })

    findings.sort(key=lambda f: abs(f["r_value"]), reverse=True)

    return {
        "matrix": matrix,
        "findings": findings[:5],  # top 5
        "p_values": p_values,
    }


def _t_cdf(t: float, df: int) -> float:
    """Approximate Student's t CDF (scipy-backed, normal-approximation fallback)."""
    try:
        from scipy import special
        x = df / (df + t**2)
        if t >= 0:
            # Student's t CDF = 1 - 0.5 * I(df/(df+t^2), df/2, 0.5)
            return float(1.0 - 0.5 * special.betainc(df / 2, 0.5, x))
        else:
            # Symmetry: CDF(-t) = 1 - CDF(t)
            return float(0.5 * special.betainc(df / 2, 0.5, x))
    except ImportError:
        from math import erf
        return float(0.5 * (1 + erf(t / 1.4142135623730951)))


def _generate_finding_story(d1: str, d2: str, r: float, strength: str, direction: str) -> str:
    """Generate a narrative description for a correlation finding."""
    stories = {
        ("security", "asset"): (
            f"Security & Asset Lifecycle show a {strength} {direction} correlation (r={r:.2f}). "
            "Stations with higher security investments tend to maintain healthier PSD assets — "
            "likely due to better maintenance protocols and monitoring coverage."
        ),
        ("security", "passenger"): (
            f"Security & Passenger Experience show a {strength} {direction} correlation (r={r:.2f}). "
            "Passengers feel safer at stations with robust security measures, boosting satisfaction scores."
        ),
        ("sustain", "passenger"): (
            f"Sustainability & Passenger Experience show a {strength} {direction} correlation (r={r:.2f}). "
            "Eco-friendly stations with better lighting, ventilation, and modern facilities "
            "tend to receive higher satisfaction ratings."
        ),
        ("sustain", "climate"): (
            f"Sustainability & Climate Resilience show a {strength} {direction} correlation (r={r:.2f}). "
            "Stations investing in green infrastructure are naturally more resilient to climate events "
            "due to overlapping adaptation measures."
        ),
        ("asset", "climate"): (
            f"Asset Lifecycle & Climate Resilience show a {strength} {direction} correlation (r={r:.2f}). "
            "Well-maintained assets with higher RUL are more resilient to weather-related disruptions."
        ),
        ("security", "climate"): (
            f"Security & Climate Resilience show a {strength} {direction} correlation (r={r:.2f}). "
            "Climate adaptation investments often include security improvements like hardened infrastructure "
            "and backup power systems."
        ),
        ("asset", "passenger"): (
            f"Asset Lifecycle & Passenger Experience show a {strength} {direction} correlation (r={r:.2f}). "
            "Stations with healthier PSD assets provide more reliable service, directly improving "
            "passenger satisfaction."
        ),
        ("sustain", "asset"): (
            f"Sustainability & Asset Lifecycle show a {strength} {direction} correlation (r={r:.2f}). "
            "Energy-efficient stations tend to have newer, better-maintained equipment with higher RUL."
        ),
        ("security", "sustain"): (
            f"Security & Sustainability show a {strength} {direction} correlation (r={r:.2f}). "
            "Security-conscious stations are more likely to adopt sustainability practices, "
            "reflecting broader operational excellence."
        ),
        ("passenger", "climate"): (
            f"Passenger Experience & Climate Resilience show a {strength} {direction} correlation (r={r:.2f}). "
            "Stations prepared for climate events maintain better service continuity, positively impacting "
            "passenger satisfaction during disruptions."
        ),
    }
    # Fallback for unseen pairs
    return stories.get(
        (d1, d2) if (d1, d2) in stories else (d2, d1),
        f"{d1.title()} & {d2.title()} show a {strength} {direction} correlation (r={r:.2f}). "
        f"This suggests linked performance drivers worth investigating."
    )


# ── Sandbox Simulation Engine ─────────────────────────────────────────────


def run_sandbox_projection(
    params: Dict[str, float],
    all_data: Dict[str, TotalVisionData],
) -> Dict[str, Any]:
    """
    Run the weighted-multiplier sandbox projection model across all 5 domains.

    Args:
        params: Dict with master param keys (investment_level, maintenance_cadence,
                green_budget, security_staffing, climate_fund) and domain-specific
                keys prefixed by domain name.
        all_data: Current TotalVisionData for all stations.

    Returns:
        {
            "projected_scores": {domain: float},
            "baseline_scores": {domain: float},
            "deltas": {domain: float},
            "timeline": [{month, domain: score}],
            "station_projections": {station: {domain: score}},
        }
    """
    # Default params if not provided
    defaults = {
        "investment_level": 1.0,
        "maintenance_cadence": 6.0,
        "green_budget": 1_000_000,
        "security_staffing": 100.0,
        "climate_fund": 2_000_000,
    }
    for k, v in defaults.items():
        params.setdefault(k, v)

    # Compute baseline scores (average across all stations)
    domains = ["security", "sustain", "passenger", "asset", "climate"]
    baseline = {}
    for d in domains:
        scores = [data.score(d) for data in all_data.values()]
        baseline[d] = round(float(np.mean(scores)), 1)

    # Compute projected scores using sensitivity matrix
    projected = {}
    for d in domains:
        base = baseline[d]
        deltas = []
        for param, value in params.items():
            if param in SENSITIVITY_MATRIX:
                multiplier = value / defaults.get(param, 1.0)
                weight = SENSITIVITY_MATRIX[param].get(d, 0.0)
                delta = (multiplier - 1.0) * weight * base
                deltas.append(delta)
        proj = _clamp(base + sum(deltas))
        projected[d] = round(proj, 1)

    # Deltas
    deltas = {d: round(projected[d] - baseline[d], 1) for d in domains}

    # 24-month timeline (monthly projected trajectory)
    timeline = []
    for month in range(1, 25):
        progress = month / 24.0
        entry = {"month": month}
        for d in domains:
            entry[d] = round(baseline[d] + deltas[d] * progress, 1)
        timeline.append(entry)

    # Per-station projections
    station_projections = {}
    for station, tv_data in all_data.items():
        station_projections[station] = {}
        for d in domains:
            base = tv_data.score(d)
            # Apply the same delta proportionally to the station's baseline
            if baseline[d] > 0:
                ratio = base / baseline[d]
                proj = _clamp(base + deltas[d] * ratio)
            else:
                proj = base + deltas[d]
            station_projections[station][d] = round(proj, 1)

    return {
        "projected_scores": projected,
        "baseline_scores": baseline,
        "deltas": deltas,
        "timeline": timeline,
        "station_projections": station_projections,
    }


# ── Scenario Persistence ──────────────────────────────────────────────────


def _get_db_path() -> str:
    """Return path to simulation database."""
    return DB_PATH


def _with_db(fn, mode=None):
    """Open connection, call fn(conn), close. Returns fn's result."""
    _init_totalvision_table()
    conn = sqlite3.connect(_get_db_path(), check_same_thread=False)
    if mode and "row" in mode:
        conn.row_factory = sqlite3.Row
    try:
        return fn(conn)
    finally:
        conn.close()


def _init_totalvision_table():
    """Ensure the totalvision_scenarios table exists."""
    db = _get_db_path()
    try:
        conn = sqlite3.connect(db, check_same_thread=False)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS totalvision_scenarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                params_json TEXT NOT NULL,
                results_json TEXT NOT NULL,
                notes TEXT DEFAULT ''
            )
        """)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logger.warning(f"Cannot initialize totalvision_scenarios table: {e}")


def save_scenario(name: str, params: Dict, results: Dict, notes: str = "") -> bool:
    """Persist a sandbox scenario to the SQLite database."""
    try:
        def _do(conn):
            conn.execute(
                "INSERT INTO totalvision_scenarios (name, params_json, results_json, notes) VALUES (?, ?, ?, ?)",
                (name, json.dumps(params), json.dumps(results), notes),
            )
            conn.commit()
            logger.info(f"TotalVision scenario '{name}' saved")
            return True
        return _with_db(_do)
    except Exception as e:
        logger.error(f"Failed to save scenario '{name}': {e}")
        return False


def load_scenario(scenario_id: int) -> Optional[Dict[str, Any]]:
    """Load a saved scenario from the SQLite database."""
    try:
        def _do(conn):
            row = conn.execute(
                "SELECT * FROM totalvision_scenarios WHERE id = ?", (scenario_id,)
            ).fetchone()
            if row is None:
                return None
            return {
                "id": row["id"],
                "name": row["name"],
                "created_at": row["created_at"],
                "params": json.loads(row["params_json"]),
                "results": json.loads(row["results_json"]),
                "notes": row["notes"],
            }
        return _with_db(_do, "row")
    except Exception as e:
        logger.error(f"Failed to load scenario {scenario_id}: {e}")
        return None


def list_saved_scenarios() -> List[Dict[str, Any]]:
    """List all saved TotalVision scenarios as summaries."""
    try:
        def _do(conn):
            rows = conn.execute(
                "SELECT id, name, created_at, notes FROM totalvision_scenarios ORDER BY created_at DESC"
            ).fetchall()
            return [dict(r) for r in rows]
        return _with_db(_do, "row")
    except Exception as e:
        logger.error(f"Failed to list scenarios: {e}")
        return []


def delete_scenario(scenario_id: int) -> bool:
    """Delete a saved scenario."""
    try:
        def _do(conn):
            conn.execute("DELETE FROM totalvision_scenarios WHERE id = ?", (scenario_id,))
            conn.commit()
            return True
        return _with_db(_do)
    except Exception as e:
        logger.error(f"Failed to delete scenario {scenario_id}: {e}")
        return False


# ── Main Data Engine Class ────────────────────────────────────────────────


class TotalVisionDataEngine:
    """
    Orchestrates data generation, correlation analysis, and sandbox simulation.

    Usage:
        engine = TotalVisionDataEngine(df=None)  # df is optional station DataFrame
        data = engine.generate_all()             # all 15 stations
        station_data = engine.generate("Berlin Hbf")
        correlations = engine.correlate(data)
        projection = engine.project(params, data)
        engine.save("My Scenario", params, projection)
    """

    def __init__(self, df: Optional[pd.DataFrame] = None):
        self.df = df  # Existing station gate sensor DataFrame (optional)

    def generate(self, station: str) -> TotalVisionData:
        """Generate all 5 domain data for a single station."""
        return generate_all_domains(station, self.df)

    def generate_all(self) -> Dict[str, TotalVisionData]:
        """Generate TotalVision data for all 15 stations."""
        return generate_all_stations(self.df)

    def correlate(self, all_data: Dict[str, TotalVisionData]) -> Dict[str, Any]:
        """Compute cross-domain correlation matrix + auto-findings."""
        return compute_cross_correlations(all_data)

    def project(self, params: Dict[str, float], all_data: Dict[str, TotalVisionData]) -> Dict[str, Any]:
        """Run sandbox projection model."""
        return run_sandbox_projection(params, all_data)

    @staticmethod
    def save(name: str, params: Dict, results: Dict, notes: str = "") -> bool:
        return save_scenario(name, params, results, notes)

    @staticmethod
    def load(scenario_id: int) -> Optional[Dict[str, Any]]:
        return load_scenario(scenario_id)

    @staticmethod
    def list_scenarios() -> List[Dict[str, Any]]:
        return list_saved_scenarios()

    @staticmethod
    def delete(scenario_id: int) -> bool:
        return delete_scenario(scenario_id)

    @staticmethod
    def stations() -> List[str]:
        return list(STATIONS)

    @staticmethod
    def domain_colors() -> Dict[str, str]:
        return dict(DOMAIN_COLORS)

    # ── Convenience: aggregate KPI scores for all stations ────────────────

    @staticmethod
    def aggregate_scores(all_data: Dict[str, TotalVisionData]) -> Dict[str, float]:
        """Return average score per domain across all stations."""
        domains = ["security", "sustain", "passenger", "asset", "climate"]
        return {
            d: round(float(np.mean([data.score(d) for data in all_data.values()])), 1)
            for d in domains
        }

    @staticmethod
    def station_scores_df(all_data: Dict[str, TotalVisionData]) -> pd.DataFrame:
        """Return a DataFrame of (station, domain, score) for charting."""
        rows = []
        for station, data in all_data.items():
            for domain, score in data.scores_dict().items():
                rows.append({"station": station, "domain": domain, "score": round(score, 1)})
        return pd.DataFrame(rows)
