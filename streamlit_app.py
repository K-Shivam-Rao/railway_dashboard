import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from data_source import (
    load_data, transform_data, get_metrics,
    get_psd_analytics, get_leadership_data,
    get_network_summary, get_maintenance_forecast,
    get_passenger_heatmap, get_incident_log,
    get_tech_stack, get_financial_model_data
)

# Cache for expensive computations
@st.cache_data(ttl=60, show_spinner=False)
def get_station_data_cached(station_name, df):
    """Cache station-specific data to avoid repeated filtering."""
    return df[df["station"] == station_name].copy()

@st.cache_data(ttl=60, show_spinner=False)
def get_psd_analytics_cached(station_name):
    """Cached wrapper for PSD analytics."""
    return get_psd_analytics(station_name)

@st.cache_data(ttl=60, show_spinner=False)
def get_network_summary_cached(df):
    """Cached wrapper for network summary."""
    return get_network_summary(df)

@st.cache_data(ttl=60, show_spinner=False)
def get_incident_log_cached(df):
    """Cached wrapper for incident log."""
    return get_incident_log(df)

@st.cache_data(ttl=3600, show_spinner=False)
def get_maintenance_forecast_cached(station_name):
    """Cached wrapper for maintenance forecast."""
    return get_maintenance_forecast(station_name)

@st.cache_data(ttl=3600, show_spinner=False)
def get_passenger_heatmap_cached(station_name):
    """Cached wrapper for passenger heatmap."""
    return get_passenger_heatmap(station_name)

# ═══════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════
st.set_page_config(
    layout="wide",
    page_title="SicherGleis Pro | BahnSetu",
    page_icon="🛡️",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════
if 'current_station' not in st.session_state:
    st.session_state.current_station = "Berlin Hauptbahnhof"
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 'ops'

# ═══════════════════════════════════════════════════
# CSS — PREMIUM DARK RAIL DASHBOARD
# ═══════════════════════════════════════════════════
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    /* ── Root Variables ── */
    :root {
        --bg-primary: #0a0e17;
        --bg-secondary: #0f1419;
        --bg-card: #111827;
        --bg-card-hover: #1a2332;
        --border-color: #1e293b;
        --border-glow: #334155;
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
        --text-muted: #64748b;
        --accent-blue: #3b82f6;
        --accent-cyan: #06b6d4;
        --accent-teal: #14b8a6;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
        --gradient-primary: linear-gradient(135deg, #3b82f6 0%, #06b6d4 50%, #14b8a6 100%);
        --gradient-danger: linear-gradient(135deg, #ef4444 0%, #f97316 100%);
        --gradient-warning: linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%);
        --gradient-success: linear-gradient(135deg, #10b981 0%, #34d399 100%);
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.3);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -1px rgba(0, 0, 0, 0.3);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.4), 0 4px 6px -2px rgba(0, 0, 0, 0.3);
        --shadow-glow: 0 0 20px rgba(59, 130, 246, 0.15);
        --transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }

    /* ── Base ── */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        background: var(--bg-primary) !important;
        color: var(--text-primary);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        line-height: 1.6;
        letter-spacing: -0.01em;
    }

    [data-testid="stSidebar"] {
        background: var(--bg-secondary) !important;
        border-right: 1px solid var(--border-color);
        box-shadow: 4px 0 24px rgba(0, 0, 0, 0.3);
        position: relative;
    }
    [data-testid="stSidebar"]::after {
        content: '';
        position: absolute; bottom: 0; left: 0; right: 0; height: 60px;
        background: linear-gradient(180deg, transparent 0%, var(--bg-secondary) 100%);
        pointer-events: none;
        z-index: 10;
    }

    /* ── Sidebar Brand Header ── */
    .sidebar-brand {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
        padding: 32px 24px 26px;
        margin: -24px -24px 28px -24px;
        border-bottom: 1px solid var(--border-color);
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(12px);
    }
    .sidebar-brand::before {
        content: '';
        position: absolute; top: -50%; right: -30%;
        width: 200px; height: 200px;
        background: radial-gradient(circle, rgba(59,130,246,0.15) 0%, transparent 70%);
        animation: pulse-glow 8s ease-in-out infinite;
    }
    @keyframes pulse-glow {
        0%, 100% { opacity: 0.6; transform: scale(1); }
        50% { opacity: 1; transform: scale(1.1); }
    }
    .brand-title {
        font-size: 1.5rem; font-weight: 800; letter-spacing: -0.5px;
        color: #fff; display: flex; align-items: center; gap: 12px;
        position: relative; z-index: 1;
        text-shadow: 0 0 20px rgba(59,130,246,0.3);
    }
    .brand-tagline {
        font-size: 0.7rem; font-family: 'JetBrains Mono', monospace;
        color: var(--text-secondary); margin-top: 8px; letter-spacing: 2px;
        text-transform: uppercase; position: relative; z-index: 1;
    }
    .brand-badge {
        display: inline-flex; align-items: center; gap: 6px;
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid rgba(16, 185, 129, 0.4);
        color: var(--success);
        font-size: 0.65rem; padding: 4px 12px; border-radius: 999px;
        margin-top: 12px; font-family: 'JetBrains Mono'; letter-spacing: 0.5px;
        position: relative; z-index: 1;
        animation: status-pulse 2s ease-in-out infinite;
    }
    @keyframes status-pulse {
        0%, 100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }
        50% { box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
    }

    /* ── Sidebar Nav Labels ── */
    .nav-label {
        font-size: 0.7rem; font-weight: 700; letter-spacing: 2.5px;
        text-transform: uppercase; color: var(--text-muted);
        margin: 24px 0 10px 4px;
        display: flex; align-items: center; gap: 8px;
    }
    .nav-label::before {
        content: ''; width: 8px; height: 8px;
        background: var(--accent-blue); border-radius: 50%;
        box-shadow: 0 0 8px var(--accent-blue);
    }
    .nav-divider {
        height: 1px; background: linear-gradient(90deg, transparent, var(--border-color), transparent);
        margin: 20px 0;
    }
    .sidebar-footer {
        font-size: 0.7rem; color: var(--text-muted); text-align: center;
        padding: 16px 0; font-family: 'JetBrains Mono';
        border-top: 1px solid var(--border-color);
        margin-top: 20px;
        opacity: 0.6;
    }

    /* ── Sidebar Buttons ── */
    [data-testid="stSidebar"] .stButton > button {
        width: 100%; border: 1px solid transparent;
        background: transparent; color: var(--text-secondary);
        text-align: left; padding: 11px 16px;
        border-radius: 8px; margin-bottom: 4px;
        font-weight: 500; font-size: 0.875rem;
        transition: var(--transition);
        display: flex; align-items: center; gap: 10px;
        position: relative;
        overflow: hidden;
    }
    [data-testid="stSidebar"] .stButton > button::before {
        content: ''; position: absolute; left: 0; top: 0;
        width: 3px; height: 100%; background: var(--accent-blue);
        transform: translateX(-100%); transition: var(--transition);
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(59, 130, 246, 0.1);
        border-color: rgba(59, 130, 246, 0.3);
        color: var(--text-primary);
        transform: translateX(4px);
    }
    [data-testid="stSidebar"] .stButton > button:hover::before {
        transform: translateX(0);
    }
    [data-testid="stSidebar"] .stButton > button:active {
        transform: translateX(2px);
    }
    .stButton > button[data-baseweb="button"][kind="secondary"] {
        background: rgba(59, 130, 246, 0.1) !important;
        border-color: rgba(59, 130, 246, 0.3) !important;
    }

    /* ── Main Header ── */
    .main-header {
        background: linear-gradient(135deg, rgba(17, 24, 39, 0.95) 0%, rgba(15, 23, 42, 0.95) 100%);
        backdrop-filter: blur(12px);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 28px 32px;
        margin-bottom: 28px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: var(--shadow-lg);
        position: relative;
        overflow: hidden;
    }
    .main-header::before {
        content: '';
        position: absolute; top: 0; left: 0; right: 0; height: 2px;
        background: var(--gradient-primary);
        animation: header-shine 3s ease-in-out infinite;
    }
    @keyframes header-shine {
        0%, 100% { opacity: 0.6; }
        50% { opacity: 1; }
    }
    .station-title {
        font-size: 1.875rem; font-weight: 800; color: #fff; margin: 0;
        letter-spacing: -0.75px; line-height: 1.2;
        text-shadow: 0 0 40px rgba(59, 130, 246, 0.3);
    }
    .station-sub {
        font-family: 'JetBrains Mono', monospace; font-size: 0.812rem;
        color: var(--text-secondary); margin-top: 8px; letter-spacing: 1.5px;
        display: flex; align-items: center; gap: 8px;
    }
    .station-sub::before {
        content: '◈'; color: var(--accent-blue); font-size: 0.5rem;
    }

    /* ── Status Badge ── */
    .status-badge {
        display: inline-flex; align-items: center; gap: 8px;
        padding: 10px 24px; border-radius: 999px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.875rem; font-weight: 600; letter-spacing: 1.5px;
        transition: var(--transition);
        border: 1px solid;
        position: relative;
        overflow: hidden;
    }
    .status-badge::before {
        content: ''; position: absolute; top: 0; left: -100%;
        width: 100%; height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
        animation: shimmer 2s ease-in-out infinite;
    }
    @keyframes shimmer {
        0%, 100% { left: -100%; }
        50% { left: 100%; }
    }
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .status-normal {
        background: rgba(16, 185, 129, 0.15);
        border-color: rgba(16, 185, 129, 0.5);
        box-shadow: 0 0 24px rgba(16, 185, 129, 0.25);
    }
    .status-alert {
        background: rgba(239, 68, 68, 0.15);
        border-color: rgba(239, 68, 68, 0.5);
        box-shadow: 0 0 20px rgba(239, 68, 68, 0.2);
        animation: alert-pulse 1.5s ease-in-out infinite;
    }
    @keyframes alert-pulse {
        0%, 100% { box-shadow: 0 0 20px rgba(239, 68, 68, 0.2); }
        50% { box-shadow: 0 0 30px rgba(239, 68, 68, 0.4); }
    }
    .status-dot {
        width: 8px; height: 8px; border-radius: 50%;
        display: inline-block; position: relative;
    }
    .status-normal .status-dot { background: var(--success); }
    .status-alert .status-dot { background: var(--danger); animation: blink-dot 1s ease-in-out infinite; }
    @keyframes blink-dot {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.4; }
    }

    /* ── Metric Cards ── */
    .metric-card {
        background: linear-gradient(135deg, rgba(17, 24, 39, 0.95) 0%, rgba(15, 23, 42, 0.95) 100%);
        backdrop-filter: blur(12px);
        border: 1px solid var(--border-color);
        border-radius: 14px;
        padding: 24px;
        position: relative;
        overflow: hidden;
        transition: var(--transition);
        box-shadow: var(--shadow-md);
        cursor: default;
        isolation: isolate;
    }
    .metric-card::after {
        content: '';
        position: absolute; top: 0; left: 0; right: 0; bottom: 0;
        background: radial-gradient(circle at top right, rgba(59, 130, 246, 0.03), transparent 60%);
        pointer-events: none;
    }
    .metric-card:hover {
        border-color: var(--accent-blue);
        transform: translateY(-3px);
        box-shadow: var(--shadow-lg), 0 8px 32px rgba(59, 130, 246, 0.15);
    }
    .metric-card::before {
        content: ''; position: absolute;
        top: 0; left: 0; right: 0; height: 3px;
        background: var(--gradient-primary);
        transition: var(--transition);
    }
    .metric-card.alert::before {
        background: var(--gradient-danger);
        box-shadow: 0 0 16px rgba(239, 68, 68, 0.5);
    }
    .metric-card.warn::before {
        background: var(--gradient-warning);
        box-shadow: 0 0 16px rgba(245, 158, 11, 0.5);
    }
    .metric-card.green::before {
        background: var(--gradient-success);
        box-shadow: 0 0 16px rgba(16, 185, 129, 0.5);
    }
    .metric-title {
        font-size: 0.6875rem; font-weight: 700;
        letter-spacing: 2px; line-height: 1;
        text-transform: uppercase;
        color: var(--text-muted);
        margin-bottom: 16px;
        display: flex; align-items: center; gap: 8px;
    }
    .metric-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2.125rem; font-weight: 700;
        color: var(--text-primary); line-height: 1.1;
        margin-bottom: 8px;
        text-shadow: 0 0 24px rgba(255, 255, 255, 0.1);
    }
    .metric-sub {
        font-size: 0.75rem; color: var(--text-muted);
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: 0.5px;
        display: flex; align-items: center; gap: 6px;
        opacity: 0.8;
    }

    /* ── Section Headings ── */
    .section-heading {
        font-size: 1.25rem; font-weight: 700; color: var(--text-primary);
        letter-spacing: -0.025em; margin-bottom: 24px;
        display: flex; align-items: center; gap: 12px;
        padding-bottom: 14px;
        border-bottom: 1px solid var(--border-color);
        position: relative;
        text-shadow: 0 0 20px rgba(59, 130, 246, 0.3);
    }
    .section-heading::before {
        content: ''; position: absolute; bottom: -1px; left: 0;
        width: 80px; height: 3px; background: var(--gradient-primary);
        border-radius: 2px;
    }

    /* ── PSD Gate Visualization ── */
    .psd-container {
        background: linear-gradient(135deg, rgba(17, 24, 39, 0.95) 0%, rgba(15, 23, 42, 0.95) 100%);
        backdrop-filter: blur(12px);
        border: 1px solid var(--border-color);
        border-radius: 14px; padding: 28px; margin-bottom: 20px;
        box-shadow: var(--shadow-lg);
        position: relative;
        overflow: hidden;
    }
    .psd-container::before {
        content: '';
        position: absolute; top: 0; left: 0; right: 0; bottom: 0;
        background: radial-gradient(circle at top left, rgba(6, 182, 212, 0.03), transparent 50%);
        pointer-events: none;
    }
    .platform-label {
        font-family: 'JetBrains Mono', monospace; font-size: 0.812rem;
        color: var(--text-secondary); margin-bottom: 18px; font-weight: 600;
        text-transform: uppercase; letter-spacing: 1.5px;
        display: flex; justify-content: space-between; align-items: center;
        padding-bottom: 12px; border-bottom: 1px solid var(--border-color);
    }
    .gate-row {
        display: flex; gap: 6px; align-items: flex-end;
        height: 125px; background: linear-gradient(180deg, #0a0e17 0%, #111827 100%);
        border-radius: 10px; padding: 14px 16px;
        position: relative; overflow: hidden;
        border: 1px solid var(--border-color);
    }
    .gate-row::before {
        content: 'PLATFORM EDGE';
        position: absolute; bottom: 8px; left: 50%; transform: translateX(-50%);
        font-family: 'JetBrains Mono'; font-size: 0.5rem;
        color: var(--text-muted); letter-spacing: 2px;
        opacity: 0.3;
    }
    .gate-row::after {
        content: ''; position: absolute;
        bottom: 16px; left: 0; right: 0; height: 2px;
        background: repeating-linear-gradient(90deg, var(--border-color) 0px, var(--border-color) 10px, transparent 10px, transparent 18px);
        opacity: 0.5;
    }
    .gate {
        flex: 1; border-radius: 4px 4px 0 0; position: relative;
        max-width: 60px; cursor: pointer;
        transition: var(--transition);
    }
    .gate:hover { filter: brightness(1.2); }
    .gate-panel { position: absolute; top: 8%; left: 12%; width: 76%; height: 55%; border-radius: 2px; }
    .gate-id-label {
        position: absolute; bottom: -18px; left: 50%;
        transform: translateX(-50%);
        font-size: 0.5rem; font-family: 'JetBrains Mono'; color: var(--text-muted);
        white-space: nowrap; opacity: 0.7;
    }
    .gate.closed { background: linear-gradient(180deg, #3b82f6 0%, #1d4ed8 100%); }
    .gate.closed .gate-panel { background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15); }
    .gate.open { height: 32% !important; opacity: 0.7; }
    .gate.open .gate-panel { background: var(--success); box-shadow: 0 0 12px rgba(16, 185, 129, 0.5); }
    .gate.jammed { background: linear-gradient(180deg, #dc2626 0%, #991b1b 100%); animation: jam-pulse 1.2s ease-in-out infinite; }
    .gate.jammed .gate-panel { background: #fca5a5; }
    .gate.closing { background: linear-gradient(180deg, #0ea5e9 0%, #0284c7 100%); opacity: 0.75; }
    .gate.closing .gate-panel { background: rgba(6, 182, 212, 0.4); }
    @keyframes jam-pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    .gate-legend {
        display: flex; gap: 20px; margin-top: 24px;
        font-size: 0.75rem; color: var(--text-muted); flex-wrap: wrap;
    }
    .legend-item {
        display: flex; align-items: center; gap: 6px;
        padding: 4px 10px; background: rgba(255,255,255,0.03);
        border-radius: 6px; border: 1px solid var(--border-color);
    }
    .legend-dot { width: 10px; height: 10px; border-radius: 2px; flex-shrink: 0; }

    /* ── Data Table ── */
    [data-testid="stDataFrame"] {
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        overflow: hidden !important;
        box-shadow: var(--shadow-md);
    }
    [data-testid="stDataFrame"] table {
        background: transparent !important;
    }
    [data-testid="stDataFrame"] th {
        background: rgba(59, 130, 246, 0.1) !important;
        color: var(--text-secondary) !important;
        font-weight: 600 !important;
        border-bottom: 1px solid var(--border-color) !important;
        font-size: 0.75rem !important;
        text-transform: uppercase; letter-spacing: 1.5px;
    }
    [data-testid="stDataFrame"] td {
        border-bottom: 1px solid rgba(30, 41, 59, 0.5) !important;
        color: var(--text-primary) !important;
        font-size: 0.875rem !important;
    }
    [data-testid="stDataFrame"] tr:hover {
        background: rgba(59, 130, 246, 0.05) !important;
    }

    /* ── Incident Table ── */
    .incident-row {
        background: linear-gradient(135deg, rgba(17, 24, 39, 0.9) 0%, rgba(15, 23, 42, 0.9) 100%);
        border: 1px solid var(--border-color);
        border-radius: 10px; padding: 16px 20px;
        margin-bottom: 10px; display: flex; gap: 16px; align-items: center;
        transition: var(--transition);
        box-shadow: var(--shadow-sm);
    }
    .incident-row:hover {
        transform: translateX(4px);
        border-color: var(--accent-blue);
        box-shadow: var(--shadow-md);
    }
    .incident-row.critical { border-left: 3px solid var(--danger); }
    .incident-row.warning { border-left: 3px solid var(--warning); }

    /* ── Team Cards ── */
    .team-grid {
        display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 20px;
    }
    .team-card {
        background: linear-gradient(135deg, rgba(17, 24, 39, 0.95) 0%, rgba(15, 23, 42, 0.95) 100%);
        backdrop-filter: blur(12px);
        border: 1px solid var(--border-color);
        border-radius: 14px; padding: 28px;
        display: flex; gap: 20px; align-items: flex-start;
        transition: var(--transition);
        box-shadow: var(--shadow-md);
        position: relative;
        overflow: hidden;
    }
    .team-card::after {
        content: '';
        position: absolute; top: 0; right: 0; width: 60px; height: 60px;
        background: radial-gradient(circle, rgba(59, 130, 246, 0.08) 0%, transparent 70%);
        border-radius: 50%;
        transform: translate(30%, -30%);
        pointer-events: none;
    }
    .team-card:hover {
        border-color: var(--accent-blue);
        transform: translateY(-4px);
        box-shadow: var(--shadow-lg), 0 0 32px rgba(59, 130, 246, 0.2);
    }
    .team-avatar img {
        width: 66px; height: 66px; border-radius: 12px;
        border: 2px solid var(--accent-blue); object-fit: cover;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4), 0 0 16px rgba(59, 130, 246, 0.2);
    }
    .team-role {
        color: var(--accent-blue); font-size: 0.75rem; font-weight: 600;
        margin: 2px 0 8px; text-transform: uppercase; letter-spacing: 1px;
    }
    .team-name { color: var(--text-primary); font-weight: 700; font-size: 1rem; margin-bottom: 6px; }
    .team-desc { color: var(--text-secondary); font-size: 0.875rem; line-height: 1.6; }

    /* ── Tech Stack Table ── */
    .tech-row {
        background: linear-gradient(135deg, rgba(17, 24, 39, 0.9) 0%, rgba(15, 23, 42, 0.9) 100%);
        border: 1px solid var(--border-color);
        border-radius: 10px; padding: 16px 20px; margin-bottom: 10px;
        display: grid; grid-template-columns: 100px 160px 1fr; gap: 16px;
        align-items: center;
        transition: var(--transition);
        box-shadow: var(--shadow-sm);
    }
    .tech-row:hover {
        border-color: var(--accent-cyan);
        box-shadow: var(--shadow-md);
        transform: translateX(4px);
    }
    .tech-layer {
        font-family: 'JetBrains Mono', monospace; font-size: 0.6875rem;
        color: var(--accent-cyan); text-transform: uppercase; letter-spacing: 1.5px;
        font-weight: 600;
    }
    .tech-name { font-weight: 700; color: var(--text-primary); font-size: 0.9375rem; }
    .tech-detail { color: var(--text-secondary); font-size: 0.875rem; }

    /* ── Info/Success Boxes ── */
    [data-testid="stInfo"], [data-testid="stSuccess"] {
        background: linear-gradient(135deg, rgba(17, 24, 39, 0.95) 0%, rgba(15, 23, 42, 0.95) 100%) !important;
        border-color: var(--accent-blue) !important;
        color: var(--text-primary) !important;
        border-radius: 10px !important;
        box-shadow: var(--shadow-md);
        padding: 16px 20px !important;
    }
    [data-testid="stSuccess"] {
        border-color: var(--success) !important;
    }

    /* ── Expander ── */
    [data-testid="stExpander"] {
        background: linear-gradient(135deg, rgba(17, 24, 39, 0.9) 0%, rgba(15, 23, 42, 0.9) 100%) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        overflow: hidden !important;
        box-shadow: var(--shadow-md);
        transition: var(--transition);
    }
    [data-testid="stExpander"]:hover {
        border-color: var(--accent-blue);
        box-shadow: var(--shadow-lg);
    }
    .streamlit-expanderHeader {
        font-weight: 600 !important; font-size: 1rem !important;
        color: var(--accent-cyan) !important;
        padding: 16px 20px !important;
        background: transparent !important;
    }
    .streamlit-expanderHeader:hover {
        background: rgba(59, 130, 246, 0.05) !important;
    }

    /* ── Plotly chart backgrounds ── */
    .js-plotly-plot .plotly .bg { fill: transparent !important; }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: var(--bg-primary); }
    ::-webkit-scrollbar-thumb { background: var(--border-glow); border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }

    /* ── Tabs ── */
    [data-testid="stTabs"] {
        border-bottom: 1px solid var(--border-color);
        padding-bottom: 8px;
    }
    [data-testid="stTab"] {
        color: var(--text-muted) !important;
        font-weight: 600 !important;
        padding: 8px 16px !important;
        border-radius: 8px 8px 0 0 !important;
        transition: var(--transition) !important;
        border: 1px solid transparent !important;
        border-bottom: none !important;
    }
    [data-testid="stTab"][aria-selected="true"] {
        background: var(--accent-blue) !important;
        color: white !important;
        border-color: var(--accent-blue) !important;
    }
    [data-testid="stTab"]:hover {
        color: var(--text-primary) !important;
        background: rgba(59, 130, 246, 0.1) !important;
    }

    /* ── Hide default streamlit chrome ── */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    [data-testid="stHeader"] { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; }
    [data-testid="stSidebarHeader"] { display: none !important; }

    /* ── Divider ── */
    .custom-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--border-color), transparent);
        margin: 32px 0;
        opacity: 0.7;
    }

    /* ── Responsive ── */
    @media (max-width: 768px) {
        .station-title { font-size: 1.5rem !important; }
        .metric-value { font-size: 1.75rem !important; }
        .section-heading { font-size: 1rem !important; }
        .metric-card { padding: 18px !important; }
        .main-header { padding: 20px 24px !important; }
    }

    /* ── Animation for page load ── */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    .animate-fade-in {
        animation: fadeInUp 0.6s ease-out forwards;
    }
    .animate-fade-in:nth-child(1) { animation-delay: 0.05s; }
    .animate-fade-in:nth-child(2) { animation-delay: 0.1s; }
    .animate-fade-in:nth-child(3) { animation-delay: 0.15s; }
    .animate-fade-in:nth-child(4) { animation-delay: 0.2s; }
    .animate-fade-in:nth-child(5) { animation-delay: 0.25s; }

    /* ── Loading spinner custom ── */
    .stSpinner > div {
        border-color: var(--accent-blue) !important;
    }

    /* ── Smooth scroll ── */
    html {
        scroll-behavior: smooth;
    }

    /* ── Form Elements ── */
    [data-testid="stNumberInput"] input,
    [data-testid="stSlider"] input {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
        transition: var(--transition);
    }
    [data-testid="stNumberInput"] input:focus,
    [data-testid="stSlider"] input:focus {
        border-color: var(--accent-blue) !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
    }
    [data-testid="stSlider"] [data-baseweb="slider"] {
        margin: 12px 0;
    }
    .stSlider [data-baseweb="range-face"] {
        background: var(--accent-blue) !important;
    }

    /* ── Radio buttons ── */
    [data-testid="stRadio"] [data-baseweb="radio"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
    }
    [data-testid="stRadio"] [data-baseweb="radio"][aria-checked="true"] {
        background: var(--accent-blue) !important;
        border-color: var(--accent-blue) !important;
    }

    /* ── Custom Container ── */
    .content-container {
        background: linear-gradient(135deg, rgba(17, 24, 39, 0.6) 0%, rgba(15, 23, 42, 0.6) 100%);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 24px;
        margin: 16px 0;
        box-shadow: var(--shadow-md);
    }
    .content-container:hover {
        border-color: var(--accent-blue);
    }

    /* ── Select boxes ── */
    [data-testid="stSelectbox"] > div > div {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
    }
    [data-testid="stSelectbox"] [aria-selected="true"] {
        background: var(--accent-blue) !important;
    }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════
# DATA LOADING WITH SESSION STATE CACHE
# ═══════════════════════════════════════════════════
# Use session state to persist transformed data across reruns
if 'transformed_df' not in st.session_state:
    with st.spinner("Loading and processing data..."):
        raw_df = load_data()
        st.session_state.transformed_df = transform_data(raw_df)
        st.session_state.data_load_time = datetime.now()

df = st.session_state.transformed_df
stations = sorted(df["station"].unique())

# ═══════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <div class="brand-title">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: #3b82f6;">
                <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                <path d="M2 17l10 5 10-5"/>
                <path d="M2 12l10 5 10-5"/>
            </svg>
            SicherGleis
        </div>
        <div class="brand-tagline">BahnSetu Pro</div>
        <div class="brand-badge">
            <span class="status-dot"></span> SYSTEM ONLINE
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Data refresh controls
    col_refresh, col_status = st.columns([1, 2])
    with col_refresh:
        if st.button("🔄", help="Refresh Data", key="refresh_btn"):
            # Clear caches and force reload
            st.cache_data.clear()
            if 'transformed_df' in st.session_state:
                del st.session_state.transformed_df
            st.rerun()
    with col_status:
        if 'data_load_time' in st.session_state:
            load_time = st.session_state.data_load_time
            time_str = load_time.strftime("%H:%M:%S")
            st.markdown(f"<small style='color:#4a6fa5;font-family:IBM Plex Mono'>Last: {time_str}</small>",
                       unsafe_allow_html=True)

    st.markdown('<div class="nav-label">Stations</div>',
                unsafe_allow_html=True)

    for s in stations:
        is_active = s == st.session_state.current_station
        if st.button(
            label=s,
            key=f"nav_{s}",
            type="secondary" if is_active else "primary",
            use_container_width=True
        ):
            st.session_state.current_station = s
            st.session_state.active_tab = 'ops'
            st.rerun()

    st.markdown('<div class="nav-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-label">Modules</div>', unsafe_allow_html=True)

    tabs = {
        'ops': '📡 Live Operations',
        'network': '🌐 Network Overview',
        'incidents': '🚨 Incident Log',
        'forecast': '📈 Predictive Analytics',
        'financial': '💹 Financial Model',
        'company': '🏢 Company & Team',
    }
    for key, label in tabs.items():
        is_active = st.session_state.active_tab == key
        if st.button(
            label=label,
            key=f"tab_{key}",
            type="secondary" if is_active else "primary",
            use_container_width=True
        ):
            st.session_state.active_tab = key
            st.rerun()

    st.markdown('<div class="nav-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-footer">⚡ Powered by German Precision & Indian Innovation<hr style="margin: 12px 0; border: none; border-top: 1px solid #1e293b; opacity: 0.3;">BahnSetu GmbH © 2025</div>',
                unsafe_allow_html=True)

# ═══════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════
current_station = st.session_state.current_station
gates_total, gates_active, p_total, alerts, avg_sync, warnings = get_metrics(
    df, current_station)
active_tab = st.session_state.active_tab

sys_status = "NORMAL" if alerts == 0 and warnings == 0 else (
    "ALERT" if alerts > 0 else "WARNING")
badge_cls = "status-normal" if sys_status == "NORMAL" else "status-alert"

# Dynamic header depending on active tab
if active_tab in ['ops', 'forecast', 'incidents']:
    display_title = current_station
    display_sub = f"PLATFORM SAFETY MONITOR // SURAKSHA PROTOCOL ACTIVE"
elif active_tab == 'network':
    display_title = "Network Overview"
    display_sub = "ALL STATIONS // LIVE STATUS"
elif active_tab == 'financial':
    display_title = "Financial Model"
    display_sub = "SAAS REVENUE SIMULATION // BAHNSETU FINANCIAL INTELLIGENCE"
else:
    display_title = "SicherGleis Pro"
    display_sub = "BAHNSETU COMPANY PROFILE"

st.markdown(f"""
<div class="main-header">
    <div>
        <div class="station-title">{display_title}</div>
        <div class="station-sub">{display_sub}</div>
    </div>
    <div class="status-badge {badge_cls}">
        <span class="status-dot"></span> {sys_status}
    </div>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════
# TRAIN ANIMATION HTML BUILDER
# ═══════════════════════════════════════════════════
@st.cache_data(ttl=60, show_spinner=False)
def build_train_animation(station_name, station_df):
    """Build a complete self-contained HTML/JS animation for the PSD platform simulation."""
    # Pre-compute platform data efficiently
    platforms_data = []
    station_df = station_df.copy()
    
    # Group by platform once
    grouped = station_df.groupby('platform')
    
    for platform, plat_df in sorted(grouped, key=lambda x: x[0]):
        gates = []
        # Use itertuples for faster iteration
        for row in plat_df.itertuples(index=False):
            gates.append({
                "id":     row.gate_id,
                "state":  row.door_state,
                "train":  str(row.train) if pd.notna(row.train) and row.train else "",
                "temp":   float(row.sensor_temp),
                "vib":    float(row.sensor_vib),
                "risk":   int(row.risk_score),
                "status": row.maintenance_status,
                "people": int(row.people),
            })
        train_name = next((g["train"] for g in gates if g["train"]),
                          f"ICE {abs(hash(platform)) % 900 + 100}")
        platforms_data.append({
            "platform":   platform,
            "gates":      gates,
            "train_name": train_name,
        })

    platforms_json = json.dumps(platforms_data)

    # Build the HTML with an embedded JS animation engine
    html = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Space+Grotesk:wght@400;600;700&display=swap');
*{box-sizing:border-box;margin:0;padding:0;}
body{background:#060c1a;color:#e2e8f0;font-family:'Space Grotesk',sans-serif;overflow-x:hidden;}

/* Banner */
.sta-banner{background:linear-gradient(90deg,#0d1b3e,#0a1628);border-bottom:1px solid #1e2d4d;padding:9px 18px;display:flex;justify-content:space-between;align-items:center;}
.sta-name{font-size:.82rem;font-weight:700;color:#7ab3d4;letter-spacing:1px;text-transform:uppercase;}
.live-dot{width:7px;height:7px;border-radius:50%;background:#10b981;display:inline-block;margin-right:5px;animation:lpulse 1.4s ease infinite;}
@keyframes lpulse{0%,100%{opacity:1;box-shadow:0 0 0 0 rgba(16,185,129,.6);}50%{opacity:.7;box-shadow:0 0 0 5px rgba(16,185,129,0);}}
.live-lbl{font-family:'IBM Plex Mono';font-size:.65rem;color:#10b981;}

/* Platform block */
.plat-block{margin:12px 14px;border:1px solid #1e2d4d;border-radius:11px;overflow:hidden;background:#0a1221;}
.plat-hdr{background:#0d1b3e;padding:7px 14px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #1e2d4d;}
.plat-lbl{font-family:'IBM Plex Mono';font-size:.72rem;font-weight:600;color:#4a6fa5;letter-spacing:1.5px;text-transform:uppercase;}
.plat-st{font-family:'IBM Plex Mono';font-size:.63rem;font-weight:600;padding:2px 9px;border-radius:20px;}
.st-ok{background:rgba(16,185,129,.12);border:1px solid rgba(16,185,129,.4);color:#10b981;}
.st-bad{background:rgba(239,68,68,.12);border:1px solid rgba(239,68,68,.4);color:#ef4444;animation:blink 1.2s ease infinite;}
@keyframes blink{0%,100%{opacity:1;}50%{opacity:.45;}}

/* Scene */
.scene{position:relative;height:195px;overflow:hidden;background:#060c1a;}
.scene-bg{position:absolute;inset:0;background:linear-gradient(180deg,#060c1a 0%,#0a1221 55%,#0d1b3e 100%);}

/* Stars */
.stars{position:absolute;top:0;left:0;right:0;height:60px;pointer-events:none;}

/* Buildings */
.bldgs{position:absolute;bottom:68px;left:0;right:0;height:55px;display:flex;align-items:flex-end;gap:2px;padding:0 8px;opacity:.15;}
.bldg{background:#4a6fa5;border-radius:2px 2px 0 0;flex-shrink:0;}

/* Platform floor */
.plat-floor{position:absolute;bottom:0;left:0;right:0;height:68px;background:linear-gradient(180deg,#0f1f40 0%,#0a1628 100%);border-top:2px solid #1e2d4d;}

/* Yellow edge strip */
.edge-strip{position:absolute;bottom:68px;left:0;right:0;height:4px;background:repeating-linear-gradient(90deg,#f59e0b 0px,#f59e0b 18px,transparent 18px,transparent 28px);opacity:.65;}

/* Track */
.track{position:absolute;bottom:38px;left:0;right:0;height:8px;}
.rail{position:absolute;left:0;right:0;height:3px;background:#1e3060;border-radius:2px;}
.rail.t{top:0;} .rail.b{bottom:0;}
.sleeper{position:absolute;bottom:-2px;width:13px;height:8px;background:#162040;border-radius:1px;}

/* TRAIN */
.train-wrap{position:absolute;bottom:40px;left:0;will-change:transform;display:flex;align-items:flex-end;z-index:10;filter:drop-shadow(0 4px 18px rgba(0,40,120,.8));}
.t-car{position:relative;display:flex;flex-direction:column;align-items:center;}
.car-body{background:linear-gradient(180deg,#cce4ff 0%,#a0ccff 28%,#1565c0 29%,#0d47a1 68%,#0a3688 100%);border-radius:5px 5px 0 0;position:relative;overflow:hidden;}
.car-body::after{content:'';position:absolute;top:0;left:0;right:0;height:5px;background:linear-gradient(90deg,#0288d1,#00b4d8,#0288d1);}
.car-stripe{position:absolute;top:14px;left:0;right:0;height:3px;background:#ef4444;}
.car-wins{position:absolute;top:20px;left:7px;right:7px;display:flex;gap:4px;}
.win{flex:1;height:16px;background:#b3d9ff;border-radius:2px;border:1px solid #7ab3d4;position:relative;overflow:hidden;transition:background .4s;}
.win.lit{background:#fff9c4;border-color:#f0c040;}
.win::after{content:'';position:absolute;top:0;left:30%;width:20%;height:100%;background:rgba(255,255,255,.3);}
.pax-sil{position:absolute;bottom:1px;left:50%;transform:translateX(-50%);width:5px;height:9px;background:rgba(20,50,110,.75);border-radius:3px 3px 0 0;opacity:0;transition:opacity .35s;}
/* Bogies */
.bogie{position:absolute;bottom:-7px;background:#1a2040;border-radius:3px;height:9px;}
.bg-l{left:11px;width:17px;} .bg-r{right:11px;width:17px;}
.wheel{position:absolute;bottom:-5px;width:11px;height:11px;background:radial-gradient(circle,#4a6fa5 28%,#1e3060 100%);border-radius:50%;border:2px solid #0a1628;}
.wl{left:0;} .wr{right:0;}
.wspin{animation:wspin .28s linear infinite;}
.wslow{animation:wspin 1.1s linear infinite;}
@keyframes wspin{from{transform:rotate(0deg);}to{transform:rotate(360deg);}}
/* Pantograph */
.panto{position:absolute;top:-15px;left:50%;transform:translateX(-50%);width:28px;height:15px;}
.pa{position:absolute;background:#4a6fa5;transform-origin:bottom center;width:2px;}
.pa1{bottom:0;left:50%;height:7px;transform:translateX(-50%) rotate(-18deg);}
.pa2{bottom:6px;left:48%;height:7px;transform:translateX(-50%) rotate(18deg);}
.pa-head{top:0;left:18%;width:64%;height:2px;background:#7ab3d4;border-radius:1px;position:absolute;}
/* Headlights */
.hl{position:absolute;bottom:16px;width:9px;height:5px;border-radius:1px;transition:opacity .4s,box-shadow .4s;}
.hl-f{right:3px;background:#fff9c4;box-shadow:0 0 10px 3px rgba(255,249,196,.6);}
.hl-r{left:3px;background:#ef4444;box-shadow:0 0 7px 2px rgba(239,68,68,.5);opacity:0;}
/* Coupling */
.coupling{width:5px;height:7px;background:#1e3060;border:1px solid #2d4f8a;border-radius:1px;margin-bottom:13px;flex-shrink:0;align-self:flex-end;}

/* Speed lines */
.splines{position:absolute;inset:0;pointer-events:none;z-index:5;overflow:hidden;opacity:0;transition:opacity .25s;}
.sl{position:absolute;height:1px;background:linear-gradient(90deg,transparent,rgba(100,160,255,.28),transparent);border-radius:1px;}

/* Sparks */
.spark{position:absolute;width:3px;height:3px;background:#fff9c4;border-radius:50%;opacity:0;pointer-events:none;z-index:30;}

/* PSD */
.psd-layer{position:absolute;bottom:68px;left:0;right:0;height:108px;display:flex;z-index:20;pointer-events:none;}
.psd-unit{flex:1;position:relative;display:flex;align-items:flex-end;}
.door-l,.door-r{position:absolute;bottom:0;height:88px;width:50%;border-radius:3px 3px 0 0;transition:width .65s cubic-bezier(.4,0,.2,1);overflow:hidden;}
.door-l{left:0;background:linear-gradient(180deg,#1565c0cc,#0d47a1cc);border:1px solid #2d4f8a;border-radius:3px 0 0 0;}
.door-r{right:0;background:linear-gradient(180deg,#1565c0cc,#0d47a1cc);border:1px solid #2d4f8a;border-radius:0 3px 0 0;}
.door-l.open,.door-r.open{width:4%!important;}
.door-l.jammed,.door-r.jammed{background:linear-gradient(180deg,#b91c1ccc,#7f1d1dcc)!important;border-color:#ef4444!important;animation:jshake .12s ease infinite alternate;}
@keyframes jshake{from{transform:translateX(-1px);}to{transform:translateX(1px);}}
.d-glass{position:absolute;top:9px;left:14%;width:72%;height:52%;background:rgba(170,215,255,.07);border-radius:2px;border:1px solid rgba(120,180,240,.18);}
.d-glass::after{content:'';position:absolute;top:0;left:18%;width:14%;height:100%;background:rgba(255,255,255,.1);}
.d-led{position:absolute;top:0;left:0;right:0;height:3px;border-radius:2px;}
.led-cl{background:#1565c0;box-shadow:0 0 5px #1565c0;}
.led-op{background:#10b981;box-shadow:0 0 7px #10b981;}
.led-jm{background:#ef4444;box-shadow:0 0 9px #ef4444;animation:blink .45s ease infinite;}
.psd-col{position:absolute;bottom:0;left:50%;transform:translateX(-50%);width:5px;height:93px;background:#0f2050;border:1px solid #1e2d4d;border-radius:2px 2px 0 0;}
.g-id{position:absolute;bottom:-15px;left:50%;transform:translateX(-50%);font-family:'IBM Plex Mono';font-size:.55rem;color:#2d4f8a;white-space:nowrap;}

/* Passengers walking */
.pax-layer{position:absolute;bottom:68px;left:0;right:0;height:48px;z-index:15;pointer-events:none;overflow:hidden;}
.pax{position:absolute;bottom:0;width:7px;height:17px;will-change:transform,opacity;}
.pax-h{width:7px;height:7px;background:#f0c090;border-radius:50%;position:absolute;top:0;}
.pax-b{width:5px;height:10px;position:absolute;top:7px;left:1px;border-radius:2px;}

/* Status bar */
.sbar{padding:7px 14px 8px;display:flex;gap:16px;align-items:center;background:#0a1221;border-top:1px solid #1e2d4d;flex-wrap:wrap;}
.si{font-family:'IBM Plex Mono';font-size:.65rem;color:#4a6fa5;display:flex;align-items:center;gap:4px;}
.sv{color:#7ab3d4;font-weight:600;}
.ph-lbl{font-family:'IBM Plex Mono';font-size:.68rem;padding:2px 9px;border-radius:20px;background:rgba(0,180,216,.1);border:1px solid rgba(0,180,216,.3);color:#00b4d8;transition:all .4s;}

/* Legend */
.leg-bar{padding:5px 14px 8px;display:flex;gap:14px;flex-wrap:wrap;background:#060c1a;}
.li{display:flex;align-items:center;gap:4px;font-size:.67rem;color:#4a6fa5;font-family:'IBM Plex Mono';}
.ld{width:9px;height:9px;border-radius:2px;flex-shrink:0;}
</style>
</head>
<body>
<div class="sta-banner">
  <span class="sta-name">""" + station_name + """</span>
  <span><span class="live-dot"></span><span class="live-lbl">LIVE SIM</span></span>
</div>
<div id="root"></div>

<script>
const PLATFORMS = """ + platforms_json + """;

// ── Easing ───────────────────────────────────────
const lerp=(a,b,t)=>a+(b-a)*t;
const clamp=(v,lo,hi)=>Math.max(lo,Math.min(hi,v));
const easeOut=t=>1-Math.pow(1-t,3);
const easeIn=t=>t*t*t;
const easeInOut=t=>t<.5?2*t*t:-1+(4-2*t)*t;

const PHASES={APPROACH:4400,BRAKE:1100,STOP:380,DOOR_OPEN:850,BOARD:3800,DOOR_CLOSE:850,WAIT:550,DEPART:3400,EMPTY:1700};

const TNAMES=["ICE 574","S7","RE 3312","ICE 891","ICE 102","RE 5","ICE 700","RE 220","ICE 11","RE 40","ICE 921","S12","S-Bahn 3","ICE 202","RE 90","ICE 77","S11","ICE 19"];
const PAX_SKINS=["#e07850","#c06840","#d09070","#b08060","#f0c090","#a07060"];
const PAX_SHIRTS=["#1565c0","#0d47a1","#10b981","#374151","#6d28d9","#b91c1c"];

function randTrain(seed){ return TNAMES[seed%TNAMES.length]; }

// ── Build platform DOM ───────────────────────────
function buildPlatform(pdata,idx){
  const isOk=!pdata.gates.some(g=>g.status==='CRITICAL');
  const div=document.createElement('div');
  div.className='plat-block';
  div.id='pb'+idx;
  div.innerHTML=`
    <div class="plat-hdr">
      <span class="plat-lbl">Platform ${pdata.platform}</span>
      <span class="plat-st ${isOk?'st-ok':'st-bad'}">${isOk?'✓ OPERATIONAL':'⚠ MAINTENANCE REQ'}</span>
    </div>
    <div class="scene" id="sc${idx}">
      <div class="scene-bg"></div>
      <div class="stars" id="st${idx}"></div>
      <div class="bldgs" id="bg${idx}"></div>
      <div class="plat-floor"></div>
      <div class="edge-strip"></div>
      <div class="track" id="tr${idx}"></div>
      <div class="splines" id="sp${idx}"></div>
      <div id="sk${idx}"></div>
      <div class="train-wrap" id="tw${idx}"></div>
      <div class="psd-layer" id="psd${idx}"></div>
      <div class="pax-layer" id="px${idx}"></div>
    </div>
    <div class="sbar">
      <span class="ph-lbl" id="ph${idx}">INIT</span>
      <span class="si">TRAIN <span class="sv" id="tn${idx}">—</span></span>
      <span class="si">TEMP <span class="sv" id="tp${idx}">—</span></span>
      <span class="si">SYNC <span class="sv" id="sy${idx}">—</span></span>
      <span class="si">PAX <span class="sv" id="pa${idx}">—</span></span>
    </div>
    <div class="leg-bar">
      <div class="li"><div class="ld" style="background:#1565c0"></div>Closed</div>
      <div class="li"><div class="ld" style="background:#10b981"></div>Open / Boarding</div>
      <div class="li"><div class="ld" style="background:#ef4444"></div>Jammed (Alert)</div>
      <div class="li"><div class="ld" style="background:#0288d1"></div>Closing</div>
    </div>`;
  return div;
}

function buildStars(idx){
  const c=document.getElementById('st'+idx);
  if(!c)return;
  for(let i=0;i<30;i++){
    const s=document.createElement('div');
    s.style.cssText=`position:absolute;width:${Math.random()>0.7?2:1}px;height:${Math.random()>0.7?2:1}px;border-radius:50%;background:rgba(180,220,255,${0.1+Math.random()*.4});top:${Math.random()*95}%;left:${Math.random()*100}%`;
    c.appendChild(s);
  }
}

function buildBuildings(idx){
  const b=document.getElementById('bg'+idx);
  if(!b)return;
  [42,28,52,22,38,58,32,46,25,50,36].forEach((h,i)=>{
    const d=document.createElement('div');
    d.className='bldg';
    d.style.height=h+'px';
    d.style.width=[20,16,24,14,18,26,15,21,13,23,17][i]+'px';
    b.appendChild(d);
  });
}

function buildTrack(idx){
  const t=document.getElementById('tr'+idx);
  if(!t)return;
  t.innerHTML='<div class="rail t"></div><div class="rail b"></div>';
  const w=t.parentElement.offsetWidth||800;
  for(let x=0;x<w;x+=26){
    const s=document.createElement('div');
    s.className='sleeper';
    s.style.left=x+'px';
    t.appendChild(s);
  }
}

function buildSpeedLines(idx){
  const sp=document.getElementById('sp'+idx);
  if(!sp)return;
  sp.innerHTML='';
  for(let i=0;i<14;i++){
    const l=document.createElement('div');
    l.className='sl';
    l.style.top=(16+i*9)+'px';
    l.style.opacity=(.25+Math.random()*.4).toString();
    sp.appendChild(l);
  }
}

function buildTrain(numCars,idx){
  let h='';
  for(let c=0;c<numCars;c++){
    const loco=c===0;
    const cw=loco?118:98, ch=loco?53:48;
    const nw=loco?3:4;
    const wins=Array.from({length:nw},(_,i)=>
      `<div class="win${Math.random()>.35?' lit':''}" id="w${c}_${i}_${idx}"><div class="pax-sil" id="ps${c}_${i}_${idx}"></div></div>`
    ).join('');
    h+=`${c>0?'<div class="coupling"></div>':''}
    <div class="t-car" style="width:${cw}px">
      ${loco?'<div class="panto"><div class="pa pa1"></div><div class="pa pa2"></div><div class="pa-head"></div></div>':''}
      <div class="car-body" style="width:${cw}px;height:${ch}px">
        <div class="car-stripe"></div>
        <div class="car-wins">${wins}</div>
        ${loco?`<div class="hl hl-f" id="hlf${idx}"></div>`:''}
        ${c===numCars-1?`<div class="hl hl-r" id="hlr${idx}"></div>`:''}
        <div class="bogie bg-l"><div class="wheel wl" id="wl${c}a${idx}"></div><div class="wheel wr" id="wr${c}a${idx}"></div></div>
        <div class="bogie bg-r"><div class="wheel wl" id="wl${c}b${idx}"></div><div class="wheel wr" id="wr${c}b${idx}"></div></div>
      </div>
    </div>`;
  }
  return h;
}

function buildPSD(idx,gates){
  const psd=document.getElementById('psd'+idx);
  if(!psd)return;
  psd.innerHTML='';
  gates.forEach((g,gi)=>{
    const unit=document.createElement('div');
    unit.className='psd-unit';
    const jm=g.status==='CRITICAL';
    const jcls=jm?' jammed':'';
    const led=jm?'led-jm':'led-cl';
    unit.innerHTML=`
      <div class="door-l${jcls}" id="dl${idx}_${gi}"><div class="d-glass"></div><div class="d-led ${led}" id="dll${idx}_${gi}"></div></div>
      <div class="door-r${jcls}" id="dr${idx}_${gi}"><div class="d-glass"></div><div class="d-led ${led}" id="drl${idx}_${gi}"></div></div>
      <div class="psd-col"></div>
      <div class="g-id">${g.id}</div>`;
    psd.appendChild(unit);
  });
}

function setGate(idx,gi,open,jammed){
  const dl=document.getElementById(`dl${idx}_${gi}`);
  const dr=document.getElementById(`dr${idx}_${gi}`);
  const dll=document.getElementById(`dll${idx}_${gi}`);
  const drl=document.getElementById(`drl${idx}_${gi}`);
  if(!dl)return;
  if(jammed){
    dl.className='door-l jammed'; dr.className='door-r jammed';
    dll.className='d-led led-jm'; drl.className='d-led led-jm';
    return;
  }
  const oc=open?' open':'';
  dl.className=`door-l${oc}`; dr.className=`door-r${oc}`;
  const lc=open?'led-op':'led-cl';
  dll.className=`d-led ${lc}`; drl.className=`d-led ${lc}`;
}

function emitSparks(idx,x,y){
  const c=document.getElementById('sk'+idx);
  if(!c)return;
  for(let i=0;i<4;i++){
    const s=document.createElement('div');
    s.className='spark';
    s.style.left=(x+Math.random()*12-6)+'px';
    s.style.top=(y+Math.random()*7-3)+'px';
    c.appendChild(s);
    let t=0;
    const iv=setInterval(()=>{
      t+=45;
      s.style.opacity=(1-t/380).toString();
      s.style.transform=`translate(${Math.random()*7-3}px,${-t*.06}px)`;
      if(t>=380){clearInterval(iv);s.remove();}
    },45);
  }
}

function spawnPax(idx,dir,x){
  const layer=document.getElementById('px'+idx);
  if(!layer)return null;
  const fig=document.createElement('div');
  fig.className='pax';
  fig.style.left=x+'px';
  fig.style.opacity='0';
  const skin=PAX_SKINS[Math.floor(Math.random()*PAX_SKINS.length)];
  const shirt=PAX_SHIRTS[Math.floor(Math.random()*PAX_SHIRTS.length)];
  const fl=dir<0?'scaleX(-1)':'';
  fig.innerHTML=`<div class="pax-h" style="background:${skin};transform:${fl}"></div><div class="pax-b" style="background:${shirt};transform:${fl}"></div>`;
  layer.appendChild(fig);
  return fig;
}

function setWheels(idx,numCars,speed){
  for(let c=0;c<numCars;c++){
    ['wl','wr'].forEach(p=>{
      ['a','b'].forEach(s=>{
        const w=document.getElementById(`${p}${c}${s}${idx}`);
        if(w) w.className='wheel '+(p==='wl'?'wl':'wr')+(speed==='fast'?' wspin':speed==='slow'?' wslow':'');
      });
    });
  }
}

// ── Main animation loop ──────────────────────────
function animatePlatform(idx,gates,initTrain){
  const sceneEl=document.getElementById('sc'+idx);
  const trainEl=document.getElementById('tw'+idx);
  const splEl  =document.getElementById('sp'+idx);
  const phEl   =document.getElementById('ph'+idx);
  const tnEl   =document.getElementById('tn'+idx);
  const tpEl   =document.getElementById('tp'+idx);
  const syEl   =document.getElementById('sy'+idx);
  const paEl   =document.getElementById('pa'+idx);
  if(!sceneEl||!trainEl)return;

  const W=sceneEl.offsetWidth||800;
  const numCars=Math.min(4,Math.max(2,Math.floor(W/128)));
  trainEl.innerHTML=buildTrain(numCars,idx);
  const trainW=numCars*104+12;
  const PARK=Math.floor((W-trainW)/2)-18;
  const ENTER=W+50, EXIT=-trainW-70;

  let cycle=0;
  const avgTemp=gates.reduce((s,g)=>s+g.temp,0)/gates.length;
  const avgVib =gates.reduce((s,g)=>s+g.vib, 0)/gates.length;
  const avgSync=Math.round(100-(avgTemp-25)*.5-avgVib*2);
  const totalPax=gates.reduce((s,g)=>s+g.people,0);

  function status(phase,tname,temp,sync,pax){
    if(phEl) phEl.textContent=phase;
    if(tnEl) tnEl.textContent=tname||'—';
    if(tpEl) tpEl.textContent=temp!=null?temp.toFixed(1)+'°C':'—';
    if(syEl) syEl.textContent=sync!=null?sync+'%':'—';
    if(paEl) paEl.textContent=pax!=null?pax.toString():'—';
  }

  function runCycle(){
    const tname=cycle===0&&initTrain?initTrain:randTrain((idx*7+cycle*3)%TNAMES.length);
    cycle++;
    trainEl.style.transform=`translateX(${ENTER}px)`;
    gates.forEach((_,gi)=>setGate(idx,gi,false,gates[gi].status==='CRITICAL'));
    setWheels(idx,numCars,'fast');
    if(splEl)splEl.style.opacity='1';
    status('APPROACHING',tname,null,null,null);

    // Headlight on
    const hlf=document.getElementById('hlf'+idx);
    if(hlf)hlf.style.opacity='1';

    let tx=ENTER;
    const phaseDefs=[
      // 0: APPROACH
      {dur:PHASES.APPROACH,fn(p){
        tx=lerp(ENTER,PARK+65,easeOut(p));
        trainEl.style.transform=`translateX(${tx}px)`;
        if(Math.random()<.025)emitSparks(idx,tx+18,26);
        status('APPROACHING',tname,null,null,null);
      }},
      // 1: BRAKE
      {dur:PHASES.BRAKE,fn(p){
        tx=lerp(PARK+65,PARK,easeIn(1-p+p*p));
        tx=lerp(PARK+65,PARK,p);
        trainEl.style.transform=`translateX(${tx}px)`;
        if(splEl)splEl.style.opacity=(1-p).toString();
        setWheels(idx,numCars,p>.5?'slow':'');
        status('BRAKING',tname,avgTemp,avgSync,null);
      }},
      // 2: STOP
      {dur:PHASES.STOP,fn(p){
        trainEl.style.transform=`translateX(${PARK}px)`;
        setWheels(idx,numCars,'');
        if(splEl)splEl.style.opacity='0';
        status('STOPPED',tname,avgTemp,avgSync,null);
      }},
      // 3: DOOR OPEN
      {dur:PHASES.DOOR_OPEN,fn(p){
        if(p>.45)gates.forEach((_,gi)=>setGate(idx,gi,true,gates[gi].status==='CRITICAL'));
        status('DOORS OPENING',tname,avgTemp,avgSync,null);
      }},
      // 4: BOARDING
      {dur:PHASES.BOARD,fn(p){
        status('BOARDING',tname,avgTemp,avgSync,Math.round(totalPax*(.45+p*.55)));
        // Animate window silhouettes
        if(p>.25&&p<.82){
          trainEl.querySelectorAll('.pax-sil').forEach(s=>{
            s.style.opacity=Math.random()>.38?'0.85':'0';
          });
        }
        // Walking passengers
        if(Math.random()<.038){
          const dir=Math.random()>.5?1:-1;
          const sx=dir>0?-12:W+12;
          const fig=spawnPax(idx,dir,sx);
          if(fig){
            fig.style.opacity='1';
            let px=sx;
            const spd=1.4+Math.random();
            const dest=PARK+20+Math.random()*trainW*.85;
            const mv=setInterval(()=>{
              px+=dir*spd;
              fig.style.left=px+'px';
              if((dir>0&&px>dest)||(dir<0&&px<dest)){
                fig.style.opacity='0';
                setTimeout(()=>fig.remove(),280);
                clearInterval(mv);
              }
            },16);
          }
        }
      }},
      // 5: DOOR CLOSE
      {dur:PHASES.DOOR_CLOSE,fn(p){
        if(p>.28)gates.forEach((_,gi)=>setGate(idx,gi,false,gates[gi].status==='CRITICAL'));
        trainEl.querySelectorAll('.pax-sil').forEach(s=>s.style.opacity='0');
        status('DOORS CLOSING',tname,avgTemp,avgSync,totalPax);
      }},
      // 6: DEPART WAIT
      {dur:PHASES.WAIT,fn(p){
        status('DEPARTURE READY',tname,avgTemp,avgSync,totalPax);
        setWheels(idx,numCars,'slow');
      }},
      // 7: DEPART
      {dur:PHASES.DEPART,fn(p){
        const t=easeIn(p);
        tx=lerp(PARK,EXIT,t);
        trainEl.style.transform=`translateX(${tx}px)`;
        setWheels(idx,numCars,p>.25?'fast':'slow');
        if(splEl)splEl.style.opacity=(p>.45?p:'0').toString();
        if(Math.random()<.035)emitSparks(idx,tx+trainW-18,26);
        // Switch headlight to rear light
        if(p>.5){
          if(hlf)hlf.style.opacity='0';
          const hlr=document.getElementById('hlr'+idx);
          if(hlr)hlr.style.opacity='1';
        }
        status('DEPARTING',tname,null,null,null);
      }},
      // 8: EMPTY
      {dur:PHASES.EMPTY,fn(p){
        setWheels(idx,numCars,'');
        if(splEl)splEl.style.opacity='0';
        const hlr=document.getElementById('hlr'+idx);
        if(hlr)hlr.style.opacity='0';
        if(hlf)hlf.style.opacity='0';
        const pxL=document.getElementById('px'+idx);
        if(pxL)pxL.innerHTML='';
        status('PLATFORM CLEAR','—',null,null,null);
        // Reset gate indicators for next train
        gates.forEach((_,gi)=>setGate(idx,gi,false,gates[gi].status==='CRITICAL'));
      }},
    ];

    let pi=0, ps=performance.now();
    function tick(now){
      if(pi>=phaseDefs.length){runCycle();return;}
      const ph=phaseDefs[pi];
      const el=now-ps;
      ph.fn(clamp(el/ph.dur,0,1));
      if(el>=ph.dur){pi++;ps=now;}
      requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }
  runCycle();
}

// ── Boot ────────────────────────────────────────
const root=document.getElementById('root');
PLATFORMS.forEach((pdata,idx)=>{
  const block=buildPlatform(pdata,idx);
  root.appendChild(block);
  requestAnimationFrame(()=>requestAnimationFrame(()=>{
    buildStars(idx);
    buildBuildings(idx);
    buildTrack(idx);
    buildSpeedLines(idx);
    buildPSD(idx,pdata.gates);
    setTimeout(()=>animatePlatform(idx,pdata.gates,pdata.train_name),idx*2100);
  }));
});
</script>
</body>
</html>"""
    return html


# ═══════════════════════════════════════════════════
# ── TAB: LIVE OPERATIONS ──────────────────────────
# ═══════════════════════════════════════════════════
if active_tab == 'ops':

    # ── KPI Row ──
    st.markdown('<div class="animate-fade-in">', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    kpis = [
        (c1, "PSD Gates", f"{gates_active}/{gates_total}",
         "Active Systems", ""),
        (c2, "Sync Efficiency",
         f"{avg_sync}%", "Door Alignment", "green" if avg_sync >= 85 else "warn"),
        (c3, "Passenger Flow", f"{p_total:,}", "On Platform", ""),
        (c4, "Critical Alerts", str(alerts), "Immediate Action",
         "alert" if alerts > 0 else "green"),
        (c5, "Warnings", str(warnings), "Under Observation",
         "warn" if warnings > 0 else "green"),
    ]
    for col, title, val, sub, cls in kpis:
        with col:
            st.markdown(f"""
            <div class="metric-card {cls}">
                <div class="metric-title">{title}</div>
                <div class="metric-value">{val}</div>
                <div class="metric-sub">{sub}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

    # ── Main Split ──
    left, right = st.columns([3, 2])

    with left:
        st.markdown('<div class="section-heading animate-fade-in">🚆 Live Platform Simulation</div>',
                    unsafe_allow_html=True)

        # Use cached station data
        station_data = get_station_data_cached(current_station, df)
        num_platforms = station_data['platform'].nunique()
        anim_html = build_train_animation(current_station, station_data)
        anim_height = num_platforms * 295 + 60
        components.html(anim_html, height=anim_height, scrolling=False)

    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

    with right:
        st.markdown(
            '<div class="section-heading animate-fade-in">Sensor Analytics</div>', unsafe_allow_html=True)
        cycles_df, temp_df = get_psd_analytics_cached(current_station)

        # Temperature Chart
        fig_temp = go.Figure()
        fig_temp.add_trace(go.Scatter(
            x=temp_df["Hour"], y=temp_df["Avg Temp (°C)"],
            mode='lines+markers',
            line=dict(color='#ef4444', width=2.5, shape='spline'),
            marker=dict(size=5, color='#ef4444'),
            fill='tozeroy',
            fillcolor='rgba(239,68,68,0.06)',
            name="Temp (°C)"
        ))
        fig_temp.add_hline(y=45, line_dash="dot", line_color="#f97316",
                           annotation_text="Warning Threshold", annotation_font_color="#f97316")
        fig_temp.update_layout(
            title=dict(text="Gate Temperature (°C)",
                       font=dict(size=13, color="#94a3b8", family="Inter"), x=0),
            height=250, margin=dict(l=0, r=0, b=40, t=50),
            paper_bgcolor='rgba(10, 14, 23, 0)',
            plot_bgcolor='rgba(10, 14, 23, 0)',
            font=dict(color="#64748b", family="Inter", size=11),
            yaxis=dict(
                gridcolor='rgba(30, 41, 59, 0.6)',
                zeroline=False,
                tickfont=dict(size=10, color="#94a3b8")
            ),
            xaxis=dict(
                gridcolor='rgba(30, 41, 59, 0.6)',
                tickfont=dict(size=10, color="#94a3b8")
            ),
            showlegend=False,
            hovermode='x unified',
            hoverlabel=dict(
                bgcolor='rgba(17, 24, 39, 0.95)',
                bordercolor='#3b82f6',
                font_color='#f1f5f9',
                font_size=11
            )
        )
        st.plotly_chart(fig_temp, use_container_width=True)

        # Door Cycles Chart
        fig_cycles = px.bar(cycles_df, x="Hour", y="Door Cycles",
                            title="Door Operation Cycles / Hour")
        fig_cycles.update_traces(
            marker_color='#3b82f6',
            marker_line_width=0,
            hovertemplate='<b>Hour</b>: %{x}<br><b>Cycles</b>: %{y}<extra></extra>'
        )
        fig_cycles.update_layout(
            height=250, margin=dict(l=0, r=0, b=40, t=50),
            paper_bgcolor='rgba(10, 14, 23, 0)',
            plot_bgcolor='rgba(10, 14, 23, 0)',
            font=dict(color="#64748b", family="Inter", size=11),
            title=dict(font=dict(size=13, color="#94a3b8", family="Inter"), x=0),
            yaxis=dict(
                gridcolor='rgba(30, 41, 59, 0.6)',
                zeroline=False,
                tickfont=dict(size=10, color="#94a3b8")
            ),
            xaxis=dict(
                gridcolor='rgba(30, 41, 59, 0.6)',
                tickfont=dict(size=10, color="#94a3b8")
            ),
            hovermode='x unified',
            hoverlabel=dict(
                bgcolor='rgba(17, 24, 39, 0.95)',
                bordercolor='#3b82f6',
                font_color='#f1f5f9',
                font_size=11
            )
        )
        st.plotly_chart(fig_cycles, use_container_width=True)

    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

    # ── Sensor Logs ──
    st.markdown('<div class="section-heading animate-fade-in">Detailed Sensor Logs</div>',
                unsafe_allow_html=True)

    def color_temp(val):
        """Color-code temperature cells without matplotlib."""
        if val > 45:
            return 'background-color: #7f1d1d; color: #fca5a5; font-weight:700'
        elif val > 35:
            return 'background-color: #78350f; color: #fcd34d; font-weight:600'
        elif val > 28:
            return 'background-color: #1c3a1c; color: #86efac'
        return ''

    def color_risk(val):
        """Color-code risk score cells without matplotlib."""
        if val >= 70:
            return 'background-color: #7f1d1d; color: #fca5a5; font-weight:700'
        elif val >= 40:
            return 'background-color: #78350f; color: #fcd34d; font-weight:600'
        elif val >= 20:
            return 'background-color: #1c3a1c; color: #86efac'
        return ''

    def color_status(val):
        """Color-code maintenance status cells."""
        colors = {
            'CRITICAL': 'color: #ef4444; font-weight:700',
            'WARNING':  'color: #f59e0b; font-weight:600',
            'MONITOR':  'color: #60a5fa',
            'OPTIMAL':  'color: #10b981',
        }
        return colors.get(val, '')

    display_cols = ['platform', 'gate_id', 'train', 'door_state',
                    'sensor_temp', 'sensor_vib', 'sync_score',
                    'risk_score', 'maintenance_status', 'people']
    styled = (
        station_data[display_cols]
        .sort_values(['platform', 'gate_id'])
        .style
        .map(color_temp,   subset=['sensor_temp'])
        .map(color_risk,   subset=['risk_score'])
        .map(color_status, subset=['maintenance_status'])
        .format({
            'sensor_temp': "{:.1f}°C",
            'sensor_vib':  "{:.2f} mm/s",
            'sync_score':  "{}%",
            'risk_score':  "{}/100",
        })
    )
    st.dataframe(styled, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════
# ── TAB: NETWORK OVERVIEW ─────────────────────────
# ═══════════════════════════════════════════════════
elif active_tab == 'network':
    net = get_network_summary_cached(df)

    # ── Network KPIs ──
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-title">Network Gates</div>
            <div class="metric-value">{net['total_gates']}</div>
            <div class="metric-sub">Across {len(stations)} Stations</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-card green">
            <div class="metric-title">Optimal Gates</div>
            <div class="metric-value">{net['optimal_count']}</div>
            <div class="metric-sub">Running Normally</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="metric-card alert">
            <div class="metric-title">Network Alerts</div>
            <div class="metric-value">{net['critical_count']}</div>
            <div class="metric-sub">Critical Incidents</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-title">Total Passengers</div>
            <div class="metric-value">{net['total_people']:,}</div>
            <div class="metric-sub">On All Platforms</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    left, right = st.columns([3, 2])

    with left:
        st.markdown(
            '<div class="section-heading">Station Performance Matrix</div>', unsafe_allow_html=True)
        styled_net = (
            net['station_summary']
            .style
            .background_gradient(subset=['Avg Sync %'], cmap='Blues', vmin=0, vmax=100)
            .background_gradient(subset=['Avg Risk'], cmap='RdYlGn_r', vmin=0, vmax=100)
            .format({'Avg Sync %': "{}%", 'Avg Risk': "{:.1f}/100", 'Passengers': "{:,}"})
        )
        st.dataframe(styled_net, use_container_width=True, hide_index=True)

        st.markdown(
            '<div class="section-heading">Passengers by Station</div>', unsafe_allow_html=True)
        fig_pass = px.bar(
            net['station_summary'].sort_values('Passengers', ascending=True),
            x='Passengers', y='Station', orientation='h',
            color='Avg Risk',
            color_continuous_scale=['#10b981', '#f59e0b', '#ef4444'],
            range_color=[0, 100],
            title=""
        )
        fig_pass.update_layout(
            height=300,
            margin=dict(l=0, r=0, b=20, t=20),
            paper_bgcolor='rgba(10, 14, 23, 0)',
            plot_bgcolor='rgba(10, 14, 23, 0)',
            font=dict(color="#94a3b8", family="Inter", size=11),
            yaxis=dict(
                gridcolor='rgba(30, 41, 59, 0.5)',
                tickfont=dict(size=10)
            ),
            xaxis=dict(
                gridcolor='rgba(30, 41, 59, 0.5)',
                tickfont=dict(size=10)
            ),
            coloraxis_colorbar=dict(
                title=dict(
                    text="Risk Score",
                    font=dict(color="#94a3b8", size=11)
                ),
                tickfont=dict(color="#94a3b8", size=10),
                thickness=8,
                len=0.8
            ),
            hovermode='y unified',
            hoverlabel=dict(
                bgcolor='rgba(17, 24, 39, 0.95)',
                bordercolor='#3b82f6',
                font_color='#f1f5f9',
                font_size=11
            )
        )
        fig_pass.update_traces(
            hovertemplate='<b>Station</b>: %{y}<br><b>Passengers</b>: %{x:,}<br><b>Avg Risk</b>: %{customdata[0]:.1f}/100<extra></extra>',
            customdata=net['station_summary'][['Avg Risk']].values
        )

        st.plotly_chart(fig_pass, use_container_width=True)

    with right:
        st.markdown(
            '<div class="section-heading">Maintenance Status Distribution</div>', unsafe_allow_html=True)
        color_map = {
            'OPTIMAL': '#10b981', 'MONITOR': '#60a5fa',
            'WARNING': '#f59e0b', 'CRITICAL': '#ef4444'
        }
        fig_pie = px.pie(
            net['status_dist'],
            names='maintenance_status',
            values='Count',
            color='maintenance_status',
            color_discrete_map=color_map,
            hole=0.55
        )
        fig_pie.update_layout(
            height=300, margin=dict(l=20, r=20, b=40, t=20),
            paper_bgcolor='rgba(10, 14, 23, 0)',
            font=dict(color="#94a3b8", family="Inter", size=11),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.15,
                xanchor="center",
                x=0.5,
                font=dict(color="#94a3b8", size=10),
                bgcolor='rgba(17, 24, 39, 0.6)',
                bordercolor='#1e293b',
                borderwidth=1
            ),
            showlegend=True,
            hoverlabel=dict(
                bgcolor='rgba(17, 24, 39, 0.95)',
                bordercolor='#3b82f6',
                font_color='#f1f5f9',
                font_size=11
            )
        )
        fig_pie.update_traces(
            textposition='inside',
            textinfo='percent+label',
            textfont_size=10,
            textfont_color='#f1f5f9',
            marker_line_color='rgba(30, 41, 59, 0.5)',
            marker_line_width=1,
            hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
        )
        st.plotly_chart(fig_pie, use_container_width=True)

        st.markdown(
            '<div class="section-heading">Door State Distribution</div>', unsafe_allow_html=True)
        door_color = {'closed': '#1565c0', 'open': '#10b981',
                      'jammed': '#ef4444', 'closing': '#0288d1'}
        fig_door = px.bar(
            net['door_dist'],
            x='door_state',
            y='Count',
            color='door_state',
            color_discrete_map=door_color,
            category_orders={'door_state': ['closed', 'open', 'closing', 'jammed']}
        )
        fig_door.update_layout(
            height=250,
            margin=dict(l=0, r=0, b=40, t=20),
            paper_bgcolor='rgba(10, 14, 23, 0)',
            plot_bgcolor='rgba(10, 14, 23, 0)',
            font=dict(color="#94a3b8", family="Inter", size=11),
            yaxis=dict(
                gridcolor='rgba(30, 41, 59, 0.6)',
                tickfont=dict(size=10),
                title=''
            ),
            xaxis=dict(
                gridcolor='rgba(30, 41, 59, 0.6)',
                tickfont=dict(size=10),
                title='',
                categoryorder='array',
                categoryarray=['closed', 'open', 'closing', 'jammed']
            ),
            showlegend=False,
            hovermode='x unified',
            hoverlabel=dict(
                bgcolor='rgba(17, 24, 39, 0.95)',
                bordercolor='#3b82f6',
                font_color='#f1f5f9',
                font_size=11
            )
        )
        fig_door.update_traces(
            hovertemplate='<b>State</b>: %{x}<br><b>Count</b>: %{y}<extra></extra>'
        )
        st.plotly_chart(fig_door, use_container_width=True)


# ═══════════════════════════════════════════════════
# ── TAB: INCIDENT LOG ─────────────────────────────
# ═══════════════════════════════════════════════════
elif active_tab == 'incidents':
    incidents = get_incident_log_cached(df)

    st.markdown('<div class="section-heading">Active Incidents — All Stations</div>',
                unsafe_allow_html=True)

    if incidents.empty:
        st.success("✓ No active incidents. All systems operating normally.")
    else:
        # Summary bar
        crit = (incidents["Severity"].str.contains("CRITICAL")).sum()
        warn = (incidents["Severity"].str.contains("WARNING")).sum()
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""<div class="metric-card alert">
                <div class="metric-title">Critical</div>
                <div class="metric-value">{crit}</div>
                <div class="metric-sub">Immediate action needed</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class="metric-card warn">
                <div class="metric-title">Warning</div>
                <div class="metric-value">{warn}</div>
                <div class="metric-sub">Under observation</div>
            </div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-title">Total Incidents</div>
                <div class="metric-value">{len(incidents)}</div>
                <div class="metric-sub">This session</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Incident cards
        for _, row in incidents.iterrows():
            cls = "critical" if "CRITICAL" in row["Severity"] else "warning"
            border_col = "#ef4444" if cls == "critical" else "#f59e0b"
            st.markdown(f"""
            <div class="incident-row {cls}" style="border-left-color:{border_col};">
                <div style="font-family:'IBM Plex Mono'; font-size:0.75rem; color:#4a6fa5; min-width:50px;">{row['Time']}</div>
                <div style="min-width:60px;">{row['Severity']}</div>
                <div style="font-size:0.78rem; color:#7ab3d4; min-width:100px;">{row['Station'][:12]}…</div>
                <div style="font-size:0.78rem; color:#e2e8f0; flex:1;">{row['Description']}</div>
                <div style="font-family:'IBM Plex Mono'; font-size:0.72rem; color:#4a6fa5;">
                    {row['Temp (°C)']}°C | {row['Vibration']} mm/s
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            '<div class="section-heading">Incident Detail Table</div>', unsafe_allow_html=True)
        st.dataframe(incidents, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════
# ── TAB: PREDICTIVE ANALYTICS ─────────────────────
# ═══════════════════════════════════════════════════
elif active_tab == 'forecast':
    st.markdown(f'<div class="section-heading">Predictive Analytics — {current_station}</div>',
                unsafe_allow_html=True)

    # FIRST ROW: 7-Day Forecast (full width)
    forecast_df = get_maintenance_forecast_cached(current_station)
    fig_fc = go.Figure()
    fig_fc.add_trace(go.Scatter(
        x=forecast_df["Date"], y=forecast_df["Predicted Risk %"],
        mode='lines+markers',
        line=dict(color='#f59e0b', width=2.5, shape='spline'),
        marker=dict(size=7, color='#f59e0b'),
        fill='tozeroy',
        fillcolor='rgba(245,158,11,0.08)',
        name="Risk %"
    ))
    fig_fc.add_hrect(y0=70, y1=100, fillcolor="rgba(239,68,68,0.08)",
                     line_width=0, annotation_text="Critical Zone",
                     annotation_font_color="#ef4444")
    fig_fc.add_hrect(y0=30, y1=70, fillcolor="rgba(245,158,11,0.05)",
                     line_width=0, annotation_text="Watch Zone",
                     annotation_font_color="#f59e0b")
    fig_fc.update_layout(
        title=dict(text="7-Day Maintenance Risk Forecast",
                   font=dict(size=14, color="#94a3b8", family="Inter"), x=0),
        height=300, margin=dict(l=0, r=0, b=50, t=60),
        paper_bgcolor='rgba(10, 14, 23, 0)',
        plot_bgcolor='rgba(10, 14, 23, 0)',
        font=dict(color="#64748b", family="Inter", size=11),
        yaxis=dict(
            gridcolor='rgba(30, 41, 59, 0.6)',
            range=[0, 100],
            title='Risk %',
            tickfont=dict(size=10, color="#94a3b8"),
            titlefont=dict(size=12, color="#94a3b8")
        ),
        xaxis=dict(
            gridcolor='rgba(30, 41, 59, 0.6)',
            tickfont=dict(size=10, color="#94a3b8")
        ),
        showlegend=False,
        hovermode='x unified',
        hoverlabel=dict(
            bgcolor='rgba(17, 24, 39, 0.95)',
            bordercolor='#f59e0b',
            font_color='#f1f5f9',
            font_size=11
        )
    )
    fig_fc.update_traces(
        hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br><b>Predicted Risk</b>: %{y:.1f}%<extra></extra>',
        line_width=2.5
    )
    st.plotly_chart(fig_fc, use_container_width=True)

    # SECOND ROW: Heatmap and Network Sync Health side by side
    col_heat, col_sync = st.columns([2, 1])

    with col_heat:
        st.markdown('<div class="section-heading">Weekly Passenger Flow Heatmap</div>',
                    unsafe_allow_html=True)
        heatmap_df = get_passenger_heatmap_cached(current_station)
        fig_heat = px.imshow(
            heatmap_df, aspect="auto",
            color_continuous_scale=["#060c1a",
                                    "#0d47a1", "#0288d1", "#00b4d8"],
            labels=dict(x="Hour", y="Day", color="Passengers"),
        )
        fig_heat.update_layout(
            height=320,
            margin=dict(l=60, r=20, b=50, t=20),
            paper_bgcolor='rgba(10, 14, 23, 0)',
            plot_bgcolor='rgba(10, 14, 23, 0)',
            font=dict(color="#94a3b8", family="Inter", size=11),
            xaxis=dict(
                side='bottom',
                tickfont=dict(size=10, color="#94a3b8"),
                title='Hour of Day',
                titlefont=dict(size=12, color="#94a3b8")
            ),
            yaxis=dict(
                tickfont=dict(size=10, color="#94a3b8"),
                title='Day of Week',
                titlefont=dict(size=12, color="#94a3b8")
            ),
            coloraxis_colorbar=dict(
                title=dict(
                    text="Passengers",
                    font=dict(color="#94a3b8", size=12)
                ),
                tickfont=dict(color="#94a3b8", size=10),
                thickness=10,
                len=0.8
            ),
            hoverlabel=dict(
                bgcolor='rgba(17, 24, 39, 0.95)',
                bordercolor='#06b6d4',
                font_color='#f1f5f9',
                font_size=11
            )
        )
        st.plotly_chart(fig_heat, use_container_width=True)

    with col_sync:
        # Sync score gauge
        st.markdown(
            '<div class="section-heading">Network Sync Health</div>', unsafe_allow_html=True)
        net_sync = int(df["sync_score"].mean())
        station_data_sync = get_station_data_cached(current_station, df)
        avg_sync = int(station_data_sync["sync_score"].mean()) if not station_data_sync.empty else 0
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=avg_sync,
            delta={'reference': net_sync, 'valueformat': '.0f'},
            gauge={
                'axis': {'range': [0, 100], 'tickcolor': '#4a6fa5'},
                'bar': {'color': '#0288d1'},
                'steps': [
                    {'range': [0, 60], 'color': 'rgba(239,68,68,0.15)'},
                    {'range': [60, 85], 'color': 'rgba(245,158,11,0.15)'},
                    {'range': [85, 100], 'color': 'rgba(16,185,129,0.15)'},
                ],
                'threshold': {
                    'line': {'color': '#10b981', 'width': 3},
                    'thickness': 0.75, 'value': 85
                },
                'bgcolor': 'rgba(0,0,0,0)',
                'bordercolor': '#1e2d4d',
            },
            title={'text': f"Sync Score<br><span style='font-size:0.7em;color:#4a6fa5'>vs. Network Avg {net_sync}%</span>",
                   'font': {'color': '#7ab3d4', 'size': 13}},
            number={'suffix': '%', 'font': {'color': '#e2e8f0', 'size': 30}},
        ))
        fig_gauge.update_layout(
            height=320,
            margin=dict(l=40, r=40, b=40, t=50),
            paper_bgcolor='rgba(10, 14, 23, 0)',
            font=dict(color="#94a3b8", family="Inter", size=11)
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

    # THIRD ROW: Gate Risk Scores (full width)
    st.markdown(
        '<div class="section-heading">Gate Risk Scores</div>', unsafe_allow_html=True)
    station_data = get_station_data_cached(current_station, df).sort_values(
        "risk_score", ascending=False)
    fig_risk = px.bar(
        station_data,
        x='risk_score', y='gate_id', orientation='h',
        color='risk_score',
        color_continuous_scale=['#10b981', '#f59e0b', '#ef4444'],
        range_color=[0, 100],
        labels={'risk_score': 'Risk Score', 'gate_id': 'Gate'}
    )
    fig_risk.update_layout(
        height=300,
        margin=dict(l=10, r=10, b=40, t=20),
        paper_bgcolor='rgba(10, 14, 23, 0)',
        plot_bgcolor='rgba(10, 14, 23, 0)',
        font=dict(color="#94a3b8", family="Inter", size=11),
        yaxis=dict(
            gridcolor='rgba(30, 41, 59, 0.6)',
            tickfont=dict(size=10, color="#94a3b8"),
            title=''
        ),
        xaxis=dict(
            gridcolor='rgba(30, 41, 59, 0.6)',
            tickfont=dict(size=10, color="#94a3b8"),
            title='Risk Score',
            range=[0, 100]
        ),
        coloraxis_showscale=False,
        hovermode='y unified',
        hoverlabel=dict(
            bgcolor='rgba(17, 24, 39, 0.95)',
            bordercolor='#ef4444',
            font_color='#f1f5f9',
            font_size=11
        )
    )
    fig_risk.update_traces(
        hovertemplate='<b>Gate</b>: %{y}<br><b>Risk Score</b>: %{x:.1f}/100<extra></extra>',
        marker_line_width=0
    )
    st.plotly_chart(fig_risk, use_container_width=True)


# ═══════════════════════════════════════════════════
# ── TAB: COMPANY & TEAM ───────────────────────────
# ═══════════════════════════════════════════════════
elif active_tab == 'financial':
    from data_source import get_financial_model_data

    PLOTLY_DARK = dict(
        plot_bgcolor='rgba(10, 14, 23, 0)',
        paper_bgcolor='rgba(10, 14, 23, 0)',
        font=dict(color='#94a3b8', family='Inter', size=11),
        xaxis=dict(gridcolor='rgba(30, 41, 59, 0.6)', zeroline=False),
        yaxis=dict(gridcolor='rgba(30, 41, 59, 0.6)', zeroline=False),
        legend=dict(
            bgcolor='rgba(17, 24, 39, 0.8)',
            bordercolor='#1e293b',
            borderwidth=1,
            font=dict(size=10, color='#94a3b8')
        ),
        margin=dict(l=40, r=20, t=50, b=40),
        hovermode='x unified',
        hoverlabel=dict(
            bgcolor='rgba(17, 24, 39, 0.95)',
            bordercolor='#3b82f6',
            font_color='#f1f5f9',
            font_size=11
        )
    )

    def fin_fig(layout_extra=None):
        d = dict(**PLOTLY_DARK)
        if layout_extra:
            d.update(layout_extra)
        return d

    # ── PARAMETER INPUTS ─────────────────────────────────────────────────────
    st.markdown('<div class="section-heading">⚙️ Model Parameters</div>', unsafe_allow_html=True)
    
    with st.expander("Configure SaaS Model Parameters", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**📊 Customer Parameters**")
            starting_customers = st.number_input(
                "Starting Customers", 
                min_value=1, max_value=1000, 
                value=50, step=5,
                help="Initial number of customers at start of simulation"
            )
            monthly_growth_rate = st.slider(
                "Monthly Growth Rate (%)", 
                min_value=1, max_value=50, 
                value=20, step=1,
                help="Monthly customer growth rate as percentage"
            ) / 100.0
            churn_rate = st.slider(
                "Monthly Churn Rate (%)", 
                min_value=1, max_value=30, 
                value=5, step=1,
                help="Monthly customer churn rate as percentage"
            ) / 100.0
        
        with col2:
            st.markdown("**💰 Pricing & Revenue**")
            price_per_customer = st.number_input(
                "Price per Customer ($/month)", 
                min_value=1, max_value=10000, 
                value=100, step=10,
                help="Average monthly revenue per customer"
            )
            cac_simplified = st.number_input(
                "Customer Acquisition Cost ($)", 
                min_value=0, max_value=10000, 
                value=150, step=10,
                help="Cost to acquire one new customer"
            )
            high_churn_multiplier = st.slider(
                "High Churn Multiplier (x)", 
                min_value=1.0, max_value=5.0, 
                value=2.0, step=0.5,
                help="Multiplier for high churn scenario vs base churn"
            )
        
        with col3:
            st.markdown("**📋 Cost Parameters**")
            fixed_costs = st.number_input(
                "Fixed Costs ($/month)", 
                min_value=0, max_value=100000, 
                value=5000, step=500,
                help="Monthly fixed operating costs"
            )
            variable_cost_per_customer = st.number_input(
                "Variable Cost per Customer ($)", 
                min_value=0, max_value=1000, 
                value=10, step=5,
                help="Variable cost per customer"
            )
            simulation_months = st.slider(
                "Simulation Period (months)", 
                min_value=12, max_value=60, 
                value=24, step=6,
                help="Number of months to simulate"
            )
    
    # Calculate high churn rate
    churn_rate_high = churn_rate * high_churn_multiplier
    
    # Re-run simulation with new parameters
    df_base, df_churn = get_financial_model_data(
        months=simulation_months,
        starting_customers=starting_customers,
        monthly_growth_rate=monthly_growth_rate,
        churn_rate=churn_rate,
        price_per_customer=price_per_customer,
        fixed_costs=fixed_costs,
        variable_cost_per_customer=variable_cost_per_customer,
        cac_simplified=cac_simplified,
        churn_rate_high=churn_rate_high
    )
    
    st.markdown('<div class="section-heading">📊 Scenario Selector</div>', unsafe_allow_html=True)
    
    scenario_labels = [
        f"Base Case ({churn_rate*100:.0f}% Churn)", 
        f"High Churn ({churn_rate_high*100:.0f}% Churn)", 
        "Side-by-Side Comparison"
    ]
    scenario = st.radio(
        "Choose scenario",
        scenario_labels,
        horizontal=True,
        label_visibility="collapsed"
    )
    df = df_base if "Base" in scenario else (df_churn if "High" in scenario else df_base)
    months = df["Month"]

    # ── KPI Summary Cards ──────────────────────────────────────────────────
    st.markdown('<div class="section-heading">💰 Key Financial Metrics</div>', unsafe_allow_html=True)
    final = df.iloc[-1]
    k1, k2, k3, k4, k5 = st.columns(5)
    kpi_items = [
        (k1, "FINAL MRR",       f"${final['MRR']:,.0f}",              "metric-card green"),
        (k2, "FINAL ARR",       f"${final['ARR']:,.0f}",              "metric-card"),
        (k3, "TOTAL CUSTOMERS", f"{int(final['Total_Customers'])}",   "metric-card"),
        (k4, "GROSS MARGIN",    f"{final['Gross_Margin_%']:.1f}%",    "metric-card green"),
        (k5, "LTV : CAC",       f"{final['LTV_CAC_Ratio']:.1f}x",    "metric-card"),
    ]
    for col, title, val, cls in kpi_items:
        with col:
            st.markdown(f"""<div class="{cls}">
                <div class="metric-title">{title}</div>
                <div class="metric-value" style="font-size:1.4rem">{val}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── ROW 1: MRR Movements + MRR Growth ─────────────────────────────────
    st.markdown('<div class="section-heading">📈 Revenue Movements</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)

    with c1:
        fig = go.Figure()
        fig.add_bar(x=months, y=df["New_MRR"],       name="New MRR",       marker_color="#2ecc71", opacity=0.85)
        fig.add_bar(x=months, y=df["Expansion_MRR"], name="Expansion MRR", marker_color="#a9dfbf", opacity=0.85)
        fig.add_bar(x=months, y=df["Churn_MRR"],     name="Churn MRR",     marker_color="#e74c3c", opacity=0.85)
        fig.add_scatter(x=months, y=df["Net_New_MRR"], name="Net New MRR",
                        mode="lines+markers", line=dict(color="#00b4d8", width=2),
                        marker=dict(size=5))
        fig.update_layout(barmode="relative", title="MRR Movements", **fin_fig())
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_bar(x=months, y=df["Net_New_MRR"], name="Net New MRR",
                    marker_color="#27ae60", opacity=0.8, secondary_y=False)
        fig.add_scatter(x=months, y=df["MoM_Growth_%"], name="MoM Growth %",
                        mode="lines+markers", line=dict(color="#2980b9", width=2),
                        marker=dict(size=5), secondary_y=True)
        fig.update_layout(title="MRR Growth & MoM %", **fin_fig())
        fig.update_yaxes(gridcolor='#1a2d50', secondary_y=False)
        fig.update_yaxes(gridcolor='#1a2d50', ticksuffix="%", secondary_y=True)
        st.plotly_chart(fig, use_container_width=True)

    # ── ROW 2: Customer Growth + Enterprise Wins ───────────────────────────
    st.markdown('<div class="section-heading">👥 Customer Analytics</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)

    with c1:
        fig = go.Figure()
        fig.add_scatter(x=months, y=df["Total_Customers"], name="Total Customers",
                        mode="lines+markers", line=dict(color="#00b4d8", width=2.5),
                        marker=dict(size=5), fill="tozeroy",
                        fillcolor="rgba(0,180,216,0.08)")
        fig.add_bar(x=months, y=df["New_Customers"], name="New Customers",
                    marker_color="#2ecc71", opacity=0.4)
        fig.update_layout(title="Customer Growth", **fin_fig())
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        fig = go.Figure()
        fig.add_bar(x=months, y=df["New_Enterprise_Wins"],  name="New Enterprise",    marker_color="#2ecc71", opacity=0.85)
        fig.add_bar(x=months, y=df["Enterprise_Upgrades"],  name="Upgrades from Pro", marker_color="#a9cce3", opacity=0.85)
        fig.add_bar(x=months, y=-df["Lost_Enterprise"],     name="Lost",              marker_color="#e74c3c", opacity=0.85)
        fig.update_layout(barmode="relative", title="Enterprise Customer Wins/Losses", **fin_fig())
        st.plotly_chart(fig, use_container_width=True)

    # ── ROW 3: Revenue/Costs/EBIT + Gross Margin ──────────────────────────
    st.markdown('<div class="section-heading">📉 Profitability</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)

    with c1:
        fig = go.Figure()
        for col_name, color, name in [
            ("COGS",    "#f0b27a", "CoGS"),
            ("RD_Cost", "#a9dfbf", "R&D"),
            ("SM_Cost", "#aed6f1", "S&M"),
            ("GA_Cost", "#d2b4de", "G&A"),
            ("CS_Cost", "#f9e79f", "CS"),
        ]:
            fig.add_scatter(x=months, y=df[col_name], name=name,
                            stackgroup="costs", fillcolor=color,
                            line=dict(color=color, width=0.5), mode="lines")
        fig.add_scatter(x=months, y=df["Total_Revenue"], name="Revenue",
                        mode="lines", line=dict(color="#27ae60", width=2.5))
        fig.add_scatter(x=months, y=df["EBIT"], name="EBIT",
                        mode="lines", line=dict(color="#2980b9", width=2, dash="dash"))
        fig.update_layout(title="Revenues, Costs & EBIT", **fin_fig())
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        fig = go.Figure()
        fig.add_scatter(x=months, y=df["Gross_Margin_%"], name="Gross Margin %",
                        mode="lines+markers", line=dict(color="#2980b9", width=2.5),
                        fill="tozeroy", fillcolor="rgba(41,128,185,0.1)",
                        marker=dict(size=4))
        fig.update_layout(title="Gross Profit Margin", yaxis_ticksuffix="%",
                          yaxis_range=[0, 100], **fin_fig())
        st.plotly_chart(fig, use_container_width=True)

    # ── ROW 4: Cost Breakdown + Salaries ──────────────────────────────────
    st.markdown('<div class="section-heading">🏗️ Cost Structure</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)

    with c1:
        fig = go.Figure()
        cost_layers = [
            ("COGS",    "#5dade2", "CoGS"),
            ("RD_Cost", "#a9cce3", "R&D"),
            ("SM_Cost", "#f9e79f", "S&M"),
            ("GA_Cost", "#f0b27a", "G&A"),
            ("CS_Cost", "#d2b4de", "CS"),
        ]
        for col_name, color, name in cost_layers:
            fig.add_scatter(x=months, y=df[col_name], name=name,
                            stackgroup="costs", fillcolor=color,
                            line=dict(color=color, width=0.5), mode="lines")
        fig.update_layout(title="Monthly Costs by P&L Category", **fin_fig())
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        fig = go.Figure()
        sal_layers = [
            ("Salary_GA",          "#5dade2", "G&A"),
            ("Salary_Engineering", "#f0b27a", "Engineering"),
            ("Salary_Marketing",   "#a9dfbf", "Marketing"),
            ("Salary_Sales",       "#f9e79f", "Sales"),
            ("Salary_CS",          "#d2b4de", "CS"),
        ]
        for col_name, color, name in sal_layers:
            fig.add_scatter(x=months, y=df[col_name], name=name,
                            stackgroup="sal", fillcolor=color,
                            line=dict(color=color, width=0.5), mode="lines")
        fig.update_layout(title="Monthly Salaries by Department", **fin_fig())
        st.plotly_chart(fig, use_container_width=True)

    # ── ROW 5: Headcount + S&M Efficiency ─────────────────────────────────
    st.markdown('<div class="section-heading">🧑‍💼 Team & Efficiency</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)

    with c1:
        fig = go.Figure()
        hc_layers = [
            ("HC_GA",          "#5dade2", "G&A"),
            ("HC_Engineering", "#f0b27a", "Engineering"),
            ("HC_Marketing",   "#a9dfbf", "Marketing"),
            ("HC_Sales",       "#f9e79f", "Sales"),
            ("HC_CS",          "#d2b4de", "CS"),
        ]
        for col_name, color, name in hc_layers:
            fig.add_scatter(x=months, y=df[col_name], name=name,
                            stackgroup="hc", fillcolor=color,
                            line=dict(color=color, width=0.5), mode="lines")
        fig.update_layout(title="Headcount by Department", **fin_fig())
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        fig = go.Figure()
        fig.add_scatter(x=months, y=df["SM_Efficiency"], name="S&M Efficiency",
                        mode="lines+markers", line=dict(color="#2980b9", width=2.5),
                        fill="tozeroy", fillcolor="rgba(41,128,185,0.08)",
                        marker=dict(size=4))
        fig.add_hline(y=1.0, line_color="#e74c3c", line_dash="dash",
                      annotation_text="1.0x break-even",
                      annotation_font_color="#e74c3c")
        fig.update_layout(title="Sales & Marketing Efficiency", **fin_fig())
        st.plotly_chart(fig, use_container_width=True)

    # ── ROW 6: CAC Payback + LTV:CAC ──────────────────────────────────────
    st.markdown('<div class="section-heading">🎯 Unit Economics</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)

    with c1:
        fig = go.Figure()
        fig.add_scatter(x=months, y=df["CAC_Payback_Basic"],      name="Basic",
                        mode="lines+markers", line=dict(color="#8e44ad", width=2), marker=dict(size=4))
        fig.add_scatter(x=months, y=df["CAC_Payback_Pro"],        name="Pro",
                        mode="lines+markers", line=dict(color="#2980b9", width=2), marker=dict(size=4))
        fig.add_scatter(x=months, y=df["CAC_Payback_Enterprise"], name="Enterprise",
                        mode="lines+markers", line=dict(color="#27ae60", width=2), marker=dict(size=4))
        fig.update_layout(title="CAC Payback Time by Pricing Plan",
                          yaxis_title="Months to Payback", **fin_fig())
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        fig = go.Figure()
        fig.add_scatter(x=months, y=df["LTV_CAC_Ratio"], name="LTV:CAC",
                        mode="lines+markers", line=dict(color="#e67e22", width=2.5),
                        marker=dict(size=4))
        fig.add_hline(y=3.0, line_color="#27ae60", line_dash="dash",
                      annotation_text="3x benchmark",
                      annotation_font_color="#27ae60")
        fig.update_layout(title="LTV / CAC Ratio", yaxis_title="LTV:CAC Ratio", **fin_fig())
        st.plotly_chart(fig, use_container_width=True)

    # ── Side-by-side comparison (only when that scenario selected) ─────────
    if "Side-by-Side" in scenario:
        st.markdown('<div class="section-heading">⚖️ Base vs High Churn Comparison</div>', unsafe_allow_html=True)
        compare_pairs = [
            ("MRR",             "MRR ($)",           "MRR Growth"),
            ("Total_Customers", "Customers",          "Total Customers"),
            ("Cumulative_Cash", "Cumulative Cash ($)","Cumulative Cash"),
            ("Gross_Margin_%",  "Gross Margin %",     "Gross Margin"),
            ("SM_Efficiency",   "Efficiency",         "S&M Efficiency"),
            ("EBIT",            "EBIT ($)",           "EBIT"),
        ]
        for i in range(0, len(compare_pairs), 2):
            cols = st.columns(2)
            for j, (col_name, ylabel, title) in enumerate(compare_pairs[i:i+2]):
                with cols[j]:
                    fig = go.Figure()
                    fig.add_scatter(x=df_base["Month"], y=df_base[col_name],
                                    name="Base (5% churn)", mode="lines+markers",
                                    line=dict(color="#2980b9", width=2), marker=dict(size=4))
                    fig.add_scatter(x=df_churn["Month"], y=df_churn[col_name],
                                    name="High Churn (10%)", mode="lines+markers",
                                    line=dict(color="#e74c3c", width=2, dash="dash"), marker=dict(size=4))
                    fig.update_layout(title=title, yaxis_title=ylabel, **fin_fig())
                    st.plotly_chart(fig, use_container_width=True)

elif active_tab == 'company':
    # ── Modern Blue Minimalist CSS ──
    st.markdown("""
    <style>
    /* Page background */
    .main {
        background: linear-gradient(135deg, #1E3C72, #2A5298);
        color: #ffffff;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        padding: 1rem;
    }

    /* Section headings */
    .section-heading {
        font-size: 1.8rem;
        font-weight: 700;
        margin: 1.5rem 0 1rem;
        color: #ffffff;
        border-left: 4px solid #00c0ff;
        padding-left: 0.75rem;
    }

    /* Info boxes */
    .stAlert {
        border-radius: 12px !important;
        padding: 1rem 1.25rem !important;
        font-family: 'Helvetica Neue', sans-serif;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        background-color: rgba(255,255,255,0.1) !important;
        border-left: 4px solid #00c0ff !important;
        color: #ffffff;
    }

    /* About section cards */
    .about-container {
        display: flex;
        flex-wrap: wrap;
        gap: 2rem;
        margin-bottom: 2rem;
    }
    .about-card {
        flex: 1 1 45%;
        background: rgba(255,255,255,0.15);
        border-radius: 15px;
        padding: 2rem;
        box-shadow: 0 6px 20px rgba(0,0,0,0.08);
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        min-width: 280px;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .about-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 30px rgba(0,0,0,0.15);
        background: rgba(255,255,255,0.2);
    }
    .about-card h3 {
        color: #00c0ff;
        font-size: 1.3rem;
        margin-bottom: 1rem;
    }
    .about-card p {
        color: #ffffff;
        font-size: 0.95rem;
        line-height: 1.6rem;
        margin-bottom: 1rem;
    }
    .about-card ul {
        color: #cce7ff;
        padding-left: 1.2rem;
        list-style: disc inside;
    }
    .about-card li {
        margin-bottom: 0.6rem;
        font-size: 0.9rem;
    }

    /* Team Grid */
    .team-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1.5rem;
        margin-top: 1rem;
    }
    .team-card {
        background: rgba(255,255,255,0.15);
        padding: 1rem;
        border-radius: 15px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.08);
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .team-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        background: rgba(255,255,255,0.2);
    }
    .team-avatar img {
        width: 100px;
        height: 100px;
        border-radius: 50%;
        object-fit: cover;
        border: 3px solid #00c0ff;
        margin-bottom: 0.5rem;
    }
    .team-name { font-weight: 700; font-size: 1.1rem; color: #ffffff; }
    .team-role { font-size: 0.9rem; color: #cce7ff; margin-bottom: 0.25rem; }
    .team-desc { font-size: 0.85rem; color: #e0f0ff; }

    /* Technology Rows */
    .tech-row {
        display: flex;
        align-items: center;
        padding: 0.6rem 0.8rem;
        margin-bottom: 0.6rem;
        background: rgba(255,255,255,0.15);
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.08);
        gap: 1rem;
        color: #ffffff;
    }
    .tech-layer { font-weight: 600; color: #00c0ff; min-width: 120px; }
    .tech-name { font-weight: 500; min-width: 150px; color: #ffffff; }
    .tech-detail { flex-grow: 1; color: #cce7ff; }

    /* Expander Modern Style */
    .streamlit-expanderHeader { font-weight: 600; font-size: 1rem; color: #00c0ff; }

    /* KPI Table */
    .stDataFrame div[data-testid="stDataFrameContainer"] {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 6px 12px rgba(0,0,0,0.1);
        background: rgba(255,255,255,0.1);
        color: #ffffff !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── About Section ──
    st.markdown('<div class="section-heading">About SicherGleis GmbH</div>',
                unsafe_allow_html=True)
    st.markdown("""
    <div class="about-container">
        <div class="about-card">
            <h3>Core Concept</h3>
            <p>SicherGleis delivers precision-engineered Platform Screen Door (PSD) systems
            that unite <strong>Suraksha</strong> (safety-first philosophy) with German engineering
            excellence to create safe, intelligent, and future-ready urban rail infrastructure.</p>
            <p>Our systems actively prevent platform edge incidents, optimize boarding flow, 
            and enable predictive maintenance — all in real time.</p>
        </div>
        <div class="about-card">
            <h3>Market & Vision</h3>
            <ul>
                <li>🎯 <strong>Target:</strong> U-Bahn, S-Bahn, Light Rail networks across DACH region + India</li>
                <li>🤝 <strong>Partnership:</strong> Indian resilience & innovation + German engineering precision</li>
                <li>📡 <strong>Innovation:</strong> Smart IoT sensors, ML-driven predictive maintenance, automated gate synchronization</li>
                <li>🌱 <strong>Scalability:</strong> Modular design deployable across any rail gauge worldwide</li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Leadership Team ──
    st.markdown('<div class="section-heading">Leadership Team</div>',
                unsafe_allow_html=True)
    team = get_leadership_data()
    for member in team:
        if not member.get('img'):
            member['img'] = "https://via.placeholder.com/100?text=DP"
    team_html = ""
    for member in team:
        team_html += f"""
        <div class="team-card">
            <div class="team-avatar">
                <img src="{member['img']}" alt="{member['name']}">
            </div>
            <div class="team-name">{member['name']}</div>
            <div class="team-role">{member['role']}</div>
            <div class="team-desc">{member['desc']}</div>
        </div>"""
    st.markdown(
        f'<div class="team-grid">{team_html}</div>', unsafe_allow_html=True)

    # ── Technology Architecture ──
    st.markdown('<div class="section-heading">Technology Architecture</div>',
                unsafe_allow_html=True)
    tech = get_tech_stack()
    for item in tech:
        st.markdown(f"""
        <div class="tech-row">
            <div class="tech-layer">{item['layer']}</div>
            <div class="tech-name">{item['tech']}</div>
            <div class="tech-detail">{item['detail']}</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Academic Context ──
    st.markdown('<div class="section-heading">Academic Project Context</div>',
                unsafe_allow_html=True)
    with st.expander("📋 Project Details & Methodology", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
**Problem Statement**

Platform Screen Door (PSD) systems require continuous monitoring
to ensure passenger safety and minimize downtime.

SicherGleis Pro introduces a real-time,
data-driven dashboard to shift to proactive maintenance.

**Data Sources**
- IoT sensor readings: temperature (°C), vibration (mm/s)
- Gate state telemetry: open / closing / closed / jammed
- Passenger flow counters per platform gate
- Train arrival/departure status per gate
            """)
        with col2:
            st.markdown("""
**Methodology**

1. **Data Pipeline**: CSV-based simulation of live sensor telemetry
2. **Sync Score**: Composite metric penalizing high temp and vibration
3. **Risk Score**: Multi-factor safety risk index (0–100) per gate
4. **Maintenance Status**: Rule-based classification (OPTIMAL → CRITICAL)
5. **Predictive Forecast**: Simulated 7-day risk trajectory
6. **Visualization**: Plotly charts + custom HTML PSD gate diagrams
            """)

    with st.expander("📊 Key Performance Indicators Explained"):
        kpi_data = {
            "KPI": ["Sync Efficiency %", "Risk Score", "Door Cycles/hr", "Passenger Flow", "Alert Count"],
            "Formula": [
                "100 - (temp-25)×0.5 - (vib×2)",
                "Weighted sum: door_state + temp + vibration",
                "Simulated from station seed (deterministic)",
                "Sum of people detected per gate sensor",
                "Count of CRITICAL maintenance_status gates"
            ],
            "Threshold": [
                "< 85% → MONITOR",
                "> 70 → Critical Zone",
                "Peak: 07–09h, 17–19h",
                "Platform capacity: 500 pax",
                "0 = NORMAL, ≥1 = ALERT"
            ]
        }
        st.dataframe(pd.DataFrame(kpi_data),
                     use_container_width=True, hide_index=True)