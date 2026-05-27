"""
Sample data module for SicherGleis Railway Dashboard.
Contains realistic German railway stations, operators, and business data.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ═══════════════════════════════════════════════════
# GERMAN RAILWAY STATIONS
# ═══════════════════════════════════════════════════

STATIONS = [
    # Established (5 stations)
    {"station": "Berlin Hbf", "lat": 52.525, "lon": 13.369, "status": "Established", "city": "Berlin", "state": "Berlin"},
    {"station": "München Hbf", "lat": 48.135, "lon": 11.582, "status": "Established", "city": "Munich", "state": "Bayern"},
    {"station": "Hamburg Hbf", "lat": 53.553, "lon": 9.992, "status": "Established", "city": "Hamburg", "state": "Hamburg"},
    {"station": "Frankfurt Hbf", "lat": 50.107, "lon": 8.664, "status": "Established", "city": "Frankfurt", "state": "Hessen"},
    {"station": "Köln Hbf", "lat": 50.943, "lon": 6.958, "status": "Established", "city": "Cologne", "state": "Nordrhein-Westfalen"},

    # Present (5 stations)
    {"station": "Stuttgart Hbf", "lat": 48.784, "lon": 9.177, "status": "Present", "city": "Stuttgart", "state": "Baden-Wurttemberg"},
    {"station": "Düsseldorf Hbf", "lat": 51.219, "lon": 6.794, "status": "Present", "city": "Dusseldorf", "state": "Nordrhein-Westfalen"},
    {"station": "Dortmund Hbf", "lat": 51.517, "lon": 7.466, "status": "Present", "city": "Dortmund", "state": "Nordrhein-Westfalen"},
    {"station": "Essen Hbf", "lat": 51.454, "lon": 7.013, "status": "Present", "city": "Essen", "state": "Nordrhein-Westfalen"},
    {"station": "Bremen Hbf", "lat": 53.079, "lon": 8.801, "status": "Present", "city": "Bremen", "state": "Bremen"},

    # Expanding (3 stations)
    {"station": "Hannover Hbf", "lat": 52.376, "lon": 9.741, "status": "Expanding", "city": "Hannover", "state": "Niedersachsen"},
    {"station": "Leipzig Hbf", "lat": 51.345, "lon": 12.383, "status": "Expanding", "city": "Leipzig", "state": "Sachsen"},
    {"station": "Nürnberg Hbf", "lat": 49.446, "lon": 11.078, "status": "Expanding", "city": "Nuremberg", "state": "Bayern"},

    # Future (2 stations)
    {"station": "Dresden Hbf", "lat": 51.045, "lon": 13.737, "status": "Future", "city": "Dresden", "state": "Sachsen"},
    {"station": "Mannheim Hbf", "lat": 49.479, "lon": 8.471, "status": "Future", "city": "Mannheim", "state": "Baden-Wurttemberg"},

    # New additions (10 stations)
    {"station": "Berlin Südkreuz", "lat": 52.475, "lon": 13.365, "status": "Expanding", "city": "Berlin", "state": "Berlin"},
    {"station": "Berlin Ostbahnhof", "lat": 52.510, "lon": 13.434, "status": "Expanding", "city": "Berlin", "state": "Berlin"},
    {"station": "München Ost", "lat": 48.127, "lon": 11.602, "status": "Expanding", "city": "Munich", "state": "Bayern"},
    {"station": "Frankfurt Flughafen", "lat": 50.050, "lon": 8.570, "status": "Present", "city": "Frankfurt", "state": "Hessen"},
    {"station": "Köln Messe/Deutz", "lat": 50.940, "lon": 6.972, "status": "Present", "city": "Cologne", "state": "Nordrhein-Westfalen"},
    {"station": "Düsseldorf Flughafen", "lat": 51.280, "lon": 6.765, "status": "Present", "city": "Düsseldorf", "state": "Nordrhein-Westfalen"},
    {"station": "Hamburg Altona", "lat": 53.552, "lon": 9.935, "status": "Present", "city": "Hamburg", "state": "Hamburg"},
    {"station": "Stuttgart Flughafen", "lat": 48.690, "lon": 9.193, "status": "Future", "city": "Stuttgart", "state": "Baden-Wurttemberg"},
    {"station": "Hannover Messe/Laatzen", "lat": 52.324, "lon": 9.814, "status": "Future", "city": "Hannover", "state": "Niedersachsen"},
    {"station": "Leipzig/Halle Flughafen", "lat": 51.423, "lon": 12.236, "status": "Future", "city": "Leipzig", "state": "Sachsen"},
]

# ═══════════════════════════════════════════════════
# CUSTOMER / OPERATOR DATA
# ═══════════════════════════════════════════════════

CUSTOMERS = [
    {
        "customer_id": "OP001",
        "customer_name": "DB Station&Service",
        "tier": "Platinum",
        "operator_type": "National",
        "satisfaction_score": 9.2,
        "rfm_segment": "Champions",
        "segment": "Strategic Partners",
        "risk_level": "Low Risk",
        "total_contract_value_eur": 500000,
        "days_to_renewal": 120,
        "avg_response_hours": 2.1,
        "psd_units": 45,
        "trains_covered": 120,
        "platforms_installed": 12,
        "recency_score": 5,
        "frequency_score": 50,
        "monetary_score": 5,
        "station": "Berlin Hbf",
        "city": "Berlin",
        "employees": 15000,
        "founded": 1994,
    },
    {
        "customer_id": "OP002",
        "customer_name": "S-Bahn Berlin",
        "tier": "Gold",
        "operator_type": "Regional",
        "satisfaction_score": 8.5,
        "rfm_segment": "Loyal",
        "segment": "Key Accounts",
        "risk_level": "Low Risk",
        "total_contract_value_eur": 350000,
        "days_to_renewal": 45,
        "avg_response_hours": 2.5,
        "psd_units": 32,
        "trains_covered": 80,
        "platforms_installed": 8,
        "recency_score": 4,
        "frequency_score": 40,
        "monetary_score": 4,
        "station": "Berlin Hbf",
        "city": "Berlin",
        "employees": 3500,
        "founded": 1924,
    },
    {
        "customer_id": "OP003",
        "customer_name": "BVG Berlin",
        "tier": "Silver",
        "operator_type": "Municipal",
        "satisfaction_score": 7.8,
        "rfm_segment": "Potential",
        "segment": "Growth Potential",
        "risk_level": "Medium Risk",
        "total_contract_value_eur": 200000,
        "days_to_renewal": 180,
        "avg_response_hours": 3.2,
        "psd_units": 28,
        "trains_covered": 65,
        "platforms_installed": 6,
        "recency_score": 3,
        "frequency_score": 25,
        "monetary_score": 3,
        "station": "Berlin Hbf",
        "city": "Berlin",
        "employees": 14500,
        "founded": 1929,
    },
    {
        "customer_id": "OP004",
        "customer_name": "DB Regio Bayern",
        "tier": "Platinum",
        "operator_type": "National",
        "satisfaction_score": 9.0,
        "rfm_segment": "Champions",
        "segment": "Strategic Partners",
        "risk_level": "Low Risk",
        "total_contract_value_eur": 450000,
        "days_to_renewal": 90,
        "avg_response_hours": 2.3,
        "psd_units": 38,
        "trains_covered": 95,
        "platforms_installed": 10,
        "recency_score": 5,
        "frequency_score": 45,
        "monetary_score": 5,
        "station": "München Hbf",
        "city": "Munich",
        "employees": 8500,
        "founded": 1999,
    },
    {
        "customer_id": "OP005",
        "customer_name": "S-Bahn Munich",
        "tier": "Gold",
        "operator_type": "Regional",
        "satisfaction_score": 8.8,
        "rfm_segment": "Loyal",
        "segment": "Key Accounts",
        "risk_level": "Low Risk",
        "total_contract_value_eur": 300000,
        "days_to_renewal": 60,
        "avg_response_hours": 2.8,
        "psd_units": 25,
        "trains_covered": 70,
        "platforms_installed": 7,
        "recency_score": 4,
        "frequency_score": 35,
        "monetary_score": 4,
        "station": "München Hbf",
        "city": "Munich",
        "employees": 2800,
        "founded": 1972,
    },
    {
        "customer_id": "OP006",
        "customer_name": "HVV Hamburg",
        "tier": "Gold",
        "operator_type": "Municipal",
        "satisfaction_score": 8.2,
        "rfm_segment": "Loyal",
        "segment": "Key Accounts",
        "risk_level": "Low Risk",
        "total_contract_value_eur": 320000,
        "days_to_renewal": 150,
        "avg_response_hours": 2.6,
        "psd_units": 30,
        "trains_covered": 85,
        "platforms_installed": 9,
        "recency_score": 4,
        "frequency_score": 38,
        "monetary_score": 4,
        "station": "Hamburg Hbf",
        "city": "Hamburg",
        "employees": 4200,
        "founded": 1965,
    },
    {
        "customer_id": "OP007",
        "customer_name": "RMV Frankfurt",
        "tier": "Silver",
        "operator_type": "Regional",
        "satisfaction_score": 7.5,
        "rfm_segment": "At Risk",
        "segment": "At Risk",
        "risk_level": "High Risk",
        "total_contract_value_eur": 180000,
        "days_to_renewal": 15,
        "avg_response_hours": 4.2,
        "psd_units": 22,
        "trains_covered": 55,
        "platforms_installed": 5,
        "recency_score": 2,
        "frequency_score": 18,
        "monetary_score": 2,
        "station": "Frankfurt Hbf",
        "city": "Frankfurt",
        "employees": 3100,
        "founded": 1995,
    },
    {
        "customer_id": "OP008",
        "customer_name": "KVB Cologne",
        "tier": "Gold",
        "operator_type": "Municipal",
        "satisfaction_score": 8.6,
        "rfm_segment": "Loyal",
        "segment": "Key Accounts",
        "risk_level": "Low Risk",
        "total_contract_value_eur": 280000,
        "days_to_renewal": 75,
        "avg_response_hours": 2.4,
        "psd_units": 28,
        "trains_covered": 72,
        "platforms_installed": 8,
        "recency_score": 4,
        "frequency_score": 36,
        "monetary_score": 4,
        "station": "Köln Hbf",
        "city": "Cologne",
        "employees": 3800,
        "founded": 1876,
    },
    {
        "customer_id": "OP009",
        "customer_name": "VVS Stuttgart",
        "tier": "Silver",
        "operator_type": "Regional",
        "satisfaction_score": 7.9,
        "rfm_segment": "Potential",
        "segment": "Growth Potential",
        "risk_level": "Medium Risk",
        "total_contract_value_eur": 220000,
        "days_to_renewal": 200,
        "avg_response_hours": 3.5,
        "psd_units": 20,
        "trains_covered": 50,
        "platforms_installed": 5,
        "recency_score": 3,
        "frequency_score": 22,
        "monetary_score": 3,
        "station": "Stuttgart Hbf",
        "city": "Stuttgart",
        "employees": 2600,
        "founded": 1993,
    },
    {
        "customer_id": "OP010",
        "customer_name": "Rhein-Ruhr Bahn",
        "tier": "Bronze",
        "operator_type": "Private",
        "satisfaction_score": 6.8,
        "rfm_segment": "At Risk",
        "segment": "At Risk",
        "risk_level": "High Risk",
        "total_contract_value_eur": 120000,
        "days_to_renewal": 10,
        "avg_response_hours": 5.1,
        "psd_units": 15,
        "trains_covered": 35,
        "platforms_installed": 3,
        "recency_score": 1,
        "frequency_score": 12,
        "monetary_score": 2,
        "station": "Essen Hbf",
        "city": "Essen",
        "employees": 1200,
        "founded": 1998,
    },
    {
        "customer_id": "OP011",
        "customer_name": "DB Regio Nord",
        "tier": "Platinum",
        "operator_type": "National",
        "satisfaction_score": 8.9,
        "rfm_segment": "Champions",
        "segment": "Strategic Partners",
        "risk_level": "Low Risk",
        "total_contract_value_eur": 420000,
        "days_to_renewal": 110,
        "avg_response_hours": 2.2,
        "psd_units": 35,
        "trains_covered": 88,
        "platforms_installed": 9,
        "recency_score": 5,
        "frequency_score": 42,
        "monetary_score": 5,
        "station": "Bremen Hbf",
        "city": "Bremen",
        "employees": 6200,
        "founded": 1999,
    },
    {
        "customer_id": "OP012",
        "customer_name": "metronom",
        "tier": "Silver",
        "operator_type": "Private",
        "satisfaction_score": 7.6,
        "rfm_segment": "Potential",
        "segment": "Growth Potential",
        "risk_level": "Medium Risk",
        "total_contract_value_eur": 160000,
        "days_to_renewal": 165,
        "avg_response_hours": 3.8,
        "psd_units": 18,
        "trains_covered": 42,
        "platforms_installed": 4,
        "recency_score": 3,
        "frequency_score": 20,
        "monetary_score": 3,
        "station": "Hannover Hbf",
        "city": "Hannover",
        "employees": 1800,
        "founded": 2002,
    },
    {
        "customer_id": "OP013",
        "customer_name": "DB Regio Sachsen",
        "tier": "Gold",
        "operator_type": "National",
        "satisfaction_score": 8.3,
        "rfm_segment": "Loyal",
        "segment": "Key Accounts",
        "risk_level": "Low Risk",
        "total_contract_value_eur": 260000,
        "days_to_renewal": 85,
        "avg_response_hours": 2.9,
        "psd_units": 24,
        "trains_covered": 60,
        "platforms_installed": 6,
        "recency_score": 4,
        "frequency_score": 32,
        "monetary_score": 4,
        "station": "Leipzig Hbf",
        "city": "Leipzig",
        "employees": 3400,
        "founded": 1999,
    },
    {
        "customer_id": "OP014",
        "customer_name": "agilis",
        "tier": "Bronze",
        "operator_type": "Private",
        "satisfaction_score": 6.5,
        "rfm_segment": "At Risk",
        "segment": "At Risk",
        "risk_level": "High Risk",
        "total_contract_value_eur": 95000,
        "days_to_renewal": 5,
        "avg_response_hours": 5.5,
        "psd_units": 12,
        "trains_covered": 28,
        "platforms_installed": 2,
        "recency_score": 1,
        "frequency_score": 10,
        "monetary_score": 1,
        "station": "Nürnberg Hbf",
        "city": "Nuremberg",
        "employees": 850,
        "founded": 2008,
    },
    {
        "customer_id": "OP015",
        "customer_name": "Vogtlandbahn",
        "tier": "Bronze",
        "operator_type": "Private",
        "satisfaction_score": 6.2,
        "rfm_segment": "At Risk",
        "segment": "At Risk",
        "risk_level": "High Risk",
        "total_contract_value_eur": 85000,
        "days_to_renewal": 3,
        "avg_response_hours": 6.2,
        "psd_units": 10,
        "trains_covered": 22,
        "platforms_installed": 2,
        "recency_score": 1,
        "frequency_score": 8,
        "monetary_score": 1,
        "station": "Dresden Hbf",
        "city": "Dresden",
        "employees": 650,
        "founded": 1997,
    },

    # New expansion customers (10 operators — hyper-growth startup scale)
    {
        "customer_id": "OP016",
        "customer_name": "ÖBB Personenverkehr",
        "tier": "Platinum",
        "operator_type": "National",
        "satisfaction_score": 9.4,
        "rfm_segment": "Champions",
        "segment": "Strategic Partners",
        "risk_level": "Low Risk",
        "total_contract_value_eur": 580000,
        "days_to_renewal": 135,
        "avg_response_hours": 1.8,
        "psd_units": 52,
        "trains_covered": 140,
        "platforms_installed": 14,
        "recency_score": 5,
        "frequency_score": 55,
        "monetary_score": 5,
        "station": "Berlin Südkreuz",
        "city": "Berlin",
        "employees": 12000,
        "founded": 2005,
    },
    {
        "customer_id": "OP017",
        "customer_name": "SBB GmbH",
        "tier": "Gold",
        "operator_type": "National",
        "satisfaction_score": 8.7,
        "rfm_segment": "Loyal",
        "segment": "Key Accounts",
        "risk_level": "Low Risk",
        "total_contract_value_eur": 380000,
        "days_to_renewal": 95,
        "avg_response_hours": 2.4,
        "psd_units": 36,
        "trains_covered": 92,
        "platforms_installed": 10,
        "recency_score": 4,
        "frequency_score": 38,
        "monetary_score": 4,
        "station": "München Ost",
        "city": "Munich",
        "employees": 2200,
        "founded": 2002,
    },
    {
        "customer_id": "OP018",
        "customer_name": "Arriva Deutschland",
        "tier": "Gold",
        "operator_type": "Private",
        "satisfaction_score": 8.1,
        "rfm_segment": "Loyal",
        "segment": "Key Accounts",
        "risk_level": "Low Risk",
        "total_contract_value_eur": 290000,
        "days_to_renewal": 140,
        "avg_response_hours": 2.7,
        "psd_units": 26,
        "trains_covered": 68,
        "platforms_installed": 7,
        "recency_score": 4,
        "frequency_score": 30,
        "monetary_score": 4,
        "station": "Frankfurt Flughafen",
        "city": "Frankfurt",
        "employees": 4200,
        "founded": 1997,
    },
    {
        "customer_id": "OP019",
        "customer_name": "National Express Rail",
        "tier": "Silver",
        "operator_type": "Private",
        "satisfaction_score": 7.7,
        "rfm_segment": "Potential",
        "segment": "Growth Potential",
        "risk_level": "Medium Risk",
        "total_contract_value_eur": 195000,
        "days_to_renewal": 170,
        "avg_response_hours": 3.4,
        "psd_units": 22,
        "trains_covered": 48,
        "platforms_installed": 5,
        "recency_score": 3,
        "frequency_score": 22,
        "monetary_score": 3,
        "station": "Köln Messe/Deutz",
        "city": "Cologne",
        "employees": 1800,
        "founded": 2000,
    },
    {
        "customer_id": "OP020",
        "customer_name": "FlixTrain GmbH",
        "tier": "Platinum",
        "operator_type": "Private",
        "satisfaction_score": 9.1,
        "rfm_segment": "Champions",
        "segment": "Strategic Partners",
        "risk_level": "Low Risk",
        "total_contract_value_eur": 620000,
        "days_to_renewal": 200,
        "avg_response_hours": 1.9,
        "psd_units": 48,
        "trains_covered": 130,
        "platforms_installed": 13,
        "recency_score": 5,
        "frequency_score": 48,
        "monetary_score": 5,
        "station": "Düsseldorf Flughafen",
        "city": "Düsseldorf",
        "employees": 3500,
        "founded": 2018,
    },
    {
        "customer_id": "OP021",
        "customer_name": "Go-Ahead Bayern",
        "tier": "Silver",
        "operator_type": "Private",
        "satisfaction_score": 7.4,
        "rfm_segment": "At Risk",
        "segment": "At Risk",
        "risk_level": "Medium Risk",
        "total_contract_value_eur": 175000,
        "days_to_renewal": 25,
        "avg_response_hours": 4.0,
        "psd_units": 18,
        "trains_covered": 40,
        "platforms_installed": 4,
        "recency_score": 2,
        "frequency_score": 16,
        "monetary_score": 2,
        "station": "Stuttgart Flughafen",
        "city": "Stuttgart",
        "employees": 950,
        "founded": 2019,
    },
    {
        "customer_id": "OP022",
        "customer_name": "Nahreisezug GmbH",
        "tier": "Bronze",
        "operator_type": "Regional",
        "satisfaction_score": 6.9,
        "rfm_segment": "At Risk",
        "segment": "At Risk",
        "risk_level": "High Risk",
        "total_contract_value_eur": 110000,
        "days_to_renewal": 12,
        "avg_response_hours": 5.0,
        "psd_units": 14,
        "trains_covered": 30,
        "platforms_installed": 3,
        "recency_score": 1,
        "frequency_score": 10,
        "monetary_score": 2,
        "station": "Hamburg Altona",
        "city": "Hamburg",
        "employees": 750,
        "founded": 2015,
    },
    {
        "customer_id": "OP023",
        "customer_name": "VBB Verkehrsverbund",
        "tier": "Gold",
        "operator_type": "Regional",
        "satisfaction_score": 8.4,
        "rfm_segment": "Loyal",
        "segment": "Key Accounts",
        "risk_level": "Low Risk",
        "total_contract_value_eur": 340000,
        "days_to_renewal": 105,
        "avg_response_hours": 2.5,
        "psd_units": 30,
        "trains_covered": 78,
        "platforms_installed": 8,
        "recency_score": 4,
        "frequency_score": 34,
        "monetary_score": 4,
        "station": "Berlin Ostbahnhof",
        "city": "Berlin",
        "employees": 2900,
        "founded": 1996,
    },
    {
        "customer_id": "OP024",
        "customer_name": "Hessische Landesbahn",
        "tier": "Silver",
        "operator_type": "Regional",
        "satisfaction_score": 7.6,
        "rfm_segment": "Potential",
        "segment": "Growth Potential",
        "risk_level": "Medium Risk",
        "total_contract_value_eur": 205000,
        "days_to_renewal": 155,
        "avg_response_hours": 3.6,
        "psd_units": 20,
        "trains_covered": 52,
        "platforms_installed": 5,
        "recency_score": 3,
        "frequency_score": 24,
        "monetary_score": 3,
        "station": "Hannover Messe/Laatzen",
        "city": "Hannover",
        "employees": 1600,
        "founded": 2003,
    },
    {
        "customer_id": "OP025",
        "customer_name": "S-Bahn Mitteldeutschland",
        "tier": "Gold",
        "operator_type": "Regional",
        "satisfaction_score": 8.0,
        "rfm_segment": "Loyal",
        "segment": "Key Accounts",
        "risk_level": "Low Risk",
        "total_contract_value_eur": 265000,
        "days_to_renewal": 80,
        "avg_response_hours": 2.8,
        "psd_units": 24,
        "trains_covered": 58,
        "platforms_installed": 6,
        "recency_score": 4,
        "frequency_score": 28,
        "monetary_score": 4,
        "station": "Leipzig/Halle Flughafen",
        "city": "Leipzig",
        "employees": 2100,
        "founded": 2004,
    },
]

# ═══════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════

def get_station_df():
    """Return DataFrame of German railway stations."""
    return pd.DataFrame(STATIONS)


def get_customer_df():
    """Return DataFrame of customer/operator data with all required columns."""
    df = pd.DataFrame(CUSTOMERS)
    # Rename columns to match what main.py expects
    df = df.rename(columns={
        "trains_covered": "total_trains",
    })
    # Add missing columns with default values
    if "total_routes" not in df.columns:
        df["total_routes"] = df.get("total_trains", 10) // 5  # Approx 1 route per 5 trains
    if "maintenance_annual_eur" not in df.columns:
        df["maintenance_annual_eur"] = df["total_contract_value_eur"] * 0.1  # 10% of contract value
    if "last_project_days" not in df.columns:
        df["last_project_days"] = np.random.randint(30, 180, len(df))  # Random 30-180 days ago
    if "open_issues" not in df.columns:
        df["open_issues"] = df["risk_level"].apply(
            lambda x: 3 if x == "High Risk" else (2 if x == "Medium Risk" else 1)
        )
    if "contract_status" not in df.columns:
        df["contract_status"] = df["days_to_renewal"].apply(
            lambda x: "Critical" if x <= 30 else ("Urgent" if x <= 60 else ("Upcoming" if x <= 90 else "Active"))
        )
    return df


def get_rfm_df():
    """Return RFM analysis DataFrame."""
    df = pd.DataFrame(CUSTOMERS)
    rfm_df = df[["customer_id", "customer_name", "rfm_segment", "segment",
                  "recency_score", "frequency_score", "monetary_score",
                  "platforms_installed", "total_contract_value_eur"]].copy()
    # Add calculated RFM score (average of R, F, M scores)
    rfm_df["rfm_score"] = rfm_df[["recency_score", "frequency_score", "monetary_score"]].mean(axis=1).round(1)
    return rfm_df


def get_customer_insights():
    """Return business insights dictionary with all required keys."""
    df = get_customer_df()
    at_risk = df[df["risk_level"].isin(["High Risk", "Medium Risk"])]
    strategic = df[df["segment"] == "Strategic Partners"]
    operator_type_counts = df["operator_type"].value_counts()
    return {
        "total_customers": len(df),
        "total_trains_covered": df["total_trains"].sum(),
        "total_contract_value_eur": df["total_contract_value_eur"].sum(),
        "avg_contract_value_eur": df["total_contract_value_eur"].mean(),
        "total_psd_units": df["psd_units"].sum(),
        "high_value_count": len(df[df["tier"].isin(["Platinum", "Gold"])]),
        "avg_satisfaction": df["satisfaction_score"].mean(),
        "risk_rate": (len(at_risk) / len(df)) * 100 if len(df) > 0 else 0,
        "at_risk_count": len(at_risk),
        "at_risk_pct": (len(at_risk) / len(df)) * 100 if len(df) > 0 else 0,
        "strategic_count": len(strategic),
        "strategic_pct": (len(strategic) / len(df)) * 100 if len(df) > 0 else 0,
        "top_operator_type": operator_type_counts.index[0] if len(operator_type_counts) > 0 else "National",
        "recommendations": [
            {"priority": "high", "category": "Risk Management", "message": "Focus on at-risk accounts to reduce churn"},
            {"priority": "medium", "category": "Customer Retention", "message": "Expand Platinum tier benefits to increase retention"},
            {"priority": "low", "category": "Pricing Strategy", "message": "Consider volume discounts for multi-station operators"},
        ],
    }


def get_operator_profile(customer_id):
    """Return detailed profile for a specific operator."""
    df = get_customer_df()
    customer = df[df["customer_id"] == customer_id]
    if customer.empty:
        return {}
    row = customer.iloc[0]
    return {
        "operator_name": row["customer_name"],
        "operator_type": row["operator_type"],
        "tier": row["tier"],
        "operator_id": row["customer_id"],
        "health_status": "Healthy" if row["risk_level"] == "Low Risk" else "Warning",
        "health_score": 85 if row["risk_level"] == "Low Risk" else 65,
        "psd_units_total": row["psd_units"],
        "platforms_installed": row["platforms_installed"],
        "total_trains": row["total_trains"],
        "satisfaction_score": row["satisfaction_score"],
        "total_contract_value_eur": row["total_contract_value_eur"],
        "days_to_renewal": row["days_to_renewal"],
        "employees": row.get("employees", 1000),
        "founded": row.get("founded", 2000),
        "active_tickets": max(1, row.get("psd_units", 10) // 10),  # At least 1 ticket per 10 PSD units
        "high_priority_tickets": max(1, row.get("psd_units", 10) // 20),  # At least 1 high-priority per 20 PSD units
        "engagement_score": int(row["satisfaction_score"] * 10),
        "recent_engagements_6mo": max(5, row.get("psd_units", 10) // 5),  # At least 5 engagements per 6mo
        "avg_response_hours": row["avg_response_hours"],
        "annual_maintenance_eur": int(row["total_contract_value_eur"] * 0.1),  # 10% of contract value
        "renewal_risk": "Low" if row["risk_level"] == "Low Risk" else ("Medium" if row["risk_level"] == "Medium Risk" else "High"),
    }


def get_contract_health_df():
    """Return contract health scores DataFrame with health_status."""
    df = get_customer_df()
    health_data = []
    for _, row in df.iterrows():
        health_score = 90 if row["risk_level"] == "Low Risk" else (70 if row["risk_level"] == "Medium Risk" else 45)
        health_status = "Healthy" if health_score >= 70 else ("Attention" if health_score >= 50 else "Critical")
        health_data.append({
            "customer_id": row["customer_id"],
            "customer_name": row["customer_name"],
            "health_score": health_score,
            "health_status": health_status,
            "risk_level": row["risk_level"],
            "tier": row["tier"],
        })
    return pd.DataFrame(health_data)


def get_renewal_forecast_df():
    """Return renewal forecast DataFrame with all required columns."""
    df = get_customer_df()
    today = datetime.now()
    forecast_data = []
    for _, row in df.iterrows():
        renewal_date = today + timedelta(days=row["days_to_renewal"])
        forecast_data.append({
            "customer_id": row["customer_id"],
            "customer_name": row["customer_name"],
            "renewal_date": renewal_date,
            "days_to_renewal": row["days_to_renewal"],
            "total_contract_value_eur": row["total_contract_value_eur"],
            "tier": row["tier"],
            "operator_type": row["operator_type"],
            "renewal_tier": row["tier"],  # Same as tier for display
            "satisfaction_score": row["satisfaction_score"],
        })
    return pd.DataFrame(forecast_data)


def get_at_risk_df():
    """Return at-risk accounts DataFrame with all required columns."""
    df = get_customer_df()
    at_risk = df[df["risk_level"].isin(["High Risk", "Medium Risk"])].copy()
    # Add open_issues based on risk level (mock data)
    at_risk["open_issues"] = at_risk["risk_level"].apply(
        lambda x: 3 if x == "High Risk" else (2 if x == "Medium Risk" else 0)
    )
    return at_risk[
        [
            "customer_id",
            "customer_name",
            "operator_type",
            "risk_level",
            "tier",
            "days_to_renewal",
            "total_contract_value_eur",
            "satisfaction_score",
            "open_issues",
        ]
    ]


def get_renewal_health_summary(customer_df=None):
    """Return renewal health summary dict with all required keys."""
    health_df = get_contract_health_df()
    avg_health = health_df["health_score"].mean()
    healthy_count = len(health_df[health_df["health_score"] >= 70])
    return {
        "avg_health_score": avg_health,
        "healthy_pct": (healthy_count / len(health_df)) * 100 if len(health_df) > 0 else 0,
        "healthy_count": healthy_count,
        "total_operators": len(health_df),
    }


def get_high_value_customers_df():
    """Return high-value customers DataFrame with all required columns."""
    df = get_customer_df()
    high_value = df[df["tier"].isin(["Platinum", "Gold"])].copy()
    # Add value_score (based on total_contract_value_eur, normalized to 0-100)
    max_value = df["total_contract_value_eur"].max()
    high_value["value_score"] = (high_value["total_contract_value_eur"] / max_value * 100).astype(int)
    # Add value_tier based on value_score
    high_value["value_tier"] = high_value["value_score"].apply(
        lambda x: "Strategic" if x >= 80 else ("Preferred" if x >= 60 else "Important")
    )
    return high_value[
        [
            "customer_id",
            "customer_name",
            "operator_type",
            "value_score",
            "value_tier",
            "psd_units",
            "total_contract_value_eur",
            "tier",
        ]
    ]


def get_operator_history(customer_id):
    """Return operator history as DataFrame with meaningful data."""
    data = [
        {"project_id": "P001", "project_name": "Berlin Hbf Phase 1", "start_date": "2024-01-15", "end_date": "2024-03-30", "status": "Completed", "psd_installed": 12, "project_value_eur": 120000, "completion_pct": 100},
        {"project_id": "P002", "project_name": "Berlin Hbf Phase 2", "start_date": "2024-04-01", "end_date": "2024-06-15", "status": "Completed", "psd_installed": 15, "project_value_eur": 150000, "completion_pct": 100},
        {"project_id": "P003", "project_name": "München Hbf Installation", "start_date": "2024-06-20", "end_date": "2024-09-10", "status": "Completed", "psd_installed": 18, "project_value_eur": 180000, "completion_pct": 100},
        {"project_id": "P004", "project_name": "Hamburg Hbf Rollout", "start_date": "2024-09-15", "end_date": "2024-12-20", "status": "Completed", "psd_installed": 20, "project_value_eur": 200000, "completion_pct": 100},
        {"project_id": "P005", "project_name": "Frankfurt Hbf Expansion", "start_date": "2025-01-10", "end_date": "2025-04-30", "status": "In Progress", "psd_installed": 8, "project_value_eur": 80000, "completion_pct": 65},
        {"project_id": "P006", "project_name": "Köln Hbf Planning", "start_date": "2025-03-01", "end_date": "2025-06-15", "status": "Planned", "psd_installed": 10, "project_value_eur": 100000, "completion_pct": 0},
    ]
    return pd.DataFrame(data)


def get_support_tickets(customer_id, limit=100):
    """Return support tickets as DataFrame with meaningful data."""
    data = [
        {"created_date": "2024-11-15", "category": "Maintenance", "priority": "Low", "status": "Completed", "summary": "Gate sensor calibration required for Platform 3", "resolution_time_hours": 3.5},
        {"created_date": "2024-11-20", "category": "Hardware", "priority": "Medium", "status": "In Progress", "summary": "Platform alignment drift detected on Track 2", "resolution_time_hours": 1.2},
        {"created_date": "2024-12-01", "category": "Safety", "priority": "High", "status": "Completed", "summary": "Emergency stop false positive on Gate 5", "resolution_time_hours": 0.8},
        {"created_date": "2024-12-10", "category": "Software", "priority": "Low", "status": "Pending", "summary": "Software update v2.3 required for PSD controllers", "resolution_time_hours": 0},
        {"created_date": "2025-01-05", "category": "Hardware", "priority": "Medium", "status": "Open", "summary": "Door motor vibration exceeds threshold", "resolution_time_hours": 0},
        {"created_date": "2025-01-15", "category": "Compliance", "priority": "Low", "status": "Completed", "summary": "Annual safety certification renewal", "resolution_time_hours": 2.0},
    ]
    return pd.DataFrame(data[:limit])


def get_engagement_timeline(customer_id, months_back=12):
    """Return engagement timeline (mock data)."""
    # Ensure months_back is a valid integer
    if not isinstance(months_back, int) or months_back < 1:
        months_back = 12
    date_range = pd.date_range(end=datetime.now(), periods=months_back, freq="ME")
    num_periods = len(date_range)  # Use actual length
    follow_up_range = date_range + timedelta(days=14)
    return pd.DataFrame({
        "date": date_range.strftime("%Y-%m-%d"),
        "type": np.random.choice(["Meeting", "Review", "Training", "Support Call", "On-site Visit"], num_periods),
        "direction": np.random.choice(["Inbound", "Outbound"], num_periods),
        "our_participants": np.random.randint(2, 6, num_periods),
        "their_participants": np.random.randint(2, 8, num_periods),
        "outcome": np.random.choice(["Successful", "Follow-up Required", "Resolved", "Pending Decision"], num_periods),
        "follow_up_date": follow_up_range.strftime("%Y-%m-%d"),
    })


def get_operator_monthly_stats(customer_id, months_back=6):
    """Return monthly stats (mock data)."""
    # Ensure months_back is a valid integer
    if not isinstance(months_back, int) or months_back < 1:
        months_back = 6
    date_range = pd.date_range(end=datetime.now(), periods=months_back, freq="ME")
    num_periods = len(date_range)  # Use actual length
    return pd.DataFrame({
        "Month": date_range.strftime("%Y-%m"),
        "PSD Activations": np.random.randint(120, 480, num_periods),
        "Incidents": np.random.randint(1, 8, num_periods),
        "Uptime %": np.round(np.random.uniform(99.2, 99.95, num_periods), 2),
        "Projects Completed": np.random.randint(1, 4, num_periods),
        "Tickets Opened": np.random.randint(2, 8, num_periods),
        "Engagements": np.random.randint(3, 10, num_periods),
    })


def get_contract_amendments(customer_id):
    """Return contract amendments with meaningful data."""
    return [
        {"amendment_date": "2024-02-15", "amendment_type": "Expansion", "description": "Added 5 PSD units to Platform 3 expansion", "financial_impact_eur": 50000, "signed_by": "Dr. Klaus Werner"},
        {"amendment_date": "2024-06-01", "amendment_type": "Maintenance", "description": "Extended 24/7 premium maintenance contract", "financial_impact_eur": 35000, "signed_by": "Sarah Mueller"},
        {"amendment_date": "2024-09-15", "amendment_type": "Upgrade", "description": "Upgraded sensor package to Gen-3 technology", "financial_impact_eur": 28000, "signed_by": "Dr. Klaus Werner"},
        {"amendment_date": "2024-11-20", "amendment_type": "Expansion", "description": "Added 3 PSD units to Platform 5", "financial_impact_eur": 42000, "signed_by": "Thomas Braun"},
    ]


def get_financial_projections(months_ahead=24, customer_id=None):
    """Return financial projections with hyper-growth startup trajectory."""
    months = pd.date_range(start=datetime.now(), periods=months_ahead, freq="ME")
    base_revenue = 2_500_000
    growth_rate = 0.05  # 5% monthly growth
    revenue = (base_revenue * (1 + growth_rate) ** np.arange(months_ahead)).astype(int)
    costs = (base_revenue * 0.55 * (1 + growth_rate * 0.85) ** np.arange(months_ahead)).astype(int)
    return pd.DataFrame({
        "Month": months.strftime("%Y-%m").tolist(),
        "Revenue": revenue.tolist(),
        "Customers": (np.linspace(500, 5000, months_ahead, dtype=int) + np.random.randint(-20, 20, months_ahead)).clip(500, 6000).tolist(),
        "Costs": costs.tolist(),
        "Profit": (revenue - costs).tolist(),
    })


def get_operator_comparison_benchmarks(customer_id=None):
    """Return benchmark data with proper percentile values."""
    return {
        "avg_satisfaction": 7.8,
        "avg_response_hours": 3.5,
        "avg_psd_units": 25,            "avg_contract_value": 350000,
        "percentiles": {"p25": 6.5, "p50": 7.8, "p75": 8.5, "psd_percentile": 85, "cost_percentile": 88, "satisfaction_percentile": 80},
        "tier_benchmarks": [
            {"tier": "Platinum", "avg_score": 9.2, "avg_value": 600000, "avg_psd": 50},
            {"tier": "Gold", "avg_score": 8.5, "avg_value": 350000, "avg_psd": 32},
            {"tier": "Silver", "avg_score": 7.5, "avg_value": 220000, "avg_psd": 22},
            {"tier": "Bronze", "avg_score": 6.5, "avg_value": 130000, "avg_psd": 12},
        ],
    }


def get_support_ticket_trend(customer_id, months_back=6):
    """Return support ticket trend."""
    # Ensure months_back is a valid integer
    if not isinstance(months_back, int) or months_back < 1:
        months_back = 6
    date_range = pd.date_range(end=datetime.now(), periods=months_back, freq="ME")
    num_periods = len(date_range)  # Use actual length
    return pd.DataFrame({
        "Month": date_range.strftime("%Y-%m"),
        "Tickets": np.random.randint(1, 8, num_periods),
    })


def get_business_map_data():
    """Return business map data with station coordinates."""
    return get_station_df()


def get_leadership_data():
    """Return leadership team data."""
    return [
        {
            "name": "Khushboo Patil",
            "role": "CEO",
            "desc": "Business Strategy, Market Expansion, and Organizational Leadership",
            "img": "https://ui-avatars.com/api/?name=Khushboo+Patil&background=0e4d92&color=fff",
            "linkedin": "#",
            "experience": "15+ years in Railway Technology and Business Development",
            "education": "MBA, Technical University of Munich",
            "specialization": "Strategic Partnerships, Market Entry Strategy",
            "achievements": [
                "Led expansion to 15+ German railway stations",
                "Secured €2.5M in Series A funding",
                "Established partnerships with DB and regional operators",
            ],
            "quote": "Safety is not just a feature, it's our foundation.",
        },
        {
            "name": "Namrata Joshi",
            "role": "COO",
            "desc": "Operations Management, Strategic Planning, and Project Coordination",
            "img": "https://ui-avatars.com/api/?name=Namrata+Joshi&background=0e4d92&color=fff",
            "linkedin": "#",
            "experience": "12+ years in Operations and Project Management",
            "education": "MSc Operations Management, ETH Zurich",
            "specialization": "Large-scale infrastructure rollouts",
            "achievements": [
                "Managed rollout of 200+ PSD units across Germany",
                "Reduced average deployment time by 40%",
                "Achieved 99.5% on-time delivery rate",
            ],
            "quote": "Efficiency and safety go hand in hand.",
        },
        {
            "name": "Kona Shivam Rao",
            "role": "CTO",
            "desc": "Systems Engineering, Automation, and Rail Technology Development",
            "img": "https://ui-avatars.com/api/?name=Kona+Shivam+Rao&background=0e4d92&color=fff",
            "linkedin": "#",
            "experience": "18+ years in Systems Engineering and IoT",
            "education": "PhD Computer Science, TU Berlin",
            "specialization": "IoT sensors, Edge computing, Safety systems",
            "achievements": [
                "Patented 3 safety-critical sensor technologies",
                "Led development of real-time monitoring platform",
                "Achieved SIL-2 safety certification for core systems",
            ],
            "quote": "Innovation in safety never sleeps.",
        },
        {
            "name": "Sanika Kale",
            "role": "CPO",
            "desc": "Product Innovation, UX Design, and Platform System Integration",
            "img": "https://ui-avatars.com/api/?name=Sanika+Kale&background=0e4d92&color=fff",
            "linkedin": "#",
            "experience": "10+ years in Product Management and UX",
            "education": "MDes Product Design, IIT Bombay",
            "specialization": "User-centric safety interfaces",
            "achievements": [
                "Designed award-winning operator dashboard",
                "Reduced user onboarding time by 60%",
                "Led integration of 5+ third-party platforms",
            ],
            "quote": "Great products make safety invisible.",
        },
        {
            "name": "Nikhil Chavan",
            "role": "CFO",
            "desc": "Financial Strategy, Infrastructure Investment, and Strategic Partnerships",
            "img": "https://ui-avatars.com/api/?name=Nikhil+Chavan&background=0e4d92&color=fff",
            "linkedin": "#",
            "experience": "14+ years in Finance and Investment Banking",
            "education": "CFA Charterholder, Wharton MBA",
            "specialization": "Infrastructure financing, SaaS metrics",
            "achievements": [
                "Raised €35M across Series A, B, and growth rounds",
                "Achieved 3x YoY revenue growth with €12M+ ARR",
                "Optimized cash flow to support 600% expansion across DACH region",
            ],
            "quote": "Sustainable growth enables safer railways.",
        },
    ]


def get_operator_health_trend(customer_id, months_back=12):
    """Return operator health trend (mock data)."""
    import numpy as np
    from datetime import datetime

    # Ensure months_back is a valid integer
    if not isinstance(months_back, int) or months_back < 1:
        months_back = 12

    date_range = pd.date_range(end=datetime.now(), periods=months_back, freq='ME')
    dates = date_range.strftime('%Y-%m')

    if customer_id is None or customer_id == "all":
        health_scores = [int(np.random.uniform(75, 95)) for _ in range(len(dates))]
    else:
        at_risk_ids = ['OP007', 'OP010', 'OP014', 'OP015', 'OP021', 'OP022']
        if customer_id in at_risk_ids:
            health_scores = np.linspace(70, 45, len(dates), dtype=int).tolist()
        else:
            health_scores = np.linspace(85, 95, len(dates), dtype=int).tolist()

    return pd.DataFrame({
        'Month': dates.tolist(),
        'Health Score': health_scores,
    })
