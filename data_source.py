import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import functools
import streamlit as st
from typing import Dict, List, Tuple, Optional


# ─────────────────────────────────────────────
# DATA LOADING & TRANSFORMATION
# ─────────────────────────────────────────────

@st.cache_data(ttl=60, show_spinner=False)
def load_data():
    """Load station data from CSV with comprehensive schema validation."""
    try:
        df = pd.read_csv("stations.csv")

        # Required core columns
        required_core = {'station', 'platform', 'gate_id', 'door_state',
                        'sensor_temp', 'sensor_vib', 'people'}

        # Optional enhanced columns (backward compatibility)
        optional_cols = {'train', 'train_type', 'operator', 'destination', 'status',
                        'capacity', 'occupancy_rate', 'eta', 'delay', 'platform_length',
                        'door_position', 'sync_score', 'maintenance_status', 'risk_score',
                        'signal_status', 'track_number', 'last_maintenance', 'power_consumption',
                        'humidity', 'door_motor_current', 'connection_line'}

        all_expected = required_core.union(optional_cols)
        available = set(df.columns)

        # Validate required columns exist
        missing_required = required_core - available
        if missing_required:
            raise ValueError(f"Missing required columns in stations.csv: {missing_required}")

        # Warn about unexpected columns
        unexpected = available - all_expected
        if unexpected:
            import warnings
            warnings.warn(f"Unexpected columns in stations.csv (will be ignored): {unexpected}")

        # Ensure numeric columns have proper types
        numeric_cols = ['sensor_temp', 'sensor_vib', 'people', 'capacity', 'occupancy_rate',
                       'eta', 'delay', 'platform_length', 'door_position', 'sync_score',
                       'risk_score', 'power_consumption', 'humidity', 'door_motor_current']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Fill missing optional columns with sensible defaults
        if 'train' not in df.columns:
            df['train'] = ''
        if 'train_type' not in df.columns:
            df['train_type'] = 'Standard'
        if 'operator' not in df.columns:
            df['operator'] = 'DB'
        if 'destination' not in df.columns:
            df['destination'] = 'Unknown'
        if 'status' not in df.columns:
            df['status'] = 'clear'
        if 'capacity' not in df.columns:
            # Estimate based on train type
            df['capacity'] = 400  # Default average
        if 'occupancy_rate' not in df.columns:
            df['occupancy_rate'] = 0.0
        if 'eta' not in df.columns:
            df['eta'] = 0
        if 'delay' not in df.columns:
            df['delay'] = 0
        if 'platform_length' not in df.columns:
            df['platform_length'] = 420  # Standard German platform
        if 'door_position' not in df.columns:
            df['door_position'] = 'middle'
        if 'sync_score' not in df.columns:
            df['sync_score'] = 100
        if 'maintenance_status' not in df.columns:
            df['maintenance_status'] = 'OPTIMAL'
        if 'risk_score' not in df.columns:
            df['risk_score'] = 0
        if 'signal_status' not in df.columns:
            df['signal_status'] = 'green'
        if 'track_number' not in df.columns:
            df['track_number'] = 1
        if 'last_maintenance' not in df.columns:
            df['last_maintenance'] = datetime.now().strftime('%Y-%m-%d')
        if 'power_consumption' not in df.columns:
            df['power_consumption'] = 15.0
        if 'humidity' not in df.columns:
            df['humidity'] = 55.0
        if 'door_motor_current' not in df.columns:
            df['door_motor_current'] = 1.5
        if 'connection_line' not in df.columns:
            df['connection_line'] = 'U1'

        # Ensure all string columns are strings
        str_cols = ['station', 'platform', 'gate_id', 'train', 'train_type', 'operator',
                   'destination', 'door_state', 'status', 'door_position',
                   'maintenance_status', 'signal_status', 'connection_line']
        for col in str_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).replace('nan', '')

        return df
    except FileNotFoundError:
        raise FileNotFoundError("stations.csv not found. Please ensure the data file exists.")
    except pd.errors.EmptyDataError:
        raise ValueError("stations.csv is empty or contains no data.")
    except Exception as e:
        raise ValueError(f"Error loading stations.csv: {str(e)}")


def transform_data(df):
    """Apply derived columns: sync score, maintenance status, risk level, and advanced metrics."""
    df = df.copy()

    # ── SYNC SCORE (if not already present) ─────────────────────────────────────
    if 'sync_score' not in df.columns or df['sync_score'].isna().any():
        temp = df['sensor_temp'].fillna(25)
        vib = df['sensor_vib'].fillna(0)
        # Advanced sync score with humidity and motor current influence
        humidity_factor = df.get('humidity', pd.Series(55, index=df.index)).fillna(55)
        humidity_penalty = np.where(humidity_factor > 70, (humidity_factor - 70) * 0.2, 0)
        motor_current = df.get('door_motor_current', pd.Series(1.5, index=df.index)).fillna(1.5)
        motor_penalty = np.where(motor_current > 2.5, (motor_current - 2.5) * 10, 0)

        df['sync_score'] = np.clip(
            100 - (temp - 25) * 0.5 - vib * 2 - humidity_penalty - motor_penalty,
            0, 100
        ).astype(int)

    # ── MAINTENANCE STATUS (if not already present) ─────────────────────────────
    if 'maintenance_status' not in df.columns or df['maintenance_status'].isna().any():
        conditions = [
            (df['door_state'] == 'jammed') | (df.get('door_motor_current', 1.5) > 3.5),
            (df['sensor_temp'] > 45) | (df.get('power_consumption', 15) > 50),
            (df['sync_score'] < 70),
            (df['sensor_vib'] > 2.5)
        ]
        choices = ['CRITICAL', 'CRITICAL', 'WARNING', 'WARNING']
        df['maintenance_status'] = np.select(conditions, choices, default='OPTIMAL')

    # ── RISK SCORE (if not already present) ───────────────────────────────────────
    if 'risk_score' not in df.columns or df['risk_score'].isna().any():
        risk = np.zeros(len(df), dtype=int)

        # Primary risk factors
        risk += np.where(df['door_state'] == 'jammed', 60, 0)
        risk += np.where(df['sensor_temp'] > 45, 25, 0)
        risk += np.where((df['sensor_temp'] > 35) & (df['sensor_temp'] <= 45), 10, 0)
        risk += np.where(df['sensor_vib'] > 3, 15, 0)
        risk += np.where((df['sensor_vib'] > 1.5) & (df['sensor_vib'] <= 3), 5, 0)

        # Additional risk factors from new sensors
        if 'power_consumption' in df.columns:
            risk += np.where(df['power_consumption'] > 40, 10, 0)
        if 'door_motor_current' in df.columns:
            risk += np.where(df['door_motor_current'] > 3.0, 15, 0)
        if 'humidity' in df.columns:
            risk += np.where(df['humidity'] > 80, 5, 0)

        # Delay risk
        if 'delay' in df.columns:
            risk += np.where(df['delay'].abs() > 10, 10, 0)

        df['risk_score'] = np.clip(risk, 0, 100)

    # ── ADVANCED METRICS ─────────────────────────────────────────────────────────
    # Congestion Score (0-100)
    if 'capacity' in df.columns and 'occupancy_rate' in df.columns:
        df['congestion_score'] = np.clip(
            df.get('occupancy_rate', 0) * 100 / df['capacity'].clip(lower=1),
            0, 100
        ).astype(int)
    else:
        # Estimate from people count and platform capacity
        platform_capacity_est = 200  # Estimated average platform capacity
        df['congestion_score'] = np.clip(df['people'] / platform_capacity_est * 100, 0, 100).astype(int)

    # Energy Efficiency Rating (A-G scale)
    if 'power_consumption' in df.columns:
        conditions = [
            df['power_consumption'] <= 12,
            (df['power_consumption'] > 12) & (df['power_consumption'] <= 18),
            (df['power_consumption'] > 18) & (df['power_consumption'] <= 25),
            (df['power_consumption'] > 25) & (df['power_consumption'] <= 35),
            (df['power_consumption'] > 35)
        ]
        choices = ['A', 'B', 'C', 'D', 'E']
        df['energy_rating'] = np.select(conditions, choices, default='F')
    else:
        df['energy_rating'] = 'B'

    # Service Reliability Score
    if 'delay' in df.columns:
        delay_penalty = np.where(df['delay'].abs() > 5, 20,
                                np.where(df['delay'].abs() > 2, 10, 0))
        df['service_reliability'] = np.clip(100 - delay_penalty, 0, 100).astype(int)
    else:
        df['service_reliability'] = 95

    # Door Health Indicator
    door_penalty = np.where(df['door_state'] == 'jammed', 50,
                           np.where(df.get('door_motor_current', 1.5) > 2.5, 25, 0))
    df['door_health'] = np.clip(100 - door_penalty, 0, 100).astype(int)

    # Peak Hour Flag
    current_hour = datetime.now().hour
    peak_hours = [6, 7, 8, 9, 16, 17, 18, 19]
    df['is_peak_hour'] = current_hour in peak_hours

    # Weekend Flag
    df['is_weekend'] = datetime.now().weekday() >= 5

    return df


# ─────────────────────────────────────────────
# STATION METRICS
# ─────────────────────────────────────────────

@st.cache_data(ttl=60, show_spinner=False)
def get_metrics(df, station_name):
    """Get comprehensive station-level metrics. Returns tuple for backward compatibility and dict for extended use."""
    station_df = df[df["station"] == station_name]
    if station_df.empty:
        # Return tuple (6 values) and None for extended data
        return 0, 0, 0, 0, 0, 0, None

    gates_total = len(station_df)
    gates_active = len(station_df[station_df["door_state"] != "offline"])
    people_total = int(station_df["people"].sum())
    critical_count = len(station_df[station_df["maintenance_status"] == "CRITICAL"])
    warning_count = len(station_df[station_df["maintenance_status"] == "WARNING"])
    monitor_count = len(station_df[station_df["maintenance_status"] == "MONITOR"])
    optimal_count = len(station_df[station_df["maintenance_status"] == "OPTIMAL"])

    avg_sync = int(station_df["sync_score"].mean()) if not station_df.empty else 0
    avg_risk = int(station_df["risk_score"].mean()) if not station_df.empty else 0
    avg_congestion = int(station_df.get('congestion_score', pd.Series(0)).mean()) if not station_df.empty else 0

    # High-risk gates
    high_risk_gates = station_df[station_df["risk_score"] >= 70]
    high_risk_count = len(high_risk_gates)

    # Energy stats
    avg_power = float(station_df.get('power_consumption', pd.Series(15)).mean())

    metrics = {
        'gates_total': gates_total,
        'gates_active': gates_active,
        'people_total': people_total,
        'critical_count': critical_count,
        'warning_count': warning_count,
        'monitor_count': monitor_count,
        'optimal_count': optimal_count,
        'avg_sync': avg_sync,
        'avg_risk': avg_risk,
        'avg_congestion': avg_congestion,
        'high_risk_count': high_risk_count,
        'avg_power': avg_power,
        'critical_gates': high_risk_gates[['gate_id', 'door_state', 'sensor_temp', 'sensor_vib', 'risk_score']].to_dict('records') if not high_risk_gates.empty else []
    }

    # Return tuple for backward compatibility: (gates_total, gates_active, people_total, alerts, avg_sync, warnings)
    # where alerts = critical_count, warnings = warning_count
    return gates_total, gates_active, people_total, critical_count, avg_sync, warning_count, metrics


# ─────────────────────────────────────────────
# ANALYTICS: PER-STATION CHARTS
# ─────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
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

@st.cache_data(ttl=60, show_spinner=False)
def get_network_summary(df):
    """Comprehensive network-wide analytics."""
    total_gates = len(df)
    total_people = int(df["people"].sum())
    total_critical = len(df[df["maintenance_status"] == "CRITICAL"])
    total_warning = len(df[df["maintenance_status"] == "WARNING"])
    total_monitor = len(df[df["maintenance_status"] == "MONITOR"])
    total_optimal = len(df[df["maintenance_status"] == "OPTIMAL"])

    # Overall performance metrics
    network_sync = int(df["sync_score"].mean()) if not df.empty else 0
    network_risk = int(df["risk_score"].mean()) if not df.empty else 0

    # Status distribution
    status_dist = df.groupby("maintenance_status").size().reset_index(name="Count")
    door_dist = df.groupby("door_state").size().reset_index(name="Count")

    # Operator performance
    if 'operator' in df.columns:
        operator_stats = df.groupby("operator").agg(
            Gates=("gate_id", "count"),
            Avg_Sync=("sync_score", "mean"),
            Avg_Risk=("risk_score", "mean"),
            Criticals=("maintenance_status", lambda x: (x == "CRITICAL").sum())
        ).round(2).reset_index()
        operator_stats.columns = ["Operator", "Gates", "Avg Sync %", "Avg Risk", "Criticals"]
    else:
        operator_stats = pd.DataFrame()

    # Train type distribution
    if 'train_type' in df.columns:
        train_type_dist = df.groupby("train_type").agg(
            Count=("gate_id", "count"),
            Avg_Sync=("sync_score", "mean")
        ).round(1).reset_index()
    else:
        train_type_dist = pd.DataFrame()

    # Station detailed summary
    station_summary = df.groupby("station").agg(
        Gates=("gate_id", "count"),
        Active_Gates=("door_state", lambda x: (x != "offline").sum()),
        Passengers=("people", "sum"),
        Avg_Sync=("sync_score", "mean"),
        Avg_Risk=("risk_score", "mean"),
        Criticals=("maintenance_status", lambda x: (x == "CRITICAL").sum()),
        Warnings=("maintenance_status", lambda x: (x == "WARNING").sum()),
        Avg_People=("people", "mean"),
        Avg_Congestion=("congestion_score", "mean") if "congestion_score" in df.columns else None
    ).reset_index()

    # Round numeric columns
    numeric_cols = ["Avg_Sync", "Avg_Risk", "Avg_People"]
    for col in numeric_cols:
        if col in station_summary.columns:
            station_summary[col] = station_summary[col].round(1)

    if "Avg_Congestion" in station_summary.columns:
        station_summary["Avg_Congestion"] = station_summary["Avg_Congestion"].round(1)

    station_summary.columns = ["Station", "Gates", "Active", "Passengers",
                               "Avg Sync %", "Avg Risk", "Criticals", "Warnings", "Avg Pax", "Avg Cong %"]

    # Network health score (0-100)
    health_components = [
        network_sync * 0.3,
        (100 - network_risk) * 0.3,
        (total_optimal / max(total_gates, 1)) * 100 * 0.2,
        (1 - total_critical / max(total_gates, 1)) * 100 * 0.2
    ]
    network_health = sum(health_components)

    # Power consumption stats
    if 'power_consumption' in df.columns:
        total_power = df['power_consumption'].sum()
        avg_power = df['power_consumption'].mean()
    else:
        total_power = 0
        avg_power = 0

    # Peak hour analysis
    if 'is_peak_hour' in df.columns:
        peak_gates = len(df[df['is_peak_hour']])
        peak_congestion = df[df['is_peak_hour']]['congestion_score'].mean() if 'congestion_score' in df.columns else 0
    else:
        peak_gates = 0
        peak_congestion = 0

    return {
        "total_gates": total_gates,
        "total_people": total_people,
        "critical_count": total_critical,
        "warning_count": total_warning,
        "monitor_count": total_monitor,
        "optimal_count": total_optimal,
        "network_sync": network_sync,
        "network_risk": network_risk,
        "network_health": round(network_health, 1),
        "status_dist": status_dist,
        "door_dist": door_dist,
        "station_summary": station_summary,
        "operator_stats": operator_stats,
        "train_type_dist": train_type_dist,
        "total_power_kw": round(total_power, 1),
        "avg_power_w": round(avg_power, 1),
        "peak_gates": peak_gates,
        "peak_congestion": round(peak_congestion, 1) if peak_congestion else 0
    }


# ─────────────────────────────────────────────
# ANALYTICS: PREDICTIVE MAINTENANCE TIMELINE
# ─────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
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

@st.cache_data(ttl=3600, show_spinner=False)
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

@st.cache_data(ttl=60, show_spinner=False)
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
# FINANCIAL MODEL (from app.py simulation)
# ─────────────────────────────────────────────

def _run_saas_simulation(starting_customers, monthly_growth_rate, churn_rate,
                          price_per_customer, fixed_costs, variable_cost_per_customer,
                          cac_simplified=150, months=24):
    """
    Self-contained SaaS financial simulation.
    Returns a DataFrame with all metrics (mirrors app.py logic).
    """
    basic_pct, pro_pct, enterprise_pct = 0.50, 0.35, 0.15
    basic_price, pro_price, enterprise_price = 49, 99, 299

    salary = {"Engineering": 8500, "Sales": 6000,
              "Marketing": 5500, "CS": 4500, "G&A": 5000}
    hc = {"Engineering": 5, "Sales": 3, "Marketing": 2, "CS": 2, "G&A": 2}

    current_customers = starting_customers
    cumulative_cash   = -(current_customers * cac_simplified)
    prev_mrr          = None
    data              = []

    for month in range(1, months + 1):
        new_customers      = int(current_customers * monthly_growth_rate)
        churned_customers  = int(current_customers * churn_rate)
        expansion_customers = int(current_customers * 0.02)
        expansion_mrr      = expansion_customers * (price_per_customer * 0.20)

        total_customers = current_customers + new_customers - churned_customers

        basic_cust      = int(total_customers * basic_pct)
        pro_cust        = int(total_customers * pro_pct)
        enterprise_cust = total_customers - basic_cust - pro_cust

        mrr         = (basic_cust * basic_price + pro_cust * pro_price
                       + enterprise_cust * enterprise_price)
        new_mrr     = new_customers * price_per_customer
        churn_mrr   = churned_customers * price_per_customer
        net_new_mrr = new_mrr - churn_mrr + expansion_mrr
        arr         = mrr * 12
        mom_growth  = ((mrr - prev_mrr) / prev_mrr * 100) if prev_mrr else 0

        churn_pct          = (churned_customers / current_customers * 100
                               if current_customers > 0 else 0)
        contribution_margin = price_per_customer - variable_cost_per_customer
        ltv                 = (contribution_margin / churn_rate
                                if churn_rate > 0 else 0)
        ltv_cac_ratio       = ltv / cac_simplified if cac_simplified > 0 else 0

        cac_payback_basic      = cac_simplified / max(basic_price      - variable_cost_per_customer, 1)
        cac_payback_pro        = cac_simplified / max(pro_price        - variable_cost_per_customer, 1)
        cac_payback_enterprise = cac_simplified / max(enterprise_price - variable_cost_per_customer, 1)

        total_cac_spent = new_customers * cac_simplified

        for dept, threshold in [("Engineering", 30), ("Sales", 20),
                                 ("Marketing", 25), ("CS", 35), ("G&A", 50)]:
            if total_customers // threshold > (current_customers // threshold):
                hc[dept] += 1

        salary_eng       = hc["Engineering"] * salary["Engineering"]
        salary_sales     = hc["Sales"]       * salary["Sales"]
        salary_marketing = hc["Marketing"]   * salary["Marketing"]
        salary_cs        = hc["CS"]          * salary["CS"]
        salary_ga        = hc["G&A"]         * salary["G&A"]
        total_salaries   = salary_eng + salary_sales + salary_marketing + salary_cs + salary_ga

        cogs     = total_customers * variable_cost_per_customer
        rd_cost  = salary_eng
        sm_cost  = salary_sales + salary_marketing + total_cac_spent
        ga_cost  = salary_ga + fixed_costs
        cs_cost  = salary_cs
        total_costs = cogs + rd_cost + sm_cost + ga_cost + cs_cost

        gross_profit     = mrr - cogs
        gross_margin_pct = (gross_profit / mrr * 100) if mrr > 0 else 0
        ebit             = mrr - total_costs
        sm_efficiency    = net_new_mrr / sm_cost if sm_cost > 0 else 0
        profit_loss      = mrr - total_costs
        cumulative_cash += profit_loss

        new_enterprise      = max(1, int(new_customers * enterprise_pct))
        lost_enterprise     = max(0, int(churned_customers * enterprise_pct))
        upgrade_enterprise  = max(0, int(expansion_customers * 0.3))

        data.append({
            "Month": month,
            "Start_Customers": current_customers,
            "New_Customers": new_customers,
            "Churned_Customers": churned_customers,
            "Total_Customers": total_customers,
            "Basic_Customers": basic_cust,
            "Pro_Customers": pro_cust,
            "Enterprise_Customers": enterprise_cust,
            "New_MRR": round(new_mrr, 2),
            "Churn_MRR": round(-churn_mrr, 2),
            "Expansion_MRR": round(expansion_mrr, 2),
            "Net_New_MRR": round(net_new_mrr, 2),
            "MRR": round(mrr, 2),
            "ARR": round(arr, 2),
            "MoM_Growth_%": round(mom_growth, 2),
            "Churn_Rate_%": round(churn_pct, 2),
            "LTV": round(ltv, 2),
            "CAC": cac_simplified,
            "LTV_CAC_Ratio": round(ltv_cac_ratio, 2),
            "CAC_Payback_Basic": round(cac_payback_basic, 2),
            "CAC_Payback_Pro": round(cac_payback_pro, 2),
            "CAC_Payback_Enterprise": round(cac_payback_enterprise, 2),
            "Contribution_Margin_$": round(contribution_margin, 2),
            "Total_Revenue": round(mrr, 2),
            "Gross_Profit": round(gross_profit, 2),
            "Gross_Margin_%": round(gross_margin_pct, 2),
            "COGS": round(cogs, 2),
            "RD_Cost": round(rd_cost, 2),
            "SM_Cost": round(sm_cost, 2),
            "GA_Cost": round(ga_cost, 2),
            "CS_Cost": round(cs_cost, 2),
            "Total_Costs": round(total_costs, 2),
            "EBIT": round(ebit, 2),
            "Profit_Loss": round(profit_loss, 2),
            "Cumulative_Cash": round(cumulative_cash, 2),
            "SM_Efficiency": round(sm_efficiency, 4),
            "HC_Engineering": hc["Engineering"],
            "HC_Sales": hc["Sales"],
            "HC_Marketing": hc["Marketing"],
            "HC_CS": hc["CS"],
            "HC_GA": hc["G&A"],
            "Total_Headcount": sum(hc.values()),
            "Salary_Engineering": salary_eng,
            "Salary_Sales": salary_sales,
            "Salary_Marketing": salary_marketing,
            "Salary_CS": salary_cs,
            "Salary_GA": salary_ga,
            "Total_Salaries": total_salaries,
            "New_Enterprise_Wins": new_enterprise,
            "Enterprise_Upgrades": upgrade_enterprise,
            "Lost_Enterprise": lost_enterprise,
        })

        prev_mrr          = mrr
        current_customers = total_customers

    return pd.DataFrame(data)


@st.cache_data(ttl=3600, show_spinner=False)
def get_financial_model_data(months=24, starting_customers=50, monthly_growth_rate=0.20,
                             churn_rate=0.05, price_per_customer=100, fixed_costs=5000,
                             variable_cost_per_customer=10, cac_simplified=150,
                             churn_rate_high=None):
    """
    Returns (df_base, df_high_churn) DataFrames for the Financial Model tab.
    
    Args:
        months: Simulation period (default 24)
        starting_customers: Initial customer count (default 50)
        monthly_growth_rate: Monthly growth rate as decimal (default 0.20 = 20%)
        churn_rate: Monthly churn rate as decimal (default 0.05 = 5%)
        price_per_customer: Average MRR per customer (default $100)
        fixed_costs: Monthly fixed costs (default $5,000)
        variable_cost_per_customer: Variable cost per customer (default $10)
        cac_simplified: Customer Acquisition Cost (default $150)
        churn_rate_high: High churn scenario rate (default 2x churn_rate)
    """
    if churn_rate_high is None:
        churn_rate_high = churn_rate * 2  # Default: high churn is 2x base churn
    
    df_base = _run_saas_simulation(
        starting_customers=starting_customers,
        monthly_growth_rate=monthly_growth_rate,
        churn_rate=churn_rate,
        price_per_customer=price_per_customer,
        fixed_costs=fixed_costs,
        variable_cost_per_customer=variable_cost_per_customer,
        cac_simplified=cac_simplified,
        months=months
    )
    df_churn = _run_saas_simulation(
        starting_customers=starting_customers,
        monthly_growth_rate=monthly_growth_rate,
        churn_rate=churn_rate_high,
        price_per_customer=price_per_customer,
        fixed_costs=fixed_costs,
        variable_cost_per_customer=variable_cost_per_customer,
        cac_simplified=cac_simplified,
        months=months
    )
    return df_base, df_churn

@st.cache_data(ttl=3600, show_spinner=False)
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

@st.cache_data(ttl=3600, show_spinner=False)
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


# ─────────────────────────────────────────────
# ADVANCED ANALYTICS: STATION DEEP DIVE
# ─────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def get_station_detailed_profile(df, station_name):
    """Generate comprehensive analytics profile for a specific station."""
    station_df = df[df["station"] == station_name].copy()
    if station_df.empty:
        return {}

    profile = {
        "station_name": station_name,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "infrastructure": {
            "total_gates": len(station_df),
            "platforms": station_df['platform'].nunique(),
            "avg_platform_length": station_df.get('platform_length', pd.Series(420)).mean(),
            "track_count": station_df.get('track_number', pd.Series(1)).nunique(),
        },
        "performance": {
            "avg_sync_score": round(station_df['sync_score'].mean(), 1),
            "avg_risk_score": round(station_df['risk_score'].mean(), 1),
            "network_health_score": round(
                station_df['sync_score'].mean() * 0.4 +
                (100 - station_df['risk_score'].mean()) * 0.4 +
                (len(station_df[station_df['maintenance_status'] == 'OPTIMAL']) / len(station_df) * 100) * 0.2,
                1
            ),
            "total_passengers": int(station_df['people'].sum()),
            "avg_occupancy_rate": round(station_df.get('occupancy_rate', pd.Series(0)).mean() * 100, 1),
        },
        "maintenance": {
            "critical_gates": len(station_df[station_df['maintenance_status'] == 'CRITICAL']),
            "warning_gates": len(station_df[station_df['maintenance_status'] == 'WARNING']),
            "optimal_gates": len(station_df[station_df['maintenance_status'] == 'OPTIMAL']),
            "jammed_gates": len(station_df[station_df['door_state'] == 'jammed']),
            "avg_days_since_maintenance": _calc_avg_maintenance_age(station_df.get('last_maintenance', pd.Series(datetime.now().strftime('%Y-%m-%d')))),
        },
        "energy": {
            "total_power_kw": round(station_df.get('power_consumption', pd.Series(15)).sum(), 1),
            "avg_power_per_gate": round(station_df.get('power_consumption', pd.Series(15)).mean(), 1),
            "energy_ratings": station_df.get('energy_rating', pd.Series('B')).value_counts().to_dict(),
        },
        "train_operations": {
            "unique_train_types": station_df.get('train_type', pd.Series('Standard')).nunique(),
            "unique_operators": station_df.get('operator', pd.Series('DB')).nunique(),
            "avg_delay": round(station_df.get('delay', pd.Series(0)).abs().mean(), 1),
            "on_time_percentage": round(
                (len(station_df[station_df.get('delay', 0) == 0]) / len(station_df) * 100),
                1
            ) if len(station_df) > 0 else 0,
        },
        "connectivity": {
            "connection_lines": station_df.get('connection_line', pd.Series('U1')).unique().tolist(),
            "signal_system": "GSM-R" if "signal_status" in station_df.columns else "Legacy",
        },
        "alerts": _generate_station_alerts(station_df)
    }

    return profile


def _calc_avg_maintenance_age(dates_series):
    """Calculate average days since last maintenance."""
    try:
        dates = pd.to_datetime(dates_series, errors='coerce')
        days_since = (datetime.now() - dates).dt.days
        return round(days_since.mean(), 1)
    except:
        return 0


def _generate_station_alerts(station_df):
    """Generate actionable alerts for station management."""
    alerts = []

    for _, row in station_df.iterrows():
        if row['maintenance_status'] == 'CRITICAL':
            alerts.append({
                "severity": "CRITICAL",
                "gate": row['gate_id'],
                "issue": f"Gate {row['gate_id']} requires immediate attention",
                "details": f"Door state: {row['door_state']}, Temp: {row['sensor_temp']}°C, Risk: {row['risk_score']}/100",
                "recommended_action": "Dispatch maintenance team immediately"
            })
        elif row['maintenance_status'] == 'WARNING' and row['sync_score'] < 70:
            alerts.append({
                "severity": "WARNING",
                "gate": row['gate_id'],
                "issue": f"Degrading performance on gate {row['gate_id']}",
                "details": f"Sync score: {row['sync_score']}%, Risk: {row['risk_score']}/100",
                "recommended_action": "Schedule preventive maintenance within 24 hours"
            })

    # Station-level alerts
    critical_count = len(station_df[station_df['maintenance_status'] == 'CRITICAL'])
    if critical_count >= 3:
        alerts.append({
            "severity": "STATION-WARNING",
            "gate": "ALL",
            "issue": f"Multiple critical alerts ({critical_count}) at station",
            "details": "System-wide maintenance review recommended",
            "recommended_action": "Escalate to operations manager"
        })

    return alerts


# ─────────────────────────────────────────────
# ADVANCED ANALYTICS: HISTORICAL TRENDS
# ─────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def get_historical_trends(df, days_back=30):
    """Generate simulated historical trend data for key metrics."""
    rng = np.random.RandomState(seed=42)

    dates = pd.date_range(end=datetime.now(), periods=days_back, freq='D')

    trends = {
        'dates': [d.strftime('%Y-%m-%d') for d in dates],
        'network_sync': [],
        'network_risk': [],
        'critical_alerts': [],
        'total_passengers': [],
        'avg_temp': [],
        'avg_vib': [],
        'power_consumption': []
    }

    # Generate realistic trends with weekly patterns
    base_sync = df['sync_score'].mean()
    base_risk = df['risk_score'].mean()

    for i, date in enumerate(dates):
        # Weekly pattern - weekends slightly different
        is_weekend = date.weekday() >= 5
        weekend_factor = 0.98 if is_weekend else 1.0

        # Slight drift over time for realism
        trend_factor = 1 + (i / days_back) * 0.05

        # Add some noise
        noise_sync = rng.normal(0, 1.5)
        noise_risk = rng.normal(0, 0.8)

        sync = np.clip(base_sync * trend_factor * weekend_factor + noise_sync, 70, 100)
        risk = np.clip(base_risk / trend_factor * (2 - weekend_factor) + noise_risk, 0, 40)

        trends['network_sync'].append(round(sync, 1))
        trends['network_risk'].append(round(risk, 1))
        trends['critical_alerts'].append(max(0, int(rng.poisson(risk / 10))))
        trends['total_passengers'].append(int(rng.randint(50000, 80000) * (0.9 if is_weekend else 1.0)))
        trends['avg_temp'].append(round(rng.normal(25, 2), 1))
        trends['avg_vib'].append(round(rng.normal(0.5, 0.2), 2))
        trends['power_consumption'].append(round(rng.normal(1200, 150), 1))

    return pd.DataFrame(trends)


# ─────────────────────────────────────────────
# ADVANCED ANALYTICS: PREDICTIVE INSIGHTS
# ─────────────────────────────────────────────

@st.cache_data(ttl=1800, show_spinner=False)
def get_predictive_insights(df):
    """Generate predictive maintenance insights and recommendations."""
    insights = {
        "high_risk_gates": [],
        "maintenance_recommendations": [],
        "capacity_warnings": [],
        "energy_optimizations": []
    }

    # Analyze each gate
    for _, row in df.iterrows():
        gate_id = row['gate_id']
        risk = row['risk_score']
        sync = row['sync_score']
        temp = row['sensor_temp']
        vib = row['sensor_vib']
        power = row.get('power_consumption', 15)
        door_state = row['door_state']

        # High risk prediction
        if risk >= 50 or temp > 40 or vib > 2.5:
            risk_level = "HIGH" if risk >= 70 else "MEDIUM"
            insights["high_risk_gates"].append({
                "gate": gate_id,
                "station": row['station'],
                "risk_score": int(risk),
                "risk_level": risk_level,
                "primary_factors": _identify_risk_factors(row),
                "predicted_failure_date": _predict_failure_date(risk)
            })

        # Maintenance scheduling
        if sync < 85 or door_state in ['closing', 'jammed']:
            urgency = "URGENT" if row['maintenance_status'] == 'CRITICAL' else "SCHEDULED"
            insights["maintenance_recommendations"].append({
                "gate": gate_id,
                "station": row['station'],
                "urgency": urgency,
                "reason": row['maintenance_status'],
                "suggested_window": _suggest_maintenance_window(row),
                "estimated_downtime": _estimate_downtime(row)
            })

        # Energy optimization
        if power > 30:
            insights["energy_optimizations"].append({
                "gate": gate_id,
                "station": row['station'],
                "current_power": power,
                "suggested_power": min(power * 0.7, 25),
                "savings_potential": f"{(power - min(power * 0.7, 25)) * 24 * 30:.0f} kWh/month"
            })

    # Sort by risk
    insights["high_risk_gates"] = sorted(
        insights["high_risk_gates"],
        key=lambda x: x['risk_score'],
        reverse=True
    )[:10]  # Top 10

    insights["maintenance_recommendations"] = sorted(
        insights["maintenance_recommendations"],
        key=lambda x: 0 if x['urgency'] == 'URGENT' else 1
    )[:10]  # Top 10

    return insights


def _identify_risk_factors(row):
    """Identify primary risk factors for a gate."""
    factors = []
    if row['sensor_temp'] > 40:
        factors.append(f"High temperature ({row['sensor_temp']:.1f}°C)")
    if row['sensor_vib'] > 2:
        factors.append(f"Excessive vibration ({row['sensor_vib']:.1f} mm/s)")
    if row['door_state'] == 'jammed':
        factors.append("Door jammed")
    if row['door_motor_current'] > 2.5:
        factors.append(f"High motor current ({row['door_motor_current']:.1f}A)")
    return factors if factors else ["Degraded performance"]


def _predict_failure_date(risk_score):
    """Predict approximate failure date based on current metrics."""
    from datetime import timedelta
    if risk_score < 30:
        return None
    # Simple heuristic: higher risk = sooner failure
    days_to_failure = max(1, int((100 - risk_score) / 10))
    failure_date = datetime.now() + timedelta(days=days_to_failure)
    return failure_date.strftime('%Y-%m-%d') if risk_score >= 50 else None


def _suggest_maintenance_window(row):
    """Suggest optimal maintenance time window."""
    current_hour = datetime.now().hour
    if 'is_peak_hour' in row and row.get('is_peak_hour', False):
        return "Tonight (off-peak)"
    elif current_hour < 6:
        return "Morning (06:00-10:00)"
    elif current_hour < 14:
        return "Afternoon (14:00-18:00)"
    else:
        return "Tonight (22:00-06:00)"


def _estimate_downtime(row):
    """Estimate maintenance downtime in minutes."""
    if row['maintenance_status'] == 'CRITICAL':
        return "60-90 min"
    elif row['maintenance_status'] == 'WARNING':
        return "30-45 min"
    else:
        return "15-20 min"


# ─────────────────────────────────────────────
# ADVANCED ANALYTICS: EFFICIENCY METRICS
# ─────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def get_efficiency_metrics(df):
    """Calculate operational and energy efficiency metrics."""
    if df.empty:
        return {}

    total_gates = len(df)
    total_power = df.get('power_consumption', pd.Series(15)).sum()

    # Energy efficiency distribution
    if 'energy_rating' in df.columns:
        energy_dist = df['energy_rating'].value_counts().to_dict()
    else:
        energy_dist = {}

    # Door operation efficiency
    door_cycle_efficiency = round(
        len(df[df['door_state'] == 'closed']) / max(total_gates, 1) * 100, 1
    )

    # Sync score distribution
    sync_excellent = len(df[df['sync_score'] >= 95])
    sync_good = len(df[(df['sync_score'] >= 85) & (df['sync_score'] < 95)])
    sync_fair = len(df[(df['sync_score'] >= 70) & (df['sync_score'] < 85)])
    sync_poor = len(df[df['sync_score'] < 70])

    # People throughput efficiency
    total_capacity = df.get('capacity', pd.Series(400)).sum()
    actual_passengers = df['people'].sum()
    throughput_efficiency = round(actual_passengers / max(total_capacity, 1) * 100, 1)

    # Maintenance efficiency
    gates_well_maintained = len(df[df['maintenance_status'] == 'OPTIMAL'])
    maintenance_efficiency = round(gates_well_maintained / max(total_gates, 1) * 100, 1)

    return {
        "total_power_kw": round(total_power, 1),
        "power_per_gate_avg": round(total_power / max(total_gates, 1), 1),
        "door_cycle_efficiency_pct": door_cycle_efficiency,
        "throughput_efficiency_pct": throughput_efficiency,
        "maintenance_efficiency_pct": maintenance_efficiency,
        "sync_score_distribution": {
            "excellent_95_plus": sync_excellent,
            "good_85_94": sync_good,
            "fair_70_84": sync_fair,
            "poor_under_70": sync_poor
        },
        "energy_rating_dist": energy_dist,
        "gates_needing_attention": len(df[df['maintenance_status'].isin(['CRITICAL', 'WARNING'])]),
        "overall_efficiency_score": round(
            (door_cycle_efficiency * 0.2 +
             throughput_efficiency * 0.2 +
             maintenance_efficiency * 0.3 +
             (100 - total_power / total_gates) * 0.3), 1
        ) if total_gates > 0 else 0
    }


# ─────────────────────────────────────────────
# REAL-TIME SIMULATION: LIVE STATUS UPDATES
# ─────────────────────────────────────────────

@st.cache_data(ttl=30, show_spinner=False)
def simulate_realtime_updates(df):
    """Simulate real-time variations in sensor readings and status changes."""
    df_updated = df.copy()

    # Random seed based on current time for smooth variations
    rng = np.random.RandomState(seed=int(datetime.now().timestamp()))

    # Small temperature fluctuations (±0.5°C)
    temp_noise = rng.uniform(-0.5, 0.5, len(df))
    df_updated['sensor_temp'] = (df_updated['sensor_temp'] + temp_noise).round(1)

    # Small vibration fluctuations (±0.05 mm/s)
    vib_noise = rng.uniform(-0.05, 0.05, len(df))
    df_updated['sensor_vib'] = (df_updated['sensor_vib'] + vib_noise).clip(0).round(2)

    # Occasional status changes for some gates (simulate real dynamics)
    for idx in range(len(df_updated)):
        if rng.random() < 0.02:  # 2% chance of status change
            current_state = df_updated.at[idx, 'door_state']
            possible_states = ['open', 'closed', 'closing', 'jammed'] if current_state != 'jammed' else ['closed', 'open']
            new_state = rng.choice(possible_states)
            df_updated.at[idx, 'door_state'] = new_state

            # Adjust people count based on state
            if new_state == 'open':
                # Add some passengers entering/exiting
                pax_change = rng.randint(-5, 10)
                df_updated.at[idx, 'people'] = max(0, df_updated.at[idx, 'people'] + pax_change)

    # Recalculate derived metrics after updates
    df_updated = transform_data(df_updated)

    return df_updated


# ─────────────────────────────────────────────
# TRAIN SCHEDULE SIMULATION
# ─────────────────────────────────────────────

@st.cache_data(ttl=60, show_spinner=False)
def get_train_schedule(station_name, df):
    """Generate a realistic train schedule for a station."""
    station_df = df[df["station"] == station_name].copy()
    if station_df.empty:
        return pd.DataFrame()

    rng = np.random.RandomState(seed=sum(ord(c) for c in station_name))

    # Get unique platforms
    platforms = sorted(station_df['platform'].unique())

    schedule_data = []

    # Generate schedule for next 2 hours
    now = datetime.now()
    current_minute = now.hour * 60 + now.minute

    for platform in platforms:
        platform_gates = station_df[station_df['platform'] == platform]

        # Generate trains every 10-20 minutes
        next_train_minutes = []
        minute = current_minute + 10  # Start 10 minutes from now
        while minute < current_minute + 120:  # Next 2 hours
            next_train_minutes.append(minute)
            minute += rng.randint(10, 20)

        for train_minute in next_train_minutes:
            # Select a random gate with a train
            gates_with_trains = platform_gates[platform_gates['train'] != '']
            if len(gates_with_trains) > 0:
                gate_row = gates_with_trains.sample(1, random_state=rng.randint(0, 1000)).iloc[0]

                # Determine status based on timing
                minutes_until = train_minute - current_minute
                if minutes_until <= 0:
                    status = 'arrived' if rng.random() < 0.5 else 'departed'
                elif minutes_until <= 5:
                    status = 'approaching'
                else:
                    status = 'scheduled'

                schedule_data.append({
                    'platform': platform,
                    'gate_id': gate_row['gate_id'],
                    'train': gate_row['train'],
                    'train_type': gate_row.get('train_type', 'Standard'),
                    'operator': gate_row.get('operator', 'DB'),
                    'destination': gate_row.get('destination', 'Unknown'),
                    'scheduled_time': f"{train_minute // 60:02d}:{train_minute % 60:02d}",
                    'minutes_until': max(0, minutes_until),
                    'status': status,
                    'platform_length': gate_row.get('platform_length', 420),
                    'track_number': gate_row.get('track_number', 1),
                })

    schedule_df = pd.DataFrame(schedule_data)
    if not schedule_df.empty:
        schedule_df = schedule_df.sort_values('minutes_until')

    return schedule_df


# ─────────────────────────────────────────────
# PLATFORM OCCUPANCY PREDICTION
# ─────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def predict_platform_occupancy(station_name, df, time_window_minutes=30):
    """Predict platform occupancy for the next time window."""
    station_df = df[df["station"] == station_name].copy()
    if station_df.empty:
        return {}

    rng = np.random.RandomState(seed=int(datetime.now().timestamp()))

    # Get current occupancy per platform
    platforms = sorted(station_df['platform'].unique())
    predictions = {}

    for platform in platforms:
        platform_data = station_df[station_df['platform'] == platform]
        current_people = int(platform_data['people'].sum())

        # Estimate arrival/departure rates based on time of day
        current_hour = datetime.now().hour
        if 6 <= current_hour <= 9 or 16 <= current_hour <= 19:
            # Peak hours
            arrival_rate = rng.uniform(15, 25)
            departure_rate = rng.uniform(10, 20)
        elif 10 <= current_hour <= 15:
            # Midday
            arrival_rate = rng.uniform(8, 15)
            departure_rate = rng.uniform(8, 12)
        else:
            # Off-peak
            arrival_rate = rng.uniform(3, 8)
            departure_rate = rng.uniform(4, 9)

        # Simulate arrivals and departures
        predicted_people = current_people
        for minute in range(time_window_minutes):
            arrivals = rng.poisson(arrival_rate / 60)
            departures = rng.poisson(departure_rate / 60)
            predicted_people = max(0, predicted_people + arrivals - departures)

            # Apply capacity limit
            platform_capacity = 200  # Estimated
            predicted_people = min(predicted_people, platform_capacity)

        predictions[platform] = {
            'current': current_people,
            'predicted': int(predicted_people),
            'change': int(predicted_people - current_people),
            'capacity': platform_capacity,
            'utilization': round(predicted_people / platform_capacity * 100, 1)
        }

    return predictions


# ─────────────────────────────────────────────
# GATE PERFORMANCE HISTORY (SIMULATED)
# ─────────────────────────────────────────────

@st.cache_data(ttl=600, show_spinner=False)
def get_gate_performance_history(gate_id, df, hours_back=24):
    """Get performance history for a specific gate (simulated)."""
    rng = np.random.RandomState(seed=hash(gate_id) % 10000)

    # Generate hourly data points
    hours = []
    now = datetime.now()
    for i in range(hours_back, 0, -1):
        dt = now - timedelta(hours=i)
        hours.append(dt.strftime('%m-%d %H:00'))

    # Generate realistic performance data
    base_temp = 25
    base_vib = 0.3
    base_cycles = 50

    temps = []
    vibs = []
    cycles = []
    syncs = []

    for i in range(hours_back):
        # Temperature with daily cycle
        hour_of_day = (now - timedelta(hours=i)).hour
        daily_temp = 22 + 8 * np.sin(2 * np.pi * hour_of_day / 24)
        temp_noise = rng.normal(0, 0.8)
        temps.append(round(daily_temp + temp_noise, 1))

        # Vibration correlated with door cycles
        cycle_count = base_cycles + rng.randint(-20, 30)
        cycles.append(cycle_count)
        vib_base = 0.2 + cycle_count / 500
        vib_noise = rng.normal(0, 0.08)
        vibs.append(round(max(0, vib_base + vib_noise), 2))

        # Sync score inversely correlated with temp/vib anomalies
        temp_anomaly = max(0, temps[-1] - 28)
        vib_anomaly = max(0, (vibs[-1] - 0.5) * 5)
        sync = np.clip(100 - temp_anomaly * 1.5 - vib_anomaly * 3 + rng.normal(0, 2), 70, 100)
        syncs.append(round(sync, 1))

    return pd.DataFrame({
        'Hour': hours,
        'Temperature (°C)': temps,
        'Vibration (mm/s)': vibs,
        'Door Cycles': cycles,
        'Sync Score (%)': syncs
    })

