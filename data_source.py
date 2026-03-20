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