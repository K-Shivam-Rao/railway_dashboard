import pandas as pd
import numpy as np
from datetime import datetime, timedelta


# ─────────────────────────────────────────────
# DATA LOADING & TRANSFORMATION
# ─────────────────────────────────────────────

def load_data():
    """Load station data from CSV with error handling."""
    try:
        df = pd.read_csv("stations.csv")
        # Validate required columns
        required_columns = {'station', 'gate_id', 'door_state', 'sensor_temp',
                           'sensor_vib', 'people', 'platform'}
        missing = required_columns - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns in stations.csv: {missing}")
        return df
    except FileNotFoundError:
        raise FileNotFoundError("stations.csv not found. Please ensure the data file exists.")
    except pd.errors.EmptyDataError:
        raise ValueError("stations.csv is empty or contains no data.")


def transform_data(df):
    """Apply derived columns: sync score, maintenance status, risk level."""

    def calculate_sync_score(row):
        base = 100
        if pd.isna(row['sensor_temp']):
            return base
        penalty = (row['sensor_temp'] - 25) * 0.5 + (row['sensor_vib'] * 2)
        return max(0, int(base - penalty))

    def get_maintenance_status(row):
        if row['door_state'] == 'jammed':
            return 'CRITICAL'
        if row['sensor_temp'] > 45:
            return 'WARNING'
        if row['sync_score'] < 85:
            return 'MONITOR'
        return 'OPTIMAL'

    def get_risk_score(row):
        """0-100 composite risk score for predictive maintenance."""
        risk = 0
        if row['door_state'] == 'jammed':
            risk += 60
        if row['sensor_temp'] > 45:
            risk += 25
        elif row['sensor_temp'] > 35:
            risk += 10
        if row['sensor_vib'] > 3:
            risk += 15
        elif row['sensor_vib'] > 1.5:
            risk += 5
        return min(100, risk)

    df['sync_score'] = df.apply(calculate_sync_score, axis=1)
    df['maintenance_status'] = df.apply(get_maintenance_status, axis=1)
    df['risk_score'] = df.apply(get_risk_score, axis=1)
    return df


# ─────────────────────────────────────────────
# STATION METRICS
# ─────────────────────────────────────────────

def get_metrics(df, station_name):
    station_df = df[df["station"] == station_name]
    gates_total = len(station_df)
    gates_active = len(station_df[station_df["door_state"] != "offline"])
    people_total = int(station_df["people"].sum())
    alerts = len(station_df[station_df["maintenance_status"] == "CRITICAL"])
    avg_sync = int(station_df["sync_score"].mean()
                   ) if not station_df.empty else 0
    warnings = len(station_df[station_df["maintenance_status"] == "WARNING"])
    return gates_total, gates_active, people_total, alerts, avg_sync, warnings


# ─────────────────────────────────────────────
# ANALYTICS: PER-STATION CHARTS
# ─────────────────────────────────────────────

def get_psd_analytics(station_name):
    """Deterministic hourly chart data for door cycles and temperature."""
    rng = np.random.RandomState(seed=sum(ord(c) for c in station_name))

    hours = ["06:00", "07:00", "08:00", "09:00", "10:00", "12:00",
             "14:00", "16:00", "17:00", "18:00", "20:00", "22:00"]
    flow = rng.randint(150, 900, size=len(hours))
    # Rush-hour spike
    flow[2] = rng.randint(700, 900)
    flow[4] = rng.randint(650, 850)
    flow[10] = rng.randint(600, 850)

    temp = np.linspace(22, 34, len(hours)) + rng.normal(0, 1, len(hours))

    return (
        pd.DataFrame({"Hour": hours, "Door Cycles": flow}),
        pd.DataFrame({"Hour": hours, "Avg Temp (°C)": temp.round(1)})
    )


# ─────────────────────────────────────────────
# ANALYTICS: NETWORK-WIDE
# ─────────────────────────────────────────────

def get_network_summary(df):
    """Aggregate stats across all stations."""
    total_gates = len(df)
    total_people = int(df["people"].sum())
    critical_count = len(df[df["maintenance_status"] == "CRITICAL"])
    warning_count = len(df[df["maintenance_status"] == "WARNING"])
    network_sync = int(df["sync_score"].mean())
    optimal_count = len(df[df["maintenance_status"] == "OPTIMAL"])

    status_dist = df.groupby(
        "maintenance_status").size().reset_index(name="Count")
    door_dist = df.groupby("door_state").size().reset_index(name="Count")

    station_summary = df.groupby("station").agg(
        Gates=("gate_id", "count"),
        People=("people", "sum"),
        Avg_Sync=("sync_score", "mean"),
        Criticals=("maintenance_status", lambda x: (x == "CRITICAL").sum()),
        Avg_Risk=("risk_score", "mean")
    ).reset_index()
    station_summary["Avg_Sync"] = station_summary["Avg_Sync"].round(1)
    station_summary["Avg_Risk"] = station_summary["Avg_Risk"].round(1)
    station_summary.columns = ["Station", "Gates",
                               "Passengers", "Avg Sync %", "Criticals", "Avg Risk"]

    return {
        "total_gates": total_gates,
        "total_people": total_people,
        "critical_count": critical_count,
        "warning_count": warning_count,
        "network_sync": network_sync,
        "optimal_count": optimal_count,
        "status_dist": status_dist,
        "door_dist": door_dist,
        "station_summary": station_summary
    }


# ─────────────────────────────────────────────
# ANALYTICS: PREDICTIVE MAINTENANCE TIMELINE
# ─────────────────────────────────────────────

def get_maintenance_forecast(station_name):
    """Simulate a 7-day risk forecast for the selected station."""
    rng = np.random.RandomState(seed=sum(ord(c) for c in station_name) + 42)

    today = datetime.today()
    days = [(today + timedelta(days=i)).strftime("%b %d") for i in range(7)]

    # Randomized but station-consistent risk forecast
    base_risk = rng.randint(10, 40)
    risks = np.clip(base_risk + rng.normal(0, 8, 7).cumsum(), 5, 95).round(1)

    return pd.DataFrame({"Date": days, "Predicted Risk %": risks})


# ─────────────────────────────────────────────
# ANALYTICS: PASSENGER FLOW HEATMAP DATA
# ─────────────────────────────────────────────

def get_passenger_heatmap(station_name):
    """7-day x 12-hour passenger flow matrix."""
    rng = np.random.RandomState(seed=sum(ord(c) for c in station_name) + 99)

    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    hours = ["06", "07", "08", "09", "10", "12",
             "14", "16", "17", "18", "20", "22"]

    matrix = rng.randint(50, 800, size=(len(days), len(hours)))
    # Add rush hour peaks Mon-Fri
    for d in range(5):
        matrix[d][2] = rng.randint(650, 900)   # 08:00
        matrix[d][9] = rng.randint(600, 850)   # 18:00
    # Lower weekends
    for d in [5, 6]:
        matrix[d] = (matrix[d] * 0.5).astype(int)

    return pd.DataFrame(matrix, index=days, columns=hours)


# ─────────────────────────────────────────────
# INCIDENT LOG
# ─────────────────────────────────────────────

def get_incident_log(df):
    """Generate incident records from critical/warning gates."""
    incidents = []
    now = datetime.now()

    critical_gates = df[df["maintenance_status"].isin(
        ["CRITICAL", "WARNING"])].copy()
    for i, (_, row) in enumerate(critical_gates.iterrows()):
        delta = timedelta(minutes=np.random.randint(2, 240))
        ts = (now - delta).strftime("%H:%M")
        severity = "🔴 CRITICAL" if row["maintenance_status"] == "CRITICAL" else "🟡 WARNING"
        if row["door_state"] == "jammed":
            desc = f"Gate {row['gate_id']} jammed — manual override required"
        elif row["sensor_temp"] > 45:
            desc = f"Thermal anomaly {row['sensor_temp']}°C on Gate {row['gate_id']}"
        else:
            desc = f"Sync score degraded ({row['sync_score']}%) on Gate {row['gate_id']}"
        incidents.append({
            "Time": ts,
            "Station": row["station"],
            "Platform": row["platform"],
            "Gate": row["gate_id"],
            "Severity": severity,
            "Description": desc,
            "Temp (°C)": row["sensor_temp"],
            "Vibration": row["sensor_vib"]
        })

    return pd.DataFrame(incidents).sort_values("Time", ascending=False) if incidents else pd.DataFrame()


# ─────────────────────────────────────────────
# LEADERSHIP DATA
# ─────────────────────────────────────────────
def get_leadership_data():
    return [
        {
            "name": "Khushboo Patil",
            "role": "CEO",
            "desc": "Business Strategy, Market Expansion, and Organizational Leadership",
            "img": "https://ui-avatars.com/api/?name=Khushboo+Patil&background=0e4d92&color=fff",
            "linkedin": "#"
        },
        {
            "name": "Namrata Joshi",
            "role": "COO",
            "desc": "Operations Management, Strategic Planning, and Project Coordination",
            "img": "https://ui-avatars.com/api/?name=Namrata+Joshi&background=0e4d92&color=fff",
            "linkedin": "#"
        },
        {
            "name": "Kona Shivam Rao",
            "role": "CTO",
            "desc": "Systems Engineering, Automation, and Rail Technology Development",
            "img": "https://ui-avatars.com/api/?name=Kona+Shivam+Rao&background=0e4d92&color=fff",
            "linkedin": "#"
        },
        {
            "name": "Sanika Kale",
            "role": "CPO",
            "desc": "Product Innovation, UX Design, and Platform System Integration",
            "img": "https://ui-avatars.com/api/?name=Sanika+Kale&background=0e4d92&color=fff",
            "linkedin": "#"
        },
        {
            "name": "Nikhil Chavan",
            "role": "CFO",
            "desc": "Financial Strategy, Infrastructure Investment, and Strategic Partnerships",
            "img": "https://ui-avatars.com/api/?name=Nikhil+Chavan&background=0e4d92&color=fff",
            "linkedin": "#"
        }
    ]


# ─────────────────────────────────────────────
# TECHNOLOGY STACK DATA
# ─────────────────────────────────────────────

def get_tech_stack():
    return [
        {"layer": "Sensing", "tech": "IoT Sensors",
            "detail": "Temperature, vibration, proximity (0.1ms latency)"},
        {"layer": "Edge", "tech": "PSD Controllers",
            "detail": "Real-time gate logic with fail-safe override"},
        {"layer": "Network", "tech": "5G / Fiber",
            "detail": "Sub-10ms station-to-cloud sync"},
        {"layer": "Platform", "tech": "BahnSetu Core",
            "detail": "Microservices architecture, 99.97% uptime SLA"},
        {"layer": "Analytics", "tech": "ML Pipeline",
            "detail": "Predictive maintenance, anomaly detection"},
        {"layer": "Interface", "tech": "SicherGleis Pro",
            "detail": "Unified dashboard (this application)"},
    ]
