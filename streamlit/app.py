import streamlit as st
import streamlit.components.v1 as components
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd
import json
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from data.loader import load_and_transform_data
from core.logic import (
    # Analytics functions
    get_metrics,
    get_psd_analytics,
    get_network_summary,
    get_maintenance_forecast,
    get_incident_log,
    get_leadership_data,
    # Financial model
    visualize_dashboard_1,
    visualize_dashboard_2,
    # OOP classes
    StationAnalytics,
    # Simulation engine
    SimulationSession,
    get_simulation_personas,
    # Placeholder functions (defined later)
    get_financial_model_data,
    get_customer_data,
    get_rfm_analysis,
    get_high_value_customers,
    get_customer_business_insights,
    get_contract_health_score,
    get_renewal_forecast,
    get_at_risk_accounts,
    get_renewal_health_summary,
    get_operator_history,
    get_contract_amendments,
    get_support_tickets,
    get_engagement_timeline,
    get_operator_profile,
    get_operator_health_trend,
    get_support_ticket_trend,
    get_financial_projections,
    get_operator_comparison_benchmarks,
    get_operator_monthly_stats,
    get_business_map_data,
    # Analytics Lab
    detect_anomalies_zscore,
    detect_anomalies_iqr,
    detect_anomalies_moving_average,
    detect_anomalies_isolation_forest,
    evaluate_detection_method,
    decompose_timeseries,
    compute_sensor_correlations,
    analyze_sensor_health_profile,
    _SKLEARN_AVAILABLE,
)
from core.visualization_engine import (
    build_architecture_flow_html,
    generate_live_metrics,
    analyze_loopholes,
    generate_recommendations,
    get_station_vulnerability_scores,
    ARCHITECTURE_NODES,
)
from core.budget_tracker import (
    get_budget_overview,
    get_station_comparison_table,
)
from data.budget_data import (
    generate_budget_data,
    generate_roi_data,
    generate_monthly_spend,
    generate_scenario_projections,
    generate_optimization_recommendations,
)
from core.anomaly_ranking import (
    rank_anomalies,
    get_anomaly_ranking_matrix,
    ANOMALY_RANKING_PRESETS,
    DEFAULT_ANOMALY_PRESET,
)
from core.narrative_html import (
    build_green_state_banner,
    build_kpi_ticker,
    build_mini_ranking,
    build_org_tree,
)

from utils.chart_styles import style_chart, style_pie, style_indicator, style_df, COLOR_SCHEMES
from utils.chart_export import render_chart
from utils.helpers import (
    format_euro,
    get_status_color,

    format_score,
    smart_format,
    format_full,
    convert_to_csv,
    show_loading_spinner,
    format_breakeven,
)
from reports.pdf_generator import (
    generate_client_report,
    get_report_bytes,
    generate_complete_pdf_report,
    generate_charts_only_pdf_report,
    generate_tables_only_pdf_report,
)

import logging
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════
if "current_station" not in st.session_state:
    st.session_state.current_station = "Berlin Hauptbahnhof"
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "ops"
if "selected_operator" not in st.session_state:
    st.session_state.selected_operator = None

# ── Query param navigation ──
nav_param = st.query_params.get("nav")
if nav_param:
    st.session_state.active_tab = nav_param
    st.query_params.clear()
    st.rerun()

# ═══════════════════════════════════════════════════
# CSS — MIDNIGHT EXPRESS DESIGN SYSTEM v3
# ═══════════════════════════════════════════════════
css_files = [
    "assets/css/design-tokens.css",
    "assets/css/base.css",
    "assets/css/typography.css",
    "assets/css/layout.css",
    "assets/css/sidebar.css",
    "assets/css/cards.css",
    "assets/css/panels.css",
    "assets/css/architecture.css",
    "assets/css/company.css",
    "assets/css/animations.css",
    "assets/css/responsive.css",
    "assets/css/ticker.css",
    "assets/css/org-tree.css",
    "assets/css/green-state.css",
    "assets/css/tabs-modern.css",
    "assets/css/tooltips.css",
    "assets/css/totalvision.css",
]
for css_file in css_files:
    with open(css_file, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════
# DATA LOADING WITH SESSION STATE CACHE
# ═══════════════════════════════════════════════════
# Use session state to persist transformed data across reruns

if "transformed_df" not in st.session_state:
    with st.spinner("Loading and processing data..."):
        st.session_state.transformed_df = load_and_transform_data()
        st.session_state.data_load_time = datetime.now()

df = st.session_state.transformed_df
stations = sorted(df["station"].unique())

# ── Smart Conditional Refresh: version counter ──
if "data_version" not in st.session_state:
    st.session_state.data_version = 1
# Increment version each rerun (tracks data freshness)
st.session_state.data_version += 1

# ═══════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════
with st.sidebar:
    # Get current station for status
    current_station_sidebar = st.session_state.current_station
    gates_total, gates_active, p_total, alerts, avg_sync, warnings, _ = get_metrics(
        df, current_station_sidebar
    )
    sys_status = (
        "NORMAL"
        if alerts == 0 and warnings == 0
        else ("ALERT" if alerts > 0 else "WARNING")
    )

    # ── Brand Header ──
    st.markdown(
        """
    <div class="sidebar-brand">
        <div class="brand-title">
            <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
                <path d="M16 2L4 7v10c0 7 5.2 12.1 12 14 6.8-1.9 12-7 12-14V7L16 2z"
                      stroke="#d4a030" stroke-width="1.5" fill="rgba(212,160,48,0.04)"/>
                <path d="M9 15.5c0-3.5 3-6 7-6s7 2.5 7 6"
                      stroke="#0d9488" stroke-width="1.5" stroke-linecap="round"/>
                <path d="M9 18.5c0-2.5 3-4.5 7-4.5s7 2 7 4.5"
                      stroke="#d4a030" stroke-width="1" stroke-linecap="round" opacity="0.5"/>
                <circle cx="16" cy="24" r="1.5" fill="#d4a030" opacity="0.7"/>
            </svg>
            SicherGleis
        </div>
        <div class="brand-tagline">BahnSetu Pro</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # ── Section: System Status ──
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section-label">System Status</div>',
                unsafe_allow_html=True)

    status_subtitle = {
        "NORMAL": "All systems operational",
        "WARNING": "Attention required",
        "ALERT": "Immediate attention needed",
    }

    st.markdown(
        f"""
    <div class="system-status-indicator status-{sys_status.lower()}">
        <div class="status-dot"></div>
        <div class="status-content">
            <div class="status-label-main">{sys_status}</div>
            <div class="status-label-sub">{status_subtitle[sys_status]}</div>
        </div>
        <div class="status-station-badge">{(st.session_state.get('current_station') or 'Hbf').split()[-1]}</div>
    </div>
    """,
        unsafe_allow_html=True,
    )
    st.html('</div>')

    # ── Section: Station ──
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section-label">Station</div>',
                unsafe_allow_html=True)

    current_station_idx = (
        stations.index(st.session_state.current_station)
        if st.session_state.current_station in stations
        else 0
    )
    selected_station = st.selectbox(
        "Choose a station",
        options=stations,
        index=current_station_idx,
        key="station_selector",
        label_visibility="collapsed",
    )
    if selected_station != st.session_state.current_station:
        st.session_state.current_station = selected_station
        st.session_state.active_tab = "ops"
        st.rerun()

    # Re-derive metrics for the (potentially changed) station
    gates_total, gates_active, p_total, alerts, avg_sync, warnings, _ = get_metrics(
        df, st.session_state.current_station
    )

    if alerts > 0:
        dot_cls = "offline"
        status_badge = "Critical"
    elif warnings > 0:
        dot_cls = "warning"
        status_badge = "Warning"
    else:
        dot_cls = "online"
        status_badge = "Operational"

    st.markdown(
        f"""
    <div class="station-info-card">
        <div class="station-info-row">
            <div class="station-info-dot {dot_cls}"></div>
            <div class="station-info-body">
                <div class="station-info-label">Active Station</div>
                <div class="station-info-name">{st.session_state.get("current_station") or "Hbf"}</div>
                <div class="station-info-meta">{(stations.index(st.session_state.get('current_station')) + 1) if st.session_state.get('current_station') in stations else '?'} / {len(stations)}</div>
            </div>
            <div class="station-info-status {dot_cls}">{status_badge}</div>
        </div>
        <div class="station-info-metrics">
            <div class="station-metric">
                <span class="station-metric-val">{gates_active}/{gates_total}</span>
                <span class="station-metric-label">Gates</span>
            </div>
            <div class="station-metric">
                <span class="station-metric-val">{avg_sync}%</span>
                <span class="station-metric-label">Sync</span>
            </div>
            <div class="station-metric">
                <span class="station-metric-val">{p_total:,}</span>
                <span class="station-metric-label">Pax</span>
            </div>
            <div class="station-metric">
                <span class="station-metric-val">{alerts + warnings}</span>
                <span class="station-metric-label">Issues</span>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )
    st.html('</div>')

    # ── Incident Mini-Ranking (network-wide) ──
    try:
        all_anomalies_sidebar = df[
            df["maintenance_status"].isin(["CRITICAL", "WARNING"])
        ] if "maintenance_status" in df.columns else pd.DataFrame()
        if not all_anomalies_sidebar.empty:
            ranked_sidebar = rank_anomalies(all_anomalies_sidebar)
            if ranked_sidebar:
                mini_html = build_mini_ranking(ranked_sidebar)
                if mini_html:
                    st.markdown(mini_html, unsafe_allow_html=True)
    except Exception as e:
        logger.warning(f"Mini-rank sidebar failed: {e}")

    # ── Navigation: grouped sections with plain headers ──
    nav_groups = [
        ("Operations", [
            ("ops", "Live Operations"),
            ("incidents", "Incident Log"),
            ("network", "Network Overview"),
        ]),
        ("Analytics", [
            ("forecast", "Predictive Analytics"),
            ("analytics", "Analytics Lab"),
            ("kpi", "KPI Dashboard"),
        ]),
        ("Business", [
            ("financial", "Financial Model"),
            ("customer", "Customer Segments"),
            ("portfolio", "Operator Portfolio"),
            ("budget", "Budget / ROI"),
        ]),
        ("Intelligence", [
            ("totalvision", "TotalVision"),
        ]),
        ("Info", [
            ("viz", "Architecture Hub"),
            ("company", "Company & Team"),
        ]),
    ]

    for group_name, items in nav_groups:
        # Category header (no accordion - always visible)
        st.markdown(
            f'<div class="nav-section-header">{group_name}</div>',
            unsafe_allow_html=True,
        )
        for key, label in items:
            is_active = st.session_state.active_tab == key
            if st.button(
                label=label,
                key=f"tab_{key}",
                type="primary" if is_active else "secondary",
                use_container_width=True,
            ):
                st.session_state.active_tab = key
                st.rerun()



    # ── Footer ──
    st.markdown(
        """
    <div class="sidebar-footer">
        <div class="footer-brand">BahnSetu GmbH</div>
        <div class="footer-version">v2.1.81 | © 2025</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

# ═══════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════
current_station = st.session_state.get("current_station") or "Hauptbahnhof"
try:
    gates_total, gates_active, p_total, alerts, avg_sync, warnings, _ = get_metrics(
        df, current_station
    )
except Exception as e:
    import logging
    logging.warning(f"Error loading metrics: {e}")
    gates_total = gates_active = p_total = alerts = avg_sync = warnings = 0

active_tab = st.session_state.get("active_tab", "ops")

display_title = "SicherGleis Pro"
display_sub = "BAHNSETU COMPANY PROFILE"

sys_status = "NORMAL"
badge_cls = "status-normal"

# Dynamic header depending on active tab
if active_tab == "incidents":
    display_title = "All Stations Log"
    display_sub = "NETWORK-WIDE INCIDENT MONITORING // ALL STATIONS"
elif active_tab == "forecast":
    display_title = "Predictive Analytics"
    display_sub = "NETWORK-WIDE MAINTENANCE FORECASTING // ALL STATIONS"
elif active_tab == "ops":
    display_title = st.session_state.get("current_station", "Operations")
    display_sub = f"PLATFORM SAFETY MONITOR // SURAKSHA PROTOCOL ACTIVE"
elif active_tab == "network":
    display_title = "Network Overview"
    display_sub = "ALL STATIONS // LIVE STATUS"
elif active_tab == "financial":
    display_title = "Financial Model"
    display_sub = "SAAS REVENUE SIMULATION // BAHNSETU FINANCIAL INTELLIGENCE"
elif active_tab == "customer":
    display_title = "Customer Segmentation"
    display_sub = "RFM ANALYSIS // CUSTOMER INSIGHTS"
elif active_tab == "portfolio":
    display_title = "Operator Portfolio"
    display_sub = "CUSTOMER DETAILS // PORTFOLIO VIEW"
    selected_op_id = st.session_state.get("selected_operator")
    if selected_op_id:
        try:
            customer_df = get_customer_data()
            if customer_df is not None and not customer_df.empty:
                op_row = customer_df[customer_df["customer_id"]
                                     == selected_op_id]
                if not op_row.empty:
                    display_title = op_row.iloc[0]["customer_name"]
        except Exception as e:
            import logging
            logging.warning(f"Error loading operator name: {e}")
elif active_tab == "kpi":
    display_title = "KPI Dashboard"
    display_sub = "KEY PERFORMANCE INDICATORS // OVERVIEW"
elif active_tab == "analytics":
    display_title = "Analytics Lab"
    display_sub = "ANOMALY DETECTION // TIME-SERIES DECOMPOSITION // CORRELATION ANALYSIS"
elif active_tab == "viz":
    display_title = "Architecture Hub"
    display_sub = "SYSTEM FLOW // LIVE RESPONSE // VULNERABILITY SCAN // INTELLIGENCE"
else:
    display_title = "SicherGleis Pro"
    display_sub = "BAHNSETU COMPANY PROFILE"

# Define status icons (SVG strings without extra whitespace)
status_icons = {
    "NORMAL": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>',
    "WARNING": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
    "ALERT": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>',
}

icon_html = f'<div class="status-icon">{status_icons[sys_status]}<div class="status-icon-ring"></div></div>'

st.markdown(
    f"""
<div class="main-header">
    <div>
        <div class="station-title">{display_title}</div>
        <div class="station-sub">{display_sub}</div>
    </div>
    <div class="status-badge {badge_cls}">
        {icon_html}
        <span class="status-label">{sys_status}</span>
    </div>
</div>
""",
    unsafe_allow_html=True,
)


# ═══════════════════════════════════════════════════
# TRAIN ANIMATION HTML BUILDER - MODERN PREMIUM EDITION
# ════════════════════════════════════════════════════
@st.cache_data(ttl=60, show_spinner=False)
def build_train_animation(station_name, station_df):
    """Build a sophisticated HTML/JS animation with modern visuals and realistic train movement."""
    platforms_data = []
    station_df = station_df.copy()

    grouped = station_df.groupby("platform")

    for platform, plat_df in sorted(grouped, key=lambda x: x[0]):
        gates = []
        train_types_found = []

        for row in plat_df.itertuples(index=False):
            gate_data = {
                "id": row.gate_id,
                "state": row.door_state,
                "train": str(row.train)
                if "train" in row._fields and pd.notna(row.train) and row.train
                else "",
                "train_type": str(row.train_type)
                if "train_type" in row._fields and pd.notna(row.train_type)
                else "ICE",
                "operator": str(row.operator)
                if "operator" in row._fields and pd.notna(row.operator)
                else "DB",
                "destination": str(row.destination)
                if "destination" in row._fields and pd.notna(row.destination)
                else "Unknown",
                "temp": float(row.sensor_temp),
                "vib": float(row.sensor_vib),
                "risk": int(row.risk_score) if "risk_score" in row._fields else 0,
                "status": row.maintenance_status
                if "maintenance_status" in row._fields
                else "OPTIMAL",
                "people": int(row.people),
                "capacity": int(row.capacity) if "capacity" in row._fields else 400,
                "door_position": str(row.door_position)
                if "door_position" in row._fields
                else "middle",
                "signal_status": str(row.signal_status)
                if "signal_status" in row._fields
                else "green",
                "track_number": int(row.track_number)
                if "track_number" in row._fields
                else 1,
            }
            gates.append(gate_data)
            if gate_data["train"] and gate_data["train_type"] not in train_types_found:
                train_types_found.append(gate_data["train_type"])

        # Determine primary train type for animation
        primary_train_type = train_types_found[0] if train_types_found else "ICE"
        train_name = next(
            (g["train"] for g in gates if g["train"]),
            f"{primary_train_type} {abs(hash(platform)) % 900 + 100}",
        )

        platforms_data.append(
            {
                "platform": platform,
                "gates": gates,
                "train_name": train_name,
                "train_type": primary_train_type,
            }
        )

    platforms_json = json.dumps(platforms_data)

    # Build the HTML with an embedded JS animation engine - MODERN PREMIUM EDITION
    html = (
        """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500;600&family=Figtree:wght@300;400;500;600;700;800;900&display=swap');
@import url('https://api.fontshare.com/v2/css?f[]=satoshi@300,400,500,700,900&f[]=clash-display@400,500,600,700&display=swap');

/* ── CSS VARIABLES & THEME ───────────────────────────────────────────── */
:root {
  --bg-primary: #0a0f24;
  --bg-secondary: #060a17;
  --bg-glass: rgba(15, 21, 48, 0.3);
  --bg-glass-hover: rgba(22, 29, 58, 0.7);
  --border-color: rgba(241, 240, 245, 0.08);
  --border-glow: rgba(245, 158, 11, 0.25);
  --text-primary: #f1f0f5;
  --text-secondary: #b8b6cc;
  --text-muted: #7a7891;
  --accent-gold: var(--color-warning);
  --accent-gold-light: #fbbf24;
  --accent-teal: #06b6d4;
  --success: var(--color-emerald);
  --warning: var(--color-warning);
  --danger: var(--color-danger);
  --glass-border: rgba(245, 158, 11, 0.12);
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.3), 0 1px 3px 0 rgba(0, 0, 0, 0.2);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.35), 0 2px 4px -1px rgba(0, 0, 0, 0.2);
  --shadow-lg: 0 10px 25px -5px rgba(0, 0, 0, 0.45);
  --shadow-glow: 0 0 20px rgba(245, 158, 11, 0.12);
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: 'Satoshi', 'Figtree', sans-serif;
  overflow-x: hidden;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* ── STATION BANNER ───────────────────────────────────────────────────────── */
.sta-banner {
  background: var(--glass-bg);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border-color);
  padding: 12px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  overflow: hidden;
}

.sta-banner::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 200%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.03), transparent);
  animation: banner-shine 8s ease-in-out infinite;
}

@keyframes banner-shine {
  0%, 100% { transform: translateX(-50%); }
  50% { transform: translateX(0%); }
}

.sta-name {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--accent-cyan);
  letter-spacing: 2px;
  text-transform: uppercase;
  position: relative;
  z-index: 1;
}

.live-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--success);
  display: inline-block;
  margin-right: 8px;
  animation: live-pulse 2s ease-in-out infinite;
  box-shadow: 0 0 12px var(--success);
  position: relative;
}

.live-dot::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 150%;
  height: 150%;
  border-radius: 50%;
  background: var(--success);
  opacity: 0.3;
  transform: translate(-50%, -50%);
  animation: live-ripple 2s ease-out infinite;
}

@keyframes live-pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.2); opacity: 0.8; }
}

@keyframes live-ripple {
  0% { transform: translate(-50%, -50%) scale(1); opacity: 0.6; }
  100% { transform: translate(-50%, -50%) scale(2.5); opacity: 0; }
}

.live-lbl {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6rem;
  color: var(--success);
  letter-spacing: 1px;
  text-transform: uppercase;
}

/* ── PLATFORM BLOCK ────────────────────────────────────────────────────────── */
.plat-block {
  margin: var(--space-lg);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: var(--bg-card);
  box-shadow: var(--shadow-md);
  transition: all var(--transition-base);
}

.plat-block:hover {
  border-color: var(--border-default);
  box-shadow: var(--shadow-lg);
  transform: translateY(-2px);
}

.plat-hdr {
  background: var(--bg-tertiary);
  padding: var(--space-md) var(--space-lg);
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border-subtle);
}

.plat-lbl {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--accent-primary);
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.plat-st {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 999px;
  transition: all var(--transition-base);
}

.st-ok {
  background: rgba(16, 185, 129, 0.15);
  border: 1px solid rgba(16, 185, 129, 0.3);
  color: var(--status-ok);
}

.st-bad {
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: var(--status-error);
}

/* ────────────────────────────────────────────────────────────── */
/* SCENE - Modern Clean */
/* ────────────────────────────────────────────────────────────── */
.scene {
  position: relative;
  height: 220px;
  overflow: hidden;
  background: var(--bg-tertiary);
  border-top: 1px solid var(--border-subtle);
  border-bottom: 1px solid var(--border-subtle);
  margin-bottom: var(--space-lg);
}

.scene-bg {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(180deg,
      rgba(6, 12, 26, 0.3) 0%,
      transparent 50%,
      rgba(6, 12, 26, 0.2) 100%
    );
}

/* Platform floor - concrete texture */
.plat-floor {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 55px;
  background: linear-gradient(
    180deg,
    #374151 0%,
    #1f2937 40%,
    #111827 100%
  );
  border-top: 1px solid #4b5563;
  box-shadow:
    inset 0 2px 4px rgba(0, 0, 0, 0.3),
    0 -4px 8px rgba(0, 0, 0, 0.2);
}

/* Yellow safety line (edge strip) */
.edge-strip {
  position: absolute;
  bottom: 55px;
  left: 0;
  right: 0;
  height: 4px;
  background: repeating-linear-gradient(
    90deg,
    var(--color-warning) 0px,
    var(--color-warning) 16px,
    transparent 16px,
    transparent 24px
  );
  opacity: 0.8;
  filter: drop-shadow(0 0 3px rgba(245, 158, 11, 0.6));
  z-index: 3;
}

/* Cityscape background buildings */
.bldgs {
  position: absolute;
  bottom: 57px;
  left: 0;
  right: 0;
  height: 45px;
  display: flex;
  align-items: flex-end;
  gap: 1px;
  padding: 0 3px;
  opacity: 0.12;
  z-index: 1;
}

.bldg {
  background: #6b7280;
  border-radius: 1px 1px 0 0;
  flex-shrink: 0;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

/* Railway track */
.track {
  position: absolute;
  bottom: 8px;
  left: 0;
  right: 0;
  height: 8px;
  z-index: 4;
  display: flex;
  align-items: center;
  justify-content: center;
}

.rail {
  position: absolute;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(
    180deg,
    #4b5563 0%,
    #374151 50%,
    #1f2937 100%
  );
  border-radius: 1px;
  box-shadow:
    0 1px 2px rgba(0, 0, 0, 0.4),
    inset 0 1px 1px rgba(255, 255, 255, 0.1);
}

.rail.t { top: 0; }
.rail.b { bottom: 0; }

.sleeper {
  position: absolute;
  bottom: -3px;
  width: 14px;
  height: 10px;
  background: linear-gradient(
    180deg,
    #1f2937 0%,
    #111827 100%
  );
  border-radius: 1.5px;
  box-shadow:
    inset 0 1px 2px rgba(255, 255, 255, 0.05),
    0 2px 4px rgba(0, 0, 0, 0.4);
}

/* Train */
.train-wrap {
  position: absolute;
  bottom: 18px;
  left: 0;
  will-change: transform;
  display: flex;
  align-items: flex-end;
  z-index: 10;
  filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.4));
  transition: filter var(--transition-base);
}

.train-wrap.approaching {
  filter: drop-shadow(0 6px 16px rgba(59, 130, 246, 0.5));
}

.train-wrap.departing {
  filter: drop-shadow(0 4px 12px rgba(239, 68, 68, 0.5));
}

/* ── GHOST TRAINS (continuous CSS animation) ─────── */
.ghost-wrap {
  position: absolute;
  bottom: 18px;
  z-index: 4;
  pointer-events: none;
  opacity: 0.3;
}
.ghost-train {
  height: 22px;
  border-radius: 3px 2px 2px 3px;
  position: relative;
  background: linear-gradient(90deg, #4a5568, #2d3748 40%, #4a5568);
  border: 1px solid rgba(100,120,160,0.15);
  box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}
.ghost-cab {
  position: absolute;
  left: 0; top: -1px; bottom: -1px;
  width: 18px;
  background: linear-gradient(90deg, #ecc94b, #d69e2e);
  border-radius: 3px 0 0 3px;
}
.ghost-wins {
  position: absolute;
  left: 22px; right: 22px; top: 4px; bottom: 4px;
  background: repeating-linear-gradient(90deg, rgba(100,140,180,0.15) 0, rgba(100,140,180,0.15) 10px, transparent 10px, transparent 14px);
}
.ghost-wins.gw2 {
  background: repeating-linear-gradient(90deg, rgba(255,215,0,0.08) 0, rgba(255,215,0,0.08) 8px, transparent 8px, transparent 12px);
}
.ghost-light {
  position: absolute;
  right: 2px; top: 4px;
  width: 4px; height: 10px;
  border-radius: 2px;
  background: #ffd700;
  box-shadow: 0 0 8px rgba(255,215,0,0.5);
}
.gt-a { animation: ghostA 14s linear infinite; }
.gt-b { animation: ghostB 10s linear infinite; }
.gt-c { animation: ghostC 18s linear infinite; }
.gt-d { animation: ghostD 9s linear infinite; }
.gt-e { animation: ghostE 12s linear infinite; }
.gt-f { animation: ghostF 7s linear infinite; }

@keyframes ghostA {
  0% { transform: translateX(-120px); }
  100% { transform: translateX(calc(100% + 140px)); }
}
@keyframes ghostB {
  0% { transform: translateX(calc(100% + 100px)); }
  100% { transform: translateX(-80px); }
}
@keyframes ghostC {
  0% { transform: translateX(-160px); }
  100% { transform: translateX(calc(100% + 180px)); }
}
@keyframes ghostD {
  0% { transform: translateX(calc(100% + 60px)); }
  100% { transform: translateX(-100px); }
}
@keyframes ghostE {
  0% { transform: translateX(-80px); }
  100% { transform: translateX(calc(100% + 100px)); }
}
@keyframes ghostF {
  0% { transform: translateX(calc(100% + 120px)); }
  100% { transform: translateX(-60px); }
}

/* ── WHEEL ANIMATIONS ──────────────────────────── */
@keyframes wheel-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
@keyframes wheel-spin-fast { from { transform: rotate(0deg); } to { transform: rotate(720deg); } }
@keyframes wheel-spin-slow { from { transform: rotate(0deg); } to { transform: rotate(180deg); } }

.wspin { animation: wheel-spin 0.6s linear infinite; }
.wspin-fast { animation: wheel-spin-fast 0.4s linear infinite; }
.wslow { animation: wheel-spin-slow 1.2s linear infinite; }

/* ═══════════════════════════════════════════════════ */
/* TRAIN - Realistic Modern Design */
/* ═══════════════════════════════════════════════════ */
.t-car {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* Main car body - 3D appearance */
.car-body {
  background: linear-gradient(
    180deg,
    #2d3748 0%,
    #1a202c 40%,
    #171923 100%
  );
  border-radius: 4px 4px 0 0;
  position: relative;
  border: 1px solid #1a202c;
  border-bottom: none;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.1),
    inset 0 -1px 0 rgba(0, 0, 0, 0.3),
    0 4px 12px rgba(0, 0, 0, 0.4);
}

.car-body::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(
    90deg,
    rgba(59, 130, 246, 0.3),
    rgba(6, 182, 212, 0.4),
    rgba(59, 130, 246, 0.3)
  );
  border-radius: 3px 3px 0 0;
}

.car-stripe {
  position: absolute;
  top: 45%;
  left: 6%;
  width: 88%;
  height: 2px;
  background: var(--color-warning);
  opacity: 0.7;
  border-radius: 1px;
  box-shadow: 0 0 4px rgba(245, 158, 11, 0.5);
}

.car-body::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(
    180deg,
    rgba(255, 255, 255, 0.05) 0%,
    transparent 30%,
    rgba(0, 0, 0, 0.1) 100%
  );
  pointer-events: none;
  border-radius: inherit;
}

/* Windows - Glass effect */
.car-wins {
  position: absolute;
  top: 18%;
  left: 10%;
  width: 80%;
  height: 52%;
  display: flex;
  gap: 4px;
  justify-content: center;
  align-items: center;
}

.win {
  flex: 1;
  height: 100%;
  background: linear-gradient(
    180deg,
    rgba(15, 23, 42, 0.9) 0%,
    rgba(30, 41, 59, 0.85) 70%,
    rgba(15, 23, 42, 0.95) 100%
  );
  border-radius: 2px;
  border: 1px solid #1a202c;
  position: relative;
  overflow: hidden;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.1),
    0 1px 2px rgba(0, 0, 0, 0.3);
}

.win::before {
  content: '';
  position: absolute;
  top: 0;
  left: 20%;
  width: 60%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.08),
    transparent
  );
}

.win.lit {
  background: linear-gradient(
    180deg,
    rgba(59, 130, 246, 0.25) 0%,
    rgba(6, 182, 212, 0.2) 70%,
    rgba(59, 130, 246, 0.25) 100%
  );
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.2),
    0 0 15px rgba(59, 130, 246, 0.3);
}

/* Passenger silhouettes */
.pax-sil {
  position: absolute;
  bottom: 8%;
  left: 50%;
  transform: translateX(-50%);
  width: 70%;
  height: 80%;
  background: linear-gradient(
    180deg,
    rgba(50, 50, 80, 0.4) 0%,
    rgba(40, 40, 60, 0.3) 100%
  );
  border-radius: 30% 30% 35% 35%;
  filter: blur(1px);
  opacity: 0;
  transition: opacity 0.5s ease;
}

.pax-sil.visible {
  opacity: 0.6;
}

.pax-sil {
  position: absolute;
  bottom: 10%;
  left: 50%;
  transform: translateX(-50%);
  width: 60%;
  height: 70%;
  background: var(--text-muted);
  opacity: 0.15;
  border-radius: 30% 30% 40% 40%;
  filter: blur(1px);
  transition: opacity var(--transition-base);
}

.win:hover .pax-sil,
.pax-sil.visible {
  opacity: 0.4;
}

/* Passenger silhouettes */
.pax-sil {
  position: absolute;
  bottom: 2px;
  left: 50%;
  transform: translateX(-50%);
  width: 6px;
  height: 11px;
  background: rgba(20, 50, 110, 0.7);
  border-radius: 3px 3px 0 0;
  opacity: 0;
  transition: opacity 0.4s ease;
  filter: blur(0.5px);
}

.win:hover .pax-sil,
.pax-sil.visible {
  opacity: 0.8;
}

/* ═══════════════════════════════════════════════════ */
/* BOGIES & WHEELS - Realistic */
/* ═══════════════════════════════════════════════════ */
.bogie {
  position: absolute;
  bottom: -6px;
  background: linear-gradient(
    180deg,
    #1a202c 0%,
    #0f161a 100%
  );
  border-radius: 3px;
  height: 10px;
  border: 1px solid #0a0a0a;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.4);
}

.bg-l { left: 12px; width: 20px; }
.bg-r { right: 12px; width: 20px; }

.wheel {
  position: absolute;
  bottom: -8px;
  width: 12px;
  height: 12px;
  background: radial-gradient(
    circle at 30% 30%,
    #4a5568 0%,
    #2d3748 60%,
    #1a202c 100%
  );
  border-radius: 50%;
  border: 2px solid #0a0a0a;
  box-shadow:
    inset 0 1px 2px rgba(255, 255, 255, 0.15),
    0 1px 2px rgba(0, 0, 0, 0.5);
}

.wl { left: 4px; }
.wr { right: 4px; }

.wheel.spinning {
  animation: wheel-spin 0.6s linear infinite;
}

.wheel.slow-spin {
  animation: wheel-spin-slow 1.2s linear infinite;
}

/* ═══════════════════════════════════════════════════ */
/* PSD GATES - Clear & Realistic */
/* ═══════════════════════════════════════════════════ */
.psd-col {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 8px;
  height: 60px;
  background: linear-gradient(
    180deg,
    #2d3748 0%,
    #1a202c 100%
  );
  border: 1px solid #0a0a0a;
  border-radius: 3px 3px 0 0;
  z-index: 8;
  box-shadow:
    inset 0 1px 2px rgba(255, 255, 255, 0.05),
    0 2px 4px rgba(0, 0, 0, 0.3);
}

.door-l, .door-r {
  position: absolute;
  top: 6px;
  width: 50%;
  height: 44px;
  background: linear-gradient(
    180deg,
    #374151 0%,
    #1f2937 100%
  );
  border: 1px solid #111827;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.door-l {
  left: 0;
  border-radius: 2px 0 0 2px;
  border-right: none;
}

.door-r {
  right: 0;
  border-radius: 0 2px 2px 0;
  border-left: none;
}

.door-l.open, .door-r.open {
  background: linear-gradient(
    180deg,
    rgba(16, 185, 129, 0.25) 0%,
    rgba(16, 185, 129, 0.15) 100%
  );
  border-color: var(--color-emerald);
  box-shadow:
    inset 0 1px 0 rgba(16, 185, 129, 0.3),
    0 0 12px rgba(16, 185, 129, 0.2);
}

.door-l.jam, .door-r.jam {
  background: linear-gradient(
    180deg,
    rgba(239, 68, 68, 0.25) 0%,
    rgba(239, 68, 68, 0.15) 100%
  );
  border-color: var(--color-danger);
  box-shadow:
    inset 0 1px 0 rgba(239, 68, 68, 0.3),
    0 0 12px rgba(239, 68, 68, 0.3);
  animation: door-jam 1s ease-in-out infinite;
}

@keyframes door-jam {
  0%, 100% { box-shadow: inset 0 1px 0 rgba(239, 68, 68, 0.3), 0 0 12px rgba(239, 68, 68, 0.3); }
  50% { box-shadow: inset 0 1px 0 rgba(239, 68, 68, 0.3), 0 0 20px rgba(239, 68, 68, 0.5); }
}

/* Train lighting */
.hl {
  position: absolute;
  bottom: 22px;
  width: 14px;
  height: 8px;
  border-radius: 4px;
  transition: opacity 0.4s ease;
  z-index: 2;
}

.hl-f {
  right: 8px;
  background: radial-gradient(
    ellipse at center,
    #fff 0%,
    #fff9c4 30%,
    rgba(255, 249, 196, 0.6) 60%,
    transparent 100%
  );
  box-shadow:
    0 0 15px 4px rgba(255, 249, 196, 0.6),
    0 0 30px 8px rgba(255, 249, 196, 0.3);
  animation: headlight-pulse 2s ease-in-out infinite;
}

.hl-r {
  left: 8px;
  background: radial-gradient(
    ellipse at center,
    #ff6b6b 0%,
    var(--color-danger) 50%,
    rgba(239, 68, 68, 0.6) 100%
  );
  box-shadow:
    0 0 10px 3px rgba(239, 68, 68, 0.6),
    0 0 20px 6px rgba(239, 68, 68, 0.3);
}

@keyframes headlight-pulse {
  0%, 100% { opacity: 0.9; }
  50% { opacity: 1; }
}

.door-r {
  right: 0;
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
}

.door-l.open, .door-r.open {
  background: rgba(16, 185, 129, 0.4);
  border-color: var(--status-ok);
}

.door-l.jam, .door-r.jam {
  background: rgba(239, 68, 68, 0.4);
  border-color: var(--status-error);
}

/* Gate status indicator */
.g-stat {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  border: 1px solid var(--bg-tertiary);
}

.g-stat.closed { background: var(--text-muted); }
.g-stat.open { background: var(--status-ok); }
.g-stat.jam { background: var(--status-error); animation: status-pulse 1.5s infinite; }

@keyframes status-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.7; transform: scale(1.2); }
}

/* Coupling - Realistic connector */
.coupling {
  width: 6px;
  height: 14px;
  background: linear-gradient(
    180deg,
    #374151 0%,
    #1f2937 100%
  );
  border: 1px solid #0a0a0a;
  border-radius: 2px;
  margin-bottom: 12px;
  flex-shrink: 0;
  align-self: flex-end;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.4);
}

/* ── MOTION EFFECTS ────────────────────────────────────────────────────────── */
.splines {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 5;
  overflow: hidden;
  opacity: 0;
  transition: opacity 0.25s ease;
}

.sl {
  position: absolute;
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(100, 160, 255, 0.4),
    rgba(150, 200, 255, 0.3),
    rgba(100, 160, 255, 0.4),
    transparent
  );
  border-radius: 2px;
  animation: speedline-move 0.6s linear infinite;
}

@keyframes speedline-move {
  0% { transform: translateX(-100%); opacity: 0; }
  50% { opacity: 0.7; }
  100% { transform: translateX(100%); opacity: 0; }
}

/* Sparks from wheels/overhead line */
.spark {
  position: absolute;
  width: 4px;
  height: 4px;
  background: radial-gradient(circle, #fff 0%, #ffd54f 50%, transparent 100%);
  border-radius: 50%;
  opacity: 0;
  pointer-events: none;
  z-index: 30;
  filter: blur(0.5px);
}

.spark.active {
  animation: spark-fly 0.5s ease-out forwards;
}

@keyframes spark-fly {
  0% {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
  100% {
    opacity: 0;
    transform: scale(0.3) translateY(-30px) translateX(var(--spark-x, 0));
  }
}

/* ── PLATFORM SCREEN DOORS (PSD) ───────────────────────────────────────────── */
.psd-layer {
  position: absolute;
  bottom: 64px;
  left: 0;
  right: 0;
  height: 110px;
  display: flex;
  z-index: 25;
  pointer-events: none;
}

.psd-unit {
  flex: 1;
  position: relative;
  display: flex;
  align-items: flex-end;
  padding: 0 2px;
}

.door-l,
.door-r {
  position: absolute;
  bottom: 0;
  height: 90px;
  width: 50%;
  border-radius: 4px 4px 0 0;
  transition: width 0.75s cubic-bezier(0.4, 0, 0.2, 1), background-color 0.4s ease;
  overflow: hidden;
  box-shadow:
    inset 0 2px 6px rgba(255, 255, 255, 0.1),
    0 -2px 4px rgba(0, 0, 0, 0.2);
}

.door-l {
  left: 0;
  background: linear-gradient(
    180deg,
    rgba(21, 101, 192, 0.85) 0%,
    rgba(13, 71, 161, 0.9) 100%
  );
  border: 1px solid rgba(45, 79, 138, 0.6);
  border-radius: 4px 0 0 0;
}

.door-r {
  right: 0;
  background: linear-gradient(
    180deg,
    rgba(21, 101, 192, 0.85) 0%,
    rgba(13, 71, 161, 0.9) 100%
  );
  border: 1px solid rgba(45, 79, 138, 0.6);
  border-radius: 0 4px 0 0;
}

.door-l.open,
.door-r.open {
  width: 5% !important;
  min-width: 8px;
  background: linear-gradient(
    180deg,
    rgba(16, 185, 129, 0.7) 0%,
    rgba(5, 150, 105, 0.8) 100%
  );
  border-color: rgba(16, 185, 129, 0.5);
  box-shadow:
    inset 0 2px 6px rgba(255, 255, 255, 0.15),
    0 0 15px rgba(16, 185, 129, 0.3);
}

.door-l.jammed,
.door-r.jammed {
  background: linear-gradient(
    180deg,
    rgba(185, 28, 28, 0.9) 0%,
    rgba(127, 29, 29, 0.9) 100%
  ) !important;
  border-color: var(--danger) !important;
  animation: door-jam 0.15s ease-in-out infinite alternate;
}

.door-l.jammed::before,
.door-r.jammed::before {
  content: '!';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  font-weight: 700;
  color: white;
  text-shadow: 0 0 10px currentColor;
  animation: alert-blink 1s ease-in-out infinite;
}

@keyframes door-jam {
  from { transform: translateX(-1px); }
  to { transform: translateX(1px); }
}

@keyframes alert-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* Glass panel */
.d-glass {
  position: absolute;
  top: 12px;
  left: 12%;
  width: 76%;
  height: 54%;
  background: rgba(170, 215, 255, 0.08);
  border-radius: 3px;
  border: 1px solid rgba(120, 180, 240, 0.22);
  backdrop-filter: blur(2px);
}

.d-glass::after {
  content: '';
  position: absolute;
  top: 10%;
  left: 15%;
  width: 20%;
  height: 80%;
  background: rgba(255, 255, 255, 0.12);
  border-radius: 2px;
  transform: skewX(-10deg);
}

/* LED indicator */
.d-led {
  position: absolute;
  top: 4px;
  left: 0;
  right: 0;
  height: 4px;
  border-radius: 3px;
  transition: all 0.3s ease;
}

.led-cl {
  background: linear-gradient(90deg, #1565c0, #0d47a1);
  box-shadow: 0 0 8px rgba(21, 101, 192, 0.6);
}

.led-op {
  background: linear-gradient(90deg, var(--color-emerald), #059669);
  box-shadow: 0 0 10px rgba(16, 185, 129, 0.8);
}

.led-jm {
  background: linear-gradient(90deg, var(--color-danger), #dc2626);
  box-shadow: 0 0 12px rgba(239, 68, 68, 0.9);
  animation: led-alert 1s ease-in-out infinite;
}

@keyframes led-alert {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Gate Label */
.g-id {
  position: absolute;
  bottom: -16px;
  left: 50%;
  transform: translateX(-50%);
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6rem;
  color: var(--text-tertiary);
  white-space: nowrap;
  opacity: 0.7;
}

/* ── STATUS BAR ────────────────────────────────────────────────────────────── */
.sbar {
  padding: var(--space-md) var(--space-lg);
  display: flex;
  gap: var(--space-lg);
  align-items: center;
  background: var(--bg-card);
  border-top: 1px solid var(--border-subtle);
  flex-wrap: wrap;
  min-height: 44px;
}

.si {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.si::before {
  content: '▸';
  color: var(--accent-primary);
  font-size: 0.6rem;
  opacity: 0.7;
}

.sv {
  color: var(--accent-tertiary);
  font-weight: 600;
  font-size: 0.75rem;
  padding: 2px 8px;
  background: rgba(59, 130, 246, 0.1);
  border-radius: var(--radius-sm);
  border: 1px solid rgba(59, 130, 246, 0.2);
}

.ph-lbl {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  padding: var(--space-xs) var(--space-md);
  border-radius: 999px;
  background: rgba(0, 180, 216, 0.1);
  border: 1px solid rgba(0, 180, 216, 0.2);
  color: var(--accent-cyan);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.ph-lbl.boarding {
  background: rgba(16, 185, 129, 0.15);
  border-color: rgba(16, 185, 129, 0.3);
  color: var(--status-ok);
}

.ph-lbl.alert {
  background: rgba(239, 68, 68, 0.15);
  border-color: rgba(239, 68, 68, 0.3);
  color: var(--status-error);
}

/* Legend Bar */
.leg-bar {
  padding: var(--space-sm) var(--space-lg);
  display: flex;
  gap: var(--space-md);
  flex-wrap: wrap;
  background: var(--bg-card);
  border-top: 1px solid var(--border-subtle);
}

.li {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: 0.7rem;
  color: var(--text-tertiary);
  font-family: 'JetBrains Mono', monospace;
}

.ld {
  width: 12px;
  height: 12px;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
  border: 1px solid var(--border-subtle);
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .scene {
    height: 160px;
  }

  .plat-block {
    margin: var(--space-sm);
    border-radius: var(--radius-md);
  }

  .plat-hdr {
    padding: var(--space-sm) var(--space-md);
  }

  .sbar {
    gap: var(--space-sm);
    padding: var(--space-sm) var(--space-md);
    font-size: 0.65rem;
  }

  .metric-card {
    padding: var(--space-md);
  }

  .metric-value {
    font-size: 1.5rem;
  }

  .main-header {
    flex-direction: column;
    gap: var(--space-md);
    align-items: flex-start;
  }

  .station-title {
    font-size: 1.25rem;
  }
}

/* GPU acceleration for smooth animations */
.train-wrap,
.car-body,
.wheel {
  transform: translateZ(0);
  backface-visibility: hidden;
  perspective: 1000px;
}

/* Smooth scrolling */
html {
  scroll-behavior: smooth;
}

/* Focus styles for accessibility */
*:focus-visible {
  outline: 2px solid var(--accent-primary);
  outline-offset: 2px;
}

/* Print styles */
@media print {
  [data-testid="stSidebar"] {
    display: none;
  }

  .main-header {
    box-shadow: none;
    border: 1px solid #ccc;
  }
}
</style>
</head>
<body>
<div class="sta-banner">
  <span class="sta-name">"""
        + station_name
        + """</span>
  <span><span class="live-dot"></span><span class="live-lbl">LIVE SIM</span></span>
</div>
<div id="root"></div>

<script>
const PLATFORMS = """
        + platforms_json
        + """;

// ── Easing ───────────────────────────────────────
const lerp=(a,b,t)=>a+(b-a)*t;
const clamp=(v,lo,hi)=>Math.max(lo,Math.min(hi,v));
const easeOut=t=>1-Math.pow(1-t,3);
const easeIn=t=>t*t*t;
const easeInOut=t=>t<.5?2*t*t:-1+(4-2*t)*t;

const PHASES={APPROACH:4400,BRAKE:1100,STOP:380,DOOR_OPEN:850,BOARD:3800,DOOR_CLOSE:850,WAIT:550,DEPART:3400,EMPTY:1700};

const TNAMES=["ICE 574","S7","RE 3312","ICE 891","ICE 102","RE 5","ICE 700","RE 220","ICE 11","RE 40","ICE 921","S12","S-Bahn 3","ICE 202","RE 90","ICE 77","S11","ICE 19"];
const PAX_SKINS=["#e07850","#c06840","#d09070","#b08060","#f0c090","#a07060"];
const PAX_SHIRTS=["#1565c0","#0d47a1","var(--color-emerald)","#374151","#6d28d9","#b91c1c"];

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
      <div class="bldgs" id="bg${idx}"></div>
      <div class="plat-floor"></div>
      <div class="edge-strip"></div>
      <div class="track" id="tr${idx}"></div>
      <div class="train-wrap" id="tw${idx}"></div>
      <div class="ghost-wrap gt-a" style="left:0"><div class="ghost-train" style="width:70px"><div class="ghost-cab"></div><div class="ghost-wins"></div></div></div>
      <div class="ghost-wrap gt-b" style="right:0"><div class="ghost-train" style="width:55px"><div class="ghost-cab"></div><div class="ghost-wins gw2"></div></div></div>
      <div class="psd-layer" id="psd${idx}"></div>
    </div>
    <div class="sbar">
      <span class="ph-lbl" id="ph${idx}">INIT</span>
      <span class="si">TRAIN <span class="sv" id="tn${idx}">—</span></span>
      <span class="si">TEMP <span class="sv" id="tp${idx}">—</span></span>
      <span class="si">SYNC <span class="sv" id="sy${idx}">—</span></span>
      <span class="si">PAX <span class="sv" id="pa${idx}">—</span></span>
    </div>
    `;
  return div;
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

function buildTrain(numCars,idx){
  let h='';
    for(let c=0;c<numCars;c++){
    const loco=c===0;
    const cw=loco?118:88, ch=loco?56:46;
    const nw=0;
    const wins='';
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
        if(w){
          let cls='wheel '+(p==='wl'?'wl':'wr');
          if(speed==='fast') cls+=' wspin';
          else if(speed==='vfast') cls+=' wspin-fast';
          else if(speed==='slow') cls+=' wslow';
          w.className=cls;
        }
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
  const numCars=Math.min(10,Math.max(3,Math.floor(W/96)));
  trainEl.innerHTML=buildTrain(numCars,idx);
  const trainW=numCars*84+16;
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
    buildBuildings(idx);
    buildTrack(idx);
    buildPSD(idx,pdata.gates);
    setTimeout(()=>animatePlatform(idx,pdata.gates,pdata.train_name),idx*2100);
  }));
});
</script>
</body>
</html>"""
    )
    return html


# ── Narrative Intelligence: Green State Banner ──
all_anomalies = df[df["maintenance_status"].isin(["CRITICAL", "WARNING"])] if "maintenance_status" in df.columns else pd.DataFrame()
ranked_all = []
try:
    if all_anomalies.empty:
        # All clear - show green state celebration
        green_html = build_green_state_banner(
            station_count=len(stations),
            streak_days=st.session_state.get("green_streak", 0),
            # TODO: Compute uptime_pct from actual data (e.g., (1 - alerts/total_gates) * 100)
            uptime_pct=round((1 - (alerts / max(gates_total, 1))) * 100, 1),
            last_incident=st.session_state.get("last_incident_time", "N/A"),
            # TODO: Compute mtbi from incident history
            mtbi="72h",
        )
        st.markdown(green_html, unsafe_allow_html=True)
        st.session_state["green_streak"] = st.session_state.get("green_streak", 0) + 1
    else:
        st.session_state["green_streak"] = 0
        ranked_all = rank_anomalies(all_anomalies)
except Exception as e:
    logger.warning(f"Narrative intelligence failed: {e}")

# ── KPI Ticker Strip ──
try:
    ticker_incidents = []
    # Use ranked anomalies (enriched with narratives & timestamps)
    if ranked_all:
        for anomaly in ranked_all[:5]:
            ticker_incidents.append({
                "station": anomaly.get("station", ""),
                "description": (
                    f"{anomaly.get('gate', '')} | "
                    f"TEMP {anomaly.get('temp', 0):.1f}°C | "
                    f"VIB {anomaly.get('vib', 0):.1f} mm/s | "
                    f"RISK {anomaly.get('risk', 0):.0f}"
                ),
                "severity": anomaly.get("severity", "warning").lower(),
                "timestamp": anomaly.get("timestamp", ""),
                "gate": anomaly.get("gate", ""),
                "temp": anomaly.get("temp", 0),
                "vib": anomaly.get("vib", 0),
                "risk": anomaly.get("risk", 0),
            })
    elif not all_anomalies.empty:
        for _, row in all_anomalies.head(5).iterrows():
            ticker_incidents.append({
                "station": str(row.get("station", "")),
                "description": str(row.get("gate_id", "") or row.get("train", "") or "anomaly"),
                "severity": str(row.get("maintenance_status", "warning")).lower(),
                "timestamp": "",
            })
    ticker_kpis = [
        {"label": "Gates Active", "value": f"{gates_active}/{gates_total}"},
        {"label": "Sync Rate", "value": f"{avg_sync}%"},
        {"label": "Passengers", "value": f"{p_total:,}"},
        {"label": "Alerts", "value": str(alerts)},
    ]
    ticker_html = build_kpi_ticker(ticker_incidents, ticker_kpis)
    st.markdown(ticker_html, unsafe_allow_html=True)
except Exception as e:
    logger.warning(f"Ticker rendering failed: {e}")

st.markdown(
    '<div class="main-content page-enter">',
    unsafe_allow_html=True,
)

# ═══════════════════════════════════════════════════
# ── TAB: LIVE OPERATIONS ──────────────────────────
# ═══════════════════════════════════════════════════
if active_tab == "ops":
    # ── Modern KPI Row — single HTML block ──
    kpi_icons = ["🚪", "⚡", "👥", "⚠️", "🔔"]
    kpi_data = [
        (f"{gates_active}/{gates_total}", "PSD Gates", "Active Systems",
         "+12%", True, ""),
        (f"{avg_sync}%", "Sync Efficiency", "Door Alignment",
         f"{'+' if avg_sync >= 85 else ''}{85 - avg_sync}%", avg_sync >= 85,
         "success" if avg_sync >= 85 else "warning"),
        (f"{p_total:,}", "Passenger Flow", "On Platform",
         "+8%", True, ""),
        (str(alerts), "Critical Alerts", "Immediate Action",
         f"{'+' if alerts > 0 else '-'}{alerts}", False,
         "critical" if alerts > 0 else "success"),
        (str(warnings), "Warnings", "Under Observation",
         "", True, "warning" if warnings > 0 else "success"),
    ]

    cards_html = ""
    for idx, (val, label, sub, trend, up, sc) in enumerate(kpi_data):
        t = f'<div class="trend {"up" if up else "down"}">{trend}</div>' if trend else ''
        sc_cls = f' {sc}' if sc else ''
        cards_html += f"""
        <div class="kpi-card-modern{sc_cls}" style="animation-delay:{idx*0.1}s">
            <div class="kpi-header">
                <div class="kpi-icon">{kpi_icons[idx]}</div>
                {t}
            </div>
            <div class="kpi-body">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{val}</div>
                <div class="kpi-sub">{sub}</div>
            </div>
            <div class="kpi-progress-bar"></div>
        </div>"""

    st.html(f'<div class="kpi-strip modern-kpi-grid">{cards_html}</div>')

    # ── Station Overview Header ──
    st.html(
        f'<div class="section-header">'
        f'<div class="section-title">'
        f'<span class="pulse-dot"></span>'
        f'<span>{current_station} — Live Operations</span>'
        f'</div>'
        f'<div class="section-badge section-badge-ok">REAL-TIME</div>'
        f'</div>'
    )

    # ── Main Split with Glassmorphism Design ──
    left, right = st.columns([65, 35], gap="large")

    with left:
        with st.container(key="panel-left"):
            st.html(
                '<div class="panel-header-modern">'
                '<div class="header-left">'
                '<span class="pulse-dot"></span>'
                '<span class="panel-title">Live Platform Simulation</span>'
                '</div>'
                '<div class="header-right">'
                '<span class="live-badge">LIVE</span>'
                '<span class="refresh-indicator">↻</span>'
                '</div>'
                '</div>'
            )

            station_data = df[df["station"] == current_station].copy()
            num_platforms = station_data["platform"].nunique()
            anim_html = build_train_animation(current_station, station_data)
            anim_height = num_platforms * 295 + 80

            st.components.v1.html(
                anim_html, height=anim_height, scrolling=False)

    with right:
        cycles_df, temp_df = get_psd_analytics(current_station)

        with st.container(key="panel-right"):
            st.html(
                '<div class="panel-header-modern">'
                '<div class="header-left">'
                '<span class="panel-icon">📊</span>'
                '<span class="panel-title">Sensor Analytics</span>'
                '</div>'
                '<div class="header-right">'
                '<span class="time-range">Last 24h</span>'
                '</div>'
                '</div>'
            )

            # Enhanced temperature chart with animations
            fig_temp = go.Figure()
            fig_temp.add_trace(
                go.Scatter(
                    x=temp_df["Hour"],
                    y=temp_df["Avg Temp (°C)"],
                    mode="lines+markers",
                    line=dict(color="var(--color-danger)", width=3, shape="spline"),
                    marker=dict(size=6, color="var(--color-danger)", symbol="circle"),
                    fill="tozeroy",
                    fillcolor="rgba(239,68,68,0.1)",
                    name="Temperature"
                )
            )

            # Add warning zone shading
            fig_temp.add_hrect(y0=45, y1=60, line_width=0,
                               fillcolor="rgba(249,115,22,0.1)", opacity=0.3)
            fig_temp.add_hline(
                y=45,
                line_dash="dash",
                line_color="#f97316",
                line_width=2,
                annotation_text="⚠️ Warning Threshold",
                annotation_font_color="#f97316",
                annotation_position="top right"
            )

            fig_temp.update_layout(
                height=280,
                margin=dict(t=30, l=0, r=0, b=0),
                hovermode='x unified',
                transition_duration=500
            )

            style_chart(fig_temp, legend=False, yaxis=dict(
                gridcolor="rgba(30,41,59,0.1)", zeroline=False))
            render_chart(fig_temp, key='fig_temp_l2371_L2371', use_container_width=True)

            # Enhanced door cycles chart with animations
            fig_cycles = px.bar(
                cycles_df,
                x="Hour",
                y="Door Cycles",
                color_discrete_sequence=["#3b82f6"]
            )
            fig_cycles.update_traces(
                marker_line_width=0,
                opacity=0.85,marker_pattern_shape=""
            )

            fig_cycles.update_layout(
                height=280,
                margin=dict(t=30, l=0, r=0, b=0),
                bargap=0.2,
                transition_duration=500,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )

            style_chart(fig_cycles, legend=False, yaxis=dict(
                gridcolor="rgba(30,41,59,0.1)", zeroline=False))
            render_chart(fig_cycles, key='fig_cycles_l2397_L2396', use_container_width=True)

    # right panel auto-closed by st.container()

    # Modern divider with gradient
    st.html('<div class="gradient-divider"></div>')

    # ── Quick Insight Bar ──
    st.html(
        f'<div class="insight-bar">'
        f'<span class="glass-trend trend-up">🚄 {num_platforms} Platforms Active</span>'
        f'<span class="glass-trend trend-up">📊 {avg_sync:.0f}% Avg Sync</span>'
        f'<span class="glass-trend trend-neutral">👥 {p_total:,} Passengers</span>'
        f'<span class="glass-trend {"trend-down" if alerts > 0 else "trend-up"}">⚠️ {alerts} Alerts</span>'
        f'</div>'
    )

    # ── Enhanced Sensor Logs with Modern Table ──
    st.html(
        '<div class="section-header">'
        '<div class="section-title">'
        '<span class="title-icon">🔍</span>'
        '<span>Detailed Sensor Diagnostics</span>'
        '</div>'
        '<div class="section-badge">Real-time</div>'
        '</div>'
    )

    # Improved color functions with gradients
    def color_temp(val):
        if val > 45:
            return "background: linear-gradient(90deg, #7f1d1d, #991b1b); color: #fca5a5; font-weight: 700; border-left: 3px solid var(--color-danger);"
        elif val > 35:
            return "background: linear-gradient(90deg, #78350f, #92400e); color: #fcd34d; font-weight: 600; border-left: 3px solid var(--color-warning);"
        elif val > 28:
            return "background: linear-gradient(90deg, #064e3b, #065f46); color: #86efac; border-left: 3px solid var(--color-emerald);"
        return "background: linear-gradient(90deg, #1e293b, #1e293b); color: var(--text-secondary);"

    def color_risk(val):
        if val >= 70:
            return "background: linear-gradient(90deg, #7f1d1d, #991b1b); color: #fca5a5; font-weight: 700; border-left: 3px solid var(--color-danger);"
        elif val >= 40:
            return "background: linear-gradient(90deg, #78350f, #92400e); color: #fcd34d; font-weight: 600; border-left: 3px solid var(--color-warning);"
        elif val >= 20:
            return "background: linear-gradient(90deg, #064e3b, #065f46); color: #86efac; border-left: 3px solid var(--color-emerald);"
        return "background: linear-gradient(90deg, #1e293b, #1e293b); color: var(--color-emerald);"

    def color_status(val):
        colors = {
            "CRITICAL": "background: linear-gradient(90deg, #7f1d1d, #991b1b); color: #fca5a5; font-weight: 700; border-left: 3px solid var(--color-danger);",
            "WARNING": "background: linear-gradient(90deg, #78350f, #92400e); color: #fcd34d; font-weight: 600; border-left: 3px solid var(--color-warning);",
            "MONITOR": "background: linear-gradient(90deg, #1e3a8a, #1e40af); color: #93c5fd; border-left: 3px solid #3b82f6;",
            "OPTIMAL": "background: linear-gradient(90deg, #064e3b, #065f46); color: #6ee7b7; border-left: 3px solid var(--color-emerald);",
        }
        return colors.get(val, "")

    display_cols = [
        "platform", "gate_id", "train", "door_state", "sensor_temp",
        "sensor_vib", "sync_score", "risk_score", "maintenance_status", "people"
    ]

    # Sort and prepare data
    display_data = station_data[display_cols].sort_values(
        ["platform", "gate_id"])

    # Apply styling
    styled = (
        display_data
        .style
        .map(color_temp, subset=["sensor_temp"])
        .map(color_risk, subset=["risk_score"])
        .map(color_status, subset=["maintenance_status"])
        .format({
            "sensor_temp": "{:.1f}°C",
            "sensor_vib": "{:.2f} mm/s",
            "sync_score": "{:.0f}%",
            "risk_score": "{:.0f}/100",
            "people": "{:,.0f}"
        })
        .set_properties(**{
            'padding': '12px',
            'font-size': '13px',
            'border-radius': '6px'
        })
        .set_table_styles([
            {'selector': 'thead th', 'props': [
                ('background', '#1e293b'),
                ('color', 'var(--text-primary)'),
                ('padding', '12px'),
                ('font-weight', '600'),
                ('font-size', '13px'),
                ('text-transform', 'uppercase'),
                ('letter-spacing', '0.5px')
            ]},
            {'selector': 'tbody tr', 'props': [
                ('transition', 'all 0.2s ease'),
                ('border-bottom', '1px solid rgba(30,41,59,0.3)')
            ]},
            {'selector': 'tbody tr:hover', 'props': [
                ('transform', 'translateX(5px)'),
                ('background', 'rgba(59,130,246,0.1)')
            ]}
        ])
    )

    # Display dataframe with custom height and scroll
    st.dataframe(
        styled,
        use_container_width=True,
        hide_index=True,
        height=400
    )

    # Enhanced export section
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.html('<div class="export-info">📋 Showing latest 100 sensor readings</div>')

    with col3:
        ops_csv = convert_to_csv(display_data)
        st.download_button(
            label="📥 Export Diagnostics (CSV)",
            data=ops_csv,
            file_name=f"station_diagnostics_{current_station.replace(' ', '_')}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )

    # ── Station Summary Stats Cards ──
    st.html(
        '<div class="section-header">'
        '<div class="section-title">'
        '<span class="title-icon">📊</span>'
        '<span>Station Performance Summary</span>'
        '</div>'
        '<div class="section-badge section-badge-ok">LIVE</div>'
        '</div>'
    )

    avg_temp = float(station_data["sensor_temp"].mean())
    avg_vib = float(station_data["sensor_vib"].mean())
    avg_risk = float(station_data["risk_score"].mean())
    gate_statuses = station_data["maintenance_status"].value_counts().to_dict()
    optimal_count = gate_statuses.get("OPTIMAL", 0)
    warning_count = gate_statuses.get("WARNING", 0) + gate_statuses.get("MONITOR", 0)
    critical_count = gate_statuses.get("CRITICAL", 0)
    total_gates_local = int(station_data["gate_id"].nunique())

    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    with col_s1:
        st.markdown(
            f'<div class="stat-card info press-effect">'
            f'<div class="stat-card-label">Avg Temperature</div>'
            f'<div class="stat-card-value">{avg_temp:.1f}°C</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col_s2:
        st.markdown(
            f'<div class="stat-card warning press-effect">'
            f'<div class="stat-card-label">Avg Vibration</div>'
            f'<div class="stat-card-value">{avg_vib:.2f} mm/s</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col_s3:
        risk_cls = "danger" if avg_risk >= 40 else ("warning" if avg_risk >= 20 else "success")
        st.markdown(
            f'<div class="stat-card {risk_cls} press-effect">'
            f'<div class="stat-card-label">Avg Risk Score</div>'
            f'<div class="stat-card-value">{avg_risk:.1f}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col_s4:
        health_pct = int(optimal_count / total_gates_local * 100) if total_gates_local > 0 else 0
        st.markdown(
            f'<div class="stat-card success press-effect">'
            f'<div class="stat-card-label">Gate Health</div>'
            f'<div class="stat-card-value">{health_pct}%</div>'
            f'<div style="font-size:0.65rem;color:var(--text-muted);">'
            f'{optimal_count}/{total_gates_local} optimal  •  {warning_count} warn  •  {critical_count} crit</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.html('<div class="gradient-divider"></div>')

    # ── Sensor Correlation Scatter ──
    st.html(
        '<div class="section-header">'
        '<div class="section-title">'
        '<span class="title-icon">🔬</span>'
        '<span>Sensor Correlation — Temperature vs Vibration</span>'
        '</div>'
        '<div class="section-badge section-badge-ok">ANALYSIS</div>'
        '</div>'
    )

    fig_scatter_corr_OPS = px.scatter(
        station_data,
        x="sensor_temp",
        y="sensor_vib",
        color="risk_score",
        size="people",
        hover_data={"station": True, "gate_id": True, "sensor_temp": ":.1f", "sensor_vib": ":.2f", "risk_score": ":.1f"},
        labels={"sensor_temp": "Temperature (°C)", "sensor_vib": "Vibration (mm/s)", "risk_score": "Risk Score"},
        color_continuous_scale="RdYlGn_r",
        title="",
        height=400,
    )
    fig_scatter_corr_OPS.update_traces(
        marker=dict(line=dict(width=0.5, color="rgba(0,0,0,0.3)")),
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Gate: %{customdata[1]}<br>"
            "Temp: %{x:.1f}°C<br>"
            "Vib: %{y:.2f} mm/s<br>"
            "Risk: %{marker.color:.1f}<br>"
            "<extra></extra>"
        ),
    )
    style_chart(fig_scatter_corr_OPS, legend=False, coloraxis_colorbar=dict(
        title=dict(text="Risk Score", font=dict(color="var(--text-secondary)", size=10)),
        tickfont=dict(color="var(--text-secondary)", size=9), thickness=6, len=0.7,
    ))
    render_chart(fig_scatter_corr_OPS, key="fig_scatter_corr_OPS", use_container_width=True)

    st.html('<div class="gradient-divider"></div>')

    # ── Platform Comparison Matrix ──
    st.html(
        '<div class="section-header">'
        '<div class="section-title">'
        '<span class="title-icon">📋</span>'
        '<span>Platform Comparison Matrix</span>'
        '</div>'
        '<div class="section-badge section-badge-ok">BENCHMARK</div>'
        '</div>'
    )

    if "platform" in station_data.columns:
        matrix_df = station_data.groupby("platform").agg(
            Gates=("gate_id", "nunique"),
            Avg_Temp=("sensor_temp", "mean"),
            Avg_Vib=("sensor_vib", "mean"),
            Avg_Sync=("sync_score", "mean"),
            Avg_Risk=("risk_score", "mean"),
            Passengers=("people", "sum"),
        ).reset_index()
        matrix_df.columns = ["Platform", "Gates", "Avg Temp (°C)", "Avg Vib (mm/s)", "Sync Rate (%)", "Avg Risk", "Passengers"]
        matrix_df["Avg Temp (°C)"] = matrix_df["Avg Temp (°C)"].round(1)
        matrix_df["Avg Vib (mm/s)"] = matrix_df["Avg Vib (mm/s)"].round(2)
        matrix_df["Sync Rate (%)"] = matrix_df["Sync Rate (%)"].round(1)
        matrix_df["Avg Risk"] = matrix_df["Avg Risk"].round(1)
        matrix_df["Passengers"] = matrix_df["Passengers"].astype(int)

        styled = matrix_df.style.background_gradient(
            subset=["Avg Temp (°C)", "Avg Vib (mm/s)", "Avg Risk"],
            cmap="RdYlGn_r",
        ).background_gradient(
            subset=["Sync Rate (%)", "Passengers"],
            cmap="RdYlGn",
        ).format({
            "Avg Temp (°C)": "{:.1f}",
            "Avg Vib (mm/s)": "{:.2f}",
            "Sync Rate (%)": "{:.1f}%",
            "Avg Risk": "{:.1f}",
            "Passengers": "{:,}",
        })

        st.dataframe(
            styled,
            use_container_width=True,
            height=min(100 + 35 * len(matrix_df), 350),
        )

# ═══════════════════════════════════════════════════
# ── TAB: NETWORK OVERVIEW ─────────────────────────
# ═══════════════════════════════════════════════════
elif active_tab == "network":
    with st.spinner("Loading network data..."):
        net = get_network_summary(df)

    # ═══════════════════════════════════════════════════
    # SECTION 1: Network KPIs
    # ═══════════════════════════════════════════════════
    st.html(
        '<div class="section-header">'
        '<div class="section-title">'
        '<span class="title-icon">📡</span>'
        '<span>Network KPIs</span>'
        '</div>'
        '<div class="section-badge section-badge-ok">LIVE</div>'
        '</div>'
    )

    kpi_icons_net = ["🚪", "✅", "⚠️", "👥"]
    kpi_data_net = [
        (
            f"{net['total_gates']}",
            "Network Gates",
            f"Across {len(stations)} Stations",
            "",
            True,
            "",
        ),
        (
            f"{net['optimal_count']}",
            "Optimal Gates",
            "Running Normally",
            f"{net['optimal_count']}/{net['total_gates']}",
            True,
            "success",
        ),
        (
            f"{net['critical_count']}",
            "Network Alerts",
            "Critical Incidents",
            f"{'+' if net['critical_count'] > 0 else ''}{net['critical_count']}",
            net["critical_count"] == 0,
            "critical" if net["critical_count"] > 0 else "success",
        ),
        (
            f"{net['total_people']:,}",
            "Total Passengers",
            "On All Platforms",
            "",
            True,
            "",
        ),
    ]

    cards_html = ""
    for idx, (val, label, sub, trend, up, sc) in enumerate(kpi_data_net):
        t = (
            f'<div class="trend {"up" if up else "down"}">{trend}</div>'
            if trend
            else ""
        )
        sc_cls = f" {sc}" if sc else ""
        cards_html += f"""
        <div class="kpi-card-modern{sc_cls}" style="animation-delay:{idx*0.1}s">
            <div class="kpi-header">
                <div class="kpi-icon">{kpi_icons_net[idx]}</div>
                {t}
            </div>
            <div class="kpi-body">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{val}</div>
                <div class="kpi-sub">{sub}</div>
            </div>
            <div class="kpi-progress-bar"></div>
        </div>"""

    st.html(f'<div class="kpi-strip modern-kpi-grid network-kpi-grid">{cards_html}</div>')

    # ═══════════════════════════════════════════════════
    # SECTION 2: Business Network Map
    # ═══════════════════════════════════════════════════
    st.html(
        '<div class="section-header">'
        '<div class="section-title">'
        '<span class="title-icon">🗺️</span>'
        '<span>Business Network Map — Germany</span>'
        '</div>'
        '</div>'
    )

    try:
        map_df = get_business_map_data()

        summary_html = '<div class="phase-summary">'
        for label, color in [
            ("Established", "#3b82f6"),
            ("Present", "#06b6d4"),
            ("Expanding", "var(--color-warning)"),
            ("Future", "var(--color-emerald)"),
        ]:
            cnt = len(map_df[map_df["status"] == label])
            summary_html += (
                '<div class="phase-card">'
                '<div class="phase-dot" style="background:' + color + ';box-shadow:0 0 10px ' + color + '80;"></div>'
                '<span class="phase-label">' + label + '</span>'
                '<span class="phase-count">' + str(cnt) + '</span>'
                '</div>'
            )
        summary_html += "</div>"
        st.html(summary_html)

        phase_colors = {
            "Established": "#3b82f6",
            "Present": "#06b6d4",
            "Expanding": "var(--color-warning)",
            "Future": "var(--color-emerald)",
        }

        def get_phase_plots(map_df_local):
            if map_df_local is None or map_df_local.empty:
                return {}
            phases = ["Established", "Present", "Expanding", "Future"]
            colors = {
                "Established": "var(--color-secondary-light)",
                "Present": "#818cf8",
                "Expanding": "#fcd34d",
                "Future": "#34d399",
            }
            sizes = {"Established": 18, "Present": 16, "Expanding": 14, "Future": 12}
            plots = {}

            geo_layout = dict(
                projection_type="natural earth",
                lonaxis_range=[5.8, 15.2],
                lataxis_range=[47.1, 55.2],
                showcountries=True, countrycolor="#4b5563", countrywidth=0.4,
                showcoastlines=True, coastlinecolor="var(--color-secondary-light)", coastlinewidth=0.5,
                showland=True, landcolor="#162a4d",
                showocean=True, oceancolor="#080c16",
                showlakes=True, lakecolor="#0f172a",
                showrivers=True, rivercolor="#1e40af", riverwidth=0.6,
                bgcolor="#080c16",
            )

            for phase in phases:
                phase_df = map_df_local[map_df_local["status"] == phase]
                color = colors[phase]
                s = sizes[phase]

                fig = go.Figure()

                if not phase_df.empty:
                    lats = phase_df["lat"].tolist()
                    lons = phase_df["lon"].tolist()
                    names = [
                        r["station"].replace(" Hbf", "").replace(" (Main)", "").replace(" Hauptbahnhof", "")
                        for _, r in phase_df.iterrows()
                    ]

                    fig.add_trace(go.Scattergeo(
                        lat=lats, lon=lons,
                        mode="markers",
                        marker=dict(size=s * 3, color=color, opacity=0.15, symbol="circle"), showlegend=False,
                    ))
                    fig.add_trace(go.Scattergeo(
                        lat=lats, lon=lons,
                        mode="markers",
                        marker=dict(size=s * 2, color=color, opacity=0.3, symbol="circle", line=dict(width=0)), showlegend=False,
                    ))
                    fig.add_trace(go.Scattergeo(
                        lat=lats, lon=lons,
                        mode="markers+text",
                        marker=dict(size=s, color=color, opacity=1.0, symbol="circle",
                                    line=dict(width=1.5, color="white")),
                        text=names, textposition="top center",
                        textfont=dict(size=10, color="#f8fafc", family="sans-serif"), hovertext=[f"<b>{n}</b><br>{phase}" for n in names],
                        showlegend=False,
                    ))

                fig.update_geos(**geo_layout)
                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=10, r=10, t=10, b=10),
                    height=320,
                    dragmode=False,
                )
                plots[phase] = fig

            return plots

        phase_order = ["Established", "Present", "Expanding", "Future"]
        col_left, col_right = st.columns(2)

        with st.spinner("Loading maps..."):
            phase_plots = get_phase_plots(map_df)

        for idx, phase in enumerate(phase_order):
            phase_df = map_df[map_df["status"] == phase]
            color = phase_colors[phase]
            station_count = len(phase_df)
            col = col_left if idx < 2 else col_right

            with col:
                st.markdown(
                    f"""
                    <div class="map-panel" style="margin-bottom:14px;">
                        <div class="map-phase-header" style="--phase-color:{color};">
                            <span class="map-phase-title">{phase}</span>
                            <span class="map-phase-count">{station_count}</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                render_chart(phase_plots[phase], key=f"phase_plots_{phase.lower()}", use_container_width=True)

    except Exception as e:
        st.error(f"Could not load business map: {e}")

    # ═══════════════════════════════════════════════════
    # SECTION 3: Station Performance Matrix
    # ═══════════════════════════════════════════════════
    st.html(
        '<div class="section-header">'
        '<div class="section-title">'
        '<span class="title-icon">📊</span>'
        '<span>Station Performance Matrix</span>'
        '</div>'
        '<div class="section-badge">Real-time</div>'
        '</div>'
    )

    with st.container():
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        styled_net = (
            net["station_summary"]
            .style.background_gradient(
                subset=["Avg Sync %"], cmap="Blues", vmin=0, vmax=100
            )
            .background_gradient(subset=["Avg Risk"], cmap="RdYlGn_r", vmin=0, vmax=100)
            .format(
                {"Avg Sync %": "{}%", "Avg Risk": "{:.1f}/100", "Passengers": "{:,}"}
            )
        )
        st.dataframe(styled_net, use_container_width=True, hide_index=True)

        matrix_csv = convert_to_csv(net["station_summary"])
        st.download_button(
            "📥 Export Station Matrix (CSV)",
            data=matrix_csv,
            file_name="station_performance_matrix.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.html('</div>')

    # ═══════════════════════════════════════════════════
    # SECTION 4: Network Analytics (3-col grid)
    # ═══════════════════════════════════════════════════
    st.html(
        '<div class="section-header">'
        '<div class="section-title">'
        '<span class="title-icon">📈</span>'
        '<span>Network Analytics</span>'
        '</div>'
        '</div>'
    )

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        with st.container():
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown(
                '<div class="panel-header">'
                '<span class="panel-icon">👥</span>'
                '<span class="panel-title">Passengers by Station</span>'
                '</div>'
                '<div class="panel-content">',
                unsafe_allow_html=True,
            )
            fig_pass = px.bar(
                net["station_summary"].sort_values("Passengers", ascending=True),
                x="Passengers",
                y="Station",
                orientation="h",
                color="Avg Risk",
                color_continuous_scale=["var(--color-emerald)", "var(--color-warning)", "var(--color-danger)"],
                range_color=[0, 100],
                title="",
            )
            style_chart(fig_pass, hovermode="y unified",
                        coloraxis_colorbar=dict(
                            title=dict(text="Risk", font=dict(
                                color="var(--text-secondary)", size=10)),
                            tickfont=dict(color="var(--text-secondary)", size=9), thickness=6, len=0.7,
                        ))
            fig_pass.update_traces(customdata=net["station_summary"][["Avg Risk"]].values)
            fig_pass.update_layout(height=320)
            render_chart(fig_pass, key="fig_pass_L2827", use_container_width=True)
            st.html('</div></div>')

    with col_b:
        with st.container():
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown(
                '<div class="panel-header">'
                '<span class="panel-icon">🔧</span>'
                '<span class="panel-title">Maintenance Status</span>'
                '</div>'
                '<div class="panel-content">',
                unsafe_allow_html=True,
            )
            color_map = {
                "OPTIMAL": "var(--color-emerald)",
                "MONITOR": "#60a5fa",
                "WARNING": "var(--color-warning)",
                "CRITICAL": "var(--color-danger)",
            }
            fig_pie = px.pie(
                net["status_dist"],
                names="maintenance_status",
                values="Count",
                color="maintenance_status",
                color_discrete_map=color_map,
                hole=0.5,
            )
            style_pie(fig_pie)
            fig_pie.update_traces(
                textposition="inside",
                textinfo="percent",
                textfont_size=10,
                textfont_color="#f1f5f9",
                marker_line_color="rgba(30, 41, 59, 0.3)",
                marker_line_width=1,
                hovertemplate="<b>%{label}</b><br>Gates: %{value}<br>Share: %{percent}<extra></extra>",
            )
            fig_pie.update_layout(height=320)
            render_chart(fig_pie, key="fig_pie_L2866", use_container_width=True)
            st.html('</div></div>')

    with col_c:
        with st.container():
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown(
                '<div class="panel-header">'
                '<span class="panel-icon">🚆</span>'
                '<span class="panel-title">Train Types</span>'
                '</div>'
                '<div class="panel-content">',
                unsafe_allow_html=True,
            )
            if not net["train_type_dist"].empty:
                train_colors = {
                    "ICE": "var(--color-secondary-light)",
                    "RE": "#818cf8",
                    "S-Bahn": "#34d399",
                    "RB": "#fbbf24",
                    "IC": "#f472b6",
                    "FLX": "#a78bfa",
                }
                fig_train = px.pie(
                    net["train_type_dist"],
                    names="train_type",
                    values="Count",
                    color="train_type",
                    color_discrete_map=train_colors,
                    hole=0.5,
                )
                style_pie(fig_train)
                fig_train.update_traces(
                    textposition="inside",
                    textinfo="percent",
                    textfont_size=10,
                    textfont_color="#f1f5f9",
                    marker_line_color="rgba(30, 41, 59, 0.3)",
                    marker_line_width=1,
                    hovertemplate="<b>%{label}</b><br>Trains: %{value}<br>Share: %{percent}<extra></extra>",
                )
                fig_train.update_layout(height=320)
                render_chart(fig_train, key="fig_train_L2908", use_container_width=True)
            else:
                st.markdown(
                    '<div style="text-align: center; color: var(--text-muted); font-size: 0.8rem; padding: 40px 20px;">No train type data available</div>',
                    unsafe_allow_html=True,
                )
            st.html('</div></div>')

    # ═══════════════════════════════════════════════════
    # SECTION 5: Operational Metrics (3-col grid)
    # ═══════════════════════════════════════════════════
    st.html(
        '<div class="section-header">'
        '<div class="section-title">'
        '<span class="title-icon">⚙️</span>'
        '<span>Operational Metrics</span>'
        '</div>'
        '</div>'
    )

    col_d, col_e, col_f = st.columns(3)

    with col_d:
        with st.container():
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown(
                '<div class="panel-header">'
                '<span class="panel-icon">🚪</span>'
                '<span class="panel-title">Door State Distribution</span>'
                '</div>'
                '<div class="panel-content">',
                unsafe_allow_html=True,
            )
            door_color = {
                "closed": "#1565c0",
                "open": "var(--color-emerald)",
                "jammed": "var(--color-danger)",
                "closing": "#0288d1",
            }
            fig_door = px.bar(
                net["door_dist"],
                x="door_state",
                y="Count",
                color="door_state",
                color_discrete_map=door_color,
                category_orders={"door_state": ["closed", "open", "closing", "jammed"]},
            )
            style_chart(fig_door,
                        xaxis=dict(title="", categoryorder="array",
                                   categoryarray=["closed", "open", "closing", "jammed"]),
                        yaxis=dict(title=""))
            fig_door.update_layout(height=320)
            render_chart(fig_door, key="fig_door_L2960", use_container_width=True)
            st.html('</div></div>')

    with col_e:
        if not net["operator_stats"].empty:
            with st.container():
                st.markdown('<div class="panel">', unsafe_allow_html=True)
                st.markdown(
                    '<div class="panel-header">'
                    '<span class="panel-icon">👤</span>'
                    '<span class="panel-title">Operator Performance</span>'
                    '</div>'
                    '<div class="panel-content">',
                    unsafe_allow_html=True,
                )
                op_display = net["operator_stats"].copy()
                op_display = op_display.rename(
                    columns={"Avg Sync %": "Sync %", "Avg Risk": "Risk"}
                )

                def style_sync(val):
                    if val >= 85:
                        return "color: var(--color-emerald); font-weight: 600;"
                    elif val >= 70:
                        return "color: var(--color-warning); font-weight: 600;"
                    else:
                        return "color: var(--color-danger); font-weight: 600;"

                def style_risk(val):
                    if val <= 20:
                        return "color: var(--color-emerald); font-weight: 600;"
                    elif val <= 40:
                        return "color: var(--color-warning); font-weight: 600;"
                    else:
                        return "color: var(--color-danger); font-weight: 600;"

                styled_op = (
                    op_display.style.format(
                        {"Sync %": "{:.1f}%", "Risk": "{:.1f}"})
                    .map(style_sync, subset=["Sync %"])
                    .map(style_risk, subset=["Risk"])
                )
                st.dataframe(styled_op, use_container_width=True, hide_index=True)

                op_csv = convert_to_csv(net["operator_stats"])
                st.download_button(
                    "📥 Export Operator Stats (CSV)",
                    data=op_csv,
                    file_name="network_operator_stats.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
                st.html('</div></div>')
        else:
            with st.container():
                st.markdown('<div class="panel">', unsafe_allow_html=True)
                st.markdown(
                    '<div class="panel-header">'
                    '<span class="panel-icon">👤</span>'
                    '<span class="panel-title">Operator Performance</span>'
                    '</div>'
                    '<div class="panel-content">',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    '<div style="text-align: center; color: var(--text-muted); font-size: 0.8rem; padding: 40px 20px;">No operator data available</div>',
                    unsafe_allow_html=True,
                )
                st.html('</div></div>')

    with col_f:
        with st.container():
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown(
                '<div class="panel-header">'
                '<span class="panel-icon">❤️</span>'
                '<span class="panel-title">Network Health</span>'
                '</div>'
                '<div class="panel-content" style="display:flex;flex-direction:column;gap:12px;">',
                unsafe_allow_html=True,
            )
            health_cls = (
                "success"
                if net["network_health"] >= 80
                else "warning"
                if net["network_health"] >= 60
                else "danger"
            )
            st.markdown(
                f'<div class="stat-card info press-effect"><div class="stat-card-label">Sync Score</div><div class="stat-card-value" data-tip="{format_full(net["network_sync"])}">{smart_format(net["network_sync"])}%</div></div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="stat-card warning press-effect"><div class="stat-card-label">Avg Risk</div><div class="stat-card-value" data-tip="{format_full(net["network_risk"])}">{smart_format(net["network_risk"])}/100</div></div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="stat-card {health_cls}"><div class="stat-card-label">Health Score</div><div class="stat-card-value">{net["network_health"]}</div></div>',
                unsafe_allow_html=True,
            )
            st.html('</div></div>')

    # ═══════════════════════════════════════════════════
    # SECTION 6: Operator Hierarchy (Org Tree)
    # ═══════════════════════════════════════════════════
    # Compute dynamic phase counts for the org tree header
    try:
        _map_df_counts = get_business_map_data()
        _est = len(_map_df_counts[_map_df_counts["status"] == "Established"])
        _pres = len(_map_df_counts[_map_df_counts["status"] == "Present"])
        _exp = len(_map_df_counts[_map_df_counts["status"] == "Expanding"])
        _fut = len(_map_df_counts[_map_df_counts["status"] == "Future"])
    except Exception:
        _est = _pres = _exp = _fut = 0

    st.html(
        '<div class="section-header">'
        '<div class="section-title">'
        '<span class="title-icon">🌐</span>'
        '<span>Operator Hierarchy</span>'
        '</div>'
        '<div class="network-stats">'
        f'<span class="net-stat established">Established <strong>{_est}</strong></span>'
        f'<span class="net-stat present">Present <strong>{_pres}</strong></span>'
        f'<span class="net-stat expanding">Expanding <strong>{_exp}</strong></span>'
        f'<span class="net-stat future">Future <strong>{_fut}</strong></span>'
        '</div>'
        '</div>'
    )
    org_search = st.text_input("", placeholder="Filter operators, contracts or stations...", key="org_search", label_visibility="collapsed")

    DUMMY_CUSTOMERS = [
        {
            "name": "Deutsche Bahn AG",
            "tier": "Platinum",
            "health_score": 92,
            "contracts": [
                {"name": "ICE-Wartung", "tier": "Platinum", "value": 2400000, "stations": [
                    {"name": "Berlin Hbf", "region": "Berlin", "status": "operational", "maint_count": 0, "tier": "Premium"},
                    {"name": "Hamburg Hbf", "region": "Hamburg", "status": "operational", "maint_count": 0, "tier": "Premium"},
                    {"name": "München Hbf", "region": "Bayern", "status": "warning", "maint_count": 2, "tier": "Premium"},
                    {"name": "Köln Hbf", "region": "NRW", "status": "operational", "maint_count": 0, "tier": "Standard"},
                    {"name": "Frankfurt Hbf", "region": "Hessen", "status": "operational", "maint_count": 1, "tier": "Standard"},
                ]},
                {"name": "Regionalnetz", "tier": "Gold", "value": 1800000, "stations": [
                    {"name": "Stuttgart Hbf", "region": "Baden-Württemberg", "status": "critical", "maint_count": 4, "tier": "Premium"},
                    {"name": "Dresden Hbf", "region": "Sachsen", "status": "operational", "maint_count": 0, "tier": "Standard"},
                    {"name": "Hannover Hbf", "region": "Niedersachsen", "status": "operational", "maint_count": 0, "tier": "Standard"},
                    {"name": "Nürnberg Hbf", "region": "Bayern", "status": "warning", "maint_count": 1, "tier": "Standard"},
                ]},
                {"name": "Signaltechnik", "tier": "Gold", "value": 950000, "stations": [
                    {"name": "Leipzig Hbf", "region": "Sachsen", "status": "operational", "maint_count": 0, "tier": "Standard"},
                    {"name": "Essen Hbf", "region": "NRW", "status": "warning", "maint_count": 2, "tier": "Standard"},
                ]},
            ],
        },
        {
            "name": "DB Regio Bayern",
            "tier": "Gold",
            "health_score": 78,
            "contracts": [
                {"name": "München S-Bahn", "tier": "Gold", "value": 1200000, "stations": [
                    {"name": "München Ost", "region": "Bayern", "status": "operational", "maint_count": 0, "tier": "Standard"},
                    {"name": "München-Pasing", "region": "Bayern", "status": "operational", "maint_count": 0, "tier": "Standard"},
                    {"name": "Augsburg Hbf", "region": "Bayern", "status": "warning", "maint_count": 2, "tier": "Standard"},
                    {"name": "Regensburg Hbf", "region": "Bayern", "status": "operational", "maint_count": 0, "tier": "Standard"},
                ]},
                {"name": "Bayern-Takt", "tier": "Standard", "value": 680000, "stations": [
                    {"name": "Würzburg Hbf", "region": "Bayern", "status": "operational", "maint_count": 0, "tier": "Standard"},
                    {"name": "Ingolstadt Hbf", "region": "Bayern", "status": "critical", "maint_count": 3, "tier": "Standard"},
                    {"name": "Rosenheim", "region": "Bayern", "status": "operational", "maint_count": 0, "tier": "Standard"},
                ]},
            ],
        },
        {
            "name": "DB Netz AG",
            "tier": "Platinum",
            "health_score": 85,
            "contracts": [
                {"name": "Schienennetz Nord", "tier": "Platinum", "value": 3100000, "stations": [
                    {"name": "Kiel Hbf", "region": "Schleswig-Holstein", "status": "operational", "maint_count": 0, "tier": "Premium"},
                    {"name": "Rostock Hbf", "region": "Mecklenburg-Vorpommern", "status": "operational", "maint_count": 0, "tier": "Standard"},
                    {"name": "Schwerin Hbf", "region": "Mecklenburg-Vorpommern", "status": "warning", "maint_count": 1, "tier": "Standard"},
                    {"name": "Bremen Hbf", "region": "Bremen", "status": "operational", "maint_count": 0, "tier": "Premium"},
                ]},
                {"name": "Korridor West", "tier": "Gold", "value": 1950000, "stations": [
                    {"name": "Düsseldorf Hbf", "region": "NRW", "status": "operational", "maint_count": 0, "tier": "Premium"},
                    {"name": "Duisburg Hbf", "region": "NRW", "status": "critical", "maint_count": 5, "tier": "Standard"},
                    {"name": "Bochum Hbf", "region": "NRW", "status": "warning", "maint_count": 1, "tier": "Standard"},
                    {"name": "Dortmund Hbf", "region": "NRW", "status": "operational", "maint_count": 0, "tier": "Standard"},
                ]},
            ],
        },
        {
            "name": "Go-Ahead Bayern",
            "tier": "Gold",
            "health_score": 71,
            "contracts": [
                {"name": "Alex-Züge", "tier": "Gold", "value": 840000, "stations": [
                    {"name": "Hof Hbf", "region": "Bayern", "status": "operational", "maint_count": 0, "tier": "Standard"},
                    {"name": "Bayreuth Hbf", "region": "Bayern", "status": "operational", "maint_count": 0, "tier": "Standard"},
                    {"name": "Nürnberg Hbf", "region": "Bayern", "status": "warning", "maint_count": 1, "tier": "Standard"},
                ]},
            ],
            "stations": [
                {"name": "Marktredwitz", "region": "Bayern", "status": "operational", "maint_count": 0, "tier": "Standard"},
            ],
        },
        {
            "name": "ÖBB Personenverkehr",
            "tier": "Gold",
            "health_score": 88,
            "contracts": [
                {"name": "Railjet", "tier": "Platinum", "value": 2150000, "stations": [
                    {"name": "Wien Hbf", "region": "Österreich", "status": "operational", "maint_count": 0, "tier": "Premium"},
                    {"name": "Salzburg Hbf", "region": "Österreich", "status": "operational", "maint_count": 0, "tier": "Premium"},
                    {"name": "Innsbruck Hbf", "region": "Österreich", "status": "operational", "maint_count": 0, "tier": "Standard"},
                    {"name": "Linz Hbf", "region": "Österreich", "status": "operational", "maint_count": 0, "tier": "Standard"},
                    {"name": "Graz Hbf", "region": "Österreich", "status": "warning", "maint_count": 1, "tier": "Standard"},
                ]},
            ],
        },
    ]

    try:
        customer_df = get_customer_data()
        customers_for_tree = []
        if customer_df is not None and not customer_df.empty:
            for idx, crow in customer_df.iterrows():
                stations_for_customer = []
                station_list = (
                    df[df["operator"].str.contains(
                        str(crow.get("customer_name", "")),
                        case=False, na=False
                    )]["station"].unique().tolist()
                    if "operator" in df.columns
                    else []
                )
                for sname in station_list[:20]:
                    sdf = df[df["station"] == sname]
                    status = "operational"
                    region = sname.split(" ")[0] if " " in sname else "Unknown"
                    maint_count = 0
                    if not sdf.empty:
                        crit_count = (sdf["maintenance_status"] == "CRITICAL").sum()
                        warn_count = (sdf["maintenance_status"] == "WARNING").sum()
                        maint_count = int(crit_count + warn_count)
                        if crit_count > 0:
                            status = "critical"
                        elif warn_count > 0:
                            status = "warning"
                    stations_for_customer.append({
                        "name": sname,
                        "status": status,
                        "region": region,
                        "maint_count": maint_count,
                        "tier": "Premium" if "Central" in sname or "Nord" in sname else "Standard",
                    })

                contract_types = ["Wartung & Instandhaltung", "Signaltechnik", "Infrastruktur"]
                contract_tiers = ["Platinum", "Gold", "Standard"]
                station_count = len(stations_for_customer)
                chunk_size = max(1, station_count // 3)
                contracts = []
                for j in range(min(3, station_count)):
                    chunk = stations_for_customer[j * chunk_size:(j + 1) * chunk_size]
                    if not chunk:
                        continue
                    contracts.append({
                        "name": contract_types[j],
                        "tier": contract_tiers[j],
                        "value": float(crow.get("total_contract_value_eur", 50000)) / max(1, len(contracts or [1])),
                        "stations": chunk,
                    })

                customers_for_tree.append({
                    "name": str(crow.get("customer_name", f"Operator {idx}")),
                    "tier": str(crow.get("tier", "Standard")),
                    "health_score": float(crow.get("health_score", 50)),
                    "stations": stations_for_customer,
                    "contracts": contracts,
                })

        tree_data = customers_for_tree if customers_for_tree else DUMMY_CUSTOMERS
        org_tree_html = build_org_tree(tree_data, search_query=org_search)
        st.html(org_tree_html)
    except Exception:
        org_tree_html = build_org_tree(DUMMY_CUSTOMERS, search_query=org_search)
        st.html(org_tree_html)


# ═══════════════════════════════════════════════════
# ── TAB: INCIDENT LOG ─────────────────────────────
# ═══════════════════════════════════════════════════


elif active_tab == "incidents":
    incidents = get_incident_log(df)

    if incidents.empty:
        st.markdown(
            '<div class="panel">'
            '<div class="panel-header">'
            '<span class="panel-icon">&#10003;</span>'
            '<span class="panel-title">All Stations Log</span>'
            "</div>"
            '<div class="panel-content" style="text-align:center;padding:40px;color:var(--text-muted);">'
            "✓ No active incidents. All systems operating normally."
            "</div></div>",
            unsafe_allow_html=True,
        )
    else:
        crit = (incidents["Severity"].str.contains("CRITICAL")).sum()
        warn = (incidents["Severity"].str.contains("WARNING")).sum()

        st.markdown('<div class="kpi-strip modern-kpi-grid">', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        kpis_inc = [
            (c1, "Critical", str(crit), "Immediate Action", "alert"),
            (c2, "Warning", str(warn), "Under Observation", "warn"),
            (c3, "Total", str(len(incidents)), "This Session", ""),
        ]
        for col, title, val, sub, cls in kpis_inc:
            with col:
                st.markdown(
                    f"""
                <div class="kpi-card {cls}">
                    <div class="kpi-icon">{("&#9888;" if cls == "alert" else "&#9888;" if cls == "warn" else "&#9679;")}</div>
                    <div class="kpi-body">
                        <div class="kpi-label">{title}</div>
                        <div class="kpi-value">{val}</div>
                        <div class="kpi-sub">{sub}</div>
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )
        st.html("</div>")

        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown(
            '<div class="panel-header">'
            '<span class="panel-icon">&#128680;</span>'
            '<span class="panel-title">Incident List</span>'
            "</div>"
            '<div class="panel-content">',
            unsafe_allow_html=True,
        )

        for _, row in incidents.iterrows():
            cls = "critical" if "CRITICAL" in row["Severity"] else "warning"
            border_col = "var(--color-danger)" if cls == "critical" else "var(--color-warning)"
            st.markdown(
                f"""
            <div class="incident-row {cls}" style="border-left-color:{border_col};">
                <div style="font-family:var(--font-mono); font-size:0.75rem; color:var(--text-muted); min-width:50px;">{row["Time"]}</div>
                <div style="min-width:70px;font-weight:600;color:{"var(--color-danger)" if "CRITICAL" in row["Severity"] else "var(--color-warning)"};">{row["Severity"]}</div>
                <div style="font-size:0.78rem; color:var(--text-secondary); min-width:100px;">{row["Station"][:14]}…</div>
                <div style="font-size:0.78rem; color:var(--text-primary); flex:1;">{row["Description"]}</div>
                <div style="font-family:var(--font-mono); font-size:0.72rem; color:var(--text-muted);">
                    {row["Temp (°C)"]}°C | {row["Vibration"]} mm/s
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )
        st.html("</div></div>")

        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown(
            '<div class="panel-header">'
            '<span class="panel-icon">&#128202;</span>'
            '<span class="panel-title">Incident Detail Table</span>'
            "</div>"
            '<div class="panel-content">',
            unsafe_allow_html=True,
        )
        st.dataframe(incidents, use_container_width=True, hide_index=True)

        # Export incident log
        incidents_csv = convert_to_csv(incidents)
        st.download_button(
            "📥 Export Incident Log (CSV)",
            data=incidents_csv,
            file_name="incident_log.csv",
            mime="text/csv",
        )
        st.html("</div></div>")

        # ── Enhanced Analytics Sections ──
        st.markdown(
            '<div class="section-heading">Incident Analytics</div>',
            unsafe_allow_html=True,
        )

        col_inc1, col_inc2 = st.columns(2)

        with col_inc1:
            st.markdown(
                '<div class="chart-label">Incidents by Station</div>',
                unsafe_allow_html=True,
            )
            station_counts = incidents.groupby(
                "Station").size().reset_index(name="Count")
            fig_station = px.bar(
                station_counts,
                x="Station",
                y="Count",
                color="Count",
                color_continuous_scale=["#0d47a1", "#0288d1", "#00b4d8"],
                text="Count",
            )
            fig_station.update_traces(
                textposition="outside", marker_line_width=0,
                hovertemplate="<b>%{x}</b><br>Incidents: %{y}<br>Count: %{z}<extra></extra>",
            )
            style_chart(fig_station, height=280, legend=False,
                        coloraxis_colorbar=dict(
                            title=dict(text="Count", font=dict(
                                color="var(--text-secondary)", size=10)),
                            tickfont=dict(color="var(--text-secondary)", size=9),
                        ))
            render_chart(fig_station, key="fig_station_L3382", use_container_width=True)

        with col_inc2:
            st.markdown(
                '<div class="chart-label">Severity Distribution</div>',
                unsafe_allow_html=True,
            )
            severity_counts = incidents["Severity"].value_counts(
            ).reset_index()
            severity_counts.columns = ["Severity", "Count"]
            fig_severity = px.pie(
                severity_counts,
                values="Count",
                names="Severity",
                color_discrete_sequence=["var(--color-danger)", "var(--color-warning)"],
                hole=0.5,
                hover_data={"Count": True},
            )
            style_pie(fig_severity, height=280)
            fig_severity.update_traces(
                textinfo="percent+label",
                hovertemplate="<b>%{label}</b><br>Incidents: %{value}<br>Share: %{percent}<extra></extra>",)
            render_chart(fig_severity, key="fig_severity_L3404", use_container_width=True)

        col_inc3, col_inc4 = st.columns(2)

        with col_inc3:
            st.markdown(
                '<div class="chart-label" style="margin-top:20px;">Incidents by Hour</div>',
                unsafe_allow_html=True,
            )
            incidents["Hour"] = incidents["Time"].str.split(
                ":").str[0].astype(int)
            hour_counts = incidents.groupby(
                "Hour").size().reset_index(name="Count")
            fig_hour = px.line(
                hour_counts,
                x="Hour",
                y="Count",
                markers=True,
                line_shape="spline",
            )
            fig_hour.update_traces(
                line=dict(color="#06b6d4", width=2.5),
                marker=dict(size=6, color="#06b6d8"),
                fill="tozeroy",
                fillcolor="rgba(6, 182, 212, 0.1)",
            )
            style_chart(fig_hour, height=280, legend=False,
                        xaxis=dict(tickmode="linear", tick0=0, dtick=2,
                                   title=dict(text="Hour", font=dict(color="var(--text-secondary)", size=11))),
                        yaxis=dict(title=dict(
                            text="Count", font=dict(color="var(--text-secondary)", size=11))),
                        margin=dict(l=50, r=16, t=35, b=50))
            render_chart(fig_hour, key="fig_hour_L3436", use_container_width=True)

        with col_inc4:
            st.markdown(
                '<div class="chart-label" style="margin-top:20px;">Platform Distribution</div>',
                unsafe_allow_html=True,
            )
            platform_counts = incidents.groupby(
                "Platform").size().reset_index(name="Count")
            fig_platform = px.bar(
                platform_counts,
                x="Platform",
                y="Count",
                color="Count",
                color_continuous_scale=["var(--color-emerald)", "#34d399", "#6ee7b7"],
                text="Count",
            )
            style_chart(fig_platform, height=280, legend=False)
            fig_platform.update_traces(
                textposition="outside", marker_line_width=0)
            render_chart(fig_platform, key="fig_platform_L3456", use_container_width=True)

        st.markdown(
            '<div class="chart-label" style="margin-top:20px;">Temperature vs Incidents</div>',
            unsafe_allow_html=True,
        )
        fig_temp_scatter = px.scatter(
            incidents,
            x="Temp (°C)",
            y="Vibration",
            color="Severity",
            color_discrete_map={
                "🔴 CRITICAL": "var(--color-danger)", "🟡 WARNING": "var(--color-warning)"},
            size_max=12,
            hover_data={"Gate": True, "Station": True, "Description": True},
        )
        style_chart(fig_temp_scatter, height=300, hovermode="closest",
                    xaxis=dict(title=dict(text="Temperature (°C)")),
                    yaxis=dict(title=dict(text="Vibration (mm/s)")),
                    legend=dict(orientation="h", y=1.0, x=1, xanchor="right", yanchor="bottom",
                               font=dict(size=10, color="var(--text-secondary)")))
        render_chart(fig_temp_scatter, key="fig_temp_scatter_L3477", use_container_width=True)


# ═══════════════════════════════════════════════════
# ── TAB: PREDICTIVE ANALYTICS ─────────────────────
# ═══════════════════════════════════════════════════
elif active_tab == "forecast":
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown(
        '<div class="panel-header">'
        '<span class="panel-icon">&#128200;</span>'
        '<span class="panel-title">Predictive Analytics - Network Overview</span>'
        "</div>"
        '<div class="panel-content">',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-heading">Network Risk Forecast by Station</div>',
        unsafe_allow_html=True,
    )

    station_risk_forecast = df.groupby(
        "station")["risk_score"].mean().reset_index()
    station_risk_forecast = station_risk_forecast.sort_values(
        "risk_score", ascending=False)

    fig_forecast = px.bar(
        station_risk_forecast,
        x="station",
        y="risk_score",
        color="risk_score",
        color_continuous_scale=["var(--color-emerald)", "var(--color-warning)", "var(--color-danger)"],
        range_color=[0, 100],
        text="risk_score",
        hover_data={"station": True, "risk_score": ":.0f"},
    )
    fig_forecast.update_traces(
        hovertemplate="<b>%{x}</b><br>Avg Risk Score: %{y:.0f}/100<extra></extra>",)
    style_chart(fig_forecast, legend=False,
                xaxis=dict(title=dict(text="Station")),
                yaxis=dict(title=dict(text="Avg Risk Score"), range=[0, 100]),
                coloraxis_colorbar=dict(
                    title=dict(text="Risk", font=dict(
                        color="var(--text-secondary)", size=10)),
                    tickfont=dict(color="var(--text-secondary)", size=9),
                ))
    fig_forecast.update_traces(textposition="outside", marker_line_width=0)
    render_chart(fig_forecast, key="fig_forecast_L3525", use_container_width=True)

    col_heat, col_sync = st.columns([2, 1])

    with col_heat:
        st.markdown(
            '<div class="chart-label">Passenger Flow by Station</div>',
            unsafe_allow_html=True,
        )
        station_passengers = df.groupby(
            "station")["people"].sum().reset_index()
        station_passengers = station_passengers.sort_values(
            "people", ascending=False)

        fig_passengers = px.bar(
            station_passengers,
            x="station",
            y="people",
            color="people",
            color_continuous_scale=["#0d47a1", "#0288d1", "#00b4d8"],
            text="people",
        )
        style_chart(fig_passengers, legend=False,
                    xaxis=dict(title=dict(text="Station")),
                    yaxis=dict(title=dict(text="Total Passengers")),
                    coloraxis_colorbar=dict(
                        title=dict(text="Passengers", font=dict(
                            color="var(--text-secondary)", size=10)),
                        tickfont=dict(color="var(--text-secondary)", size=9),
                    ))
        fig_passengers.update_traces(
            textposition="outside", marker_line_width=0)
        render_chart(fig_passengers, key="fig_passengers_L3557", use_container_width=True)

    with col_sync:
        st.markdown(
            '<div class="section-heading">Network Sync Health</div>',
            unsafe_allow_html=True,
        )
        net_sync = int(df["sync_score"].mean())

        fig_gauge = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=net_sync,
                gauge={
                    "axis": {"range": [0, 100], "tickcolor": "#4a6fa5"},
                    "bar": {"color": "#0288d1"},
                    "steps": [
                        {"range": [0, 60], "color": "rgba(239,68,68,0.15)"},
                        {"range": [60, 85], "color": "rgba(245,158,11,0.15)"},
                        {"range": [85, 100], "color": "rgba(16,185,129,0.15)"},
                    ],
                    "threshold": {
                        "line": {"color": "var(--color-emerald)", "width": 3},
                        "thickness": 0.75,
                        "value": 85,
                    },
                    "bgcolor": "rgba(0,0,0,0)",
                    "bordercolor": "#1e2d4d",
                },
                title={
                    "text": "Network-wide Sync Score<br><span style='font-size:0.7em;color:#4a6fa5'>All Stations Average</span>",
                    "font": {"color": "#7ab3d4", "size": 12},
                },
                number={"suffix": "%", "font": {
                    "color": "var(--text-primary)", "size": 30}},
            )
        )
        style_indicator(fig_gauge, height=340)
        render_chart(fig_gauge, key="fig_gauge_L3595", use_container_width=True)

        st.markdown(
            '<div class="chart-label" style="text-align:center;margin-top:10px;">Sync Score by Station</div>',
            unsafe_allow_html=True,
        )
        station_sync = df.groupby("station")["sync_score"].mean().reset_index()
        station_sync = station_sync.sort_values("sync_score", ascending=True)
        fig_sync_bar = px.bar(
            station_sync,
            x="sync_score",
            y="station",
            orientation="h",
            color="sync_score",
            color_continuous_scale=["var(--color-danger)", "var(--color-warning)", "var(--color-emerald)"],
            range_color=[0, 100],
        )
        style_chart(fig_sync_bar, height=280, legend=False,
                    yaxis=dict(title="", tickfont=dict(
                        size=9, color="var(--text-secondary)")),
                    xaxis=dict(title="Sync Score", range=[0, 100]),
                    margin=dict(l=50, r=16, t=20, b=45))
        render_chart(fig_sync_bar, key="fig_sync_bar_L3617", use_container_width=True)

    # THIRD ROW: Gate Risk Scores (all stations)
    st.markdown(
        '<div class="section-heading">Gate Risk Scores - All Stations</div>', unsafe_allow_html=True
    )

    all_stations_data = df.copy().sort_values("risk_score", ascending=False)

    fig_risk = px.bar(
        all_stations_data,
        x="risk_score",
        y="gate_id",
        orientation="h",
        color="risk_score",
        color_continuous_scale=["var(--color-emerald)", "var(--color-warning)", "var(--color-danger)"],
        range_color=[0, 100],
        labels={"risk_score": "Risk Score",
                "gate_id": "Gate", "station": "Station"},
        hover_data={"platform": True},
    )
    style_chart(fig_risk, hovermode="y unified",
                yaxis=dict(title=""), xaxis=dict(title="Risk Score", range=[0, 100]),
                coloraxis_colorbar=dict(
                    title=dict(text="Risk", font=dict(
                        color="var(--text-secondary)", size=10)),
                    tickfont=dict(color="var(--text-secondary)", size=9), thickness=6, len=0.7,
                ),)
    fig_risk.update_traces(marker_line_width=0,
    )
    render_chart(fig_risk, key="fig_risk_L3647", use_container_width=True)
    st.html("</div></div>")

    # Export network risk data
    station_risk_export = df.groupby("station").agg({
        "risk_score": "mean",
        "sync_score": "mean",
        "people": "sum",
        "gate_id": "count"
    }).reset_index()
    station_risk_export.columns = [
        "Station", "Avg_Risk", "Avg_Sync", "Total_Passengers", "Gate_Count"]
    risk_csv = convert_to_csv(station_risk_export)
    st.download_button(
        "📥 Export Network Risk Data (CSV)",
        data=risk_csv,
        file_name="network_risk_overview.csv",
        mime="text/csv",
    )

    # ── PSD Analytics (Door Cycles & Temperature) ──
    st.markdown(
        '<div class="section-heading">PSD Analytics - Door Cycles & Temperature</div>',
        unsafe_allow_html=True,
    )

    cycles_df, temp_df = get_psd_analytics(current_station)

    col_psd1, col_psd2 = st.columns(2)

    with col_psd1:
        st.markdown(
            '<div class="chart-label">Door Cycles by Hour</div>',
            unsafe_allow_html=True,
        )
        fig_cycles = px.bar(
            cycles_df,
            x="Hour",
            y="Door Cycles",
            color="Door Cycles",
            color_continuous_scale=["#3b82f6", "#60a5fa", "#93c5fd"],
            text="Door Cycles",
        )
        style_chart(fig_cycles, legend=False)
        fig_cycles.update_traces(textposition="outside", marker_line_width=0)
        render_chart(fig_cycles, key="fig_cycles_L3692", use_container_width=True)

    with col_psd2:
        st.markdown(
            '<div class="chart-label">Average Temperature by Hour</div>',
            unsafe_allow_html=True,
        )
        fig_temp_psd = go.Figure()
        fig_temp_psd.add_trace(
            go.Scatter(
                x=temp_df["Hour"],
                y=temp_df["Avg Temp (°C)"],
                mode="lines+markers",
                line=dict(color="var(--color-danger)", width=2.5, shape="spline"),
                marker=dict(size=6, color="var(--color-danger)"),
                fill="tozeroy",
                fillcolor="rgba(239,68,68,0.08)",
                name="Temp (°C)",
            )
        )
        fig_temp_psd.add_hline(
            y=45,
            line_dash="dot",
            line_color="#f97316",
            annotation_text="Warning Threshold (45°C)",
            annotation_font_color="#f97316",
            annotation_font_size=10,
        )
        style_chart(fig_temp_psd, legend=False,
                    yaxis=dict(title=dict(text="Temp (°C)")))
        render_chart(fig_temp_psd, key="fig_temp_psd_L3722", use_container_width=True)

    # ── Maintenance Predictions & Recommendations (All Stations) ──
    st.markdown(
        '<div class="section-heading">Maintenance Predictions & Recommendations - All Stations</div>',
        unsafe_allow_html=True,
    )

    all_stations_data = df.copy()
    high_risk_gates = all_stations_data[all_stations_data["risk_score"] >= 70].sort_values(
        "risk_score", ascending=False
    )
    medium_risk_gates = all_stations_data[
        (all_stations_data["risk_score"] >= 40) & (
            all_stations_data["risk_score"] < 70)
    ].sort_values("risk_score", ascending=False)

    if not high_risk_gates.empty:
        st.markdown(
            '<div style="font-size:0.9rem;font-weight:600;color:var(--color-danger);margin:16px 0 10px 0;display:flex;align-items:center;gap:8px;">🔴 Critical Risk Gates - Immediate Action Required (Network-wide)</div>',
            unsafe_allow_html=True,
        )

        for _, gate in high_risk_gates.head(8).iterrows():
            main_status = gate.get("maintenance_status", "UNKNOWN")
            sync_score = int(gate.get("sync_score", 0))
            temp = gate.get("sensor_temp", 0)
            station_name = gate.get("station", "Unknown")

            if main_status == "CRITICAL":
                rec = "Replace sensor module, perform full diagnostic"
            elif sync_score < 60:
                rec = "Recalibrate sync system, check network connectivity"
            elif temp > 45:
                rec = "Cooling system inspection, thermal sensor replacement"
            else:
                rec = "Schedule preventive maintenance immediately"

            st.markdown(
                f"""
            <div class="maint-card critical">
                <div class="maint-card-header">
                    <span class="maint-card-title">Gate {gate['gate_id']} @ {station_name[:20]}</span>
                    <span class="maint-card-risk">Risk: {int(gate['risk_score'])}%</span>
                </div>
                <div class="maint-card-meta">
                    <span>🔧 Status: {main_status}</span>
                    <span>📡 Sync: {sync_score}%</span>
                    <span>🌡️ Temp: {temp}°C</span>
                </div>
                <div class="maint-card-rec">→ {rec}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

    if not medium_risk_gates.empty:
        st.markdown(
            '<div style="font-size:0.9rem;font-weight:600;color:var(--color-warning);margin:16px 0 10px 0;">🟡 Medium Risk Gates - Schedule Maintenance (Network-wide)</div>',
            unsafe_allow_html=True,
        )

        for _, gate in medium_risk_gates.head(8).iterrows():
            main_status = gate.get("maintenance_status", "UNKNOWN")
            sync_score = int(gate.get("sync_score", 0))
            station_name = gate.get("station", "Unknown")

            if main_status == "WARNING":
                rec = "Monitor closely, schedule maintenance within 7 days"
            elif sync_score < 80:
                rec = "Performance optimization, check software updates"
            else:
                rec = "Routine inspection recommended"

            st.markdown(
                f"""
            <div class="maint-card warning">
                <div class="maint-card-header">
                    <span class="maint-card-title">Gate {gate['gate_id']} @ {station_name[:20] if station_name else ''}</span>
                    <span class="maint-card-risk">Risk: {int(gate['risk_score'])}%</span>
                </div>
                <div class="maint-card-meta">
                    <span>🔧 Status: {main_status}</span>
                    <span>📡 Sync: {sync_score}%</span>
                </div>
                <div class="maint-card-rec">→ {rec}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            st.markdown(
                f"""
            <div style="background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.3);border-radius:8px;padding:12px;margin-bottom:10px;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                    <span style="font-weight:600;color:#fcd34d;font-size:0.95rem;">Gate {gate['gate_id']}</span>
                    <span style="background:rgba(245,158,11,0.2);color:#fcd34d;padding:2px 8px;border-radius:4px;font-size:0.75rem;font-weight:600;">Risk: {int(gate['risk_score'])}%</span>
                </div>
                <div style="font-size:0.8rem;color:var(--text-secondary);margin-bottom:6px;">
                    <span style="margin-right:15px;">🔧 Status: {main_status}</span>
                    <span style="margin-right:15px;">📡 Sync: {sync_score}%</span>
                </div>
                <div style="font-size:0.85rem;color:#fbbf24;font-weight:500;">→ {rec}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

    # ── Anomaly Detection (All Stations) ──
    st.markdown(
        '<div class="section-heading">Anomaly Detection - Network-wide</div>',
        unsafe_allow_html=True,
    )

    all_stations_anomaly = df.copy()

    temp_anomalies = all_stations_anomaly[all_stations_anomaly["sensor_temp"] > 40]
    vib_anomalies = all_stations_anomaly[all_stations_anomaly["sensor_vib"] > 3.0]
    sync_anomalies = all_stations_anomaly[all_stations_anomaly["sync_score"] < 50]

    col_anom1, col_anom2, col_anom3 = st.columns(3)

    with col_anom1:
        st.markdown(
            f"""
        <div class="stat-card danger press-effect">
            <div class="stat-card-value">{smart_format(len(temp_anomalies))}</div>
            <div class="stat-card-label">High Temp Anomalies</div>
            <div class="stat-card-sub">&gt; 40°C threshold</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col_anom2:
        st.markdown(
            f"""
        <div class="stat-card warning press-effect">
            <div class="stat-card-value">{smart_format(len(vib_anomalies))}</div>
            <div class="stat-card-label">Vibration Anomalies</div>
            <div class="stat-card-sub">&gt; 3.0 mm/s threshold</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col_anom3:
        st.markdown(
            f"""
        <div class="stat-card danger press-effect">
            <div class="stat-card-value">{smart_format(len(sync_anomalies))}</div>
            <div class="stat-card-label">Low Sync Anomalies</div>
            <div class="stat-card-sub">&lt; 50% sync score</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    if not temp_anomalies.empty:
        with st.expander("View Temperature Anomaly Details"):
            st.dataframe(
                temp_anomalies[["station", "gate_id",
                                "platform", "sensor_temp", "sync_score"]]
                .rename(
                    columns={
                        "station": "Station",
                        "gate_id": "Gate",
                        "platform": "Platform",
                        "sensor_temp": "Temp (°C)",
                        "sync_score": "Sync Score",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

    if not vib_anomalies.empty:
        with st.expander("View Vibration Anomaly Details"):
            st.dataframe(
                vib_anomalies[["station", "gate_id",
                               "platform", "sensor_vib", "sync_score"]]
                .rename(
                    columns={
                        "station": "Station",
                        "gate_id": "Gate",
                        "platform": "Platform",
                        "sensor_vib": "Vibration (mm/s)",
                        "sync_score": "Sync Score",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

    if not sync_anomalies.empty:
        with st.expander("View Low Sync Anomaly Details"):
            st.dataframe(
                sync_anomalies[["station", "gate_id",
                                "platform", "sync_score", "risk_score"]]
                .rename(
                    columns={
                        "station": "Station",
                        "gate_id": "Gate",
                        "platform": "Platform",
                        "sync_score": "Sync Score",
                        "risk_score": "Risk Score",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

    # ── Risk Trend Comparison (All Stations) ──
    st.markdown(
        '<div class="section-heading">Risk Trend - All Stations</div>',
        unsafe_allow_html=True,
    )

    station_risk_data = df.groupby(
        "station")["risk_score"].mean().reset_index()
    station_risk_data = station_risk_data.sort_values(
        "risk_score", ascending=False)
    station_risk_data.columns = ["Station", "Avg Risk"]

    fig_station_risk = px.bar(
        station_risk_data,
        x="Station",
        y="Avg Risk",
        color="Avg Risk",
        color_continuous_scale=["var(--color-emerald)", "var(--color-warning)", "var(--color-danger)"],
        range_color=[0, 100],
        text="Avg Risk",
    )
    style_chart(fig_station_risk, legend=False,
                yaxis=dict(title=dict(text="Avg Risk Score"), range=[0, 100]))
    fig_station_risk.update_traces(textposition="outside", marker_line_width=0)
    render_chart(fig_station_risk, key="fig_station_risk_L3958", use_container_width=True)

    col_trend1, col_trend2 = st.columns(2)

    with col_trend1:
        st.markdown(
            '<div class="chart-label">Network Risk Distribution</div>',
            unsafe_allow_html=True,
        )
        risk_ranges = pd.cut(
            df["risk_score"],
            bins=[0, 30, 60, 100],
            labels=["Low (0-30)", "Medium (31-60)", "High (61-100)"],
        )
        risk_dist = risk_ranges.value_counts().reset_index()
        risk_dist.columns = ["Risk Level", "Count"]

        fig_risk_dist = px.pie(
            risk_dist,
            values="Count",
            names="Risk Level",
            color_discrete_sequence=["var(--color-emerald)", "var(--color-warning)", "var(--color-danger)"],
            hole=0.5,
        )
        style_pie(fig_risk_dist, height=280)
        fig_risk_dist.update_traces(
            textinfo="percent+label",)
        render_chart(fig_risk_dist, key="fig_risk_dist_L3985", use_container_width=True)

    with col_trend2:
        st.markdown(
            '<div class="chart-label">Top 5 High Risk Gates</div>',
            unsafe_allow_html=True,
        )
        top_risk_gates = (
            df.nlargest(5, "risk_score")[
                ["gate_id", "station", "risk_score", "maintenance_status"]]
            .rename(
                columns={
                    "gate_id": "Gate",
                    "station": "Station",
                    "risk_score": "Risk",
                    "maintenance_status": "Status",
                }
            )
        )
        st.dataframe(top_risk_gates, use_container_width=True, hide_index=True)

    overall_risk = df["risk_score"].mean()
    network_avg = overall_risk
    risk_cls = "success" if overall_risk < 40 else "warning" if overall_risk < 70 else "danger"
    st.markdown(
        f"""
    <div class="stat-card {risk_cls}" style="margin-top:15px;">
        <div class="stat-card-label">Network Average Risk Score</div>
        <div class="stat-card-value">{overall_risk:.1f}%</div>
    </div>
    """,
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════
# ── TAB: COMPANY & TEAM ───────────────────────────
# ═══════════════════════════════════════════════════
elif active_tab == "financial":
    def fin_fig(layout_extra=None):
        d = dict(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#9a9284", size=11, family="Satoshi, Figtree, sans-serif"),
            xaxis=dict(gridcolor="rgba(212,160,48,0.08)", zeroline=False,
                       tickfont=dict(size=11, color="#9a9284"), automargin=True),
            yaxis=dict(gridcolor="rgba(212,160,48,0.08)", zeroline=False,
                       tickfont=dict(size=11, color="#9a9284"), automargin=True),
            legend=dict(x=0.98, y=0.98, xanchor="right", yanchor="top",
                        bgcolor="rgba(8,12,24,0.8)", bordercolor="rgba(212,160,48,0.2)",
                        borderwidth=1, font=dict(size=11, color="var(--text-secondary)")),
            margin=dict(l=60, r=24, t=65, b=55),
            hovermode="x unified",
        )
        if layout_extra:
            d.update(layout_extra)
        return d

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown(
        '<div class="panel-header">'
        '<span class="panel-icon">&#9881;</span>'
        '<span class="panel-title">Financial Model</span>'
        "</div>"
        '<div class="panel-content">',
        unsafe_allow_html=True,
    )

    with st.expander("Configure SaaS Model Parameters", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**📊 Customer Parameters**")
            starting_customers = st.number_input(
                "Starting Customers",
                min_value=1,
                max_value=1000,
                value=50,
                step=5,
                help="Initial number of customers at start of simulation",
            )
            monthly_growth_rate = (
                st.slider(
                    "Monthly Growth Rate (%)",
                    min_value=1,
                    max_value=50,
                    value=20,
                    step=1,
                    help="Monthly customer growth rate as percentage",
                )
                / 100.0
            )
            churn_rate = (
                st.slider(
                    "Monthly Churn Rate (%)",
                    min_value=1,
                    max_value=30,
                    value=5,
                    step=1,
                    help="Monthly customer churn rate as percentage",
                )
                / 100.0
            )

        with col2:
            st.markdown("**💰 Pricing & Revenue**")
            price_per_customer = st.number_input(
                "Price per Customer ($/month)",
                min_value=1,
                max_value=10000,
                value=100,
                step=10,
                help="Average monthly revenue per customer",
            )
            cac_simplified = st.number_input(
                "Customer Acquisition Cost ($)",
                min_value=0,
                max_value=10000,
                value=150,
                step=10,
                help="Cost to acquire one new customer",
            )
            high_churn_multiplier = st.slider(
                "High Churn Multiplier (x)",
                min_value=1.0,
                max_value=5.0,
                value=2.0,
                step=0.5,
                help="Multiplier for high churn scenario vs base churn",
            )

        with col3:
            st.markdown("**📋 Cost Parameters**")
            fixed_costs = st.number_input(
                "Fixed Costs ($/month)",
                min_value=0,
                max_value=100000,
                value=5000,
                step=500,
                help="Monthly fixed operating costs",
            )
            variable_cost_per_customer = st.number_input(
                "Variable Cost per Customer ($)",
                min_value=0,
                max_value=1000,
                value=10,
                step=5,
                help="Variable cost per customer",
            )
            simulation_months = st.slider(
                "Simulation Period (months)",
                min_value=12,
                max_value=60,
                value=24,
                step=6,
                help="Number of months to simulate",
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
        churn_rate_high=churn_rate_high,
    )

    st.markdown(
        '<div class="section-heading">📊 Scenario Selector</div>',
        unsafe_allow_html=True,
    )

    scenario_labels = [
        f"Base Case ({churn_rate * 100:.0f}% Churn)",
        f"High Churn ({churn_rate_high * 100:.0f}% Churn)",
        "Side-by-Side Comparison",
    ]
    scenario = st.radio(
        "Choose scenario",
        scenario_labels,
        horizontal=True,
        label_visibility="collapsed",
    )
    df = (
        df_base if "Base" in scenario else (
            df_churn if "High" in scenario else df_base)
    )
    months = df["Month"]

    # ── KPI Summary Cards ──────────────────────────────────────────────────
    st.markdown(
        '<div class="section-heading">💰 Key Financial Metrics</div>',
        unsafe_allow_html=True,
    )
    final = df.iloc[-1]
    k1, k2, k3, k4, k5 = st.columns(5)
    kpi_items = [
        (k1, "FINAL MRR", f"${final['MRR']:,.0f}", "metric-card green"),
        (k2, "FINAL ARR", f"${final['ARR']:,.0f}", "metric-card"),
        (k3, "TOTAL CUSTOMERS",
         f"{int(final['Total_Customers'])}", "metric-card"),
        (k4, "GROSS MARGIN",
         f"{final['Gross_Margin_%']:.1f}%", "metric-card green"),
        (k5, "LTV : CAC", f"{final['LTV_CAC_Ratio']:.1f}x", "metric-card"),
    ]
    for col, title, val, cls in kpi_items:
        with col:
            st.markdown(
                f"""<div class="{cls}">
                <div class="metric-title">{title}</div>
                <div class="metric-value" style="font-size:1.4rem">{val}</div>
            </div>""",
                unsafe_allow_html=True,
            )

    st.html("<br>")

    # ── ROW 1: MRR Movements + MRR Growth ─────────────────────────────────
    st.markdown(
        '<div class="section-heading">📈 Revenue Movements</div>',
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)

    with c1:
        fig = go.Figure()
        fig.add_bar(
            x=months,
            y=df["New_MRR"],
            name="New MRR",
            marker_color="#2ecc71",
            opacity=0.85,
        )
        fig.add_bar(
            x=months,
            y=df["Expansion_MRR"],
            name="Expansion MRR",
            marker_color="#a9dfbf",
            opacity=0.85,
        )
        fig.add_bar(
            x=months,
            y=df["Churn_MRR"],
            name="Churn MRR",
            marker_color="#e74c3c",
            opacity=0.85,
        )
        fig.add_scatter(
            x=months,
            y=df["Net_New_MRR"],
            name="Net New MRR",
            mode="lines+markers",
            line=dict(color="#00b4d8", width=2),
            marker=dict(size=5),
        )
        fig.update_layout(barmode="relative",
                          title="MRR Movements", **fin_fig())
        render_chart(fig, key="fig_L4250", use_container_width=True)

    with c2:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_bar(
            x=months,
            y=df["Net_New_MRR"],
            name="Net New MRR",
            marker_color="#27ae60",
            opacity=0.8,
            secondary_y=False,
        )
        fig.add_scatter(
            x=months,
            y=df["MoM_Growth_%"],
            name="MoM Growth %",
            mode="lines+markers",
            line=dict(color="#2980b9", width=2),
            marker=dict(size=5),
            secondary_y=True,
        )
        fig.update_layout(title="MRR Growth & MoM %", **fin_fig())
        fig.update_yaxes(gridcolor="#1a2d50", secondary_y=False)
        fig.update_yaxes(gridcolor="#1a2d50", ticksuffix="%", secondary_y=True)
        render_chart(fig, key="fig_L4274", use_container_width=True)

    # ── ROW 2: Customer Growth + Enterprise Wins ───────────────────────────
    st.markdown(
        '<div class="section-heading">👥 Customer Analytics</div>',
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)

    with c1:
        fig = go.Figure()
        fig.add_scatter(
            x=months,
            y=df["Total_Customers"],
            name="Total Customers",
            mode="lines+markers",
            line=dict(color="#00b4d8", width=2.5),
            marker=dict(size=5),
            fill="tozeroy",
            fillcolor="rgba(0,180,216,0.08)",
        )
        fig.add_bar(
            x=months,
            y=df["New_Customers"],
            name="New Customers",
            marker_color="#2ecc71",
            opacity=0.4,
        )
        fig.update_layout(title="Customer Growth", **fin_fig())
        render_chart(fig, key="fig_L4303", use_container_width=True)

    with c2:
        fig = go.Figure()
        fig.add_bar(
            x=months,
            y=df["New_Enterprise_Wins"],
            name="New Enterprise",
            marker_color="#2ecc71",
            opacity=0.85,
        )
        fig.add_bar(
            x=months,
            y=df["Enterprise_Upgrades"],
            name="Upgrades from Pro",
            marker_color="#a9cce3",
            opacity=0.85,
        )
        fig.add_bar(
            x=months,
            y=-df["Lost_Enterprise"],
            name="Lost",
            marker_color="#e74c3c",
            opacity=0.85,
        )
        fig.update_layout(
            barmode="relative", title="Enterprise Customer Wins/Losses", **fin_fig()
        )
        render_chart(fig, key="fig_L4331", use_container_width=True)

    # ── ROW 3: Revenue/Costs/EBIT + Gross Margin ──────────────────────────
    st.markdown(
        '<div class="section-heading">📉 Profitability</div>', unsafe_allow_html=True
    )
    c1, c2 = st.columns(2)

    with c1:
        fig = go.Figure()
        for col_name, color, name in [
            ("COGS", "#f0b27a", "CoGS"),
            ("RD_Cost", "#a9dfbf", "R&D"),
            ("SM_Cost", "#aed6f1", "S&M"),
            ("GA_Cost", "#d2b4de", "G&A"),
            ("CS_Cost", "#f9e79f", "CS"),
        ]:
            fig.add_scatter(
                x=months,
                y=df[col_name],
                name=name,
                stackgroup="costs",
                fillcolor=color,
                line=dict(color=color, width=0.5),
                mode="lines",
            )
        fig.add_scatter(
            x=months,
            y=df["Total_Revenue"],
            name="Revenue",
            mode="lines",
            line=dict(color="#27ae60", width=2.5),
        )
        fig.add_scatter(
            x=months,
            y=df["EBIT"],
            name="EBIT",
            mode="lines",
            line=dict(color="#2980b9", width=2, dash="dash"),
        )
        fig.update_layout(title="Revenues, Costs & EBIT", **fin_fig())
        render_chart(fig, key="fig_L4372", use_container_width=True)

    with c2:
        fig = go.Figure()
        fig.add_scatter(
            x=months,
            y=df["Gross_Margin_%"],
            name="Gross Margin %",
            mode="lines+markers",
            line=dict(color="#2980b9", width=2.5),
            fill="tozeroy",
            fillcolor="rgba(41,128,185,0.1)",
            marker=dict(size=4),
        )
        fig.update_layout(
            title="Gross Profit Margin",
            yaxis_ticksuffix="%",
            yaxis_range=[0, 100],
            **fin_fig(),
        )
        render_chart(fig, key="fig_L4392", use_container_width=True)

    # ── ROW 4: Cost Breakdown + Salaries ──────────────────────────────────
    st.markdown(
        '<div class="section-heading">🏗️ Cost Structure</div>', unsafe_allow_html=True
    )
    c1, c2 = st.columns(2)

    with c1:
        fig = go.Figure()
        cost_layers = [
            ("COGS", "#5dade2", "CoGS"),
            ("RD_Cost", "#a9cce3", "R&D"),
            ("SM_Cost", "#f9e79f", "S&M"),
            ("GA_Cost", "#f0b27a", "G&A"),
            ("CS_Cost", "#d2b4de", "CS"),
        ]
        for col_name, color, name in cost_layers:
            fig.add_scatter(
                x=months,
                y=df[col_name],
                name=name,
                stackgroup="costs",
                fillcolor=color,
                line=dict(color=color, width=0.5),
                mode="lines",
            )
        fig.update_layout(title="Monthly Costs by P&L Category", **fin_fig())
        render_chart(fig, key="fig_L4420", use_container_width=True)

    with c2:
        fig = go.Figure()
        sal_layers = [
            ("Salary_GA", "#5dade2", "G&A"),
            ("Salary_Engineering", "#f0b27a", "Engineering"),
            ("Salary_Marketing", "#a9dfbf", "Marketing"),
            ("Salary_Sales", "#f9e79f", "Sales"),
            ("Salary_CS", "#d2b4de", "CS"),
        ]
        for col_name, color, name in sal_layers:
            fig.add_scatter(
                x=months,
                y=df[col_name],
                name=name,
                stackgroup="sal",
                fillcolor=color,
                line=dict(color=color, width=0.5),
                mode="lines",
            )
        fig.update_layout(title="Monthly Salaries by Department", **fin_fig())
        render_chart(fig, key="fig_L4442", use_container_width=True)

    # ── ROW 5: Headcount + S&M Efficiency ─────────────────────────────────
    st.markdown(
        '<div class="section-heading">🧑‍💼 Team & Efficiency</div>',
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)

    with c1:
        fig = go.Figure()
        hc_layers = [
            ("HC_GA", "#5dade2", "G&A"),
            ("HC_Engineering", "#f0b27a", "Engineering"),
            ("HC_Marketing", "#a9dfbf", "Marketing"),
            ("HC_Sales", "#f9e79f", "Sales"),
            ("HC_CS", "#d2b4de", "CS"),
        ]
        for col_name, color, name in hc_layers:
            fig.add_scatter(
                x=months,
                y=df[col_name],
                name=name,
                stackgroup="hc",
                fillcolor=color,
                line=dict(color=color, width=0.5),
                mode="lines",
            )
        fig.update_layout(title="Headcount by Department", **fin_fig())
        render_chart(fig, key="fig_L4471", use_container_width=True)

    with c2:
        fig = go.Figure()
        fig.add_scatter(
            x=months,
            y=df["SM_Efficiency"],
            name="S&M Efficiency",
            mode="lines+markers",
            line=dict(color="#2980b9", width=2.5),
            fill="tozeroy",
            fillcolor="rgba(41,128,185,0.08)",
            marker=dict(size=4),
        )
        fig.add_hline(
            y=1.0,
            line_color="#e74c3c",
            line_dash="dash",
            annotation_text="1.0x break-even",
            annotation_font_color="#e74c3c",
        )
        fig.update_layout(title="Sales & Marketing Efficiency", **fin_fig())
        render_chart(fig, key="fig_L4493", use_container_width=True)

    # ── ROW 6: CAC Payback + LTV:CAC ──────────────────────────────────────
    st.markdown(
        '<div class="section-heading">🎯 Unit Economics</div>', unsafe_allow_html=True
    )
    c1, c2 = st.columns(2)

    with c1:
        fig = go.Figure()
        fig.add_scatter(
            x=months,
            y=df["CAC_Payback_Basic"],
            name="Basic",
            mode="lines+markers",
            line=dict(color="#8e44ad", width=2),
            marker=dict(size=4),
        )
        fig.add_scatter(
            x=months,
            y=df["CAC_Payback_Pro"],
            name="Pro",
            mode="lines+markers",
            line=dict(color="#2980b9", width=2),
            marker=dict(size=4),
        )
        fig.add_scatter(
            x=months,
            y=df["CAC_Payback_Enterprise"],
            name="Enterprise",
            mode="lines+markers",
            line=dict(color="#27ae60", width=2),
            marker=dict(size=4),
        )
        fig.update_layout(
            title="CAC Payback Time by Pricing Plan",
            yaxis_title="Months to Payback",
            **fin_fig(),
        )
        render_chart(fig, key="fig_L4532", use_container_width=True)

    with c2:
        fig = go.Figure()
        fig.add_scatter(
            x=months,
            y=df["LTV_CAC_Ratio"],
            name="LTV:CAC",
            mode="lines+markers",
            line=dict(color="#e67e22", width=2.5),
            marker=dict(size=4),
        )
        fig.add_hline(
            y=3.0,
            line_color="#27ae60",
            line_dash="dash",
            annotation_text="3x benchmark",
            annotation_font_color="#27ae60",
        )
        fig.update_layout(
            title="LTV / CAC Ratio", yaxis_title="LTV:CAC Ratio", **fin_fig()
        )
        render_chart(fig, key="fig_L4554", use_container_width=True)

    # ── Side-by-side comparison (only when that scenario selected) ─────────
    if "Side-by-Side" in scenario:
        st.markdown(
            '<div class="section-heading">⚖️ Base vs High Churn Comparison</div>',
            unsafe_allow_html=True,
        )
        compare_pairs = [
            ("MRR", "MRR ($)", "MRR Growth"),
            ("Total_Customers", "Customers", "Total Customers"),
            ("Cumulative_Cash", "Cumulative Cash ($)", "Cumulative Cash"),
            ("Gross_Margin_%", "Gross Margin %", "Gross Margin"),
            ("SM_Efficiency", "Efficiency", "S&M Efficiency"),
            ("EBIT", "EBIT ($)", "EBIT"),
        ]
        for i in range(0, len(compare_pairs), 2):
            cols = st.columns(2)
            for j, (col_name, ylabel, title) in enumerate(compare_pairs[i: i + 2]):
                with cols[j]:
                    fig = go.Figure()
                    fig.add_scatter(
                        x=df_base["Month"],
                        y=df_base[col_name],
                        name="Base (5% churn)",
                        mode="lines+markers",
                        line=dict(color="#2980b9", width=2),
                        marker=dict(size=4),
                    )
                    fig.add_scatter(
                        x=df_churn["Month"],
                        y=df_churn[col_name],
                        name="High Churn (10%)",
                        mode="lines+markers",
                        line=dict(color="#e74c3c", width=2, dash="dash"),
                        marker=dict(size=4),
                    )
                    fig.update_layout(
                        title=title, yaxis_title=ylabel, **fin_fig())
        render_chart(fig, key='fig_financial_l4595_L4593', use_container_width=True)

    # Export financial simulation data
    fin_csv = convert_to_csv(df)
    st.download_button(
        "📥 Export Financial Data (CSV)",
        data=fin_csv,
        file_name="financial_simulation.csv",
        mime="text/csv",
    )

    # Export base scenario if side-by-side comparison was shown
    if "Side-by-Side" in scenario:
        base_csv = convert_to_csv(df_base)
        st.download_button(
            "📥 Export Base Scenario (CSV)",
            data=base_csv,
            file_name="financial_base_scenario.csv",
            mime="text/csv",
        )

    # ── Scenario Comparison Overlay ──
    st.html(
        '<div class="section-header">'
        '<div class="section-title">'
        '<span class="title-icon">📈</span>'
        '<span>Scenario Comparison — Net Income Overlay</span>'
        '</div>'
        '</div>'
    )

    if 'df' in dir() and df is not None and not df.empty:
        scenario_cols = [c for c in df.columns if 'net_income' in c or 'optimistic' in c or 'conservative' in c or 'baseline' in c]
        if scenario_cols:
            fig_scenario = go.Figure()
            colors_map = {'optimistic': '#22c55e', 'baseline': '#3b82f6', 'conservative': '#facc15'}
            for col in scenario_cols:
                label = col.replace('_net_income', '').replace('_', ' ').title()
                color = next((v for k, v in colors_map.items() if k in col.lower()), '#a78bfa')
                fig_scenario.add_trace(go.Scatter(
                    x=df['Month'],
                    y=df[col],
                    mode='lines+markers',
                    name=label,
                    line=dict(width=3, color=color, shape='spline'),
                    marker=dict(size=6, color=color),
                ))
            fig_scenario.update_layout(
                height=350,
                margin=dict(t=10, l=0, r=0, b=0),
                hovermode='x unified',
                yaxis_title='Net Income (€)',
            )
            style_chart(fig_scenario, legend=True)
            render_chart(fig_scenario, key='fig_scenario_FIN', use_container_width=True)
        else:
            fig_base = go.Figure()
            fig_base.add_trace(go.Scatter(
                x=df['Month'], y=df['Profit_Loss'],
                mode='lines+markers', name='Net Income',
                line=dict(color='#3b82f6', width=3, shape='spline'),
                fill='tozeroy', fillcolor='rgba(59,130,246,0.1)',
            ))
            fig_base.add_trace(go.Scatter(
                x=df['Month'], y=df['MRR'],
                mode='lines', name='MRR',
                line=dict(color='#22c55e', width=2, dash='dot'),
            ))
            fig_base.update_layout(height=350, margin=dict(t=10, l=0, r=0, b=0), hovermode="x unified")
            style_chart(fig_base, legend=True)
            render_chart(fig_base, key='fig_base_FIN', use_container_width=True)

    # ── Unit Economics Summary ──
    st.html(
        '<div class="section-header">'
        '<div class="section-title">'
        '<span class="title-icon">💰</span>'
        '<span>Unit Economics Snapshot</span>'
        '</div>'
        '</div>'
    )

    # Always use artificial big-startup data
    avg_rev_per_cust  = 249
    gross_margin      = 78.0
    total_customers    = 8400
    total_mrr          = 2091600

    ue1, ue2, ue3, ue4 = st.columns(4)
    with ue1:
        st.markdown(
            f'<div class="stat-card success press-effect">'
            f'<div class="stat-card-label">ARPU</div>'
            f'<div class="stat-card-value">€{avg_rev_per_cust:,.0f}</div>'
            f'<div style="font-size:0.7rem;color:var(--text-muted);">Avg Revenue / Customer</div>'
            f'</div>', unsafe_allow_html=True,
        )
    with ue2:
        st.markdown(
            f'<div class="stat-card info press-effect">'
            f'<div class="stat-card-label">Gross Margin</div>'
            f'<div class="stat-card-value">{gross_margin:.1f}%</div>'
            f'<div style="font-size:0.7rem;color:var(--text-muted);">Per Customer</div>'
            f'</div>', unsafe_allow_html=True,
        )
    with ue3:
        st.markdown(
            f'<div class="stat-card warning press-effect">'
            f'<div class="stat-card-label">Customers</div>'
            f'<div class="stat-card-value">{total_customers:,}</div>'
            f'<div style="font-size:0.7rem;color:var(--text-muted);">Active</div>'
            f'</div>', unsafe_allow_html=True,
        )
    with ue4:
        st.markdown(
            f'<div class="stat-card info press-effect">'
            f'<div class="stat-card-label">Monthly MRR</div>'
            f'<div class="stat-card-value">€{total_mrr:,.0f}</div>'
            f'<div style="font-size:0.7rem;color:var(--text-muted);">Recurring Revenue</div>'
            f'</div>', unsafe_allow_html=True,
        )

    st.html("</div></div>")

elif active_tab == "customer":
    # ═══════════════════════════════════════════════════════════
    # CUSTOMER SEGMENTATION TAB - B2B Railway Operators
    # ═══════════════════════════════════════════════════════════
    with st.spinner("Loading customer data..."):
        customer_df = get_customer_data()
        rfm_df = get_rfm_analysis(customer_df)
        high_value_df = get_high_value_customers(customer_df)
        insights = get_customer_business_insights(customer_df)
        health_df = get_contract_health_score(customer_df)
        renewal_df = get_renewal_forecast(customer_df)
        at_risk_df = get_at_risk_accounts(customer_df)
        health_summary = get_renewal_health_summary(customer_df)

    # Top-level metrics with icons
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f"""
        <div class="viz-metric-card">
            <div class="viz-metric-icon">🚂</div>
            <div class="viz-metric-value">{insights["total_customers"]}</div>
            <div class="viz-metric-label">Railway Operators</div>
            <div class="viz-metric-sub">{insights["total_trains_covered"]:,} trains covered</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
        <div class="viz-metric-card">
            <div class="viz-metric-icon">💰</div>
            <div class="viz-metric-value">{format_euro(insights["total_contract_value_eur"])}</div>
            <div class="viz-metric-label">Total Contract Value</div>
            <div class="viz-metric-sub">{format_euro(insights["avg_contract_value_eur"])} avg per account</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""
        <div class="viz-metric-card">
            <div class="viz-metric-icon">🚪</div>
            <div class="viz-metric-value">{smart_format(insights["total_psd_units"])}</div>
            <div class="viz-metric-label">PSD Units Installed</div>
            <div class="viz-metric-sub">Platform screen doors</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f"""
        <div class="viz-metric-card">
            <div class="viz-metric-icon">⭐</div>
            <div class="viz-metric-value">{insights["high_value_count"]}</div>
            <div class="viz-metric-label">High-Value Accounts</div>
            <div class="viz-metric-sub">{format_score(insights["avg_satisfaction"])} satisfaction</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="section-heading">📊 RFM Segment Distribution</div>',
        unsafe_allow_html=True,
    )

    col_left, col_right = st.columns([2, 1])
    with col_left:
        segment_counts = rfm_df["rfm_segment"].value_counts().reset_index()
        segment_counts.columns = ["Segment", "Count"]

        segment_colors = {
            "Strategic Partners": "var(--color-emerald)",
            "Key Accounts": "#3b82f6",
            "Growth Potential": "#8b5cf6",
            "At Risk": "var(--color-warning)",
            "Dormant": "var(--color-danger)",
        }

        fig_rfm = px.bar(
            segment_counts,
            x="Segment",
            y="Count",
            color="Segment",
            color_discrete_map=segment_colors,
            title="Customer Segments by RFM Score",
            text="Count",
        )
        fig_rfm.update_traces(
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>RFM Score: %{x:.1f}<br>Count: %{text}<extra></extra>",
        )
        style_chart(fig_rfm, legend=False)
        render_chart(fig_rfm, key="fig_rfm_L4713", use_container_width=True)

    with col_right:
        segment_pct = segment_counts.copy()
        segment_pct["Percentage"] = (
            segment_pct["Count"] / segment_pct["Count"].sum() * 100
        ).astype(int)
        segment_pct["Display"] = (
            segment_pct["Segment"] + ": ~" +
            segment_pct["Percentage"].astype(str) + "%"
        )

        fig_pie = px.pie(
            segment_pct,
            values="Count",
            names="Segment",
            color="Segment",
            color_discrete_map=segment_colors,
            hole=0.4,
            title="Segment Share",
        )
        style_pie(fig_pie, title="Segment Share")
        render_chart(fig_pie, key="fig_pie_L4735", use_container_width=True)

    st.markdown(
        '<div class="section-heading">📈 RFM Score Breakdown by Segment</div>',
        unsafe_allow_html=True,
    )

    def highlight_rfm(val, max_val=5):
        ratio = val / max_val
        if ratio >= 0.8:
            return "background-color: rgba(16, 185, 129, 0.3); color: var(--color-emerald)"
        elif ratio >= 0.6:
            return "background-color: rgba(59, 130, 246, 0.3); color: #3b82f6"
        elif ratio >= 0.4:
            return "background-color: rgba(245, 158, 11, 0.3); color: var(--color-warning)"
        else:
            return "background-color: rgba(239, 68, 68, 0.3); color: var(--color-danger)"

    if rfm_df is not None and not rfm_df.empty and "rfm_segment" in rfm_df.columns:
        rfm_summary = (
            rfm_df.groupby("rfm_segment")
            .agg(
                {
                    "recency_score": "mean",
                    "frequency_score": "mean",
                    "monetary_score": "mean",
                    "platforms_installed": "mean",
                    "total_contract_value_eur": "mean",
                }
            )
            .round(0)
        )
        rfm_summary.columns = [
            "Avg Recency",
            "Avg Frequency",
            "Avg Monetary",
            "Avg Platforms",
            "Avg Contract (€)",
        ]
        rfm_summary = rfm_summary.reset_index()
        rfm_summary.columns = [
            "Segment",
            "Avg Recency",
            "Avg Frequency",
            "Avg Monetary",
            "Avg Platforms",
            "Avg Contract (€)",
        ]
    else:
        rfm_summary = pd.DataFrame(columns=[
                                   "Segment", "Avg Recency", "Avg Frequency", "Avg Monetary", "Avg Platforms", "Avg Contract (€)"])

    if not rfm_summary.empty:
        st.dataframe(
            rfm_summary.style.map(
                highlight_rfm, subset=["Avg Recency",
                                       "Avg Frequency", "Avg Monetary"]
            ),
            use_container_width=True,
            hide_index=True,
        )

    # Additional visualizations
    st.markdown(
        '<div class="section-heading">📊 Contract Value by Operator Type</div>',
        unsafe_allow_html=True,
    )

    col_extra1, col_extra2 = st.columns(2)
    with col_extra1:
        type_value = (
            customer_df.groupby("operator_type")
            .agg(
                {
                    "total_contract_value_eur": "sum",
                    "psd_units": "sum",
                    "customer_id": "count",
                }
            )
            .reset_index()
        )
        type_value.columns = [
            "Operator Type",
            "Total Contract (€)",
            "PSD Units",
            "Count",
        ]

        fig_type = px.bar(
            type_value,
            x="Operator Type",
            y="Total Contract (€)",
            color="Operator Type",
            title="Contract Value by Operator Type",
            text="Total Contract (€)",
        )
        style_chart(fig_type, legend=False)
        fig_type.update_traces(textposition="outside")
        render_chart(fig_type, key="fig_type_L4833", use_container_width=True)

    with col_extra2:
        fig_type_psd = px.bar(
            type_value,
            x="Operator Type",
            y="PSD Units",
            color="Operator Type",
            title="PSD Units by Operator Type",
            text="PSD Units",
        )
        style_chart(fig_type_psd, legend=False)
        fig_type_psd.update_traces(textposition="outside")
        render_chart(fig_type_psd, key="fig_type_psd_L4846", use_container_width=True)

    # Tier distribution
    st.markdown(
        '<div class="section-heading">🏆 Contract Tier Distribution</div>',
        unsafe_allow_html=True,
    )

    col_tier1, col_tier2 = st.columns(2)
    with col_tier1:
        tier_value = (
            customer_df.groupby("tier")
            .agg(
                {
                    "total_contract_value_eur": "sum",
                    "psd_units": "sum",
                    "customer_id": "count",
                }
            )
            .reset_index()
        )
        tier_value.columns = [
            "Tier", "Total Contract (€)", "PSD Units", "Count"]

        tier_colors_map = {
            "Platinum": "#e5e7eb",
            "Gold": "#fbbf24",
            "Silver": "var(--text-secondary)",
            "Bronze": "#b45309",
        }

        fig_tier_bar = px.bar(
            tier_value,
            x="Tier",
            y="Total Contract (€)",
            color="Tier",
            color_discrete_map=tier_colors_map,
            title="Contract Value by Tier",
            text="Total Contract (€)",
        )
        style_chart(fig_tier_bar, legend=False,
                    xaxis=dict(title="Contract Tier"))
        fig_tier_bar.update_traces(textposition="outside")
        render_chart(fig_tier_bar, key="fig_tier_bar_L4889", use_container_width=True)

    with col_tier2:
        fig_tier_donut = px.pie(
            tier_value,
            values="Total Contract (€)",
            names="Tier",
            color="Tier",
            color_discrete_map=tier_colors_map,
            hole=0.4,
            title="Contract Share by Tier",
        )
        style_pie(fig_tier_donut)
        render_chart(fig_tier_donut, key="fig_tier_donut_L4902", use_container_width=True)

    st.markdown(
        '<div class="section-heading">📈 RFM Score Distribution</div>',
        unsafe_allow_html=True,
    )

    col_rfm1, col_rfm2 = st.columns(2)
    with col_rfm1:
        fig_rfm_hist = px.histogram(
            rfm_df,
            x="rfm_score",
            nbins=15,
            title="RFM Score Distribution",
            color_discrete_sequence=["#3b82f6"],
        )
        style_chart(fig_rfm_hist, legend=False)
        render_chart(fig_rfm_hist, key="fig_rfm_hist_L4919", use_container_width=True)

    with col_rfm2:
        fig_scatter = px.scatter(
            rfm_df,
            x="recency_score",
            y="monetary_score",
            size="platforms_installed",
            color="rfm_segment",
            color_discrete_map=segment_colors,
            title="Recency vs Monetary Score",
            hover_data=["customer_name"],
        )
        fig_scatter.update_traces(
            hovertemplate="<b>%{hovertext}</b><br>" +
                          "Recency: %{x:.0f} days<br>" +
                          "Monetary: %{y:.0f}<br>" +
                          "Customer: %{customdata[0]}<extra></extra>",
        )
        style_chart(fig_scatter, hovermode="closest")
        render_chart(fig_scatter, key="fig_scatter_L4939", use_container_width=True)

    st.markdown(
        '<div class="section-heading">⭐ High-Value Accounts Ranking</div>',
        unsafe_allow_html=True,
    )

    high_value_display = (
        high_value_df[
            [
                "customer_id",
                "customer_name",
                "operator_type",
                "value_score",
                "value_tier",
                "psd_units",
                "total_contract_value_eur",
            ]
        ]
        .head(15)
        .copy()
    )

    high_value_display["Contract Value"] = high_value_display[
        "total_contract_value_eur"
    ].apply(format_euro)
    high_value_display["Display Score"] = "~" + high_value_display[
        "value_score"
    ].astype(int).astype(str)

    tier_colors = {
        "Strategic": "var(--color-emerald)",
        "Preferred": "#fbbf24",
        "Important": "var(--text-secondary)",
    }

    fig_hv = px.bar(
        high_value_display,
        x="value_score",
        y="customer_name",
        color="value_tier",
        color_discrete_map=tier_colors,
        orientation="h",
        title="Top 15 High-Value Accounts by Contract Value",
        text="Display Score",
        custom_data=["Contract Value", "psd_units", "operator_type"],
        hover_name="customer_name",
    )
    fig_hv.update_traces(
        textposition="outside",
    )
    style_chart(fig_hv, height=500,
                xaxis=dict(title="Value Score"), yaxis=dict(title=""),
                legend=dict(orientation="h", y=-0.25, x=0.5, xanchor="center"),
                margin=dict(l=60, r=24, t=65, b=80))
    render_chart(fig_hv, key="fig_hv_L4994", use_container_width=True)

    col_hv1, col_hv2 = st.columns(2)
    with col_hv1:
        st.markdown("**Value Tier Distribution**", unsafe_allow_html=True)
        tier_counts = high_value_df["value_tier"].value_counts()
        tier_df = pd.DataFrame(
            {"Tier": tier_counts.index, "Count": tier_counts.values})

        fig_tier = px.pie(
            tier_df,
            values="Count",
            names="Tier",
            color="Tier",
            color_discrete_map=tier_colors,
            hole=0.4,
            title="Account Tier Breakdown",
        )
        style_pie(fig_tier, height=350, title="Account Tier Breakdown")
        fig_tier.update_traces(
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>Accounts: %{value}<br>Share: %{percent}<extra></extra>",)
        render_chart(fig_tier, key="fig_tier_L5016", use_container_width=True)

    with col_hv2:
        st.markdown("**Top 5 by Contract Value**", unsafe_allow_html=True)
        top5_value = high_value_df.nlargest(5, "total_contract_value_eur")[
            ["customer_name", "operator_type",
                "total_contract_value_eur", "psd_units"]
        ].copy()
        top5_value["Contract Value"] = top5_value["total_contract_value_eur"].apply(
            format_euro
        )
        top5_value = top5_value.drop(columns=["total_contract_value_eur"])

        top5_value.columns = ["Operator", "Type", "PSD Units", "Value"]

        st.dataframe(
            top5_value,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Value": st.column_config.TextColumn("Value", help="Contract value"),
                "PSD Units": st.column_config.NumberColumn("PSD Units", format="~%d"),
            },
        )

    st.markdown(
        '<div class="section-heading">💡 Business Insights &amp; Recommendations</div>',
        unsafe_allow_html=True,
    )

    col_ins1, col_ins2 = st.columns(2)
    with col_ins1:
        st.markdown("**Key Metrics**", unsafe_allow_html=True)
        st.markdown(
            f"""
        <div style="display: grid; gap: 0.5rem;">
            <div style="display: flex; justify-content: space-between; padding: 0.5rem; background: var(--bg-tertiary); border-radius: 8px;">
                <span style="color: var(--text-secondary);">At-Risk Rate</span>
                <span style="color: {"var(--color-danger)" if insights["risk_rate"] > 20 else "var(--color-emerald)"}; font-weight: 600;">~{int(insights["risk_rate"])}%</span>
            </div>
            <div style="display: flex; justify-content: space-between; padding: 0.5rem; background: var(--bg-tertiary); border-radius: 8px;">
                <span style="color: var(--text-secondary);">At-Risk Accounts</span>
                <span style="color: var(--color-warning); font-weight: 600;">{insights["at_risk_count"]} (~{int(insights["at_risk_pct"])}%)</span>
            </div>
            <div style="display: flex; justify-content: space-between; padding: 0.5rem; background: var(--bg-tertiary); border-radius: 8px;">
                <span style="color: var(--text-secondary);">Strategic Partners</span>
                <span style="color: var(--color-emerald); font-weight: 600;">{insights["strategic_count"]} (~{int(insights["strategic_pct"])}%)</span>
            </div>
            <div style="display: flex; justify-content: space-between; padding: 0.5rem; background: var(--bg-tertiary); border-radius: 8px;">
                <span style="color: var(--text-secondary);">Top Segment</span>
                <span style="color: var(--accent-primary); font-weight: 600;">{insights["top_operator_type"]}</span>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col_ins2:
        st.markdown("**AI Recommendations**", unsafe_allow_html=True)
        for rec in insights["recommendations"]:
            rec_class = f"recommendation-{rec['priority']}"
            priority_emoji = (
                "🔴"
                if rec["priority"] == "high"
                else ("🟡" if rec["priority"] == "medium" else "🔵")
            )
            st.markdown(
                f"""
            <div class="recommendation-card {rec_class}">
                <div style="font-weight: 600; margin-bottom: 0.25rem;">
                    {priority_emoji} {rec["category"]}
                </div>
                <div style="color: var(--text-secondary); font-size: 0.9rem;">{rec["message"]}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

    # ─────────────────────────────────────────────────────────────
    # RENEWAL & HEALTH SIGNALS SECTION
    # ─────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        '<div class="section-heading">💚 Renewal &amp; Health Signals</div>',
        unsafe_allow_html=True,
    )

    # Health Summary Cards
    col_h1, col_h2, col_h3, col_h4 = st.columns(4)
    with col_h1:
        health_color = (
            "var(--color-emerald)"
            if health_summary["avg_health_score"] >= 70
            else ("var(--color-warning)" if health_summary["avg_health_score"] >= 50 else "var(--color-danger)")
        )
        st.markdown(
            f"""
        <div class="viz-metric-card" style="border-left: 4px solid {health_color};">
            <div class="viz-metric-icon">💚</div>
            <div class="viz-metric-value" style="color: {health_color};">~{int(health_summary["avg_health_score"])}</div>
            <div class="viz-metric-label">Avg Health Score</div>
            <div class="viz-metric-sub">{health_summary["healthy_count"]} Healthy / {health_summary["total_operators"]} Total</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col_h2:
        st.markdown(
            f"""
        <div class="viz-metric-card" style="border-left: 4px solid var(--color-danger);">
            <div class="viz-metric-icon">🔴</div>
            <div class="viz-metric-value" style="color: var(--color-danger);">{health_summary["critical_count"]}</div>
            <div class="viz-metric-label">Critical Health</div>
            <div class="viz-metric-sub">Needs Immediate Attention</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col_h3:
        st.markdown(
            f"""
        <div class="viz-metric-card" style="border-left: 4px solid var(--color-warning);">
            <div class="viz-metric-icon">⚠️</div>
            <div class="viz-metric-value" style="color: var(--color-warning);">{health_summary["at_risk_high"]}</div>
            <div class="viz-metric-label">High Risk Accounts</div>
            <div class="viz-metric-sub">{format_euro(health_summary["contract_value_at_risk"])} at risk</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col_h4:
        renewal_color = (
            "var(--color-danger)" if health_summary["renewal_critical"] > 0 else "var(--color-emerald)"
        )
        st.markdown(
            f"""
        <div class="viz-metric-card" style="border-left: 4px solid {renewal_color};">
            <div class="viz-metric-icon">📅</div>
            <div class="viz-metric-value" style="color: {renewal_color};">{health_summary["renewal_critical"]}</div>
            <div class="viz-metric-label">Critical Renewals</div>
            <div class="viz-metric-sub">{health_summary["renewal_urgent"]} urgent / {health_summary["renewal_upcoming"]} upcoming</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Renewal Forecast & At-Risk Accounts
    col_r1, col_r2 = st.columns(2)

    with col_r1:
        st.markdown('<p style="margin-top: 1rem;"><strong>📅 Upcoming Renewals (Next 90 Days)</strong></p>',
                    unsafe_allow_html=True)
        upcoming_renewals = renewal_df[renewal_df["days_to_renewal"] <= 90].copy(
        )

        if len(upcoming_renewals) > 0:
            display_renewals = upcoming_renewals[
                [
                    "customer_name",
                    "operator_type",
                    "days_to_renewal",
                    "renewal_tier",
                    "total_contract_value_eur",
                    "satisfaction_score",
                ]
            ].head(10)
            display_renewals.columns = [
                "Operator",
                "Type",
                "Days Left",
                "Urgency",
                "Contract (€)",
                "Satisfaction",
            ]

            def urgency_color(urgency):
                if urgency == "Critical (<30d)":
                    return "background-color: rgba(239, 68, 68, 0.3); color: var(--color-danger)"
                elif urgency == "Urgent (<60d)":
                    return "background-color: rgba(245, 158, 11, 0.3); color: var(--color-warning)"
                return "background-color: rgba(59, 130, 246, 0.3); color: #3b82f6"

            st.dataframe(
                display_renewals.style.map(urgency_color, subset=["Urgency"]),
                use_container_width=True,
                hide_index=True,
                height=300,
            )
        else:
            st.info("No renewals in the next 90 days")

    with col_r2:
        st.markdown(
            '<p style="margin-top: 1rem;"><strong>🔴 At-Risk Accounts</strong></p>', unsafe_allow_html=True)
        at_risk_display = at_risk_df[
            at_risk_df["risk_level"].isin(["High Risk", "Medium Risk"])
        ].head(10)

        if len(at_risk_display) > 0:
            risk_table = at_risk_display[
                [
                    "customer_name",
                    "operator_type",
                    "risk_level",
                    "satisfaction_score",
                    "open_issues",
                    "days_to_renewal",
                    "total_contract_value_eur",
                ]
            ]
            risk_table.columns = [
                "Operator",
                "Type",
                "Risk Level",
                "Satisfaction",
                "Open Issues",
                "Days to Renewal",
                "Contract (€)",
            ]

            def risk_color(level):
                if level == "High Risk":
                    return "background-color: rgba(239, 68, 68, 0.3); color: var(--color-danger)"
                return "background-color: rgba(245, 158, 11, 0.3); color: var(--color-warning)"

            st.dataframe(
                risk_table.style.map(risk_color, subset=["Risk Level"]),
                use_container_width=True,
                hide_index=True,
                height=300,
            )
        else:
            st.info("No at-risk accounts identified")

    # Health Score Distribution
    st.markdown('<p style="margin-top: 1rem;"><strong>📊 Health Score Distribution</strong></p>', unsafe_allow_html=True)
    col_health1, col_health2 = st.columns(2)

    with col_health1:
        health_dist = (
            health_df.groupby("health_status")[
                "customer_id"].count().reset_index()
        )
        health_dist.columns = ["Status", "Count"]

        status_colors = {
            "Healthy": "var(--color-emerald)",
            "Attention": "var(--color-warning)",
            "Critical": "var(--color-danger)",
        }

        fig_health = px.pie(
            health_dist,
            values="Count",
            names="Status",
            color="Status",
            color_discrete_map=status_colors,
            hole=0.4,
            title="Account Health Distribution",
        )
        style_pie(fig_health)
        render_chart(fig_health, key="fig_health_L5277", use_container_width=True)

    with col_health2:
        fig_health_bar = px.bar(
            health_df.sort_values("health_score", ascending=False).head(15),
            x="customer_name",
            y="health_score",
            color="health_score",
            color_continuous_scale="RdYlGn",
            title="Health Scores by Operator",
            text="health_score",
        )
        style_chart(fig_health_bar,
                    xaxis=dict(tickangle=-45), yaxis=dict(title="Health Score"),
                    coloraxis=dict(colorscale="RdYlGn", cmin=0, cmax=100))
        fig_health_bar.update_traces(textposition="outside")
        render_chart(fig_health_bar, key="fig_health_bar_L5293", use_container_width=True)

    # Upcoming Renewal Value
    st.markdown('<p style="margin-top: 1rem;"><strong>💰 Upcoming Renewal Value</strong></p>', unsafe_allow_html=True)
    col_val1, col_val2, col_val3 = st.columns(3)
    with col_val1:
        st.metric(
            "Next 30 Days",
            format_euro(health_summary["upcoming_renewals_30d"]),
            delta=f"~{health_summary['renewal_critical']} critical",
        )
    with col_val2:
        st.metric(
            "Next 60 Days",
            format_euro(health_summary["upcoming_renewals_60d"]),
            delta=f"~{health_summary['renewal_urgent']} urgent",
        )
    with col_val3:
        st.metric(
            "Next 90 Days",
            format_euro(health_summary["upcoming_renewals_90d"]),
            delta=f"~{health_summary['renewal_upcoming']} upcoming",
        )

    st.markdown("---")
    # ─────────────────────────────────────────────────────────────
    # ALL OPERATORS DATA
    # ─────────────────────────────────────────────────────────────
    st.markdown(
        '<div class="section-heading">📋 All Railway Operators Data</div>',
        unsafe_allow_html=True,
    )

    customer_table = customer_df[
        [
            "customer_id",
            "customer_name",
            "operator_type",
            "tier",
            "total_trains",
            "total_routes",
            "platforms_installed",
            "psd_units",
            "total_contract_value_eur",
            "maintenance_annual_eur",
            "total_contract_value_eur",
            "last_project_days",
            "open_issues",
            "satisfaction_score",
            "contract_status",
        ]
    ]
    customer_table.columns = [
        "ID",
        "Operator",
        "Type",
        "Tier",
        "Trains",
        "Routes",
        "Platforms",
        "PSD Units",
        "Contract (€)",
        "Maint. (€)",
        "Total (€)",
        "Days Ago",
        "Issues",
        "Satisfaction",
        "Status",
    ]

    st.dataframe(
        customer_table.style.background_gradient(
            subset=["Total (€)"], cmap="Greens"
        ).background_gradient(subset=["Satisfaction"], cmap="RdYlGn", vmin=5, vmax=10),
        use_container_width=True,
        hide_index=True,
    )

    # Download button
    csv = customer_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download All Operator Data (CSV)",
        data=csv,
        file_name="railway_operators_data.csv",
        mime="text/csv",
    )

    # ── Frequency vs Monetary Scatter ──
    if rfm_df is not None and not rfm_df.empty:
        st.html(
            '<div class="section-header">'
            '<div class="section-title">'
            '<span class="title-icon">📊</span>'
            '<span>Customer Value Map — Frequency vs Spend</span>'
            '</div>'
            '</div>'
        )

        fig_rfm = px.scatter(
            rfm_df,
            x="frequency_score",
            y="monetary_score",
            color="segment",
            size="recency_score",
            hover_data=["customer_name"],
            title="",
            labels={"frequency_score": "Transaction Frequency", "monetary_score": "Total Spend (€)", "segment": "Segment"},
        )
        fig_rfm.update_traces(
            marker=dict(line=dict(width=1, color="rgba(0,0,0,0.3)"), opacity=0.85),
            hovertemplate="<b>%{customdata[0]}</b><br>"
                          "Frequency: %{x}<br>"
                          "Spend: €%{y:,.0f}<br>"
                          "Segment: %{marker.color}<extra></extra>",
        )
        fig_rfm.update_layout(height=380, margin=dict(t=10, l=0, r=0, b=0))
        style_chart(fig_rfm, legend=True)
        render_chart(fig_rfm, key='fig_rfm_scatter_CUST', use_container_width=True)

    # ── Health Score Distribution Bar ──
    if health_df is not None and not health_df.empty:
        st.html(
            '<div class="section-header">'
            '<div class="section-title">'
            '<span class="title-icon">❤️</span>'
            '<span>Contract Health Score Distribution</span>'
            '</div>'
            '</div>'
        )

        health_counts = health_df["health_status"].value_counts().reset_index()
        health_counts.columns = ["Status", "Count"]

        health_colors = {"Healthy": "#22c55e", "At Risk": "#facc15", "Critical": "#ef4444", "Warning": "#f97316"}
        fig_health = px.bar(
            health_counts,
            x="Status",
            y="Count",
            color="Status",
            color_discrete_map=health_colors,
            title="",
            text="Count",
        )
        fig_health.update_traces(
            texttemplate="%{text}",
            textposition="outside",
            marker_line_width=0,
        )
        fig_health.update_layout(height=320, margin=dict(t=10, l=0, r=0, b=0))
        style_chart(fig_health, legend=False,
                    xaxis=dict(categoryorder="array", categoryarray=["Healthy", "At Risk", "Warning", "Critical"]))
        render_chart(fig_health, key='fig_health_bar_CUST', use_container_width=True)

    # ── Operator Benchmark Comparison ──
    if customer_df is not None and not customer_df.empty and "segment" in customer_df.columns and "total_contract_value_eur" in customer_df.columns:
        st.html(
            '<div class="section-header">'
            '<div class="section-title">'
            '<span class="title-icon">🏆</span>'
            '<span>Operator Type Benchmark — Avg Contract Value</span>'
            '</div>'
            '</div>'
        )

        bench_data = customer_df.groupby("segment").agg(
            Avg_Value=("total_contract_value_eur", "mean"),
            Count=("customer_id", "count"),
            Total_Value=("total_contract_value_eur", "sum"),
        ).reset_index().sort_values("Avg_Value", ascending=True)

        fig_bench = px.bar(
            bench_data,
            x="Avg_Value",
            y="segment",
            orientation="h",
            color="Avg_Value",
            color_continuous_scale=["#22c55e", "#3b82f6", "#a78bfa"],
            text="Avg_Value",
            title="",
            labels={"Avg_Value": "Avg Contract (€)", "segment": "Operator Type"},
            hover_data={"Count": True, "Total_Value": ":,.0f"},
        )
        fig_bench.update_traces(
            texttemplate="€%{x:,.0f}",
            textposition="outside",
            marker_line_width=0,
        )
        fig_bench.update_layout(height=350, margin=dict(t=10, l=0, r=0, b=0))
        style_chart(fig_bench, legend=False,
                    coloraxis_colorbar=dict(
                        title=dict(text="Avg Value", font=dict(color="var(--text-secondary)", size=10)),
                        tickfont=dict(color="var(--text-secondary)", size=9), thickness=6, len=0.7,
                    ))
        render_chart(fig_bench, key='fig_bench_hbar_CUST', use_container_width=True)

elif active_tab == "portfolio":
    # ── Load Operator Data ──
    try:
        customer_df = get_customer_data()
    except Exception as e:
        st.error(f"Failed to load operator data: {e}")
        st.stop()

    # ── Operator Selection (Inline) ──
    st.markdown(
        '<div class="operator-select-card">'
        '<div class="operator-select-label">Select Operator</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Build operator options
    if customer_df is not None and not customer_df.empty:
        operators = customer_df[
            ["customer_id", "customer_name", "tier", "satisfaction_score"]
        ].sort_values("customer_name")

        operator_options = []
        for _, row in operators.iterrows():
            tier_icon = {
                "Platinum": "💎",
                "Gold": "🥇",
                "Silver": "🥈",
                "Bronze": "🥉",
            }.get(row["tier"], "📌")
            option_label = f"{tier_icon} {row['customer_name']} ({row['tier']})"
            operator_options.append((option_label, row["customer_id"]))
    else:
        operator_options = []

    option_labels = [opt[0] for opt in operator_options]
    option_to_id = dict(operator_options)

    # Auto-select first operator if none selected yet
    if st.session_state.selected_operator is None and operator_options:
        st.session_state.selected_operator = operator_options[0][1]

    current_id = st.session_state.selected_operator
    current_index = 0
    for i, (label, oid) in enumerate(operator_options):
        if oid == current_id:
            current_index = i
            break

    if operator_options:
        option_labels_with_all = ["All Operators"] + option_labels
        option_to_id_with_all = {"All Operators": "all"}
        option_to_id_with_all.update(option_to_id)

        if not current_index:
            current_index = 0

        selected_operator_label = st.selectbox(
            "Select an operator to view details",
            options=option_labels_with_all,
            index=current_index,
            key="operator_selector",
        )

        selected_operator_id = option_to_id_with_all[selected_operator_label]
        if st.session_state.selected_operator != selected_operator_id:
            st.session_state.selected_operator = selected_operator_id
            st.rerun()
    else:
        st.info("No customer data available")
        selected_operator_id = "all"

    if selected_operator_id == "all":
        st.markdown("### 📊 All Operators Overview")

    if selected_operator_id != "all":
        selected_op = customer_df[customer_df["customer_id"] == selected_operator_id].iloc[
            0
        ]
        col_quick1, col_quick2, col_quick3 = st.columns(3)
        with col_quick1:
            st.markdown(
                f"""<div class="stat-card info press-effect"><div class="stat-card-label">Satisfaction</div><div class="stat-card-value">{selected_op["satisfaction_score"]}/10</div></div>""",
                unsafe_allow_html=True,
            )
        with col_quick2:
            st.markdown(
                f"""<div class="stat-card info press-effect"><div class="stat-card-label">PSD Units</div><div class="stat-card-value" data-tip="{format_full(selected_op["psd_units"])}">{smart_format(selected_op["psd_units"])}</div></div>""",
                unsafe_allow_html=True,
            )
        with col_quick3:
            st.markdown(
                f"""<div class="stat-card info press-effect"><div class="stat-card-label">Contract Value</div><div class="stat-card-value">{format_euro(selected_op["total_contract_value_eur"])}</div></div>""",
                unsafe_allow_html=True,
            )
    else:
        col_quick1, col_quick2, col_quick3 = st.columns(3)
        total_psd = customer_df["psd_units"].sum()
        avg_satisfaction = round(customer_df["satisfaction_score"].mean(), 1)
        total_contract = customer_df["total_contract_value_eur"].sum()
        with col_quick1:
            st.markdown(
                f"""
                <div style="background:var(--bg-card);border:1px solid var(--border-color);border-radius:10px;padding:14px;text-align:center;">
                    <div style="font-size:0.65rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">Avg Satisfaction</div>
                    <div style="font-size:1.4rem;font-weight:700;color:var(--text-primary);">{avg_satisfaction}/10</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_quick2:
            st.markdown(
                f"""
                <div style="background:var(--bg-card);border:1px solid var(--border-color);border-radius:10px;padding:14px;text-align:center;">
                    <div style="font-size:0.65rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">Total PSD Units</div>
                    <div style="font-size:1.4rem;font-weight:700;color:var(--text-primary);">{total_psd:,}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_quick3:
            st.markdown(
                f"""
                <div style="background:var(--bg-card);border:1px solid var(--border-color);border-radius:10px;padding:14px;text-align:center;">
                    <div style="font-size:0.65rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">Total Contract Value</div>
                    <div style="font-size:1.4rem;font-weight:700;color:var(--text-primary);">{format_euro(total_contract)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # Get operator profile
    profile = get_operator_profile(selected_operator_id)

    if not profile:
        st.error("Operator not found.")
        st.stop()

    # ── Operator Profile Card ──
    st.markdown(
        f"""
        <div class="operator-profile-card">
            <div class="profile-header">
                <div>
                    <div class="operator-title">{profile["operator_name"]}</div>
                    <div class="operator-subtitle">{profile["operator_type"]} · Tier: {profile["tier"]} · ID: {profile["operator_id"]}</div>
                </div>
                <div class="health-badge {profile["health_status"].lower()}">
                    ~{int(profile["health_score"])}/100 · {profile["health_status"]}
                </div>
            </div>
            <div class="profile-metrics">
                <div class="profile-metric">
                    <div class="profile-metric-label">PSD Units Installed</div>
                    <div class="profile-metric-value">{profile["psd_units_total"]:,}</div>
                </div>
                <div class="profile-metric">
                    <div class="profile-metric-label">Platforms</div>
                    <div class="profile-metric-value">{profile["platforms_installed"]}</div>
                </div>
                <div class="profile-metric">
                    <div class="profile-metric-label">Trains Covered</div>
                    <div class="profile-metric-value">{profile["total_trains"]:,}</div>
                </div>
                <div class="profile-metric">
                    <div class="profile-metric-label">Contract Value</div>
                    <div class="profile-metric-value">{format_euro(profile["total_contract_value_eur"])}</div>
                </div>
                <div class="profile-metric">
                    <div class="profile-metric-label">Satisfaction</div>
                    <div class="profile-metric-value">{profile["satisfaction_score"]}/10</div>
                </div>
                <div class="profile-metric">
                    <div class="profile-metric-label">Contract End</div>
                    <div class="profile-metric-value">~{profile["days_to_renewal"]} days</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Tabbed Detail View ──
    tab_titles = [
        "📊 Overview",
        "📅 History",
        "❤️ Health",
        "💰 Financial",
        "⚡ Quick Actions",
    ]
    tabs = st.tabs(tab_titles)

    # ── OVERVIEW TAB ──
    with tabs[0]:
        # KPI Row
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(
                "Health Score",
                f"~{int(profile['health_score'])}/100",
                delta=f"{'↑' if profile['health_score'] >= 60 else '↓'} vs last quarter",
            )
        with col2:
            renewal_days = profile["days_to_renewal"]
            st.metric(
                "Days to Renewal",
                f"{renewal_days}",
                delta=f"{'⚠️ Critical' if renewal_days <= 30 else ('⚡ Soon' if renewal_days <= 90 else '✓ OK')}",
            )
        with col3:
            st.metric(
                "Active Tickets",
                profile["active_tickets"],
                delta=f"{profile['high_priority_tickets']} high-priority",
            )
        with col4:
            st.metric(
                "Engagement Score",
                f"{profile['engagement_score']}/100",
                delta=f"{profile['recent_engagements_6mo']} touchpoints in 6mo",
            )

        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown(
                '<div class="portfolio-section-header">Health Score Trend (12mo)</div>',
                unsafe_allow_html=True,
            )
            health_trend_df = get_operator_health_trend(
                selected_operator_id, months_back=12
            )
            if not health_trend_df.empty:
                fig_health = px.line(
                    health_trend_df,
                    x="Month",
                    y="Health Score",
                    markers=True,
                    line_shape="spline",
                )
                style_chart(fig_health, yaxis_range=[0, 100],
                            shapes=[
                    dict(type="line", y0=70, y1=70, x0=0, x1=1,
                         line=dict(color="var(--color-emerald)", dash="dash", width=1)),
                    dict(type="line", y0=50, y1=50, x0=0, x1=1,
                         line=dict(color="var(--color-warning)", dash="dash", width=1)),
                    dict(type="line", y0=30, y1=30, x0=0, x1=1,
                         line=dict(color="var(--color-danger)", dash="dash", width=1)),
                ])
                render_chart(fig_health, key="fig_health_L5631", use_container_width=True)
            else:
                st.info("No health trend data available.")

            st.markdown(
                '<div class="portfolio-section-header">Support Ticket Volume Trend</div>',
                unsafe_allow_html=True,
            )
            ticket_trend_df = get_support_ticket_trend(
                selected_operator_id, months_back=6
            )
            if not ticket_trend_df.empty:
                fig_tickets = px.bar(
                    ticket_trend_df,
                    x="Month",
                    y="Tickets",
                    color_discrete_sequence=["#3b82f6"],
                )
                style_chart(fig_tickets, legend=False)
                render_chart(fig_tickets, key="fig_tickets_L5650", use_container_width=True)
            else:
                st.info("No ticket trend data available.")

        with col2:
            st.markdown(
                '<div class="portfolio-section-header">Monthly Activity Summary</div>',
                unsafe_allow_html=True,
            )
            monthly_df = get_operator_monthly_stats(
                selected_operator_id, months_back=6)
            if not monthly_df.empty:
                st.dataframe(monthly_df, use_container_width=True,
                             hide_index=True)

                # Activity chart
                fig_activity = px.bar(
                    monthly_df,
                    x="Month",
                    y=["Projects Completed", "Tickets Opened", "Engagements"],
                    title="Monthly Activity",
                    barmode="group",
                )
                style_chart(fig_activity)
                render_chart(fig_activity, key="fig_activity_L5674", use_container_width=True)
            else:
                st.info("No monthly activity data.")

    # ── HISTORY TAB ──
    with tabs[1]:
        st.markdown(
            '<div class="portfolio-section-header">Project History &amp; Installations</div>',
            unsafe_allow_html=True,
        )
        history_df = get_operator_history(selected_operator_id)
        if not history_df.empty:
            # Statistics row
            total_projects = len(history_df)
            total_psd = int(history_df["psd_installed"].sum())
            avg_project_value = history_df["project_value_eur"].mean()
            completed_psd = int(
                history_df[history_df["status"] ==
                           "Completed"]["psd_installed"].sum()
            )

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Projects", total_projects)
            with col2:
                st.metric("Total PSDs", total_psd)
            with col3:
                st.metric("Avg Project Value",
                          f"€{avg_project_value / 1e3:.0f}K")
            with col4:
                st.metric(
                    "Completion Rate",
                    f"{(len(history_df[history_df['status'] == 'Completed']) / total_projects * 100):.0f}%",
                )

            # Project timeline Gantt chart
            st.markdown(
                '<div class="portfolio-section-header">Project Timeline (Gantt)</div>',
                unsafe_allow_html=True,
            )

            # Prepare Gantt data
            gantt_data = history_df.copy()
            gantt_data["start_date"] = pd.to_datetime(gantt_data["start_date"])
            gantt_data["end_date"] = pd.to_datetime(gantt_data["end_date"])

            # Color by status
            status_colors = {
                "Completed": "var(--color-emerald)",
                "In Progress": "#3b82f6",
                "Planned": "var(--color-warning)",
            }
            gantt_data["color"] = gantt_data["status"].map(status_colors)

            fig_gantt = px.timeline(
                gantt_data,
                x_start="start_date",
                x_end="end_date",
                y="project_name",
                color="status",
                color_discrete_map=status_colors,
                hover_data=["psd_installed",
                            "project_value_eur", "completion_pct"],
            )
            fig_gantt.update_yaxes(autorange="reversed")
            style_chart(fig_gantt, height=400, xaxis=dict(
                title="Timeline"), yaxis=dict(title="Projects"))
            render_chart(fig_gantt, key="fig_gantt_L5741", use_container_width=True)

            # Project status breakdown
            st.markdown(
                '<div class="portfolio-section-header">Project Status Distribution</div>',
                unsafe_allow_html=True,
            )
            col1, col2 = st.columns([1, 1])

            with col1:
                status_counts = history_df["status"].value_counts(
                ).reset_index()
                status_counts.columns = ["Status", "Count"]
                fig_status = px.bar(
                    status_counts,
                    x="Status",
                    y="Count",
                    color="Status",
                    color_discrete_map={
                        "Completed": "var(--color-emerald)",
                        "In Progress": "#3b82f6",
                        "Planned": "var(--color-warning)",
                    },
                )
                style_chart(fig_status, legend=False)
                render_chart(fig_status, key="fig_status_L5766", use_container_width=True)

            with col2:
                # PSD per project scatter
                fig_psd = px.scatter(
                    history_df,
                    x="start_date",
                    y="psd_installed",
                    size="project_value_eur",
                    color="status",
                    hover_name="project_name",
                    color_discrete_map=status_colors,
                    title="Project Scale Over Time",
                )
                style_chart(fig_psd, legend=False, hovermode="closest")
                render_chart(fig_psd, key="fig_psd_L5781", use_container_width=True)

            # Full data table
            st.markdown(
                '<div class="portfolio-section-header">Detailed Project Data</div>',
                unsafe_allow_html=True,
            )
            display_history = history_df[
                [
                    "project_name",
                    "start_date",
                    "end_date",
                    "psd_installed",
                    "project_value_eur",
                    "status",
                    "completion_pct",
                ]
            ].rename(
                columns={
                    "project_name": "Project",
                    "start_date": "Start",
                    "end_date": "End",
                    "psd_installed": "PSD Count",
                    "project_value_eur": "Value (€)",
                    "status": "Status",
                    "completion_pct": "Complete %",
                }
            )
            st.dataframe(display_history,
                         use_container_width=True, hide_index=True)
        else:
            st.info("No project history available.")

    # ── HEALTH TAB ──
    with tabs[2]:
        support_df = get_support_tickets(selected_operator_id, limit=100)
        timeline_df = get_engagement_timeline(
            selected_operator_id, months_back=12)

        # KPI row
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            open_tickets = (
                len(support_df[support_df["status"].isin(
                    ["Open", "In Progress"])])
                if not support_df.empty
                else 0
            )
            st.metric("Open Tickets", open_tickets)
        with col2:
            sla_ok = 0
            if not support_df.empty:
                avg_res = support_df[support_df["status"].isin(["Resolved", "Closed"])][
                    "resolution_time_hours"
                ].mean()
                sla_ok = len(
                    support_df[
                        (support_df["priority"].isin(["High", "Critical"]))
                        & (support_df["resolution_time_hours"] <= 4)
                    ]
                )
            st.metric("SLA Met (<4h)", sla_ok)
        with col3:
            csat_estimate = profile["satisfaction_score"]
            st.metric("Est. CSAT", f"{csat_estimate}/10")
        with col4:
            engagement_count = len(timeline_df)
            st.metric("Engagements (12mo)", engagement_count)

        if not support_df.empty:
            # Ticket trend chart
            st.markdown(
                '<div class="portfolio-section-header">Ticket Volume Trend (6mo)</div>',
                unsafe_allow_html=True,
            )
            ticket_trend = get_support_ticket_trend(
                selected_operator_id, months_back=6)
            if not ticket_trend.empty:
                fig_trend = px.area(
                    ticket_trend,
                    x="Month",
                    y="Tickets",
                    title="Monthly Ticket Volume",
                    color_discrete_sequence=["rgba(59, 130, 246, 0.3)"],
                )
                style_chart(fig_trend)
                render_chart(fig_trend, key="fig_trend_L5867", use_container_width=True)

            col1, col2 = st.columns(2)

            with col1:
                st.markdown(
                    '<div class="portfolio-section-header">Tickets by Category</div>',
                    unsafe_allow_html=True,
                )
                cat_data = support_df["category"].value_counts().reset_index()
                cat_data.columns = ["Category", "Count"]
                fig_cat = px.pie(cat_data, values="Count",
                                 names="Category", hole=0.4)
                style_pie(fig_cat)
                render_chart(fig_cat, key="fig_cat_L5881", use_container_width=True)

            with col2:
                st.markdown(
                    '<div class="portfolio-section-header">Tickets by Priority</div>',
                    unsafe_allow_html=True,
                )
                pri_data = support_df["priority"].value_counts().reset_index()
                pri_data.columns = ["Priority", "Count"]
                priority_order = {"Critical": 0,
                                  "High": 1, "Medium": 2, "Low": 3}
                pri_data["order"] = pri_data["Priority"].map(priority_order)
                pri_data = pri_data.sort_values("order").drop("order", axis=1)
                pri_colors = {
                    "Critical": "var(--color-danger)",
                    "High": "var(--color-warning)",
                    "Medium": "#3b82f6",
                    "Low": "var(--color-emerald)",
                }
                fig_pri = px.bar(
                    pri_data,
                    x="Priority",
                    y="Count",
                    color="Priority",
                    color_discrete_map=pri_colors,
                )
                style_chart(fig_pri, legend=False)
                render_chart(fig_pri, key="fig_pri_L5908", use_container_width=True)

            # Resolution time analysis
            st.markdown(
                '<div class="portfolio-section-header">Resolution Time Analysis</div>',
                unsafe_allow_html=True,
            )
            resolved_tickets = support_df[
                support_df["status"].isin(["Resolved", "Closed"])
            ].copy()
            if not resolved_tickets.empty:
                resolved_tickets["resolution_time_hours"] = pd.to_numeric(
                    resolved_tickets["resolution_time_hours"], errors="coerce"
                )
                avg_by_priority = (
                    resolved_tickets.groupby("priority")[
                        "resolution_time_hours"]
                    .mean()
                    .reset_index()
                )
                avg_by_priority.columns = ["Priority", "Avg Resolution (hrs)"]
                fig_res = px.bar(
                    avg_by_priority,
                    x="Priority",
                    y="Avg Resolution (hrs)",
                    color="Priority",
                    color_discrete_map=pri_colors,
                    title="Average Resolution Time by Priority",
                )
                style_chart(fig_res, legend=False)
                render_chart(fig_res, key="fig_res_L5938", use_container_width=True)

            # Recent tickets table
            st.markdown(
                '<div class="portfolio-section-header">Recent Tickets</div>',
                unsafe_allow_html=True,
            )
            display_support = support_df[
                [
                    "created_date",
                    "category",
                    "priority",
                    "status",
                    "summary",
                    "resolution_time_hours",
                ]
            ].rename(
                columns={
                    "created_date": "Created",
                    "category": "Category",
                    "priority": "Priority",
                    "status": "Status",
                    "summary": "Summary",
                    "resolution_time_hours": "Res. Time (h)",
                }
            )
            st.dataframe(
                display_support.head(25), use_container_width=True, hide_index=True
            )

            # Export option
            csv = support_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Export Support Tickets (CSV)",
                csv,
                file_name=f"{selected_operator_id}_support_tickets.csv",
                mime="text/csv",
            )
        else:
            st.info("No support tickets on record.")

        st.markdown(
            '<div class="portfolio-section-header">Engagement &amp; Relationship Timeline</div>',
            unsafe_allow_html=True,
        )
        timeline_df = get_engagement_timeline(
            selected_operator_id, months_back=12)
        if not timeline_df.empty:
            st.dataframe(
                timeline_df[
                    [
                        "date",
                        "type",
                        "direction",
                        "our_participants",
                        "their_participants",
                        "outcome",
                        "follow_up_date",
                    ]
                ].rename(
                    columns={
                        "date": "Date",
                        "type": "Type",
                        "direction": "Direction",
                        "our_participants": "Our Team",
                        "their_participants": "Their Team",
                        "outcome": "Outcome",
                        "follow_up_date": "Follow-up",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No engagement history found.")

    # ── FINANCIAL TAB ──
    with tabs[3]:
        st.markdown(
            '<div class="portfolio-section-header">Contract Financials</div>',
            unsafe_allow_html=True,
        )

        # Financial KPI strip
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.markdown(
                f"""
                <div class="profile-metric">
                    <div class="profile-metric-label">Contract Value</div>
                    <div class="profile-metric-value">€{profile["total_contract_value_eur"] / 1e6:.2f}M</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown(
                f"""
                <div class="profile-metric">
                    <div class="profile-metric-label">Annual Maintenance</div>
                    <div class="profile-metric-value">€{int(profile["annual_maintenance_eur"]):,}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col3:
            st.markdown(
                f"""
                <div class="profile-metric">
                    <div class="profile-metric-label">Avg Response Time</div>
                    <div class="profile-metric-value">{profile["avg_response_hours"]}h</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col4:
            total_value = profile["total_contract_value_eur"]
            remaining_months = max(0, profile["days_to_renewal"] // 30)
            if remaining_months > 0:
                remaining_value = (
                    int(profile["annual_maintenance_eur"]) / 12
                ) * remaining_months
                st.markdown(
                    f"""
                    <div class="profile-metric">
                        <div class="profile-metric-label">Remaining Value</div>
                        <div class="profile-metric-value">€{remaining_value / 1e3:.0f}K</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                    <div class="profile-metric">
                        <div class="profile-metric-label">Remaining Value</div>
                        <div class="profile-metric-value">N/A</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        with col5:
            st.markdown(
                f"""
                <div class="profile-metric">
                    <div class="profile-metric-label">Renewal Risk</div>
                    <div class="profile-metric-value">{profile.get("renewal_risk", "Unknown")}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown(
            '<div class="portfolio-section-header">Revenue Projections (12-Month)</div>',
            unsafe_allow_html=True,
        )
        projections_df = get_financial_projections(
            months_ahead=12
        )
        if not projections_df.empty:
            fig_proj = px.line(
                projections_df,
                x="Month",
                y="Revenue",
                markers=True,
                title="Projected Revenue",
            )
            style_chart(fig_proj)
            render_chart(fig_proj, key="fig_proj_L6106", use_container_width=True)
        else:
            st.info("No financial projections available.")

        st.markdown(
            '<div class="portfolio-section-header">Contract Amendments History</div>',
            unsafe_allow_html=True,
        )
        amendments_df = get_contract_amendments(
            selected_operator_id, customer_df)
        if not amendments_df.empty:
            col1, col2 = st.columns([2, 1])

            with col1:
                display_amendments = amendments_df[
                    [
                        "amendment_date",
                        "amendment_type",
                        "description",
                        "financial_impact_eur",
                        "signed_by",
                    ]
                ].rename(
                    columns={
                        "amendment_date": "Date",
                        "amendment_type": "Type",
                        "description": "Description",
                        "financial_impact_eur": "Impact (€)",
                        "signed_by": "Signed By",
                    }
                )
                st.dataframe(
                    display_amendments, use_container_width=True, hide_index=True
                )

            with col2:
                total_amendments_value = amendments_df["financial_impact_eur"].sum(
                )
                st.markdown(
                    f"""
                    <div class="profile-metric">
                        <div class="profile-metric-label">Total Amendment Value</div>
                        <div class="profile-metric-value">€{total_amendments_value:,.0f}</div>
                    </div>
                    <div class="profile-metric" style="margin-top:12px;">
                        <div class="profile-metric-label">Amendments Count</div>
                        <div class="profile-metric-value">{len(amendments_df)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Amendment value by type chart
                amend_by_type = (
                    amendments_df.groupby("amendment_type")[
                        "financial_impact_eur"]
                    .sum()
                    .reset_index()
                )
                amend_by_type.columns = ["Type", "Total Impact (€)"]
                fig_amend = px.bar(amend_by_type, x="Type",
                                   y="Total Impact (€)")
                style_chart(fig_amend, legend=False)
                render_chart(fig_amend, key="fig_amend_L6169", use_container_width=True)
        else:
            st.info("No contract amendments found.")

        # Project financial summary
        st.markdown(
            '<div class="portfolio-section-header">Project Financial Summary</div>',
            unsafe_allow_html=True,
        )
        history_df = get_operator_history(selected_operator_id)
        if not history_df.empty:
            project_summary = (
                history_df.groupby("status")
                .agg(
                    project_count=("project_id", "count"),
                    total_psd=("psd_installed", "sum"),
                    total_value=("project_value_eur", "sum"),
                    avg_value=("project_value_eur", "mean"),
                )
                .reset_index()
            )

            col1, col2 = st.columns([2, 1])
            with col1:
                fig_value = px.bar(
                    project_summary,
                    x="status",
                    y="total_value",
                    title="Contract Value by Project Status",
                    labels={
                        "total_value": "Total Value (€)", "status": "Status"},
                )
                style_chart(fig_value, legend=False)
                render_chart(fig_value, key="fig_value_L6202", use_container_width=True)

            with col2:
                st.markdown("**Summary Table**")
                display_summary = project_summary.copy()
                display_summary["total_value"] = display_summary["total_value"].apply(
                    lambda x: f"€{x / 1e3:.0f}K"
                )
                display_summary["avg_value"] = display_summary["avg_value"].apply(
                    lambda x: f"€{x / 1e3:.0f}K"
                )
                display_summary.columns = [
                    "Status",
                    "Projects",
                    "Total PSD",
                    "Total Value",
                    "Avg Value",
                ]
                st.dataframe(display_summary,
                             use_container_width=True, hide_index=True)

    # ── HEALTH TAB ── (already enhanced above) ──

    # ── QUICK ACTIONS TAB ──
    with tabs[4]:
        st.markdown(
            '<div class="portfolio-section-header">Quick Actions</div>', unsafe_allow_html=True
        )
        st.write("Common actions for managing this operator relationship:")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📧 Send Email", key="email_btn", use_container_width=True):
                st.success(
                    "Email composer would open here (integrate with your email client)"
                )
            if st.button("📅 Schedule Call", key="call_btn", use_container_width=True):
                st.success("Calendar integration would open here")
            if st.button(
                "📞 Request Callback", key="callback_btn", use_container_width=True
            ):
                st.success("Callback request noted")
            if st.button(
                "🔍 Deep Analysis", key="analysis_btn", use_container_width=True
            ):
                st.success("Comprehensive analysis report would be generated")

        with col2:
            if st.button(
                "🚩 Flag for Review", key="flag_btn", use_container_width=True
            ):
                st.warning("Operator flagged for quarterly business review")
            if st.button(
                "📊 Generate Report", key="report_btn", use_container_width=True
            ):
                # Generate comprehensive report data
                report_data = {
                    "operator_name": profile["operator_name"],
                    "tier": profile["tier"],
                    "health_score": profile["health_score"],
                    "psd_units": profile["psd_units_total"],
                    "contract_value": profile["total_contract_value_eur"],
                    "satisfaction": profile["satisfaction_score"],
                    "days_to_renewal": profile["days_to_renewal"],
                }
                report_df = pd.DataFrame([report_data])
                csv = report_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "📥 Download Operator Summary (CSV)",
                    data=csv,
                    file_name=f"{selected_operator_id}_summary.csv",
                    mime="text/csv",
                    key="download_summary",
                )
                st.success("Operator summary report ready for download")
            if st.button(
                "🔔 Set Renewal Reminder", key="reminder_btn", use_container_width=True
            ):
                st.success(f"Reminder set for {profile['contract_end']}")
            if st.button("📋 Create Task", key="task_btn", use_container_width=True):
                st.success("Task created in project management system")

        st.markdown(
            '<div class="portfolio-section-header">Notes &amp; Actions</div>', unsafe_allow_html=True
        )
        if "operator_notes" not in st.session_state:
            st.session_state.operator_notes = {}

        notes_key = f"notes_{selected_operator_id}"
        if notes_key not in st.session_state.operator_notes:
            st.session_state.operator_notes[notes_key] = ""

        notes = st.text_area(
            "Add notes about this operator",
            value=st.session_state.operator_notes[notes_key],
            height=320,
            placeholder="Enter notes here...",
            key=f"notes_area_{selected_operator_id}",
        )
        col_a, col_b = st.columns([1, 4])
        with col_a:
            if st.button("Save Note", key="save_note_btn"):
                st.session_state.operator_notes[notes_key] = notes
                st.success("Note saved to session")
        with col_b:
            if st.button("Clear", key="clear_note_btn"):
                st.session_state.operator_notes[notes_key] = ""
                st.rerun()

        # Show quick benchmark
        st.markdown(
            '<div class="portfolio-section-header">Quick Benchmark (by Tier)</div>',
            unsafe_allow_html=True,
        )
        benchmark = get_operator_comparison_benchmarks(selected_operator_id)
        if benchmark and "percentiles" in benchmark:
            pcts = benchmark["percentiles"]
            tier_stats = next((item for item in benchmark.get(
                "tier_benchmarks", []) if item.get("tier") == profile.get("tier")), {})
            st.markdown(
                f"""
                <div class="profile-metric">
                    <div class="profile-metric-label">Your PSD Count vs. {profile.get("tier", "N/A")} Tier</div>
                    <div class="profile-metric-value">{pcts.get("psd_percentile", "N/A")}th Percentile</div>
                    <div class="profile-metric-label" style="margin-top:8px;">
                        Tier Avg: {tier_stats.get("avg_psd", "N/A")} PSDs
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

elif active_tab == "kpi":
    st.markdown(
        '<div class="kpi-hero">'
        '<h1>KPI Dashboard</h1>'
        '<p>Business performance overview</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ═══════════════════════════════════════════════════════════
    # OPERATIONAL KPIs - ENHANCED
    # ═══════════════════════════════════════════════════
    ops_df = load_and_transform_data()
    stations = ops_df["station"].unique()
    total_stations = len(stations)
    total_gates = len(ops_df)

    gates_summary = (
        ops_df.groupby("station")
        .agg(
            {
                "gate_id": "count",
                "door_state": lambda x: (x == "open").sum(),
                "people": "sum",
                "sync_score": "mean",
                "risk_score": "mean",
            }
        )
        .reset_index()
    )

    total_active = gates_summary["door_state"].sum()
    total_people = ops_df["people"].sum()
    avg_sync = ops_df["sync_score"].mean()
    avg_risk = ops_df["risk_score"].mean()

    critical_count = (ops_df["maintenance_status"] == "CRITICAL").sum()
    warning_count = (
        (ops_df["maintenance_status"].isin(["WARNING", "MONITOR"])).sum()
        if ops_df["maintenance_status"].isin(["WARNING", "MONITOR"]).sum() > 0
        else 5
    )
    optimal_count = (ops_df["maintenance_status"] == "OPTIMAL").sum()

    # Additional operational metrics
    if "door_health" in ops_df.columns:
        avg_door_health = ops_df["door_health"].mean()
    else:
        avg_door_health = 95 - (ops_df["risk_score"].mean() * 0.3)

    if "service_reliability" in ops_df.columns:
        service_reliability = ops_df["service_reliability"].mean()
    else:
        service_reliability = 95

    if "energy_rating" in ops_df.columns:
        energy_dist = ops_df["energy_rating"].value_counts()
    else:
        energy_dist = {"A": 20, "B": 30, "C": 30, "D": 15, "E": 5}

    is_peak = (
        ops_df["is_peak_hour"].sum()
        if "is_peak_hour" in ops_df.columns and ops_df["is_peak_hour"].sum() > 0
        else 12
    )
    is_weekend = ops_df["is_weekend"].sum(
    ) if "is_weekend" in ops_df.columns else 2

    # Historical trends
    hist_trend = None
    try:
        hist_trend = get_historical_trends(ops_df, days_back=7)
    except Exception as e:
        import logging
        logging.warning(f"Error loading historical trends: {e}")

    # Maintenance forecast
    maint_forecast = None
    if stations.shape[0] > 0:
        try:
            maint_forecast = get_maintenance_forecast(stations[0])
        except Exception as e:
            import logging
            logging.warning(f"Error loading maintenance forecast: {e}")

    st.markdown(
        '<div class="kpi-section-header"><span class="icon">🚂</span> Operations</div>',
        unsafe_allow_html=True,
    )

    # Core metrics - simplified to 4 key cards
    st.markdown(
        f"""
        <div class="kpi-grid-4">
            <div class="glass-card section-reveal">
                <div class="glass-value" data-tip="{format_full(total_stations)}">{smart_format(total_stations)}</div>
                <div class="glass-label">Active Stations</div>
                <div class="glass-trend trend-up">Operational</div>
            </div>
            <div class="glass-card section-reveal">
                <div class="glass-value counter-animate" data-tip="{format_full(total_gates)}">{smart_format(total_gates)}</div>
                <div class="glass-label">PSD Gates</div>
                <div class="glass-trend trend-up">{total_active} Active</div>
            </div>
            <div class="glass-card section-reveal">
                <div class="glass-value counter-animate">{avg_sync:.1f}%</div>
                <div class="glass-label">Sync Efficiency</div>
                <div class="glass-trend {"trend-up" if avg_sync >= 85 else "trend-neutral"}">Target: 85%</div>
            </div>
            <div class="glass-card section-reveal">
                <div class="glass-value counter-animate" data-tip="{format_full(avg_risk)}">{avg_risk:.1f}</div>
                <div class="glass-label">Risk Score</div>
                <div class="glass-trend {"trend-up" if avg_risk < 30 else "trend-down"}">Target: &lt;30</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Energy Rating Distribution
    col_energy1, col_energy2 = st.columns(2)
    with col_energy1:
        if energy_dist is not None and len(energy_dist) > 0:
            energy_df = pd.DataFrame(
                list(energy_dist.items()), columns=["Rating", "Count"]
            )
            fig_energy = px.bar(
                energy_df,
                x="Rating",
                y="Count",
                title="Energy Efficiency Distribution",
                color="Rating",
                color_discrete_map={
                    "A": "#00ff88",
                    "B": "#00c0ff",
                    "C": "#ffd700",
                    "D": "#ed8936",
                    "E": "#f56565",
                },
            )
            fig_energy.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="var(--text-muted)"),
                title=dict(font=dict(size=14, color="#00c0ff")),
                margin=dict(l=20, r=20, t=40, b=30),
                height=320,
            )
            render_chart(fig_energy, key="fig_energy_L6483", use_container_width=True)

    with col_energy2:
        if hist_trend is not None and not hist_trend.empty:
            cols_to_plot = [
                c
                for c in hist_trend.columns
                if c != "date" and hist_trend[c].dtype in ["int64", "float64"]
            ][:3]
            if cols_to_plot:
                fig_hist = px.line(
                    hist_trend,
                    x="date",
                    y=cols_to_plot,
                    title="7-Day Historical Trend",
                    color_discrete_sequence=["#00c0ff", "#00ff88", "#ffd700"],
                )
                fig_hist.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="var(--text-muted)"),
                    title=dict(font=dict(size=14, color="#00c0ff")),
                    margin=dict(l=20, r=20, t=40, b=20),
                    height=320,
                )
                render_chart(fig_hist, key="fig_hist_L6509", use_container_width=True)
            else:
                st.markdown(
                    """
                    <div class="glass-card" style="height: 250px; display: flex; flex-direction: column; justify-content: center; align-items: center;">
                        <div class="glass-value counter-animate" style="background: linear-gradient(90deg, var(--text-muted), var(--text-muted)); -webkit-background-clip: text;">📈</div>
                        <div class="glass-label">Historical Trend</div>
                        <div class="glass-trend trend-neutral">◆ Data Compiling</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                """
                <div class="glass-card" style="height: 250px; display: flex; flex-direction: column; justify-content: center; align-items: center;">
                    <div class="glass-value counter-animate" style="background: linear-gradient(90deg, var(--text-muted), var(--text-muted)); -webkit-background-clip: text;">📈</div>
                    <div class="glass-label">Historical Trend</div>
                    <div class="glass-trend trend-neutral">◆ Coming Soon</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Maintenance Forecast Heatmap
    if maint_forecast is not None and not maint_forecast.empty:
        col_maint1, col_maint2 = st.columns(2)
        with col_maint1:
            fig_forecast = px.line(
                maint_forecast,
                x="Date",
                y="Predicted Risk %",
                title="7-Day Maintenance Risk Forecast",
                color_discrete_sequence=["#ffd700"],
            )
            fig_forecast.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="var(--text-muted)"),
                title=dict(font=dict(size=14, color="#ffd700")),
                margin=dict(l=20, r=20, t=40, b=20),
                height=320,
            )
            fig_forecast.update_traces(fill="tozeroy", line=dict(width=3))
            render_chart(fig_forecast, key="fig_forecast_L6554", use_container_width=True)
        with col_maint2:
            if "Predicted Risk %" in maint_forecast.columns:
                avg_forecast_risk = maint_forecast["Predicted Risk %"].mean()
                st.markdown(
                    f"""
                    <div class="glass-card" style="height: 250px; display: flex; flex-direction: column; justify-content: center; align-items: center;">
                        <div class="glass-value glass-value-lg counter-animate">{avg_forecast_risk:.1f}%</div>
                        <div class="glass-label">Avg Predicted Risk</div>
                        <div class="glass-trend {"trend-up" if avg_forecast_risk < 30 else "trend-down"}">◆ 7-Day Outlook</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # Station Performance Treemap
    if not gates_summary.empty:
        fig_treemap = px.treemap(
            gates_summary,
            path=["station"],
            values="gate_id",
            title="Station Performance Hierarchy",
            color="sync_score",
            color_continuous_scale=["#f56565", "#ffd700", "#00ff88"],
        )
        fig_treemap.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#ffffff"),
            title=dict(font=dict(size=14, color="#00c0ff")),
            margin=dict(l=0, r=0, t=40, b=0),
            height=320,
        )
        render_chart(fig_treemap, key="fig_treemap_L6587", use_container_width=True)

    # Key Performance Gauges
    st.markdown(
        '<div class="kpi-sub-header">Performance Indicators</div>',
        unsafe_allow_html=True,
    )
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        fig_gauge_sync = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=avg_sync,
                title={"text": "Sync Efficiency", "font": {"size": 14}},
                gauge={
                    "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#00c0ff"},
                    "bar": {"color": "#00c0ff"},
                    "bgcolor": "rgba(0,0,0,0.3)",
                    "borderwidth": 0,
                    "steps": [
                        {"range": [0, 70], "color": "rgba(245,101,101,0.15)"},
                        {"range": [70, 85], "color": "rgba(255,215,0,0.15)"},
                        {"range": [85, 100], "color": "rgba(0,255,136,0.15)"},
                    ],
                    "threshold": {
                        "line": {"color": "#00ff88", "width": 3},
                        "thickness": 0.75,
                        "value": 85,
                    },
                },
            )
        )
        fig_gauge_sync.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="var(--text-muted)", size=12),
            height=320,
            margin=dict(l=30, r=30, t=40, b=30),
        )
        render_chart(fig_gauge_sync, key="fig_gauge_sync_L6626", use_container_width=True)

    with col_g2:
        fig_gauge_risk = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=avg_risk,
                title={"text": "Risk Score", "font": {"size": 14}},
                gauge={
                    "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#f56565"},
                    "bar": {"color": "#f56565"},
                    "bgcolor": "rgba(0,0,0,0.3)",
                    "borderwidth": 0,
                    "steps": [
                        {"range": [0, 30], "color": "rgba(0,255,136,0.15)"},
                        {"range": [30, 50], "color": "rgba(255,215,0,0.15)"},
                        {"range": [50, 100],
                            "color": "rgba(245,101,101,0.15)"},
                    ],
                    "threshold": {
                        "line": {"color": "#f56565", "width": 3},
                        "thickness": 0.75,
                        "value": 30,
                    },
                },
            )
        )
        fig_gauge_risk.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="var(--text-muted)", size=12),
            height=320,
            margin=dict(l=30, r=30, t=40, b=30),
        )
        render_chart(fig_gauge_risk, key="fig_gauge_risk_L6660", use_container_width=True)

    # Distribution Charts
    st.markdown(
        '<div class="kpi-sub-header">Distribution</div>', unsafe_allow_html=True
    )
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        door_counts = ops_df["door_state"].value_counts().reset_index()
        door_counts.columns = ["State", "Count"]
        door_colors = {"open": "#00ff88", "closed": "#f56565"}
        fig_door = px.pie(
            door_counts,
            values="Count",
            names="State",
            title="Door State",
            color="State",
            color_discrete_map=door_colors,
            hole=0.55,
        )
        fig_door.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="var(--text-muted)"),
            title=dict(font=dict(size=13, color="#00c0ff")),
            height=320,
            margin=dict(l=10, r=10, t=30, b=10),
        )
        render_chart(fig_door, key="fig_door_L6688", use_container_width=True)

    with col_d2:
        maint_counts = ops_df["maintenance_status"].value_counts(
        ).reset_index()
        maint_counts.columns = ["Status", "Count"]
        fig_maint_bar = px.bar(
            maint_counts,
            y="Status",
            x="Count",
            orientation="h",
            title="Maintenance",
            color="Status",
            color_discrete_sequence=["#00ff88",
                                     "#00c0ff", "#ffd700", "#f56565"],
        )
        fig_maint_bar.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="var(--text-muted)"),
            title=dict(font=dict(size=13, color="#00c0ff")),
            height=320,
            yaxis=dict(categoryorder="total ascending"),
        )
        render_chart(fig_maint_bar, key="fig_maint_bar_L6713", use_container_width=True)

    # ═══════════════════════════════════════════════════
    # FINANCIAL KPIs - ENHANCED
    # ═══════════════════════════════════════════════════
    mrr = arr = cac = ltv = ltv_cac_ratio = gross_margin = payback_period = (
        churn_rate
    ) = growth_rate = 0
    net_revenue = burn_rate = runway = revenue_per_cust = expansion_rev = 0
    total_customers = 0
    df_fin = None

    try:
        df_base, df_churn = get_financial_model_data(
            months=24,
            starting_customers=100,
            monthly_growth_rate=0.13,
            churn_rate=0.05,
            price_per_customer=100,
            fixed_costs=5000,
            variable_cost_per_customer=10,
            cac_simplified=150,
        )
        df_fin = df_base
        final = df_fin.iloc[-1]
        mrr = final["MRR"]
        arr = final["ARR"]
        cac = 150
        ltv = 1800
        ltv_cac_ratio = ltv / cac
        gross_margin = 90.4
        churn_rate = 4.2
        growth_rate = 0.0
        payback_period = 12
        total_customers = int(final["Total_Customers"])

        # New enhanced metrics
        net_revenue = mrr - (mrr * (1 - gross_margin / 100))
        burn_rate = 15000
        runway = 122
        revenue_per_cust = mrr / total_customers if total_customers > 0 else 0
        expansion_rev = mrr * 0.15
    except Exception as e:
        pass

    st.markdown(
        '<div class="kpi-section-header"><span class="icon">💰</span> Financial</div>',
        unsafe_allow_html=True,
    )

    if df_fin is not None:
        # Revenue metrics
        st.markdown(
            f"""
            <div class="kpi-grid-4">
                <div class="glass-card section-reveal">
                    <div class="glass-value counter-animate" data-tip="{format_full(mrr)}">${smart_format(mrr)}</div>
                    <div class="glass-label">Monthly Revenue</div>
                    <div class="glass-trend trend-up">↑ {growth_rate:.1f}% MoM</div>
                </div>
                <div class="glass-card section-reveal">
                    <div class="glass-value counter-animate" data-tip="{format_full(arr)}">${smart_format(arr)}</div>
                    <div class="glass-label">Annual Revenue</div>
                    <div class="glass-trend {"trend-up" if arr >= 600000 else "trend-neutral"}">Target: $2M</div>
                </div>
                <div class="glass-card section-reveal">
                    <div class="glass-value counter-animate" data-tip="{format_full(expansion_rev)}">${smart_format(expansion_rev)}</div>
                    <div class="glass-label">Expansion Revenue</div>
                    <div class="glass-trend trend-up">◆ Upsells</div>
                </div>
                <div class="glass-card section-reveal">
                    <div class="glass-value counter-animate" data-tip="{format_full(revenue_per_cust)}">${smart_format(revenue_per_cust)}</div>
                    <div class="glass-label">Revenue/Customer</div>
                    <div class="glass-trend trend-up">◆ ARPU</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Profitability metrics
        st.markdown(
            f"""
            <div class="kpi-grid-4">
                <div class="glass-card section-reveal">
                    <div class="glass-value counter-animate" data-tip="{format_full(ltv)}">${smart_format(ltv)}</div>
                    <div class="glass-label">Customer LTV</div>
                    <div class="glass-trend trend-up">LTV:CAC {ltv_cac_ratio:.1f}x</div>
                </div>
                <div class="glass-card section-reveal">
                    <div class="glass-value counter-animate" style="background: linear-gradient(90deg, #ffd700, #ffaa00); -webkit-background-clip: text;">{gross_margin:.1f}%</div>
                    <div class="glass-label">Gross Margin</div>
                    <div class="glass-trend {"trend-up" if gross_margin >= 70 else "trend-neutral"}">Target: &gt;70%</div>
                </div>
                <div class="glass-card section-reveal">
                    <div class="glass-value counter-animate" data-tip="{format_full(net_revenue)}">${smart_format(net_revenue)}</div>
                    <div class="glass-label">Net Revenue</div>
                    <div class="glass-trend trend-up">◆ After Costs</div>
                </div>
                <div class="glass-card section-reveal">
                    <div class="glass-value counter-animate" data-tip="{format_full(burn_rate)}">${smart_format(burn_rate)}</div>
                    <div class="glass-label">Monthly Burn</div>
                    <div class="glass-trend trend-neutral">◆ OPERATING</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Growth & Efficiency
        st.markdown(
            f"""
            <div class="kpi-grid-4">
                <div class="glass-card section-reveal">
                    <div class="glass-value counter-animate" data-tip="{format_full(cac)}">${smart_format(cac)}</div>
                    <div class="glass-label">CAC</div>
                    <div class="glass-trend trend-up">Payback: {payback_period:.0f}mo</div>
                </div>
                <div class="glass-card section-reveal">
                    <div class="glass-value counter-animate" data-tip="{format_full(payback_period)}">{payback_period:.0f}</div>
                    <div class="glass-label">CAC Payback</div>
                    <div class="glass-trend {"trend-up" if payback_period <= 12 else "trend-neutral"}">Target: &lt;12mo</div>
                </div>
                <div class="glass-card section-reveal">
                    <div class="glass-value counter-animate" data-tip="{format_full(runway)}">{runway:.0f}</div>
                    <div class="glass-label">Runway (Months)</div>
                    <div class="glass-trend {"trend-up" if runway >= 18 else "trend-neutral"}">◆ Cash Reserve</div>
                </div>
                <div class="glass-card section-reveal">
                    <div class="glass-value counter-animate" style="background: linear-gradient(90deg, #f56565, #ed8936); -webkit-background-clip: text;">{churn_rate:.1f}%</div>
                    <div class="glass-label">Churn Rate</div>
                    <div class="glass-trend {"trend-down" if churn_rate > 5 else "trend-up"}">Target: &lt;5%</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Key Financial Charts
        st.markdown('<div class="kpi-sub-header">Trends</div>',
                    unsafe_allow_html=True)
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            fig_mrr = px.area(
                df_fin,
                x="Month",
                y="MRR",
                title="Revenue (MRR)",
                color_discrete_sequence=["var(--color-secondary-light)"],
            )
            fig_mrr.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="var(--text-muted)"),
                title=dict(font=dict(size=13, color="#00c0ff")),
                margin=dict(l=20, r=20, t=30, b=20),
                height=300,
            )
            fig_mrr.update_traces(line=dict(width=2))
            render_chart(fig_mrr, key="fig_mrr_L6873", use_container_width=True)

        with col_f2:
            fig_cust = px.line(
                df_fin,
                x="Month",
                y="Total_Customers",
                title="Customers",
                color_discrete_sequence=["var(--color-emerald)"],
            )
            fig_cust.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="var(--text-muted)"),
                title=dict(font=dict(size=13, color="#00ff88")),
                margin=dict(l=20, r=20, t=30, b=20),
                height=300,
            )
            fig_cust.update_traces(line=dict(width=2))
            render_chart(fig_cust, key="fig_cust_L6893", use_container_width=True)

        # Additional Financial Charts
        col_wf1, col_wf2 = st.columns(2)
        with col_wf1:
            waterfall_data = pd.DataFrame(
                {
                    "Stage": [
                        "Gross Revenue",
                        "COGS",
                        "Gross Profit",
                        "OpEx",
                        "Net Income",
                    ],
                    "Value": [
                        mrr,
                        mrr * 0.096,
                        net_revenue,
                        burn_rate,
                        max(0, net_revenue - burn_rate),
                    ],
                    "Type": ["total", "decrease", "total", "decrease", "total"],
                }
            )
            fig_waterfall = go.Figure(
                go.Waterfall(
                    name="Financial Flow",
                    orientation="v",
                    x=waterfall_data["Stage"],
                    y=waterfall_data["Value"],
                    measure=waterfall_data["Type"],
                    connector={"line": {"color": "rgb(63, 63, 63)"}},
                    increasing={"marker": {"color": "#00ff88"}},
                    decreasing={"marker": {"color": "#f56565"}},
                    totals={"marker": {"color": "#00c0ff"}},
                )
            )
            fig_waterfall.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="var(--text-muted)"),
                title=dict(
                    text="Revenue Waterfall", font=dict(size=13, color="#00c0ff")
                ),
                height=300,
                showlegend=False,
                margin=dict(l=10, r=10, t=30, b=10),
            )
            render_chart(fig_waterfall, key="fig_waterfall_L6941", use_container_width=True)

        with col_wf2:
            revenue_mix = pd.DataFrame(
                {
                    "Source": ["Base MRR", "Expansion", "New Business", "Upsell"],
                    "Value": [mrr * 0.7, expansion_rev, mrr * 0.1, mrr * 0.05],
                }
            )
            fig_mix = px.bar(
                revenue_mix,
                x="Source",
                y="Value",
                title="Revenue Mix",
                color="Source",
                color_discrete_sequence=["#00c0ff",
                                         "#00ff88", "#ffd700", "#8b5cf6"],
            )
            fig_mix.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="var(--text-muted)"),
                title=dict(font=dict(size=13, color="#00c0ff")),
                height=300,
            )
            render_chart(fig_mix, key="fig_mix_L6967", use_container_width=True)
    else:
        st.info("Financial data loading...")

    # ═══════════════════════════════════════════════════
    # CUSTOMER KPIs - ENHANCED
    # ═══════════════════════════════════════════
    customer_df = None
    rfm_data = None
    total_customers = at_risk_count = renewal_value = avg_health = 0
    nps_score = avg_ticket_res = contract_renewal_rate = premium_cust = new_cust = 0
    seg_counts = {}

    try:
        customer_df = get_customer_data()
        total_customers = len(customer_df)

        rfm_data = get_rfm_analysis(customer_df)
        at_risk = get_at_risk_accounts(customer_df)
        renewals = get_renewal_forecast(customer_df)
        renewal_summary = get_renewal_health_summary(customer_df)
        contract_health = get_contract_health_score(customer_df)

        seg_col = "rfm_segment" if "rfm_segment" in rfm_data.columns else "segment"
        seg_counts = (
            rfm_data[seg_col].value_counts().to_dict()
            if seg_col in rfm_data.columns
            else {}
        )

        if seg_counts and "At Risk" in seg_counts:
            at_risk_count = int(seg_counts["At Risk"])
        elif "risk_level" in at_risk.columns:
            at_risk_count = len(
                at_risk[at_risk["risk_level"].isin(
                    ["High Risk", "Medium Risk"])]
            )
        else:
            at_risk_count = 0

        renewals_180d = (
            renewals[renewals["days_to_renewal"] <= 180]
            if "days_to_renewal" in renewals.columns
            else renewals
        )
        renewal_value = (
            int(renewals_180d["total_contract_value_eur"].sum())
            if "total_contract_value_eur" in renewals_180d.columns
            else int(renewals["total_contract_value_eur"].sum())
            if "total_contract_value_eur" in renewals.columns
            else 1850000
        )

        if isinstance(renewal_summary, dict):
            avg_health = renewal_summary.get("avg_health_score", 84)
            contract_renewal_rate = renewal_summary.get("healthy_pct", 91)
        else:
            avg_health = 82
            contract_renewal_rate = 91

        nps_score = (
            int(customer_df["satisfaction_score"].mean() * 10)
            if "satisfaction_score" in customer_df.columns
            else 71
        )
        avg_ticket_res = (
            customer_df["avg_response_hours"].mean()
            if "avg_response_hours" in customer_df.columns
            else 3.2
        )

        at_risk_display = (
            min(4, at_risk_count + 2) if at_risk_count < 5 else at_risk_count
        )
        premium_cust = (
            len(customer_df[customer_df["tier"].isin(["Platinum", "Gold"])])
            if "tier" in customer_df.columns
            else 8
        )
        new_cust = (
            len(customer_df[customer_df["tier"] == "Silver"])
            if "tier" in customer_df.columns
            else 4
        )

    except Exception as e:
        import logging

        logging.warning(f"KPI Customer data error: {e}")
        total_customers = at_risk_count = renewal_value = avg_health = 0
        nps_score = avg_ticket_res = contract_renewal_rate = premium_cust = new_cust = 0

    st.markdown(
        '<div class="kpi-section-header"><span class="icon">👥</span> Customer</div>',
        unsafe_allow_html=True,
    )

    # Customer Core
    st.markdown(
        f"""
        <div class="kpi-grid-4">
            <div class="glass-card section-reveal">
                <div class="glass-value counter-animate" data-tip="{format_full(total_customers)}">{total_customers}</div>
                <div class="glass-label">Total Customers</div>
                <div class="glass-trend trend-up">◆ Active</div>
            </div>
            <div class="glass-card section-reveal">
                <div class="glass-value counter-animate" style="background: linear-gradient(90deg, #f56565, #ed8936); -webkit-background-clip: text;">{at_risk_count}</div>
                <div class="glass-label">At-Risk</div>
                <div class="glass-trend {"trend-down" if at_risk_count > 3 else "trend-up"}">{"Needs Attention" if at_risk_count > 3 else "Healthy"}</div>
            </div>
            <div class="glass-card section-reveal">
                <div class="glass-value counter-animate" data-tip="{format_full(renewal_value)}">${renewal_value:,.0f}</div>
                <div class="glass-label">Renewal Value</div>
                <div class="glass-trend trend-up">Next 180 Days</div>
            </div>
            <div class="glass-card section-reveal">
                <div class="glass-value counter-animate" style="background: linear-gradient(90deg, #00c0ff, #00ff88); -webkit-background-clip: text;">{avg_health:.0f}</div>
                <div class="glass-label">Health Score</div>
                <div class="glass-trend {"trend-up" if avg_health >= 80 else "trend-neutral"}">Target: &gt;80</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Customer Engagement
    st.markdown(
        f"""
        <div class="kpi-grid-4">
            <div class="glass-card section-reveal">
                <div class="glass-value counter-animate" data-tip="{format_full(nps_score)}">{nps_score}</div>
                <div class="glass-label">NPS Score</div>
                <div class="glass-trend {"trend-up" if nps_score >= 50 else "trend-neutral"}">◆ Industry: 41</div>
            </div>
            <div class="glass-card section-reveal">
                <div class="glass-value counter-animate">{avg_ticket_res:.1f}h</div>
                <div class="glass-label">Avg Ticket Res.</div>
                <div class="glass-trend {"trend_up" if avg_ticket_res <= 4 else "trend-neutral"}">Target: &lt;4h</div>
            </div>
            <div class="glass-card section-reveal">
                <div class="glass-value counter-animate">{contract_renewal_rate:.0f}%</div>
                <div class="glass-label">Renewal Rate</div>
                <div class="glass-trend trend-up">◆ Contract Health</div>
            </div>
            <div class="glass-card section-reveal">
                <div class="glass-value counter-animate" data-tip="{format_full(premium_cust)}">{premium_cust}</div>
                <div class="glass-label">Premium Customers</div>
                <div class="glass-trend trend-up">◆ High Value</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Customer Segmentation
    st.markdown(
        f"""
        <div class="kpi-grid-4">
            <div class="glass-card section-reveal">
                <div class="glass-value counter-animate" style="background: linear-gradient(90deg, #00ff88, #00c0ff); -webkit-background-clip: text;">{seg_counts.get("Strategic Partners", 8)}</div>
                <div class="glass-label">Strategic Partners</div>
                <div class="glass-trend trend-up">◆ Top Tier</div>
            </div>
            <div class="glass-card section-reveal">
                <div class="glass-value counter-animate" data-tip="{format_full(seg_counts.get("Key Accounts", seg_counts.get("Potential", 15)))}">{seg_counts.get("Key Accounts", seg_counts.get("Potential", 15))}</div>
                <div class="glass-label">Key Accounts</div>
                <div class="glass-trend trend-up">Growth Ready</div>
            </div>
            <div class="glass-card section-reveal">
                <div class="glass-value counter-animate" data-tip="{format_full(seg_counts.get("Growth Potential", seg_counts.get("Loyal", 20)))}">{seg_counts.get("Growth Potential", seg_counts.get("Loyal", 20))}</div>
                <div class="glass-label">Growth Potential</div>
                <div class="glass-trend trend-up">Stable Base</div>
            </div>
            <div class="glass-card section-reveal">
                <div class="glass-value counter-animate" data-tip="{format_full(seg_counts.get("At Risk", seg_counts.get("Churned", 5)))}">{seg_counts.get("At Risk", seg_counts.get("Churned", 5))}</div>
                <div class="glass-label">At Risk</div>
                <div class="glass-trend trend-down">Need Win-back</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Customer Charts
    if customer_df is not None and rfm_data is not None:
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            if "segment" in rfm_data.columns:
                seg_df = rfm_data["segment"].value_counts().reset_index()
                seg_df.columns = ["Segment", "Count"]
                colors_map = {
                    "Strategic Partners": "#00ff88",
                    "Key Accounts": "#00c0ff",
                    "Growth Potential": "#ffd700",
                    "At Risk": "#f56565",
                    "Dormant": "#888888",
                }
                fig_seg = px.pie(
                    seg_df,
                    values="Count",
                    names="Segment",
                    title="Customer Segmentation",
                    color="Segment",
                    color_discrete_map=colors_map,
                )
                fig_seg.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="var(--text-muted)"),
                    title=dict(font=dict(size=13, color="#00c0ff")),
                    margin=dict(l=10, r=10, t=30, b=10),
                    height=320,
                )
                render_chart(fig_seg, key="fig_seg_L7181", use_container_width=True)

        with col_c2:
            if "segment" in rfm_data.columns and "recency" in rfm_data.columns:
                fig_rfm = px.scatter(
                    rfm_data,
                    x="recency",
                    y="monetary_score",
                    size="frequency",
                    color="segment",
                    title="RFM Analysis",
                    color_discrete_map=colors_map,
                    size_max=30,
                )
                fig_rfm.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="var(--text-muted)"),
                    title=dict(font=dict(size=13, color="#00c0ff")),
                    margin=dict(l=10, r=10, t=30, b=10),
                    height=320,
                )
                render_chart(fig_rfm, key="fig_rfm_L7204", use_container_width=True)

    # Customer Funnel
    st.markdown(
        '<div class="kpi-sub-header">Acquisition Funnel</div>', unsafe_allow_html=True
    )
    funnel_stages = pd.DataFrame(
        {
            "Stage": ["Leads", "Qualified", "Proposals", "Closed Won", "Active"],
            "Count": [200, 150, 80, 50, total_customers if total_customers > 0 else 50],
        }
    )
    fig_cust_funnel = px.funnel(
        funnel_stages,
        x="Count",
        y="Stage",
        title="Funnel",
        color_discrete_sequence=["#00c0ff", "#00ff88",
                                 "#ffd700", "#f56565", "#8b5cf6"],
    )
    fig_cust_funnel.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="var(--text-muted)"),
        title=dict(font=dict(size=13, color="#00c0ff")),
        margin=dict(l=10, r=10, t=30, b=10),
        height=300,
    )
    render_chart(fig_cust_funnel, key="fig_cust_funnel_L7232", use_container_width=True)

    # Satisfaction and Renewals
    st.markdown(
        '<div class="kpi-sub-header">Satisfaction & Renewals</div>',
        unsafe_allow_html=True,
    )
    col_sat1, col_sat2 = st.columns(2)
    with col_sat1:
        satisfaction_dist = pd.DataFrame(
            {
                "Rating": ["Very Satisfied", "Satisfied", "Neutral", "Dissatisfied"],
                "Count": [45, 30, 15, 10],
            }
        )
        fig_sat = px.bar(
            satisfaction_dist,
            x="Rating",
            y="Count",
            title="Satisfaction",
            color="Rating",
            color_discrete_sequence=["#00ff88",
                                     "#00c0ff", "#ffd700", "#f56565"],
        )
        fig_sat.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="var(--text-muted)"),
            title=dict(font=dict(size=13, color="#00c0ff")),
            height=300,
        )
        render_chart(fig_sat, key="fig_sat_L7264", use_container_width=True)

    with col_sat2:
        renewal_calendar = pd.DataFrame(
            {
                "Month": [
                    "Jan",
                    "Feb",
                    "Mar",
                    "Apr",
                    "May",
                    "Jun",
                    "Jul",
                    "Aug",
                    "Sep",
                    "Oct",
                    "Nov",
                    "Dec",
                ],
                "Renewals": [8, 12, 6, 15, 10, 18, 14, 9, 11, 16, 13, 20],
            }
        )
        fig_renewal_cal = px.bar(
            renewal_calendar,
            x="Month",
            y="Renewals",
            title="Renewals",
            color="Renewals",
            color_continuous_scale=["#ffd700", "#00ff88"],
        )
        fig_renewal_cal.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="var(--text-muted)"),
            title=dict(font=dict(size=13, color="#00c0ff")),
            height=300,
        )
        render_chart(fig_renewal_cal, key="fig_renewal_cal_L7302", use_container_width=True)

    # Executive Scorecard
    overall_score = (
        avg_sync + avg_door_health + (nps_score / 10) + contract_renewal_rate
    ) / 4

    # Hero Score Cards
    col_h1, col_h2, col_h3 = st.columns(3)
    with col_h1:
        st.markdown(
            f"""
            <div class="hero-card">
                <div class="glass-value glass-value-lg counter-animate" data-tip="{format_full(overall_score)}">{overall_score:.0f}</div>
                <div class="glass-label">Overall Score</div>
                <div class="glass-trend {"trend-up" if overall_score >= 75 else "trend-neutral"}">Business Health</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_h2:
        st.markdown(
            f"""
            <div class="hero-card">
                <div class="glass-value glass-value-lg counter-animate" style="background: linear-gradient(90deg, #00ff88, #00c0ff); -webkit-background-clip: text;">{smart_format(total_stations)}</div>
                <div class="glass-label">Active Stations</div>
                <div class="glass-trend trend-up">Network Coverage</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_h3:
        st.markdown(
            f"""
            <div class="hero-card">
                <div class="glass-value glass-value-lg counter-animate" style="background: linear-gradient(90deg, #ffd700, #ffaa00); -webkit-background-clip: text;">${smart_format(arr)}</div>
                <div class="glass-label">Annual Revenue</div>
                <div class="glass-trend {"trend-up" if arr >= 600000 else "trend-neutral"}">ARR Target</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Summary Table
    st.markdown(
        '<div class="kpi-section-header"><span class="icon">📋</span> Summary</div>',
        unsafe_allow_html=True,
    )

    kpi_summary = pd.DataFrame(
        {
            "Category": [
                "Operations",
                "Operations",
                "Operations",
                "Operations",
                "Operations",
                "Operations",
                "Financial",
                "Financial",
                "Financial",
                "Financial",
                "Financial",
                "Financial",
                "Customer",
                "Customer",
                "Customer",
                "Customer",
                "Customer",
                "Customer",
            ],
            "KPI": [
                "Total Stations",
                "Total PSD Gates",
                "Sync Efficiency",
                "Risk Score",
                "Door Health",
                "Service Reliability",
                "MRR",
                "ARR",
                "LTV",
                "LTV:CAC Ratio",
                "Gross Margin",
                "Churn Rate",
                "Total Customers",
                "At-Risk",
                "Renewal Value",
                "Health Score",
                "NPS Score",
                "Contract Renewal",
            ],
            "Current Value": [
                str(total_stations),
                str(total_gates),
                f"{avg_sync:.1f}%",
                f"{avg_risk:.1f}",
                f"{avg_door_health:.0f}%",
                f"{service_reliability:.0f}%",
                f"${smart_format(mrr)}",
                f"${smart_format(arr)}",
                f"${smart_format(ltv)}",
                f"{ltv_cac_ratio:.1f}x",
                f"{gross_margin:.1f}%",
                f"{churn_rate:.1f}%",
                str(total_customers),
                str(at_risk_count),
                f"${renewal_value:,.0f}",
                f"{avg_health:.1f}",
                str(nps_score),
                f"{contract_renewal_rate:.0f}%",
            ],
            "Target": [
                "N/A",
                "N/A",
                ">85%",
                "<30",
                ">90%",
                ">95%",
                ">$50K",
                ">$600K",
                ">$5K",
                ">3x",
                ">70%",
                "<5%",
                "N/A",
                "<5",
                "100%",
                ">80",
                ">50",
                ">90%",
            ],
            "Status": [
                "✅ Active" if total_stations > 0 else "N/A",
                "✅ Active" if total_gates > 0 else "N/A",
                "✅ Good"
                if avg_sync >= 85
                else "⚠️ Monitor"
                if avg_sync >= 70
                else "❌ Warning",
                "✅ Good"
                if avg_risk < 30
                else "⚠️ Monitor"
                if avg_risk < 50
                else "❌ Critical",
                "✅ Good"
                if avg_door_health >= 90
                else "⚠️ Monitor"
                if avg_door_health >= 75
                else "❌ Warning",
                "✅ Good"
                if service_reliability >= 95
                else "⚠️ Monitor"
                if service_reliability >= 90
                else "❌ Warning",
                "✅ Good"
                if mrr > 50000
                else "⚠️ Building"
                if mrr > 20000
                else "❌ Below",
                "✅ Good"
                if arr > 600000
                else "⚠️ Building"
                if arr > 240000
                else "❌ Below",
                "✅ Good" if ltv > 3000 else "⚠️ Building" if ltv > 1500 else "❌ Below",
                "✅ Good"
                if ltv_cac_ratio >= 3
                else "⚠️ Monitor"
                if ltv_cac_ratio >= 2
                else "❌ Warning",
                "✅ Good"
                if gross_margin >= 70
                else "⚠️ Building"
                if gross_margin >= 50
                else "❌ Warning",
                "✅ Good"
                if churn_rate < 5
                else "⚠️ Monitor"
                if churn_rate < 10
                else "❌ High",
                "✅ Active" if total_customers > 0 else "N/A",
                "✅ Healthy"
                if at_risk_count < 3
                else "⚠️ Monitor"
                if at_risk_count < 5
                else "❌ Critical",
                "✅ Good" if renewal_value > 0 else "⚠️ No Data",
                "✅ Good"
                if avg_health >= 80
                else "⚠️ Monitor"
                if avg_health >= 60
                else "❌ Warning",
                "✅ Good"
                if nps_score >= 50
                else "⚠️ Monitor"
                if nps_score >= 30
                else "❌ Low",
                "✅ Good"
                if contract_renewal_rate >= 90
                else "⚠️ Monitor"
                if contract_renewal_rate >= 75
                else "❌ Warning",
            ],
        }
    )

    def highlight_status(val):
        if "✅" in str(val):
            return "color: #00ff88; font-weight: bold;"
        elif "⚠️" in str(val):
            return "color: #ffd700; font-weight: bold;"
        elif "❌" in str(val):
            return "color: #f56565; font-weight: bold;"
        return ""

    st.dataframe(kpi_summary, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════
# BUDGET & ROI TAB
# ═══════════════════════════════════════════════════════════════════
elif active_tab == "budget":
    st.markdown('<div class="budget-hero"><h1>Budget &amp; ROI</h1><p>Multi-year financial performance and investment analysis</p></div>', unsafe_allow_html=True)

    overview = get_budget_overview()
    budget_df = generate_budget_data()
    roi_df = generate_roi_data()

    tab_overview, tab_past, tab_present, tab_future, tab_optim = st.tabs([
        "📊 Overview", "📅 Past (2022-2024)", "🔄 Present (2025)", "🔮 Future (2026-2030)", "💡 Optimization"
    ])

    # ── Overview Tab ──
    with tab_overview:
        st.markdown(f"""
        <div class="kpi-grid-4">
            <div class="glass-card section-reveal">
                <div class="glass-value counter-animate" style="font-size:1.6rem;">€{overview['total_capex']:,.0f}</div>
                <div class="glass-label">Total CapEx</div>
                <div class="glass-trend trend-up">All stations · 2022-2030</div>
            </div>
            <div class="glass-card section-reveal">
                <div class="glass-value counter-animate">{overview['avg_roi']}%</div>
                <div class="glass-label">Avg ROI</div>
                <div class="glass-trend trend-up">Across portfolio</div>
            </div>
            <div class="glass-card section-reveal">
                <div class="glass-value counter-animate">{overview['avg_payback']} yrs</div>
                <div class="glass-label">Avg Payback</div>
                <div class="glass-trend trend-up">Target: &lt;5 yrs</div>
            </div>
            <div class="glass-card section-reveal">
                <div class="glass-value counter-animate" data-tip="{format_full(overview['health_score'])}">{overview['health_score']}</div>
                <div class="glass-label">Health Score</div>
                <div class="glass-trend trend-up">Portfolio health</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        yearly = budget_df.groupby("year").agg(capex=("capex", "sum"), opex=(
            "opex", "sum"), savings=("savings", "sum")).reset_index()
        fig_trend = px.line(yearly, x="year", y=["capex", "opex", "savings"], title="Multi-Year Cost & Savings Trend",
                            color_discrete_sequence=COLOR_SCHEMES["status_reverse"])
        fig_trend.update_traces(line=dict(width=3))
        style_chart(fig_trend, height=350, legend=True)
        fig_trend.update_layout(xaxis=dict(dtick=1))
        render_chart(fig_trend, key="fig_trend_L7567", use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            melt = yearly.melt(id_vars="year", value_vars=[
                               "capex", "opex"], var_name="type", value_name="amount")
            fig_bar = px.bar(melt, x="year", y="amount", color="type", barmode="group",
                             title="CapEx vs OpEx",
                             color_discrete_map={"capex": COLOR_SCHEMES["status_reverse"][0], "opex": COLOR_SCHEMES["status_reverse"][2]})
            style_chart(fig_bar, height=300, legend=True)
            render_chart(fig_bar, key="fig_bar_L7577", use_container_width=True)

        with col2:
            roi_sorted = roi_df.sort_values("roi_pct")
            fig_roi = px.bar(roi_sorted, y="station", x="roi_pct", orientation="h", title="ROI by Station",
                             color="roi_pct", color_continuous_scale=["#f56565", "#ffd700", "#00ff88"], text_auto=".1f")
            fig_roi.update_traces(textposition="outside")
            style_chart(fig_roi, height=300, legend=False)
            render_chart(fig_roi, key="fig_roi_L7585", use_container_width=True)

        monthly = generate_monthly_spend(2025)
        col3, col4 = st.columns(2)
        with col3:
            monthly_line = monthly.groupby("month").agg(
                planned=("planned", "sum"), actual=("actual", "sum")).reset_index()
            fig_monthly = px.line(monthly_line, x="month", y=["planned", "actual"],
                                  title="Monthly Spend Trend (2025)",
                                  color_discrete_sequence=COLOR_SCHEMES["blue"])
            style_chart(fig_monthly, height=280, legend=True)
            fig_monthly.update_layout(xaxis=dict(tickmode="linear", dtick=1))
            render_chart(fig_monthly, key="fig_monthly_L7597", use_container_width=True)

        with col4:
            cat_dist = monthly.groupby("category")[
                "actual"].sum().reset_index()
            fig_pie = px.pie(cat_dist, values="actual", names="category", title="Cost Distribution",
                             color_discrete_sequence=COLOR_SCHEMES["kpi"], hole=0.5)
            style_pie(fig_pie, height=280)
            render_chart(fig_pie, key="fig_pie_L7605", use_container_width=True)

        scenarios = generate_scenario_projections()
        fig_scen = px.line(scenarios, x="year", y="roi_pct", color="scenario", markers=True,
            hover_data={"year": True, "roi_pct": ":.1f"},
                           title="Scenario ROI Projections",
                           color_discrete_sequence=COLOR_SCHEMES["status_reverse"])
        style_chart(fig_scen, height=300, legend=True)
        fig_scen.update_layout(xaxis=dict(dtick=1))
        render_chart(fig_scen, key="fig_scen_L7614", use_container_width=True)

        comp = get_station_comparison_table()
        if not comp.empty:
            st.markdown("**Station Comparison**")
            styled = comp.style.format({
                "total_capex": "€{:,.0f}", "total_opex": "€{:,.0f}",
                "roi_pct": "{:.1f}%", "payback_years": "{:.1f} yrs",
                "npv": "€{:,.0f}", "irr": "{:.1f}%",
                "savings_to_cost_ratio": "{:.2f}x",
            })
            st.dataframe(styled, use_container_width=True, hide_index=True)
            csv = comp.to_csv(index=False).encode("utf-8")
            st.download_button("⬇ Export CSV", csv,
                               "station_comparison.csv", "text/csv")

    # ── Past Tab (2022-2024) ──
    with tab_past:
        hist = generate_budget_data()
        hist_yr = hist[hist["year"].between(2022, 2024)]
        hp = hist_yr.groupby("year").agg(capex=("capex", "sum"), opex=(
            "opex", "sum"), savings=("savings", "sum")).reset_index()

        st.markdown(f"""
        <div class="kpi-grid-3">
            <div class="glass-card section-reveal">
                <div class="glass-value counter-animate">€{hp['capex'].sum():,.0f}</div>
                <div class="glass-label">Total CapEx (2022-2024)</div>
                <div class="glass-trend trend-neutral">Infrastructure build-out phase</div>
            </div>
            <div class="glass-card section-reveal">
                <div class="glass-value counter-animate">€{hp['savings'].sum():,.0f}</div>
                <div class="glass-label">Total Savings</div>
                <div class="glass-trend trend-up">Cumulative efficiency gains</div>
            </div>
            <div class="glass-card section-reveal">
                <div class="glass-value counter-animate">€{hp['opex'].sum():,.0f}</div>
                <div class="glass-label">Total OpEx</div>
                <div class="glass-trend trend-neutral">Operating expenses</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        hp_display = hp.copy()
        hp_display["savings_ratio"] = hp_display["savings"] / \
            hp_display["opex"] * 100
        hp_display.columns = [
            "Year", "CapEx (€)", "OpEx (€)", "Savings (€)", "Savings/OpEx (%)"]
        st.dataframe(hp_display.style.format({
            "CapEx (€)": "€{:,.0f}", "OpEx (€)": "€{:,.0f}", "Savings (€)": "€{:,.0f}",
            "Savings/OpEx (%)": "{:.1f}%",
        }), use_container_width=True, hide_index=True)

        melt_past = hp.melt(id_vars="year", value_vars=[
                            "capex", "savings"], var_name="type", value_name="amount")
        fig_past = px.bar(melt_past, x="year", y="amount", color="type", barmode="group",
                          title="CapEx vs Savings (2022-2024)",
                          color_discrete_map={"capex": COLOR_SCHEMES["status_reverse"][0], "savings": COLOR_SCHEMES["status_reverse"][2]})
        style_chart(fig_past, height=300, legend=True)
        render_chart(fig_past, key="fig_past_L7673", use_container_width=True)

    # ── Present Tab (2025) ──
    with tab_present:
        present_spend = generate_monthly_spend(2025)
        total_planned = present_spend["planned"].sum()
        total_actual = present_spend["actual"].sum()
        variance = total_planned - total_actual
        variance_pct = (variance / total_planned * 100) if total_planned else 0
        var_class = "status-ok" if variance >= 0 else "status-err"

        st.markdown(f"""
        <div class="kpi-grid-3">
            <div class="glass-card section-reveal">
                <div class="glass-value counter-animate">€{total_planned:,.0f}</div>
                <div class="glass-label">Budgeted (2025)</div>
                <div class="glass-trend trend-neutral">Annual planned spend</div>
            </div>
            <div class="glass-card section-reveal">
                <div class="glass-value counter-animate">€{total_actual:,.0f}</div>
                <div class="glass-label">Actual Spend</div>
                <div class="glass-trend {"trend-up" if variance >= 0 else "trend-down"}">YTD actuals</div>
            </div>
            <div class="glass-card section-reveal">
                <div class="glass-value {var_class}">€{variance:,.0f}</div>
                <div class="glass-label">Variance</div>
                <div class="glass-trend {"trend-up" if variance >= 0 else "trend-down"}">{variance_pct:+.1f}% vs budget</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        bva = present_spend.groupby("month").agg(
            planned=("planned", "sum"), actual=("actual", "sum")).reset_index()
        fig_bva = px.bar(bva, x="month", y=["planned", "actual"], barmode="group",
                         title="Budget vs Actuals (Monthly)",
                         color_discrete_map={"planned": COLOR_SCHEMES["blue"][0], "actual": COLOR_SCHEMES["teal"][1]})
        style_chart(fig_bva, height=300, legend=True)
        fig_bva.update_layout(xaxis=dict(tickmode="linear", dtick=1))
        render_chart(fig_bva, key="fig_bva_L7711", use_container_width=True)

        bva["variance"] = bva["planned"] - bva["actual"]
        bva["variance_pct"] = (bva["variance"] / bva["planned"] * 100).round(1)
        bva_display = bva.rename(columns={"month": "Month", "planned": "Planned (€)",
                                 "actual": "Actual (€)", "variance": "Variance (€)", "variance_pct": "Var %"})
        st.dataframe(bva_display.style.format({
            "Planned (€)": "€{:,.0f}", "Actual (€)": "€{:,.0f}", "Variance (€)": "€{:+,.0f}", "Var %": "{:+.1f}%",
        }), use_container_width=True, hide_index=True)

    # ── Future Tab (2026-2030) ──
    with tab_future:
        fut = generate_scenario_projections()
        fut_agg = fut.groupby("year").agg(capex=("capex", "sum"), opex=(
            "opex", "sum"), savings=("savings", "sum"), roi_pct=("roi_pct", "mean")).reset_index()

        st.markdown(f"""
        <div class="kpi-grid-3">
            <div class="glass-card section-reveal">
                <div class="glass-value counter-animate">€{fut_agg['savings'].sum():,.0f}</div>
                <div class="glass-label">Projected Total Savings</div>
                <div class="glass-trend trend-up">2026-2030 cumulative</div>
            </div>
            <div class="glass-card section-reveal">
                <div class="glass-value counter-animate">{fut_agg['roi_pct'].mean():.1f}%</div>
                <div class="glass-label">Avg Projected ROI</div>
                <div class="glass-trend trend-up">Across all scenarios</div>
            </div>
            <div class="glass-card section-reveal">
                <div class="glass-value counter-animate">€{fut_agg['capex'].sum():,.0f}</div>
                <div class="glass-label">Projected CapEx</div>
                <div class="glass-trend trend-neutral">Maintenance & upgrades</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("**Yearly Projections by Scenario**")
        fut_pivot = fut.pivot_table(
            index="year", columns="scenario", values="roi_pct", aggfunc="mean").reset_index()
        st.dataframe(fut_pivot.style.format(
            "{:.1f}%"), use_container_width=True, hide_index=True)

        fig_fut = px.line(fut, x="year", y="roi_pct", color="scenario", markers=True,
                          title="Projected ROI Trajectory",
                          color_discrete_sequence=COLOR_SCHEMES["status_reverse"])
        style_chart(fig_fut, height=300, legend=True)
        fig_fut.update_layout(xaxis=dict(dtick=1))
        render_chart(fig_fut, key="fig_fut_L7758", use_container_width=True)

    # ── Optimization Tab ──
    with tab_optim:
        recs = generate_optimization_recommendations()
        total_savings = sum(r["potential_savings_eur"] for r in recs)
        total_cost = sum(r["implementation_cost_eur"] for r in recs)

        st.markdown(f"""
        <div class="glass-card" style="text-align:center; padding:1.5rem; margin-bottom:1rem;">
            <div class="glass-value counter-animate">€{total_savings:,.0f}</div>
            <div class="glass-label">Total Potential Savings</div>
            <div class="glass-trend trend-up">Implementation cost: €{total_cost:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

        priorities = {"High": "high", "Medium": "medium", "Low": "low"}
        filtered = sorted(recs, key=lambda r: {
                          "High": 0, "Medium": 1, "Low": 2}.get(r["priority"], 99))

        for r in filtered:
            pcls = priorities.get(r["priority"], "low")
            st.markdown(f"""
            <div class="rec-card" style="border-left: 3px solid var(--{'status-error' if r['priority']=='High' else 'status-warning' if r['priority']=='Medium' else 'text-muted'});">
                <div class="rec-header">
                    <div>
                        <div class="rec-title">{r['title']}</div>
                        <div class="rec-desc">{r['description']}</div>
                        <div class="rec-meta">{r['station']} · {r['category']}</div>
                    </div>
                    <div class="rec-savings">
                        <div class="rec-savings-value">€{r['potential_savings_eur']:,}</div>
                        <div class="rec-payback">Payback: {r['payback_months']}mo</div>
                        <span class="priority-badge {pcls}">{r['priority']}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
elif active_tab == "totalvision":
    from core.tv_renderer import render_tv
    render_tv(df)

elif active_tab == "company":
    st.markdown('<div class="company-section">', unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════
    # HERO SECTION
    # ═══════════════════════════════════════════════════
    st.markdown("""
    <div class="hero-section" style="text-align:center;padding:2rem 1rem 1rem;">
        <div class="hero-title" style="font-size:2.8rem;font-weight:900;background:linear-gradient(135deg,#f59e0b 0%,#d946ef 60%,#06b6d4 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;letter-spacing:-0.03em;">SicherGleis GmbH</div>
        <div class="hero-subtitle" style="font-size:1.2rem;color:var(--text-secondary);margin-top:0.3rem;font-weight:600;letter-spacing:0.06em;">Precision Railway Safety Systems</div>
        <div class="hero-tagline" style="margin-top:0.75rem;display:flex;align-items:center;justify-content:center;gap:0.6rem;flex-wrap:wrap;">
            <span style="font-size:1.5rem;">🛡️</span>
            <span style="color:var(--text-muted);font-size:0.85rem;letter-spacing:0.03em;">Suraksha (Safety-First) &bull; German Engineering Excellence &bull; Since 2023</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════
    # IMPACT METRICS ROW — animated with trends
    # ═══════════════════════════════════════════════════
    st.markdown("""
    <div class="section-header"><span class="section-icon">📊</span><span class="section-title">Company at a Glance</span></div>
    <div class="stagger-children" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:var(--space-md);margin-bottom:var(--space-xl);">
        <div class="stat-card info press-effect" style="text-align:center;padding:1.5rem 1rem;">
            <div style="font-size:2rem;margin-bottom:0.3rem;">🚉</div>
            <div class="metric-value" style="font-size:2rem;color:var(--color-accent-light);">127</div>
            <div class="metric-label" style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.08em;color:var(--text-muted);margin-top:0.2rem;">Stations Deployed</div>
            <div class="trend up" style="margin-top:0.5rem;font-size:0.6rem;">+18% YoY</div>
        </div>
        <div class="stat-card success press-effect" style="text-align:center;padding:1.5rem 1rem;">
            <div style="font-size:2rem;margin-bottom:0.3rem;">🚪</div>
            <div class="metric-value" style="font-size:2rem;color:var(--color-emerald);">2,450</div>
            <div class="metric-label" style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.08em;color:var(--text-muted);margin-top:0.2rem;">PSD Units Installed</div>
            <div class="trend up" style="margin-top:0.5rem;font-size:0.6rem;">+32% YoY</div>
        </div>
        <div class="stat-card warning press-effect" style="text-align:center;padding:1.5rem 1rem;">
            <div style="font-size:2rem;margin-bottom:0.3rem;">🌍</div>
            <div class="metric-value" style="font-size:2rem;color:var(--color-primary-light);">5</div>
            <div class="metric-label" style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.08em;color:var(--text-muted);margin-top:0.2rem;">Countries</div>
            <div class="trend up" style="margin-top:0.5rem;font-size:0.6rem;">+2 new in 2025</div>
        </div>
        <div class="stat-card info press-effect" style="text-align:center;padding:1.5rem 1rem;">
            <div style="font-size:2rem;margin-bottom:0.3rem;">💶</div>
            <div class="metric-value" style="font-size:2rem;color:var(--color-accent-light);">€7.5M</div>
            <div class="metric-label" style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.08em;color:var(--text-muted);margin-top:0.2rem;">Total Funding</div>
            <div class="trend up" style="margin-top:0.5rem;font-size:0.6rem;">Series A + Seed</div>
        </div>
        <div class="stat-card success press-effect" style="text-align:center;padding:1.5rem 1rem;">
            <div style="font-size:2rem;margin-bottom:0.3rem;">👥</div>
            <div class="metric-value" style="font-size:2rem;color:var(--color-emerald);">14</div>
            <div class="metric-label" style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.08em;color:var(--text-muted);margin-top:0.2rem;">Team Members</div>
            <div class="trend up" style="margin-top:0.5rem;font-size:0.6rem;">+5 in 2025</div>
        </div>
        <div class="stat-card success press-effect" style="text-align:center;padding:1.5rem 1rem;">
            <div style="font-size:2rem;margin-bottom:0.3rem;">⚡</div>
            <div class="metric-value" style="font-size:2rem;color:var(--color-emerald);">99.97%</div>
            <div class="metric-label" style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.08em;color:var(--text-muted);margin-top:0.2rem;">System Uptime</div>
            <div class="trend up" style="margin-top:0.5rem;font-size:0.6rem;">+0.02% this year</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════
    # ABOUT US
    # ═══════════════════════════════════════════════════
    st.markdown(
        '<div class="section-header"><span class="section-icon">🏢</span><span class="section-title">About Us</span></div>',
        unsafe_allow_html=True,
    )

    st.markdown("""
    <div class="glass-card section-reveal">
        <h3>Core Concept</h3>
        <p>SicherGleis delivers precision-engineered Platform Screen Door (PSD) systems that unite 
        <strong>Suraksha</strong> (safety-first philosophy) with German engineering excellence to create 
        safe, intelligent, and future-ready urban rail infrastructure.</p>
        <p>Our systems actively prevent platform edge incidents, optimize boarding flow, and enable predictive 
        maintenance &mdash; all in real time. With deployments across 127 stations in 5 countries, we're redefining 
        railway safety standards across Europe and Asia.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="glass-card section-reveal">
        <h3>Market &amp; Vision</h3>
        <div class="stats-row">
            <div class="stat-item">
                <div class="stat-label">Target Market</div>
                <div class="stat-value">DACH + India</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">Founded</div>
                <div class="stat-value">2023</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">Main Office</div>
                <div class="stat-value">Berlin, Germany</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">Regulatory</div>
                <div class="stat-value">SIL-2 Certified</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════
    # COMPANY TIMELINE
    # ═══════════════════════════════════════════════════
    st.markdown(
        '<div class="section-header"><span class="section-icon">📅</span><span class="section-title">Company Timeline</span></div>',
        unsafe_allow_html=True,
    )

    timeline_html = '''
    <div class="timeline-wrapper" style="padding:1.5rem 0;margin-bottom:1.5rem;">
        <div style="display:flex;gap:0;overflow-x:auto;padding:1rem 0;scroll-snap-type:x mandatory;position:relative;">
            <div style="position:absolute;top:50%;left:5%;right:5%;height:2px;background:linear-gradient(90deg,var(--color-primary-border),var(--color-fuchsia-subtle),var(--color-secondary-border));transform:translateY(-50%);z-index:0;"></div>'''
    milestones = [
        ("2023 Q1", "Founded", "Company incorporated\\nin Berlin", "🚀", "#f59e0b"),
        ("2023 Q3", "Seed Round", "€1.5M raised for\\nR&amp;D &amp; prototyping", "💶", "#06b6d4"),
        ("2024 Q1", "First Pilot", "PSD system deployed\\nat Berlin Hbf", "🚉", "#10b981"),
        ("2024 Q3", "Product Launch", "BahnSetu platform\\nofficially launched", "🎯", "#d946ef"),
        ("2025 Q1", "Series A", "€6M secured for\\nEuropean expansion", "💰", "#f59e0b"),
        ("2025 Q3", "5-Country Reach", "Operations across\\nGermany, Austria, etc.", "🌍", "#06b6d4"),
        ("2026 Q1", "SIL-2 Cert.", "Safety certification\\nfor core systems", "✓", "#10b981"),
        ("2026 H2", "India Entry", "Expansion into\\nIndian metro market", "🚈", "#d946ef"),
    ]
    for year, title, desc, icon, color in milestones:
        timeline_html += f'''
            <div style="flex:0 0 150px;scroll-snap-align:start;position:relative;z-index:1;display:flex;flex-direction:column;align-items:center;padding:0.5rem;">
                <div style="width:42px;height:42px;border-radius:50%;background:var(--bg-elevated);border:2px solid {color};display:flex;align-items:center;justify-content:center;font-size:1.1rem;box-shadow:0 0 12px {color}44;margin-bottom:0.6rem;">
                    {icon}
                </div>
                <div style="font-size:0.6rem;font-weight:700;color:{color};text-transform:uppercase;letter-spacing:0.08em;font-family:var(--font-mono);">{year}</div>
                <div style="font-size:0.75rem;font-weight:700;color:var(--text-primary);margin-top:0.15rem;text-align:center;">{title}</div>
                <div style="font-size:0.6rem;color:var(--text-muted);text-align:center;white-space:pre-line;line-height:1.4;margin-top:0.1rem;">{desc}</div>
            </div>'''
    timeline_html += '</div></div>'
    st.markdown(timeline_html, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════
    # SERVICES SECTION
    # ═══════════════════════════════════════════════════
    st.markdown(
        '<div class="section-header"><span class="section-icon">🛠️</span><span class="section-title">Our Services</span></div>',
        unsafe_allow_html=True,
    )

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        service_breakdown = pd.DataFrame({
            "Service": ["PSD Systems", "Analytics", "Dashboard", "BI Tools"],
            "Revenue": [45, 25, 20, 10],
        })
        fig_svc = px.pie(
            service_breakdown,
            values="Revenue",
            names="Service",
            title="Revenue by Service Line",
            color_discrete_sequence=["#f59e0b", "#06b6d4", "#10b981", "#d946ef"],
            hole=0.4,
        )
        fig_svc.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="var(--text-muted)"),
            title=dict(font=dict(size=13, color="#fbbf24")),
            margin=dict(l=10, r=10, t=40, b=10),
            height=260,
            legend=dict(orientation="h", y=-0.15, font=dict(size=9)),
        )
        render_chart(fig_svc, key="fig_svc_L7972", use_container_width=True)

    with col_s2:
        st.markdown("""
        <div style="padding:1rem;border-radius:var(--radius-2xl);background:var(--bg-glass);backdrop-filter:blur(14px);border:1px solid var(--border-subtle);height:260px;display:flex;flex-direction:column;justify-content:center;">
            <div style="text-align:center;font-size:0.8rem;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.75rem;">Service Highlights</div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.5rem;">
                <div style="padding:0.6rem;border-radius:var(--radius-lg);background:var(--color-primary-subtle);border:1px solid var(--color-primary-border);text-align:center;">
                    <div style="font-size:0.75rem;font-weight:700;color:var(--color-primary-light);">45%</div>
                    <div style="font-size:0.55rem;color:var(--text-muted);">PSD Systems</div>
                </div>
                <div style="padding:0.6rem;border-radius:var(--radius-lg);background:var(--color-secondary-subtle);border:1px solid var(--color-secondary-border);text-align:center;">
                    <div style="font-size:0.75rem;font-weight:700;color:var(--color-secondary-light);">25%</div>
                    <div style="font-size:0.55rem;color:var(--text-muted);">Analytics</div>
                </div>
                <div style="padding:0.6rem;border-radius:var(--radius-lg);background:var(--color-emerald-subtle);border:1px solid var(--color-emerald-border);text-align:center;">
                    <div style="font-size:0.75rem;font-weight:700;color:var(--color-emerald);">20%</div>
                    <div style="font-size:0.55rem;color:var(--text-muted);">Dashboard</div>
                </div>
                <div style="padding:0.6rem;border-radius:var(--radius-lg);background:var(--color-fuchsia-subtle);border:1px solid var(--color-fuchsia-subtle);text-align:center;">
                    <div style="font-size:0.75rem;font-weight:700;color:var(--color-fuchsia);">10%</div>
                    <div style="font-size:0.55rem;color:var(--text-muted);">BI Tools</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    services_data = [
        {"icon": "🚪", "title": "PSD Systems", "desc": "Smart PSD systems with real-time monitoring, automated gate sync, and predictive diagnostics.", "color": "#f59e0b"},
        {"icon": "🔮", "title": "Predictive Maintenance", "desc": "AI-powered system forecasting potential failures with 7-day risk analysis.", "color": "#d946ef"},
        {"icon": "📊", "title": "Operations Dashboard", "desc": "Comprehensive real-time dashboard for monitoring all station operations.", "color": "#06b6d4"},
        {"icon": "👥", "title": "Customer BI", "desc": "RFM segmentation, contract health scoring, and renewal forecasting.", "color": "#10b981"},
    ]
    cols = st.columns(4)
    for i, svc in enumerate(services_data):
        with cols[i]:
            st.markdown(f"""
            <div class="press-effect" style="padding:1.25rem;border-radius:var(--radius-2xl);background:var(--bg-glass);backdrop-filter:blur(14px);border:1px solid {svc['color']}33;text-align:center;transition:all 0.22s ease;height:100%;">
                <div style="font-size:2rem;margin-bottom:0.5rem;">{svc['icon']}</div>
                <div style="font-size:0.85rem;font-weight:700;color:var(--text-primary);margin-bottom:0.4rem;">{svc['title']}</div>
                <div style="font-size:0.7rem;color:var(--text-muted);line-height:1.5;">{svc['desc']}</div>
            </div>
            """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════
    # GROWTH & INNOVATION CHARTS
    # ═══════════════════════════════════════════════════
    st.markdown(
        '<div class="section-header"><span class="section-icon">📈</span><span class="section-title">Growth & Innovation</span></div>',
        unsafe_allow_html=True,
    )

    col_c1, col_c2 = st.columns(2)

    with col_c1:
        months = ["Q1'23","Q2'23","Q3'23","Q4'23","Q1'24","Q2'24","Q3'24","Q4'24","Q1'25","Q2'25","Q3'25","Q4'25"]
        growth_data = pd.DataFrame({
            "Quarter": months,
            "Revenue (€K)": [0, 0, 50, 120, 250, 380, 520, 680, 850, 1050, 1280, 1520],
            "Funding (€K)": [1500, 0, 0, 0, 0, 0, 6000, 0, 0, 0, 0, 0],
        })
        fig_growth = go.Figure()
        fig_growth.add_trace(go.Scatter(
            x=growth_data["Quarter"], y=growth_data["Revenue (€K)"],
            fill="tozeroy", name="Revenue",
            line=dict(color="#f59e0b", width=2.5),
            fillcolor="rgba(245,158,11,0.12)",
        ))
        fig_growth.add_trace(go.Bar(
            x=growth_data["Quarter"], y=growth_data["Funding (€K)"],
            name="Funding Raised",
            marker_color="rgba(6,182,212,0.5)",
            marker_line_color="#06b6d4",
            marker_line_width=1,
        ))
        fig_growth.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="var(--text-muted)"),
            title=dict(text="Revenue Growth & Funding", font=dict(size=13, color="#fbbf24")),
            margin=dict(l=20, r=20, t=40, b=20),
            height=280,
            legend=dict(orientation="h", y=1.1, font=dict(size=9)),
            yaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
        )
        render_chart(fig_growth, key="fig_growth_L8058", use_container_width=True)

    with col_c2:
        radar_categories = ["PSD Hardware", "Edge AI/ML", "IoT Sensors", "Safety Systems", "Cloud Platform", "UX Design"]
        radar_values = [85, 75, 90, 95, 80, 70]
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=radar_values,
            theta=radar_categories,
            fill="toself",
            name="R&D Focus",
            line=dict(color="#d946ef", width=2),
            fillcolor="rgba(217,70,239,0.12)",
        ))
        fig_radar.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="var(--text-muted)"),
            title=dict(text="R&D Innovation Focus Areas", font=dict(size=13, color="#fbbf24")),
            margin=dict(l=40, r=40, t=40, b=20),
            height=280,
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100], gridcolor="rgba(255,255,255,0.06)"),
                bgcolor="rgba(0,0,0,0)",
            ),
        )
        render_chart(fig_radar, key="fig_radar_L8084", use_container_width=True)

    # ═══════════════════════════════════════════════════
    # PERFORMANCE & IMPACT CHARTS
    # ═══════════════════════════════════════════════════
    st.markdown(
        '<div class="section-header"><span class="section-icon">🎯</span><span class="section-title">Performance & Impact</span></div>',
        unsafe_allow_html=True,
    )

    col_c3, col_c4, col_c5 = st.columns([1.2, 1, 1])

    with col_c3:
        geo_data = pd.DataFrame({
            "Country": ["Germany", "Austria", "Switzerland", "Poland", "India"],
            "Stations": [52, 28, 22, 15, 10],
            "PSD Units": [980, 520, 410, 290, 250],
        })
        fig_geo = px.bar(
            geo_data, x="Stations", y="Country", orientation="h",
            title="Geographic Presence",
            text="Stations",
            color="Stations",
            color_continuous_scale=["#06b6d4", "#f59e0b", "#d946ef"],
        )
        fig_geo.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="var(--text-muted)"),
            title=dict(text="Stations by Country", font=dict(size=13, color="#fbbf24")),
            margin=dict(l=10, r=20, t=40, b=10),
            height=260,
            coloraxis_showscale=False,
            xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
            yaxis=dict(autorange="reversed"),
        )
        fig_geo.update_traces(textposition="outside", textfont=dict(size=10, color="var(--text-secondary)"))
        render_chart(fig_geo, key="fig_geo_L8122", use_container_width=True)

    with col_c4:
        kpi_scores = pd.DataFrame({
            "KPI": ["Uptime", "Safety", "Satisfaction", "Efficiency"],
            "Score": [99.7, 98.2, 94.5, 91.8],
            "Target": [99.5, 98.0, 93.0, 90.0],
        })
        fig_kpi = go.Figure()
        fig_kpi.add_trace(go.Bar(
            x=kpi_scores["KPI"], y=kpi_scores["Score"],
            name="Actual",
            marker_color=["#10b981", "#f59e0b", "#06b6d4", "#d946ef"],
            text=kpi_scores["Score"].apply(lambda x: f"{x:.1f}%"),
            textposition="outside",
            textfont=dict(size=10, color="var(--text-secondary)"),
        ))
        fig_kpi.add_trace(go.Scatter(
            x=kpi_scores["KPI"], y=kpi_scores["Target"],
            name="Target",
            mode="markers+lines",
            marker=dict(color="rgba(255,255,255,0.3)", size=8, symbol="diamond"),
            line=dict(color="rgba(255,255,255,0.15)", dash="dot", width=1),
        ))
        fig_kpi.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="var(--text-muted)"),
            title=dict(text="Key Performance Indicators", font=dict(size=13, color="#fbbf24")),
            margin=dict(l=10, r=10, t=40, b=10),
            height=260,
            yaxis_range=[0, 105],
            yaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickfont=dict(size=9)),
            xaxis=dict(tickfont=dict(size=9)),
            legend=dict(orientation="h", y=1.1, font=dict(size=8)),
            bargap=0.3,
        )
        render_chart(fig_kpi, key="fig_kpi_L8160", use_container_width=True)

    with col_c5:
        esg_data = pd.DataFrame({
            "Metric": ["Energy Eff.", "CO₂ Saved", "Waste Red.", "Green Ops"],
            "Score": [92, 88, 78, 85],
        })
        fig_esg = px.bar(
            esg_data, x="Metric", y="Score",
            title="ESG & Sustainability",
            color="Score",
            color_continuous_scale=["#06b6d4", "#10b981", "#f59e0b"],
            text=esg_data["Score"].apply(lambda x: f"{x}%"),
        )
        fig_esg.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="var(--text-muted)"),
            title=dict(text="Environmental Impact", font=dict(size=13, color="#fbbf24")),
            margin=dict(l=10, r=10, t=40, b=10),
            height=260,
            coloraxis_showscale=False,
            yaxis_range=[0, 100],
            yaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickfont=dict(size=9)),
            xaxis=dict(tickfont=dict(size=8)),
            bargap=0.3,
        )
        fig_esg.update_traces(textposition="outside", textfont=dict(size=9, color="var(--text-secondary)"))
        render_chart(fig_esg, key="fig_esg_L8189", use_container_width=True)

    # ═══════════════════════════════════════════════════
    # AWARDS & CERTIFICATIONS
    # ═══════════════════════════════════════════════════
    st.markdown(
        '<div class="section-header"><span class="section-icon">🏆</span><span class="section-title">Awards & Certifications</span></div>',
        unsafe_allow_html=True,
    )

    awards_data = [
        {"icon": "🥇", "title": "Innovation in Urban Transit", "org": "UITP 2024", "desc": "Best new safety technology for urban rail systems"},
        {"icon": "🔒", "title": "ISO 27001 Certified", "org": "Information Security", "desc": "Enterprise-grade security management system"},
        {"icon": "🌿", "title": "EcoRail Excellence Award", "org": "German Transport Forum", "desc": "Recognized for sustainable rail innovation"},
        {"icon": "⭐", "title": "Best PSD Solution Provider", "org": "Smart City Expo", "desc": "Leading platform safety solution globally"},
    ]

    award_cols = st.columns(4)
    for i, award in enumerate(awards_data):
        with award_cols[i]:
            st.markdown(f"""
            <div class="press-effect" style="padding:1.25rem;border-radius:var(--radius-2xl);background:var(--bg-glass);backdrop-filter:blur(14px);border:1px solid var(--border-subtle);text-align:center;height:100%;transition:all 0.22s ease;">
                <div style="font-size:2.2rem;margin-bottom:0.4rem;">{award['icon']}</div>
                <div style="font-size:0.8rem;font-weight:700;color:var(--text-primary);margin-bottom:0.2rem;">{award['title']}</div>
                <div style="font-size:0.6rem;color:var(--color-primary-light);font-weight:600;margin-bottom:0.3rem;">{award['org']}</div>
                <div style="font-size:0.6rem;color:var(--text-muted);line-height:1.4;">{award['desc']}</div>
            </div>
            """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════
    # PARTNERS & CLIENTS
    # ═══════════════════════════════════════════════════
    st.markdown(
        '<div class="section-header"><span class="section-icon">🤝</span><span class="section-title">Partners & Clients</span></div>',
        unsafe_allow_html=True,
    )

    partner_cols = st.columns(6)
    partners = [
        {"name": "DB Station&Service", "logo": "🚂"},
        {"name": "S-Bahn Berlin", "logo": "🚇"},
        {"name": "BVG Berlin", "logo": "🚌"},
        {"name": "MVV Munich", "logo": "🚆"},
        {"name": "Wiener Linien", "logo": "🚊"},
        {"name": "Indian Metro", "logo": "🚈"},
    ]
    for i, partner in enumerate(partners):
        with partner_cols[i]:
            st.markdown(f"""
            <div class="press-effect" style="padding:1rem;border-radius:var(--radius-xl);background:var(--bg-glass);backdrop-filter:blur(14px);border:1px solid var(--border-subtle);text-align:center;height:100%;transition:all 0.22s ease;">
                <div style="font-size:1.5rem;margin-bottom:0.3rem;">{partner['logo']}</div>
                <div style="font-size:0.65rem;font-weight:600;color:var(--text-secondary);line-height:1.3;">{partner['name']}</div>
            </div>
            """, unsafe_allow_html=True)

    # ═════════════════════════════════════════════════
    # LEADERSHIP TEAM
    # ═════════════════════════════════════════════════
    st.markdown(
        '<div class="section-header"><span class="section-icon">👥</span><span class="section-title">Leadership Team</span></div>',
        unsafe_allow_html=True,
    )

    if "team_selected" not in st.session_state:
        st.session_state.team_selected = None

    team = get_leadership_data()
    team_cols = st.columns(len(team))

    role_colors = {
        "CEO": "#f59e0b",
        "COO": "#06b6d4",
        "CTO": "#d946ef",
        "CPO": "#10b981",
        "CFO": "#3b82f6",
    }

    for i, member in enumerate(team):
        with team_cols[i]:
            img_url = member.get("img") or f"https://ui-avatars.com/api/?name={member['name'].replace(' ', '+')}&background=1a365d&color=fff&size=120"
            role_color = role_colors.get(member["role"], "#f59e0b")
            is_active = st.session_state.team_selected == member["name"]

            st.markdown(f"""
            <div style="padding:1.25rem 0.75rem;border-radius:var(--radius-2xl);background:{'var(--bg-glass-hover)' if is_active else 'var(--bg-glass)'};backdrop-filter:blur(14px);border:1px solid {'var(--border-default)' if is_active else 'var(--border-subtle)'};text-align:center;margin-bottom:0.5rem;position:relative;overflow:hidden;transition:all 0.22s ease;">
                <div style="position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,{role_color},{role_color}88,transparent);opacity:{'1' if is_active else '0.4'};"></div>
                <img src="{img_url}" style="width:64px;height:64px;border-radius:50%;border:2px solid {role_color}44;object-fit:cover;margin-bottom:0.5rem;">
                <div style="font-size:0.8rem;font-weight:700;color:var(--text-primary);line-height:1.2;">{member['name']}</div>
                <div style="font-size:0.65rem;font-weight:600;color:{role_color};margin-top:0.15rem;">{member['role']}</div>
                <div style="font-size:0.6rem;color:var(--text-muted);margin-top:0.3rem;line-height:1.3;">{member.get('desc','')[:50]}...</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button(f"👤 View Profile", key=f"btn_{i}", use_container_width=True):
                st.session_state.team_selected = member["name"]
                st.rerun()

    if st.session_state.team_selected:
        member = next((m for m in team if m["name"] == st.session_state.team_selected), None)
        if member:
            img_url = member.get("img") or f"https://ui-avatars.com/api/?name={member['name'].replace(' ', '+')}&background=1a365d&color=fff&size=200"
            role_color = role_colors.get(member["role"], "#f59e0b")

            st.markdown(f'<div style="margin-top:1rem;padding:1.5rem;border-radius:var(--radius-2xl);background:var(--bg-glass);backdrop-filter:blur(14px);border:1px solid var(--border-default);">', unsafe_allow_html=True)

            col_l, col_r = st.columns([1, 2.2])
            with col_l:
                st.markdown(f"""
                <div style="text-align:center;">
                    <img src="{img_url}" style="width:160px;height:160px;border-radius:50%;border:3px solid {role_color}55;object-fit:cover;margin-bottom:0.75rem;">
                    <div style="font-size:1.1rem;font-weight:800;color:var(--text-primary);">{member['name']}</div>
                    <div style="font-size:0.8rem;font-weight:600;color:{role_color};">{member['role']}</div>
                    <div style="margin-top:0.5rem;font-size:0.65rem;color:var(--text-muted);font-style:italic;">&ldquo;{member.get('quote','')}&rdquo;</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("✕ Close", key="close_profile", use_container_width=True):
                    st.session_state.team_selected = None
                    st.rerun()

            with col_r:
                st.markdown(f"""
                <div style="margin-bottom:0.75rem;padding:1rem;border-radius:var(--radius-xl);background:var(--bg-elevated);border:1px solid var(--border-subtle);">
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.75rem;">
                        <div><div style="font-size:0.55rem;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.08em;">Experience</div><div style="font-size:0.75rem;color:var(--text-secondary);margin-top:0.15rem;">{member.get('experience','')}</div></div>
                        <div><div style="font-size:0.55rem;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.08em;">Education</div><div style="font-size:0.75rem;color:var(--text-secondary);margin-top:0.15rem;">{member.get('education','')}</div></div>
                        <div style="grid-column:1/3;"><div style="font-size:0.55rem;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.08em;">Specialization</div><div style="font-size:0.75rem;color:var(--text-secondary);margin-top:0.15rem;">{member.get('specialization','')}</div></div>
                    </div>
                </div>
                <div style="padding:1rem;border-radius:var(--radius-xl);background:var(--bg-elevated);border:1px solid var(--border-subtle);">
                    <div style="font-size:0.55rem;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.4rem;">Key Achievements</div>
                """, unsafe_allow_html=True)
                for ach in member.get('achievements', []):
                    st.markdown(f'<div style="display:flex;align-items:center;gap:0.4rem;padding:0.25rem 0;border-bottom:1px solid var(--border-subtle);"><span style="color:{role_color};font-size:0.6rem;">&#9656;</span><span style="font-size:0.7rem;color:var(--text-secondary);">{ach}</span></div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

    # ═════════════════════════════════════════════════
    # DOWNLOAD PDF REPORT
    # ═════════════════════════════════════════════════
    st.markdown(
        '<div class="section-header"><span class="section-icon">📥</span><span class="section-title">Company Profile Report</span></div>',
        unsafe_allow_html=True,
    )

    col_rep1, col_rep2 = st.columns([2, 1])
    with col_rep1:
        st.markdown("""
        <div class="glass-card section-reveal">
            <h3>PDF Report for Prospective Clients</h3>
            <p>Download our comprehensive company profile report featuring services, case studies, leadership team, and contact information.</p>
        </div>
        """, unsafe_allow_html=True)

    with col_rep2:
        try:
            pdf_buffer = generate_client_report()
            pdf_bytes = pdf_buffer.getvalue()
            st.download_button(
                label="📥 Download PDF",
                data=pdf_bytes,
                file_name="SicherGleis_Company_Profile.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as e:
            st.warning("PDF not available")

    # Close company section
    st.html("</div>")


elif active_tab == "analytics":
    st.markdown(
        '<div class="analytics-hero">'
        '<h1>Analytics Lab</h1>'
        "<p>Interactive anomaly detection &bull; Time-series decomposition &bull; Sensor correlation analysis &mdash; "
        "Learn core data analytics methods on live railway sensor data</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    tab_anomaly, tab_decomp, tab_corr = st.tabs([
        "Anomaly Detection Playground",
        "Time-Series Decomposition",
        "Correlation & Health Explorer",
    ])

    with tab_anomaly:
        col_method, col_sensor, col_param = st.columns([1, 1, 1])
        with col_method:
            method = st.selectbox(
                "Detection Method",
                ["Z-Score", "IQR (Tukey's Fences)",
                 "Moving Average Band", "Isolation Forest"],
                key="anomaly_method",
            )
        with col_sensor:
            sensor_col = st.selectbox(
                "Sensor Column",
                ["sensor_temp", "sensor_vib", "people", "risk_score"],
                key="anomaly_sensor",
            )
        with col_param:
            station_filter = st.selectbox(
                "Station", ["All Stations"] + stations, key="anomaly_station"
            )

        param_cols = st.columns(4)
        threshold = 3.0
        iqr_mult = 1.5
        ma_window = 12
        ma_std = 2.0
        if_method = "Z-Score"

        if method == "Z-Score":
            with param_cols[0]:
                threshold = st.slider(
                    "Z-Score Threshold", 1.0, 5.0, 3.0, 0.1, key="z_thresh")
            if_method = "Z-Score"
        elif method == "IQR (Tukey's Fences)":
            with param_cols[0]:
                iqr_mult = st.slider("IQR Multiplier", 0.5,
                                     4.0, 1.5, 0.1, key="iqr_mult")
            if_method = "IQR"
        elif method == "Moving Average Band":
            with param_cols[0]:
                ma_window = st.slider("Window", 3, 48, 12, 1, key="ma_win")
            with param_cols[1]:
                ma_std = st.slider("Std Multiplier", 0.5,
                                   4.0, 2.0, 0.1, key="ma_std")
            if_method = "MA"
        elif method == "Isolation Forest":
            with param_cols[0]:
                contamination = st.slider(
                    "Contamination", 0.01, 0.5, 0.05, 0.01, key="if_cont")
            if_method = "IF"

        # Prepare data
        base_df = df if station_filter == "All Stations" else df[df["station"]
                                                                 == station_filter]
        series_data = base_df[sensor_col].dropna().reset_index(drop=True)

        if series_data.empty:
            st.warning("No data available for the selected filters.")
        else:
            # Build ground truth from maintenance_status if available
            has_gt = "maintenance_status" in base_df.columns
            if has_gt:
                gt_series = base_df["maintenance_status"].isin(
                    ["CRITICAL", "WARNING"]).reset_index(drop=True)
            else:
                gt_series = pd.Series([False] * len(series_data))

            # Run selected method
            if if_method == "Z-Score":
                result_df = detect_anomalies_zscore(
                    series_data, threshold=threshold)
            elif if_method == "IQR":
                result_df = detect_anomalies_iqr(
                    series_data, multiplier=iqr_mult)
            elif if_method == "MA":
                result_df = detect_anomalies_moving_average(
                    series_data, window=ma_window, std_mult=ma_std)
            elif if_method == "IF":
                temp_df = base_df[[sensor_col]].dropna().reset_index(drop=True)
                temp_df.columns = ["value"]
                enriched = detect_anomalies_isolation_forest(
                    temp_df, features=["value"], contamination=contamination)
                result_df = pd.DataFrame({"value": series_data})
                result_df["is_anomaly"] = enriched["is_anomaly"]
                result_df["anomaly_score"] = enriched["anomaly_score"]

            # Evaluate
            eval_metrics = evaluate_detection_method(
                gt_series, result_df["is_anomaly"])

            # ── Chart ──
            anomaly_count = int(result_df["is_anomaly"].sum())
            total_points = len(result_df)
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=list(range(total_points)),
                y=result_df["value"],
                mode="lines",
                name=sensor_col,
                line=dict(color="#d4a030", width=1.5),))
            anomaly_pts = result_df[result_df["is_anomaly"]]
            if not anomaly_pts.empty:
                fig.add_trace(go.Scatter(
                    x=anomaly_pts.index,
                    y=anomaly_pts["value"],
                    mode="markers",
                    name="Anomalies",
                    marker=dict(color="var(--color-danger)", size=6, symbol="x",
                                line=dict(width=1, color="#dc2626")),))

            # Threshold bands
            if "threshold_upper" in result_df.columns:
                fig.add_trace(go.Scatter(
                    x=list(range(total_points)),
                    y=result_df["threshold_upper"],
                    mode="lines", name="Upper Threshold",
                    line=dict(color="var(--color-danger)", width=1, dash="dash"),
                ))
                fig.add_trace(go.Scatter(
                    x=list(range(total_points)),
                    y=result_df["threshold_lower"],
                    mode="lines", name="Lower Threshold",
                    line=dict(color="var(--color-danger)", width=1, dash="dash"),
                ))
            elif "rolling_upper" in result_df.columns:
                fig.add_trace(go.Scatter(
                    x=list(range(total_points)),
                    y=result_df["rolling_upper"],
                    mode="lines", name="Upper Band",
                    line=dict(color="var(--color-warning)", width=1, dash="dash"),
                ))
                fig.add_trace(go.Scatter(
                    x=list(range(total_points)),
                    y=result_df["rolling_lower"],
                    mode="lines", name="Lower Band",
                    line=dict(color="var(--color-warning)", width=1, dash="dash"),
                ))

            style_chart(
                fig, height=400, title=f"{sensor_col} — {method} ({anomaly_count}/{total_points} anomalies)")
            render_chart(fig, key="fig_L8516", use_container_width=True)

            # ── Metrics ──
            cols = st.columns(6)
            metric_data = [
                ("Precision", eval_metrics["precision"],
                 eval_metrics["precision"] >= 0.7, ".0%"),
                ("Recall", eval_metrics["recall"],
                 eval_metrics["recall"] >= 0.7, ".0%"),
                ("F1 Score", eval_metrics["f1_score"],
                 eval_metrics["f1_score"] >= 0.7, ".0%"),
                ("Accuracy", eval_metrics["accuracy"],
                 eval_metrics["accuracy"] >= 0.8, ".0%"),
                ("Anomalies Found", anomaly_count, False, "d"),
                ("Ground Truth", eval_metrics["total_true"], False, "d"),
            ]
            for i, (label, val, is_good, fmt) in enumerate(metric_data):
                with cols[i]:
                    bg = "rgba(16,185,129,0.12)" if is_good else (
                        "rgba(239,68,68,0.12)" if not is_good and val < 0.5 else "rgba(245,158,11,0.12)")
                    color = "#34d399" if is_good else (
                        "#f87171" if not is_good and val < 0.5 else "#fbbf24")
                    st.markdown(
                        f'<div style="background:{bg};border-radius:12px;padding:12px;text-align:center;border:1px solid {color}30;">'
                        f'<div style="font-size:0.75rem;color:var(--text-secondary);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;">{label}</div>'
                        f'<div style="font-size:1.1rem;font-weight:700;color:{color};font-family:monospace;">{val:{fmt}}</div>'
                        f"</div>",
                        unsafe_allow_html=True,
                    )

        # ── Method comparison table ──
        with st.expander("How this method works & comparison with other methods"):
            method_descriptions = {
                "Z-Score": (
                    "**Z-Score** measures how many standard deviations a point is from the mean. "
                    "Points with |Z| > threshold (default 3) are flagged."
                    " Best for normally distributed data. Sensitive to outliers in small datasets."
                ),
                "IQR (Tukey's Fences)": (
                    "**IQR Method** uses quartiles to define fences: Q1 - 1.5×IQR and Q3 + 1.5×IQR. "
                    "Robust to extreme outliers since it uses percentiles. "
                    "The standard 1.5 multiplier catches 'outside' points; 3× catches 'far out' points."
                ),
                "Moving Average Band": (
                    "**Moving Average Band** uses a rolling window to compute local mean ± k×std. "
                    "Adapts to local trends. Best for time-series with changing baselines. "
                    "Window size controls smoothness; smaller windows detect local spikes."
                ),
                "Isolation Forest": (
                    "**Isolation Forest** is an ML ensemble method that isolates anomalies by randomly "
                    "partitioning the feature space. Anomalies are isolated with fewer splits. "
                    "Works well with high-dimensional data. Contamination parameter sets expected % of anomalies."
                ),
            }
            desc = method_descriptions.get(method, "")
            st.markdown(desc)

            # Run all methods for comparison
            st.markdown('<div class="section-subheading">Method Comparison</div>', unsafe_allow_html=True)
            methods_to_run = [
                ("Z-Score", detect_anomalies_zscore(series_data,
                 threshold=3.0)["is_anomaly"]),
                ("IQR", detect_anomalies_iqr(series_data)["is_anomaly"]),
                ("MvAvg", detect_anomalies_moving_average(
                    series_data)["is_anomaly"]),
            ]
            if _SKLEARN_AVAILABLE:
                try:
                    temp_df = pd.DataFrame({"value": series_data})
                    if_result = detect_anomalies_isolation_forest(
                        temp_df, features=["value"], contamination=0.05)
                    methods_to_run.append(
                        ("IsoForest", if_result["is_anomaly"]))
                except Exception:
                    pass

            compare_rows = []
            for mname, mpreds in methods_to_run:
                me = evaluate_detection_method(gt_series, mpreds)
                compare_rows.append({
                    "Method": mname,
                    "Precision": f"{me['precision']:.0%}",
                    "Recall": f"{me['recall']:.0%}",
                    "F1": f"{me['f1_score']:.3f}",
                    "Accuracy": f"{me['accuracy']:.0%}",
                    "Found": int(mpreds.sum()),
                })
            if compare_rows:
                st.dataframe(pd.DataFrame(compare_rows),
                             use_container_width=True, hide_index=True)

            # ── Enhanced Analytics: Summary Stats Row ──
            st.html('<div class="gradient-divider"></div>')
            st.html(
                '<div class="section-header">'
                '<div class="section-title">'
                '<span class="title-icon">📊</span>'
                '<span>Analysis Summary</span>'
                '</div>'
                '<div class="section-badge section-badge-ok">INSIGHTS</div>'
                '</div>'
            )

            col_stats = st.columns(4)
            anomaly_rate = anomaly_count / total_points * 100 if total_points > 0 else 0
            with col_stats[0]:
                st.markdown(
                    f'<div class="stat-card info press-effect">'
                    f'<div class="stat-card-label">Data Points</div>'
                    f'<div class="stat-card-value">{total_points:,}</div>'
                    f'<div style="font-size:0.65rem;color:var(--text-muted);">{sensor_col} · {station_filter}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with col_stats[1]:
                anomaly_cls = "danger" if anomaly_rate > 10 else ("warning" if anomaly_rate > 5 else "success")
                st.markdown(
                    f'<div class="stat-card {anomaly_cls} press-effect">'
                    f'<div class="stat-card-label">Anomaly Rate</div>'
                    f'<div class="stat-card-value">{anomaly_rate:.1f}%</div>'
                    f'<div style="font-size:0.65rem;color:var(--text-muted);">{anomaly_count} of {total_points} points</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with col_stats[2]:
                f1_cls = "success" if eval_metrics["f1_score"] >= 0.7 else ("warning" if eval_metrics["f1_score"] >= 0.4 else "danger")
                st.markdown(
                    f'<div class="stat-card {f1_cls} press-effect">'
                    f'<div class="stat-card-label">F1 Score</div>'
                    f'<div class="stat-card-value">{eval_metrics["f1_score"]:.3f}</div>'
                    f'<div style="font-size:0.65rem;color:var(--text-muted);">Method: {method}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with col_stats[3]:
                st.markdown(
                    f'<div class="stat-card info press-effect">'
                    f'<div class="stat-card-label">Method</div>'
                    f'<div class="stat-card-value" style="font-size:1rem;">{method.split("(")[0].strip()}</div>'
                    f'<div style="font-size:0.65rem;color:var(--text-muted);">Threshold-based detection</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            # ── Sensor Box Plot ──
            st.html(
                '<div class="section-header">'
                '<div class="section-title">'
                '<span class="title-icon">📦</span>'
                '<span>Sensor Value Distribution</span>'
                '</div>'
                '<div class="section-badge section-badge-ok">DISTRIBUTION</div>'
                '</div>'
            )

            fig_box = go.Figure()
            fig_box.add_trace(go.Box(
                y=series_data.values,
                name=sensor_col,
                boxmean="sd",
                marker_color="#d4a030",
                line=dict(color="#d4a030", width=2),
                fillcolor="rgba(212,160,48,0.2)",
                boxpoints="outliers",
                jitter=0.3,
                pointpos=-1.8,
            ))
            style_chart(fig_box, height=350, title=f"{sensor_col} - Distribution with Outliers", legend=False)
            fig_box.update_xaxes(showgrid=False)
            fig_box.update_yaxes(title=sensor_col, gridcolor="rgba(30,41,59,0.15)")
            render_chart(fig_box, key="fig_box_anomaly_L9050", use_container_width=True)

            # ── Method Comparison Bar Chart ──
            st.html(
                '<div class="section-header">'
                '<div class="section-title">'
                '<span class="title-icon">⚖️</span>'
                '<span>Method Performance Comparison</span>'
                '</div>'
                '<div class="section-badge section-badge-ok">BENCHMARK</div>'
                '</div>'
            )

            if not compare_rows:
                st.info("No methods available for comparison.")
            else:
                compare_df = pd.DataFrame(compare_rows)
                fig_compare = go.Figure()
                metrics_to_plot = ["Precision", "Recall", "F1", "Accuracy"]
                for met in metrics_to_plot:
                    vals = []
                    for r in compare_df[met]:
                        try:
                            vals.append(float(r.replace("%","").replace(",","")) / 100 if "%" in str(r) else float(r))
                        except Exception:
                            vals.append(0)
                    fig_compare.add_trace(go.Bar(
                        name=met,
                        x=compare_df["Method"],
                        y=vals,
                        hovertemplate="%{x}<br>%{y:.1%}<extra></extra>",
                    ))
                fig_compare.update_layout(
                barmode="group",
                height=300,
                margin=dict(t=20, l=0, r=0, b=0),
                yaxis_tickformat=".0%",
                hovermode="x unified",
                legend=dict(orientation="h", y=1.08, x=0.5, xanchor="center",
                           font=dict(size=10, color="var(--text-secondary)")),
                )
                style_chart(fig_compare, legend=True, showlegend=True)
                render_chart(fig_compare, key="fig_compare_anomaly", use_container_width=True)

            # ── Anomaly Breakdown Table ──
            anomaly_found = result_df[result_df["is_anomaly"]].copy()
            if not anomaly_found.empty:
                st.html(
                    '<div class="section-header">'
                    '<div class="section-title">'
                    '<span class="title-icon">🔍</span>'
                    '<span>Detected Anomalies - Detail View</span>'
                    '</div>'
                    '<div class="section-badge section-badge-ok">FLAGGED</div>'
                    '</div>'
                )
                anomaly_display = anomaly_found[["value"]].copy()
                anomaly_display.columns = [sensor_col]
                score_col = [c for c in ["anomaly_score", "z_score", "score"] if c in anomaly_found.columns]
                if score_col:
                    anomaly_display["Score"] = anomaly_found[score_col[0]]
                    if anomaly_display["Score"].dtype in ["float64", "float32", "int64"]:
                        anomaly_display["Score"] = anomaly_display["Score"].round(3)
                else:
                    anomaly_display["Score"] = ""
                anomaly_display["Index"] = anomaly_found.index
                anomaly_display = anomaly_display[["Index", sensor_col, "Score"]].reset_index(drop=True)

                styled_anom = anomaly_display.style.map(
                    lambda v: "color: var(--color-danger); font-weight: 700",
                    subset=[sensor_col],
                )
                st.dataframe(styled_anom, use_container_width=True, height=min(60 + 30 * len(anomaly_display), 300))


    with tab_decomp:
        col_ds, col_dp = st.columns([1, 1])
        with col_ds:
            decomp_col = st.selectbox(
                "Sensor Column",
                ["sensor_temp", "sensor_vib", "people", "risk_score"],
                key="decomp_col",
            )
        with col_dp:
            decomp_station = st.selectbox(
                "Station", ["All Stations"] + stations, key="decomp_station"
            )

        decomp_period = st.slider("Seasonal Period", 4, 72, 24, 1, key="decomp_period",
                                  help="Number of data points in one seasonal cycle (24 = daily for hourly data)")

        decomp_df = df if decomp_station == "All Stations" else df[df["station"]
                                                                   == decomp_station]
        decomp_series = decomp_df[decomp_col].dropna().reset_index(drop=True)

        if decomp_series.empty:
            st.warning("No data available for the selected filters.")
        else:
            decomp_result = decompose_timeseries(
                decomp_series, period=decomp_period)
            n = len(decomp_result["original"])

            # Component charts
            components = [
                ("Original", decomp_result["original"], "#d4a030"),
                ("Trend", decomp_result["trend"], "#0d9488"),
                ("Seasonal", decomp_result["seasonal"], "var(--color-warning)"),
                ("Residual", decomp_result["residual"], "var(--text-muted)"),
            ]

            fig_decomp = make_subplots(
                rows=4, cols=1, shared_xaxes=True,
                subplot_titles=[c[0] for c in components],
                vertical_spacing=0.04,
            )
            for i, (name, vals, color) in enumerate(components, 1):
                fig_decomp.add_trace(
                    go.Scatter(
                        x=list(range(n)), y=vals,
                        mode="lines", name=name,
                        line=dict(color=color, width=1.5),),
                    row=i, col=1,
                )
            style_chart(fig_decomp, height=700, legend=True, showlegend=True)
            render_chart(fig_decomp, key="fig_decomp_L8656", use_container_width=True)

            # Seasonal pattern
            period = decomp_result["period"]
            seasonal_vals = decomp_result["seasonal"][:period]
            fig_seasonal = go.Figure()
            fig_seasonal.add_trace(go.Scatter(
                x=list(range(period)),
                y=seasonal_vals,
                mode="lines+markers",
                name="Average Seasonal Pattern",
                line=dict(color="var(--color-warning)", width=2),
                marker=dict(size=6, color="var(--color-warning)"),
                fill="tozeroy",
                fillcolor="rgba(245,158,11,0.1)",
            ))
            style_chart(fig_seasonal, height=280,
                        title=f"Average Seasonal Pattern (period={period})", legend=False)
            fig_seasonal.update_xaxes(title="Position in Period")
            render_chart(fig_seasonal, key="fig_seasonal_L8675", use_container_width=True)

            with st.expander("Understanding Time-Series Decomposition"):
                st.markdown(
                    """
                **Time-series decomposition** separates a series into 3 components:
                - **Trend**: Long-term direction (smoothed via moving average)
                - **Seasonal**: Repeating patterns at fixed periods (e.g., daily cycles)
                - **Residual**: Random noise / irregular component (original - trend - seasonal)

                **Analytics application**: If the residual shows patterns (not random), your model is missing structure.
                Large residuals often correspond to anomaly events.
                """)
    
            # ── Enhanced Decomposition: Summary Stats ──
            st.html('<div class="gradient-divider"></div>')
            st.html(
                '<div class="section-header">'
                '<div class="section-title">'
                '<span class="title-icon">📊</span>'
                '<span>Decomposition Summary</span>'
                '</div>'
                '<div class="section-badge section-badge-ok">STATISTICS</div>'
                '</div>'
            )

            # Compute stats
            orig_var = float(np.var(decomp_result["original"]))
            trend_var = float(np.var(decomp_result["trend"][~np.isnan(decomp_result["trend"])])) if not np.all(np.isnan(decomp_result["trend"])) else 0
            residual_std = float(np.nanstd(decomp_result["residual"]))
            seasonal_amp = float(np.nanmax(decomp_result["seasonal"]) - np.nanmin(decomp_result["seasonal"]))
            trend_strength = min(1.0, trend_var / orig_var) if orig_var > 0 else 0
            noise_ratio = residual_std / np.nanstd(decomp_result["original"]) if np.nanstd(decomp_result["original"]) > 0 else 0

            col_ds1, col_ds2, col_ds3, col_ds4 = st.columns(4)
            with col_ds1:
                st.markdown(
                    f'<div class="stat-card info press-effect">'
                    f'<div class="stat-card-label">Trend Strength</div>'
                    f'<div class="stat-card-value">{trend_strength:.1%}</div>'
                    f'<div style="font-size:0.65rem;color:var(--text-muted);">Variance explained by trend</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with col_ds2:
                st.markdown(
                    f'<div class="stat-card warning press-effect">'
                    f'<div class="stat-card-label">Seasonal Amplitude</div>'
                    f'<div class="stat-card-value">{seasonal_amp:.2f}</div>'
                    f'<div style="font-size:0.65rem;color:var(--text-muted);">Peak-to-trough range</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with col_ds3:
                noise_cls = "success" if noise_ratio < 0.3 else ("warning" if noise_ratio < 0.5 else "danger")
                st.markdown(
                    f'<div class="stat-card {noise_cls} press-effect">'
                    f'<div class="stat-card-label">Noise Ratio</div>'
                    f'<div class="stat-card-value">{noise_ratio:.1%}</div>'
                    f'<div style="font-size:0.65rem;color:var(--text-muted);">Residual / Original std</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with col_ds4:
                st.markdown(
                    f'<div class="stat-card info press-effect">'
                    f'<div class="stat-card-label">Period</div>'
                    f'<div class="stat-card-value">{decomp_period}</div>'
                    f'<div style="font-size:0.65rem;color:var(--text-muted);">Seasonal cycle length</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            # ── Original vs Reconstructed Overlay ──
            st.html(
                '<div class="section-header">'
                '<div class="section-title">'
                '<span class="title-icon">🔁</span>'
                '<span>Original vs Reconstructed (Trend + Seasonal)</span>'
                '</div>'
                '<div class="section-badge section-badge-ok">VALIDATION</div>'
                '</div>'
            )

            reconstructed = decomp_result["trend"] + decomp_result["seasonal"]
            fig_overlay = go.Figure()
            fig_overlay.add_trace(go.Scatter(
                x=list(range(n)), y=decomp_result["original"],
                mode="lines", name="Original",
                line=dict(color="#d4a030", width=1.5),
                opacity=0.7,
            ))
            fig_overlay.add_trace(go.Scatter(
                x=list(range(n)), y=reconstructed,
                mode="lines", name="Trend + Seasonal",
                line=dict(color="#0d9488", width=2),
                opacity=0.9,
            ))
            fig_overlay.add_trace(go.Scatter(
                x=list(range(n)), y=decomp_result["residual"],
                mode="lines", name="Residual (shifted)",
                line=dict(color="rgba(148,163,184,0.4)", width=1, dash="dot"),
                yaxis="y2",
            ))
            fig_overlay.update_layout(
                height=350,
                yaxis2=dict(overlaying="y", side="right", showgrid=False, zeroline=False,
                           title=dict(text="Residual", font=dict(size=10, color="var(--text-muted)")),
                           tickfont=dict(size=9, color="var(--text-muted)")),
                hovermode="x unified",
                legend=dict(orientation="h", y=1.08, x=0.5, xanchor="center", font=dict(size=10, color="var(--text-secondary)")),
            )
            style_chart(fig_overlay, legend=True, showlegend=True)
            render_chart(fig_overlay, key="fig_overlay_decomp_L9150", use_container_width=True)

            # ── Residual Distribution ──
            st.html(
                '<div class="section-header">'
                '<div class="section-title">'
                '<span class="title-icon">📈</span>'
                '<span>Residual Distribution Analysis</span>'
                '</div>'
                '<div class="section-badge section-badge-ok">DIAGNOSTIC</div>'
                '</div>'
            )

            residuals_clean = decomp_result["residual"][~np.isnan(decomp_result["residual"])]
            col_rh, col_rq = st.columns(2)
            with col_rh:
                fig_resid_hist = go.Figure()
                fig_resid_hist.add_trace(go.Histogram(
                    x=residuals_clean,
                    nbinsx=30,
                    name="Residuals",
                    marker=dict(color="#0d9488", line=dict(color="#0b7a6e", width=0.5)),
                    opacity=0.8,
                ))
                fig_resid_hist.add_vline(x=0, line=dict(color="var(--color-danger)", width=2, dash="dash"))
                style_chart(fig_resid_hist, height=280, title="Residual Distribution", legend=False)
                fig_resid_hist.update_xaxes(title="Residual Value")
                fig_resid_hist.update_yaxes(title="Frequency")
                render_chart(fig_resid_hist, key="fig_resid_hist_decomp_L9160", use_container_width=True)

            with col_rq:
                # Q-Q plot-like: sorted residuals vs theoretical normal quantiles
                sorted_resid = np.sort(residuals_clean)
                normal_quantiles = (np.arange(1, len(sorted_resid) + 1) - 0.5) / len(sorted_resid)
                try:
                    from scipy import stats as scipy_stats
                    theoretical = scipy_stats.norm.ppf(normal_quantiles, loc=np.nanmean(residuals_clean), scale=np.nanstd(residuals_clean))

                    fig_qq = go.Figure()
                    fig_qq.add_trace(go.Scatter(
                        x=theoretical, y=sorted_resid,
                        mode="markers",
                        name="Residuals",
                        marker=dict(color="#0d9488", size=4, opacity=0.6),
                    ))
                    min_val = min(theoretical.min(), sorted_resid.min())
                    max_val = max(theoretical.max(), sorted_resid.max())
                    fig_qq.add_trace(go.Scatter(
                        x=[min_val, max_val], y=[min_val, max_val],
                        mode="lines", name="Normal",
                        line=dict(color="var(--color-danger)", width=2, dash="dash"),
                    ))
                    style_chart(fig_qq, height=280, title="Q-Q Plot (Residuals vs Normal)", legend=False)
                    fig_qq.update_xaxes(title="Theoretical Quantiles")
                    fig_qq.update_yaxes(title="Sample Quantiles")
                    render_chart(fig_qq, key="fig_qq_decomp_L9180", use_container_width=True)
                except ImportError:
                    st.info("Q-Q plot requires scipy. Install with: pip install scipy")


    with tab_corr:
        corr_cols_input = st.multiselect(
            "Select columns for correlation analysis",
            ["sensor_temp", "sensor_vib", "people", "risk_score"],
            default=["sensor_temp", "sensor_vib", "people", "risk_score"],
            key="corr_cols",
        )
        corr_station = st.selectbox(
            "Station", ["All Stations"] + stations, key="corr_station"
        )

        corr_df = df if corr_station == "All Stations" else df[df["station"] == corr_station]

        if corr_df.empty or len(corr_cols_input) < 2:
            st.info("Select at least 2 sensor columns to compute correlations.")
        else:
            corr_matrix = compute_sensor_correlations(corr_df, corr_cols_input)
            if corr_matrix.empty:
                st.warning("Could not compute correlation matrix.")
            else:
                fig_heatmap = go.Figure(data=go.Heatmap(
                    z=corr_matrix.values,
                    x=corr_matrix.columns,
                    y=corr_matrix.index,
                    colorscale="RdBu_r",
                    zmin=-1, zmax=1,
                    text=np.round(corr_matrix.values, 2),
                    texttemplate="%{text}",
                    textfont=dict(size=12, color="#f8fafc"),))
                style_chart(fig_heatmap, height=400,
                            title="Sensor Correlation Matrix (Pearson r)", legend=False)
                render_chart(fig_heatmap, key="fig_heatmap_L8721", use_container_width=True)

                st.markdown('<div class="section-subheading">Interpretation</div>', unsafe_allow_html=True)
                strong_pairs = []
                for i in range(len(corr_matrix.columns)):
                    for j in range(i + 1, len(corr_matrix.columns)):
                        val = corr_matrix.iloc[i, j]
                        if abs(val) >= 0.5:
                            direction = "strong positive" if val > 0 else "strong negative"
                            strong_pairs.append(
                                f"- **{corr_matrix.columns[i]}** & **{corr_matrix.columns[j]}**: r = {val:.2f} ({direction})")
                if strong_pairs:
                    st.markdown("Strong correlations detected:")
                    for line in strong_pairs:
                        st.markdown(line)
                else:
                    st.markdown(
                        "No strong correlations (|r| ≥ 0.5) between selected sensors at this station.")

        # Health Profile
        st.markdown('<div class="section-subheading">Per-Gate Sensor Health Profile</div>', unsafe_allow_html=True)
        health_station = st.selectbox(
            "Station for Health Profile", stations, key="health_station"
        )
        health_profile = analyze_sensor_health_profile(
            df, station=health_station)
        if health_profile.empty:
            st.info("No health profile data available.")
        else:
            display_cols = ["gate_id", "avg_temp", "avg_vib",
                            "avg_people", "avg_risk", "total_flags"]
            display_cols = [
                c for c in display_cols if c in health_profile.columns]
            st.dataframe(
                health_profile[display_cols].style.map(
                    lambda v: "color: var(--color-danger); font-weight: 700" if isinstance(
                        v, (int, float)) and v > 0 else "",
                    subset=["total_flags"],
                ),
                use_container_width=True,
                hide_index=True,
            )

            # Distribution charts
            st.markdown('<div class="section-subheading">Sensor Distributions with Anomaly Thresholds</div>', unsafe_allow_html=True)
            dist_cols = st.columns(2)
            for idx, scol in enumerate(["sensor_temp", "sensor_vib"][:2]):
                with dist_cols[idx]:
                    if scol in corr_df.columns:
                        vals = corr_df[scol].dropna()
                        q1, q3 = vals.quantile(0.25), vals.quantile(0.75)
                        iqr = q3 - q1
                        low_fence = q1 - 1.5 * iqr
                        high_fence = q3 + 1.5 * iqr

                        fig_hist = go.Figure()
                        fig_hist.add_trace(go.Histogram(
                            x=vals, nbinsx=40, name=scol,
                            marker=dict(color="#d4a030", line=dict(
                                color="#b8861e", width=0.5)),
                            opacity=0.8,
                        ))
                        fig_hist.add_vline(x=low_fence, line=dict(color="var(--color-danger)", width=2, dash="dash"),
                                           annotation_text="IQR Lower Fence", annotation_position="top left")
                        fig_hist.add_vline(x=high_fence, line=dict(color="var(--color-danger)", width=2, dash="dash"),
                                           annotation_text="IQR Upper Fence", annotation_position="top right")
                        style_chart(fig_hist, height=280,
                                    title=f"{scol} Distribution", legend=False)
                        fig_hist.update_xaxes(title=scol)
                        fig_hist.update_yaxes(title="Count")
                        render_chart(fig_hist, key="fig_hist_L8791", use_container_width=True)

        with st.expander("Understanding Correlation Analysis"):
            st.markdown(
                """
            **Pearson correlation coefficient (r)** measures linear relationships between -1 and +1:
            - **r > 0**: Positive correlation (both move in same direction)
            - **r < 0**: Negative correlation (one increases, other decreases)
            - **r ≈ 0**: No linear relationship

            **IQR Fences** on distributions show the Tukey outlier boundaries.
            Points beyond the dashed lines are potential statistical outliers.
            """)

            # ── Enhanced Correlation: Summary Stats ──
            st.html('<div class="gradient-divider"></div>')
            st.html(
                '<div class="section-header">'
                '<div class="section-title">'
                '<span class="title-icon">📊</span>'
                '<span>Correlation Summary</span>'
                '</div>'
                '<div class="section-badge section-badge-ok">INSIGHTS</div>'
                '</div>'
            )

            # Find strongest pair
            strong_pairs_list = []
            strongest_r = 0
            strongest_pair = ("", "")
            pair_count = 0
            for i in range(len(corr_matrix.columns)):
                for j in range(i + 1, len(corr_matrix.columns)):
                    val = corr_matrix.iloc[i, j]
                    pair_count += 1
                    if abs(val) >= 0.5:
                        strong_pairs_list.append((corr_matrix.columns[i], corr_matrix.columns[j], val))
                    if abs(val) > abs(strongest_r):
                        strongest_r = val
                        strongest_pair = (corr_matrix.columns[i], corr_matrix.columns[j])

            col_cs1, col_cs2, col_cs3, col_cs4 = st.columns(4)
            with col_cs1:
                st.markdown(
                    f'<div class="stat-card info press-effect">'
                    f'<div class="stat-card-label">Top Correlation</div>'
                    f'<div class="stat-card-value" style="font-size:1rem;">{strongest_r:.3f}</div>'
                    f'<div style="font-size:0.65rem;color:var(--text-muted);">{strongest_pair[0]} vs {strongest_pair[1]}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with col_cs2:
                direction = "Positive" if strongest_r > 0 else "Negative"
                direction_cls = "success" if direction == "Positive" else "danger"
                st.markdown(
                    f'<div class="stat-card {direction_cls} press-effect">'
                    f'<div class="stat-card-label">Direction</div>'
                    f'<div class="stat-card-value">{direction}</div>'
                    f'<div style="font-size:0.65rem;color:var(--text-muted);">Strongest pair relationship</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with col_cs3:
                strong_count = len(strong_pairs_list)
                st.markdown(
                    f'<div class="stat-card {"danger" if strong_count > 0 else "success"} press-effect">'
                    f'<div class="stat-card-label">Strong Pairs</div>'
                    f'<div class="stat-card-value">{strong_count}</div>'
                    f'<div style="font-size:0.65rem;color:var(--text-muted);">|r| ≥ 0.5 of {pair_count} pairs</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with col_cs4:
                st.markdown(
                    f'<div class="stat-card info press-effect">'
                    f'<div class="stat-card-label">Sensors</div>'
                    f'<div class="stat-card-value" style="font-size:1rem;">{len(corr_cols_input)}</div>'
                    f'<div style="font-size:0.65rem;color:var(--text-muted);">Selected for analysis</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            # ── Scatter Matrix for Sensor Pairs ──
            if len(corr_cols_input) >= 2:
                st.html(
                    '<div class="section-header">'
                    '<div class="section-title">'
                    '<span class="title-icon">🔬</span>'
                    '<span>Sensor Pair Scatter Matrix</span>'
                    '</div>'
                    '<div class="section-badge section-badge-ok">PAIRWISE</div>'
                    '</div>'
                )

                # Build scatter matrix using px.scatter_matrix
                fig_scatter_matrix = px.scatter_matrix(
                    corr_df[corr_cols_input].dropna(),
                    dimensions=corr_cols_input,
                    opacity=0.6,
                    color=corr_df["risk_score"] if "risk_score" in corr_df.columns else None,
                    color_continuous_scale="RdYlGn_r",
                    labels={c: c.replace("_", " ").title() for c in corr_cols_input},
                    height=500,
                )
                fig_scatter_matrix.update_traces(
                    marker=dict(size=4, line=dict(width=0.5, color="rgba(0,0,0,0.2)")),
                    diagonal_visible=False,
                )
                style_chart(fig_scatter_matrix, legend=False)
                render_chart(fig_scatter_matrix, key="fig_scatter_matrix_corr_L9250", use_container_width=True)

            # ── Sorted Correlation Pair Table ──
            if pair_count > 0:
                st.html(
                    '<div class="section-header">'
                    '<div class="section-title">'
                    '<span class="title-icon">📋</span>'
                    '<span>Correlation Pairs — Sorted by Strength</span>'
                    '</div>'
                    '<div class="section-badge section-badge-ok">RANKED</div>'
                    '</div>'
                )

                pair_rows = []
                for i in range(len(corr_matrix.columns)):
                    for j in range(i + 1, len(corr_matrix.columns)):
                        val = corr_matrix.iloc[i, j]
                        strength = "Strong" if abs(val) >= 0.7 else ("Moderate" if abs(val) >= 0.5 else ("Weak" if abs(val) >= 0.3 else "None"))
                        direction = "Positive" if val > 0 else "Negative"
                        pair_rows.append({
                            "Sensor A": corr_matrix.columns[i].replace("_", " ").title(),
                            "Sensor B": corr_matrix.columns[j].replace("_", " ").title(),
                            "R Value": round(val, 3),
                            "Strength": strength,
                            "Direction": direction,
                        })
                pair_df = pd.DataFrame(pair_rows).sort_values("R Value", key=abs, ascending=False).reset_index(drop=True)

                def color_r(val):
                    if abs(val) >= 0.7:
                        return "color: #fca5a5; font-weight: 700" if val > 0 else "color: #93c5fd; font-weight: 700"
                    elif abs(val) >= 0.5:
                        return "color: #fcd34d; font-weight: 600"
                    return "color: var(--text-secondary)"

                styled_pairs = pair_df.style.map(color_r, subset=["R Value"])
                st.dataframe(styled_pairs, use_container_width=True, hide_index=True, height=min(60 + 35 * len(pair_df), 350))

            # ── Health Profile Pie Chart ──
            if not health_profile.empty:
                # Bin avg_risk into categories
                if "avg_risk" in health_profile.columns:
                    health_profile["risk_category"] = pd.cut(
                        health_profile["avg_risk"],
                        bins=[-1, 20, 40, 60, 200],
                        labels=["Low", "Medium", "High", "Critical"]
                    )
                elif "risk_category" not in health_profile.columns:
                    health_profile["risk_category"] = "Unknown"
                st.html(
                    '<div class="section-header">'
                    '<div class="section-title">'
                    '<span class="title-icon">❤️</span>'
                    '<span>Gate Health Overview — {health_station}</span>'
                    '</div>'
                    '<div class="section-badge section-badge-ok">HEALTH</div>'
                    '</div>'
                )

                risk_dist = health_profile["risk_category"].value_counts().reset_index()
                risk_dist.columns = ["Risk Category", "Count"]
                risk_colors = {"Low": "var(--color-emerald)", "Medium": "var(--color-warning)", "High": "var(--color-danger)", "Critical": "#dc2626"}
                fig_health_pie = px.pie(
                    risk_dist,
                    names="Risk Category",
                    values="Count",
                    color="Risk Category",
                    color_discrete_map=risk_colors,
                    hole=0.5,
                    title=f"Gate Risk Distribution — {health_station}",
                )
                style_pie(fig_health_pie)
                fig_health_pie.update_traces(
                    textposition="inside", textinfo="percent+label",
                    textfont_size=11, textfont_color="#f1f5f9",
                    marker_line_color="rgba(30,41,59,0.3)", marker_line_width=1,
                    hovertemplate="<b>%{label}</b><br>Gates: %{value}<br>Share: %{percent}<extra></extra>",
                )
                fig_health_pie.update_layout(height=350)
                render_chart(fig_health_pie, key="fig_health_pie_corr_L9260", use_container_width=True)

            # ── Health Profile Trend (sensor values by gate) ──
            if not health_profile.empty:
                st.html(
                    '<div class="section-header">'
                    '<div class="section-title">'
                    '<span class="title-icon">📈</span>'
                    '<span>Gate-by-Gate Sensor Profile</span>'
                    '</div>'
                    '<div class="section-badge section-badge-ok">PROFILE</div>'
                    '</div>'
                )

                hp_cols = [c for c in ["gate_id", "avg_temp", "avg_vib", "avg_risk", "avg_people", "total_flags"] if c in health_profile.columns]
                if len(hp_cols) >= 3:
                    fig_hp = go.Figure()
                    if "gate_id" in health_profile.columns:
                        gates_arr = health_profile["gate_id"].astype(str).values
                        if "avg_temp" in health_profile.columns:
                            fig_hp.add_trace(go.Bar(
                                name="Avg Temp (°C)",
                                x=gates_arr,
                                y=health_profile["avg_temp"].values,
                                marker_color="#f97316",
                                hovertemplate="Gate: %{x}<br>Temp: %{y:.1f}°C<extra></extra>",
                                yaxis="y",
                            ))
                        if "avg_vib" in health_profile.columns:
                            fig_hp.add_trace(go.Bar(
                                name="Avg Vibration (mm/s)",
                                x=gates_arr,
                                y=health_profile["avg_vib"].values,
                                marker_color="#06b6d4",
                                hovertemplate="Gate: %{x}<br>Vib: %{y:.2f} mm/s<extra></extra>",
                                yaxis="y2",
                            ))
                    fig_hp.update_layout(
                        height=350,
                        barmode="group",
                        hovermode="x unified",
                        yaxis=dict(title="Temperature (°C)", gridcolor="rgba(30,41,59,0.15)"),
                        yaxis2=dict(overlaying="y", side="right", title="Vibration (mm/s)", showgrid=False),
                        legend=dict(orientation="h", y=1.08, x=0.5, xanchor="center", font=dict(size=10, color="var(--text-secondary)")),
                    )
                    style_chart(fig_hp, legend=True, showlegend=True)
                    render_chart(fig_hp, key="fig_hp_bar_corr_L9270", use_container_width=True)



# ═══════════════════════════════════════════════════
# ARCHITECTURE HUB
# ═══════════════════════════════════════════════════
elif active_tab == "viz":
    # Initialize session state
    if "viz_sim" not in st.session_state:
        st.session_state.viz_sim = None
    if "viz_running" not in st.session_state:
        st.session_state.viz_running = False
    if "viz_paused" not in st.session_state:
        st.session_state.viz_paused = False
    if "viz_incidents" not in st.session_state:
        st.session_state.viz_incidents = []
    if "viz_scenario" not in st.session_state:
        st.session_state.viz_scenario = "quick_drill"
    if "viz_rate" not in st.session_state:
        st.session_state.viz_rate = 2
    if "viz_target" not in st.session_state:
        st.session_state.viz_target = 20
    if "viz_tick" not in st.session_state:
        st.session_state.viz_tick = 0
    if "viz_started" not in st.session_state:
        st.session_state.viz_started = False

    arch_tabs = st.tabs(["🏗 System Flow", "⚡ Live Response",
                        "🔍 Vulnerability Scan", "💡 Intelligence"])

    # ─── TAB 1: SYSTEM FLOW ──────────────────────────────────
    with arch_tabs[0]:
        st.markdown(
            '<div class="viz-tab-subtitle">End-to-End Data Pipeline</div>'
            '<div class="viz-tab-desc">'
            'Real-time visualization of how station data flows through the system to the dashboard and response team</div>',
            unsafe_allow_html=True,
        )

        # Animated pipeline
        with st.container():
            pipeline_html = build_architecture_flow_html()
            components.html(pipeline_html, height=330)

        # Live component metrics
        live_metrics = generate_live_metrics()

        # Pipeline subtitle
        st.markdown(
            '<div class="viz-pipeline-sub">12 nodes &middot; 17 data connections &middot; &lt;10 ms end-to-end</div>',
            unsafe_allow_html=True,
        )

        # Live component metrics (set above, reused here)
        st.markdown(
            '<div class="viz-section-header"><div class="viz-section-title">System Component Status</div></div>', unsafe_allow_html=True)

        _LAYER_GROUPS = {
            "DATA TIER": ["stations", "sensors", "mobile_edge", "cloud_api"],
            "PROCESSING TIER": ["ml_engine", "analytics", "maintenance"],
            "DELIVERY TIER": ["notifications", "compliance", "database", "dashboard", "team"],
        }
        _node_icons = {n.id: n.icon for n in ARCHITECTURE_NODES}
        seen_nodes = set()
        for tier_name, node_ids in _LAYER_GROUPS.items():
            tier_ids = [nid for nid in node_ids if nid in live_metrics]
            if not tier_ids:
                continue
            st.markdown(
                f'<div class="viz-tier-header">{tier_name}</div>',
                unsafe_allow_html=True,
            )
            tier_rows = [tier_ids[i:i+3]
                         for i in range(0, len(tier_ids), 3)]
            st.markdown('<div class="viz-comp-grid">', unsafe_allow_html=True)
            for row_idx, row in enumerate(tier_rows):
                cols = st.columns(len(row), gap="medium")
                for ci, cid in enumerate(row):
                    m = live_metrics[cid]
                    seen_nodes.add(cid)
                    uptime = m.get("uptime", 100)
                    icon = _node_icons.get(cid, "")

                    # Status classification
                    if uptime >= 99.5:
                        status_cls = "ok"
                        status_label = "Operational"
                    elif uptime >= 99.0:
                        status_cls = "warn"
                        status_label = "Degraded"
                    else:
                        status_cls = "err"
                        status_label = "Critical"

                    # Build component-specific metrics
                    if cid == "stations":
                        pv = f"{m.get('online', 0)}/{m.get('total', 0)}"
                        pu = ""
                        pl = "Stations Online"
                        s1v = f"{m.get('avg_latency_ms', 0)}ms"
                        s1l = "Latency"
                        s2v = ""
                        s2l = ""
                    elif cid == "sensors":
                        pv = f"{m.get('active', 0)}/{m.get('total', 0)}"
                        pu = ""
                        pl = "Sensors Active"
                        s1v = f"{m.get('data_rate_hz', 0)} Hz"
                        s1l = "Data Rate"
                        s2v = ""
                        s2l = ""
                    elif cid == "cloud_api":
                        pv = f"{m.get('requests_s', 0):,}"
                        pu = "/s"
                        pl = "Requests"
                        s1v = f"{m.get('p99_latency_ms', 0)}ms"
                        s1l = "P99 Latency"
                        s2v = f"{m.get('error_rate', 0):.2f}%"
                        s2l = "Error Rate"
                    elif cid == "analytics":
                        pv = f"{m.get('queries_s', 0):,}"
                        pu = "/s"
                        pl = "Queries"
                        s1v = f"{m.get('avg_batch_size', 0):,}"
                        s1l = "Batch Size"
                        s2v = ""
                        s2l = ""
                    elif cid == "database":
                        pv = str(m.get('connections', 0))
                        pu = ""
                        pl = "Connections"
                        s1v = f"{m.get('queries_s', 0):,}/s"
                        s1l = "Throughput"
                        s2v = f"{m.get('disk_usage_pct', 0):.0f}%"
                        s2l = "Disk Used"
                    elif cid == "dashboard":
                        pv = str(m.get('active_users', 0))
                        pu = ""
                        pl = "Active Users"
                        s1v = str(m.get('widgets_loaded', 0))
                        s1l = "Widgets"
                        s2v = f"{m.get('refresh_rate_s', 0)}s"
                        s2l = "Refresh"
                    elif cid == "team":
                        pv = str(m.get('on_duty', 0))
                        pu = ""
                        pl = "On Duty"
                        s1v = f"{m.get('avg_response_m', 0):.1f}m"
                        s1l = "Avg Response"
                        s2v = str(m.get('active_incidents', 0))
                        s2l = "Active Inc"
                    elif cid == "mobile_edge":
                        pv = str(m.get('active_devices', 0))
                        pu = ""
                        pl = "Active Devices"
                        s1v = f"{m.get('latency_ms', 0)}ms"
                        s1l = "Mobile Latency"
                        s2v = ""
                        s2l = ""
                    elif cid == "notifications":
                        pv = str(m.get('delivery_rate', 0))
                        pu = "%"
                        pl = "Delivery Rate"
                        s1v = f"{m.get('p95_delivery_ms', 0)}ms"
                        s1l = "P95 Delivery"
                        s2v = str(m.get('queued', 0))
                        s2l = "Queued"
                    elif cid == "ml_engine":
                        pv = str(m.get('inferences_s', 0))
                        pu = "/s"
                        pl = "Inferences/s"
                        s1v = f"v{m.get('model_version', '?')}"
                        s1l = "Model"
                        s2v = str(m.get('anomalies_flagged', 0))
                        s2l = "Anomalies"
                    elif cid == "compliance":
                        pv = f"{m.get('audit_events_24h', 0):,}"
                        pu = "24h"
                        pl = "Audit Events"
                        s1v = f"{m.get('retention_days', 0):,}d"
                        s1l = "Retention"
                        s2v = f"{m.get('integrity_pct', 0):.3f}%"
                        s2l = "Integrity"
                    elif cid == "maintenance":
                        pv = str(m.get('jobs_scheduled', 0))
                        pu = "jobs"
                        pl = "Scheduled"
                        s1v = str(m.get('jobs_running', 0))
                        s1l = "Running"
                        s2v = str(m.get('jobs_failed', 0))
                        s2l = "Failed"
                    else:
                        pv = ""
                        pu = ""
                        pl = ""
                        s1v = ""
                        s1l = ""
                        s2v = ""
                        s2l = ""

                    delay = 0.08 * (row_idx * len(row) + ci)
                    with cols[ci]:
                        st.markdown(
                            f'<div class="viz-comp-card" style="animation-delay:{delay}s;">'
                            f'<div class="viz-comp-card-header">'
                            f'<div class="viz-comp-card-left">'
                            f'<span class="viz-comp-card-icon">{icon}</span>'
                            f'<span class="viz-comp-card-name">{cid.replace("_"," ").title()}</span>'
                            f'</div>'
                            f'<div class="viz-comp-status">'
                            f'<div class="viz-comp-status-dot {status_cls}"></div>'
                            f'<span class="viz-comp-status-label {status_cls}">{status_label}</span>'
                            f'</div>'
                            f'</div>'
                            f'<div class="viz-comp-primary">'
                            f'<span class="viz-comp-primary-value">{pv}</span>'
                            + (f'<span class="viz-comp-primary-unit">{pu}</span>' if pu else '')
                            + f'<div class="viz-comp-primary-label">{pl}</div>'
                            f'</div>'
                            f'<div class="viz-comp-uptime">'
                            f'<div class="viz-comp-uptime-track">'
                            f'<div class="viz-comp-uptime-fill {status_cls}" style="width:{min(uptime,100):.2f}%;"></div>'
                            f'</div>'
                            f'<span class="viz-comp-uptime-text">{uptime:.2f}%</span>'
                            f'</div>'
                            f'<div class="viz-comp-secondary">'
                            f'<div class="viz-comp-secondary-item">'
                            f'<div class="viz-comp-secondary-value">{s1v}</div>'
                            f'<div class="viz-comp-secondary-label">{s1l}</div>'
                            f'</div>'
                            + (f'<div class="viz-comp-secondary-item">'
                               f'<div class="viz-comp-secondary-value">{s2v}</div>'
                               f'<div class="viz-comp-secondary-label">{s2l}</div>'
                               f'</div>' if s2v else '')
                            + f'</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

            st.html('</div>')

        # Quick station status grid
        st.markdown(
            '<div class="viz-section-header"><div class="viz-section-title">Station Health Overview</div></div>', unsafe_allow_html=True)
        from data.sample_data import get_station_df
        sdf = get_station_df()
        s_cols = st.columns(5)
        for i, srow in sdf.iterrows():
            with s_cols[i % 5]:
                sts = srow.get("status", "Established")
                dot_color = "var(--color-emerald)" if sts in ("Established", "Present") else (
                    "var(--color-warning)" if sts == "Expanding" else "var(--text-muted)")
                st.markdown(
                    '<span class="viz-health-pill" '
                    f'style="border-color:{dot_color}40;color:{dot_color};">'
                    f'{srow["station"]}</span>',
                    unsafe_allow_html=True,
                )

        # Architecture Network Graph
        st.markdown(
            '<div class="viz-section-header"><div class="viz-section-title">System Topology</div></div>', unsafe_allow_html=True)
        net_cols = st.columns([1.6, 1])
        with net_cols[0]:
            _node_positions = {
                "stations":     (0.048, 0.50),
                "sensors":      (0.152, 0.50),
                "mobile_edge":  (0.152, 0.22),
                "cloud_api":    (0.280, 0.50),
                "ml_engine":    (0.306, 0.78),
                "analytics":    (0.418, 0.30),
                "maintenance":  (0.418, 0.70),
                "database":     (0.548, 0.70),
                "notifications": (0.572, 0.50),
                "compliance":   (0.704, 0.78),
                "dashboard":    (0.820, 0.50),
                "team":         (0.944, 0.50),
            }
            _node_colors = {
                "stations":     "#d4a030",
                "sensors":      "#0d9488",
                "mobile_edge":  "#6366f1",
                "cloud_api":    "#e8b84b",
                "ml_engine":    "#ec4899",
                "analytics":    "var(--color-warning)",
                "maintenance":  "var(--color-emerald)",
                "database":     "#0f766e",
                "notifications": "var(--color-danger)",
                "compliance":   "var(--text-secondary)",
                "dashboard":    "#d4a030",
                "team":         "var(--color-danger)",
            }
            _node_icons_list = [
                "🚉", "📡", "📱", "☁️", "🤖", "📊", "🔧",
                "🗄️", "🔔", "📋", "📈", "👥",
            ]
            fig_net = go.Figure()
            for src, dst in [
                ("stations", "sensors"),
                ("stations", "mobile_edge"),
                ("sensors", "cloud_api"),
                ("mobile_edge", "cloud_api"),
                ("cloud_api", "analytics"),
                ("cloud_api", "database"),
                ("cloud_api", "ml_engine"),
                ("cloud_api", "compliance"),
                ("ml_engine", "analytics"),
                ("ml_engine", "notifications"),
                ("analytics", "dashboard"),
                ("analytics", "maintenance"),
                ("maintenance", "notifications"),
                ("database", "dashboard"),
                ("notifications", "dashboard"),
                ("notifications", "mobile_edge"),
                ("dashboard", "team"),
            ]:
                sx, sy = _node_positions[src]
                dx, dy = _node_positions[dst]
                fig_net.add_trace(go.Scatter(
                    x=[sx, dx], y=[sy, dy], mode="lines",
                    line=dict(color="rgba(148,163,184,0.3)",
                              width=1.5, dash="dot"),showlegend=False,
                ))
            node_ids = list(_node_positions.keys())
            nx = [_node_positions[n][0] for n in node_ids]
            ny = [_node_positions[n][1] for n in node_ids]
            nc = [_node_colors[n] for n in node_ids]
            fig_net.add_trace(go.Scatter(
                x=nx, y=ny, mode="markers+text",
                marker=dict(size=28, color=nc, line=dict(
                    width=2, color="rgba(255,255,255,0.2)")),
                text=_node_icons_list,
                textfont=dict(size=16),
                textposition="middle center",
                hovertext=[n.replace("_", " ").title() for n in node_ids],showlegend=False,
            ))
            fig_net.update_layout(
                template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=10, r=10, t=10, b=10), height=260,
                xaxis=dict(visible=False, range=[-0.05, 1.05]),
                yaxis=dict(visible=False, range=[0.1, 0.9]),
            )
            render_chart(fig_net, key="fig_net_L9145", use_container_width=True)

        with net_cols[1]:
            # Tech Stack Treemap
            tech_data = [
                {"category": "Frontend", "tech": "Streamlit", "value": 35},
                {"category": "Frontend", "tech": "Plotly", "value": 25},
                {"category": "Backend", "tech": "Python 3.10", "value": 45},
                {"category": "Backend", "tech": "Pandas", "value": 20},
                {"category": "Backend", "tech": "NumPy", "value": 15},
                {"category": "Data", "tech": "PostgreSQL", "value": 30},
                {"category": "Data", "tech": "Redis Cache", "value": 15},
                {"category": "Data", "tech": "RabbitMQ", "value": 10},
                {"category": "ML", "tech": "scikit-learn", "value": 20},
                {"category": "ML", "tech": "Polars", "value": 12},
                {"category": "Mobile", "tech": "Streamlit Mobile", "value": 15},
                {"category": "Notifications",
                    "tech": "SMTP / SMS Gateway", "value": 8},
                {"category": "Compliance", "tech": "Audit Logger", "value": 10},
                {"category": "Infra", "tech": "Docker", "value": 25},
                {"category": "Infra", "tech": "Kubernetes", "value": 18},
                {"category": "Reports", "tech": "ReportLab", "value": 10},
                {"category": "Reports", "tech": "Matplotlib", "value": 8},
            ]
            td_df = pd.DataFrame(tech_data)
            fig_tech = px.treemap(
                td_df, path=["category", "tech"], values="value",
                color="value", color_continuous_scale="ylorrd",
            )
            fig_tech.update_layout(
                template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=5, r=50, t=28, b=5), height=260,
                title=dict(text="Technology Stack",
                           font=dict(size=11, color="var(--text-secondary)")),
                coloraxis=dict(
                    colorbar=dict(
                        title=dict(text="Usage", font=dict(size=9, color="#94a3b8")),
                        tickfont=dict(size=8, color="#94a3b8"),
                        thickness=8, len=0.6,
                    ),
                    showscale=True,
                ),
            )
            fig_tech.update_traces(
                textinfo="label+percent entry", textfont=dict(size=9))
            render_chart(fig_tech, key="fig_tech_L9190", use_container_width=True)

        # Data Pipeline Metrics — multi-chart row
        st.markdown(
            '<div class="viz-section-header"><div class="viz-section-title">Live Pipeline Metrics <span class="viz-section-muted">(last 60s — simulated)</span></div></div>',
            unsafe_allow_html=True,
        )

        # Simulated multi-metric history
        hist_req = st.session_state.get("viz_hist_req")
        hist_lat = st.session_state.get("viz_hist_lat")
        hist_err = st.session_state.get("viz_hist_err")
        if hist_req is None:
            import random as _r
            hist_req = [round(_r.uniform(800, 1500), 0) for _ in range(60)]
            hist_lat = [round(_r.uniform(40, 90), 1) for _ in range(60)]
            hist_err = [round(_r.uniform(0.01, 0.15), 3) for _ in range(60)]
            st.session_state.viz_hist_req = hist_req
            st.session_state.viz_hist_lat = hist_lat
            st.session_state.viz_hist_err = hist_err
        else:
            _rr = __import__("random")
            hist_req = hist_req[1:] + [round(_rr.uniform(800, 1500), 0)]
            hist_lat = hist_lat[1:] + [round(_rr.uniform(40, 90), 1)]
            hist_err = hist_err[1:] + [round(_rr.uniform(0.01, 0.15), 3)]
            st.session_state.viz_hist_req = hist_req
            st.session_state.viz_hist_lat = hist_lat
            st.session_state.viz_hist_err = hist_err

        mcol1, mcol2 = st.columns([2.2, 1], gap="small")
        with mcol1:
            x_axis = list(range(len(hist_req)))
            fig_metrics = go.Figure()
            fig_metrics.add_trace(go.Scatter(
                x=x_axis, y=hist_req, mode="lines",
                name="Requests/s", line=dict(color="#d4a030", width=2, shape="spline"),
                fill="tozeroy", fillcolor="rgba(212,160,48,0.08)",yaxis="y",
            ))
            fig_metrics.add_trace(go.Scatter(
                x=x_axis, y=hist_lat, mode="lines",
                name="P99 Latency", line=dict(color="#6366f1", width=2, shape="spline"),
                fill="tozeroy", fillcolor="rgba(99,102,241,0.08)",yaxis="y2",
            ))
            fig_metrics.add_trace(go.Scatter(
                x=x_axis, y=[v * 100 for v in hist_err], mode="lines",
                name="Error Rate", line=dict(color="var(--color-danger)", width=1.5, shape="spline"),yaxis="y3",
            ))
            avg_req = sum(hist_req) / len(hist_req)
            fig_metrics.add_hline(
                y=avg_req,
                line=dict(color="rgba(212,160,48,0.25)", width=1, dash="dash"),
                annotation_text=f'{avg_req:.0f}/s',
                annotation_font=dict(size=8, color="var(--text-muted)"),
            )
            fig_metrics.update_layout(
                template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=10, r=10, t=10, b=10), height=170,
                xaxis=dict(visible=False, range=[0, 61]),
                yaxis=dict(
                    showgrid=True, gridcolor="rgba(148,163,184,0.06)", title="", visible=False),
                yaxis2=dict(overlaying="y", side="right",
                            showgrid=False, title="", visible=False),
                yaxis3=dict(overlaying="y", side="right", showgrid=False,
                            title="", visible=False, position=0.96),
                hovermode="x unified",
                legend=dict(orientation="h", y=1.1, x=0,
                            font=dict(size=10, color="var(--text-secondary)")),
            )
            render_chart(fig_metrics, key="fig_metrics_L9258", use_container_width=True)

        with mcol2:
            ok_n = sum(1 for v in live_metrics.values()
                       if v.get("uptime", 0) >= 99.5)
            warn_n = sum(1 for v in live_metrics.values()
                         if 99.0 <= v.get("uptime", 0) < 99.5)
            err_n = sum(1 for v in live_metrics.values()
                        if v.get("uptime", 0) < 99.0)
            fig_donut = go.Figure(go.Pie(
                values=[ok_n, warn_n, err_n],
                labels=["Healthy", "Degraded", "Critical"],
                marker=dict(colors=["var(--color-emerald)", "var(--color-warning)", "var(--color-danger)"]),
                hole=0.6, textinfo="label+value",
                textfont=dict(size=9, color="var(--text-secondary)"),
                hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{percent}<extra></extra>",))
            fig_donut.update_layout(
                template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=5, r=5, t=5, b=5), height=170,
                showlegend=True,
                legend=dict(
                    orientation="h", y=-0.3, x=0.5, xanchor="center",
                    font=dict(size=8, color="#94a3b8"),
                    itemclick=False, itemdoubleclick=False,
                ),
                annotations=[dict(
                    text=f"{ok_n}/{ok_n + warn_n + err_n}", x=0.5, y=0.5,
                    font=dict(size=18, color="var(--text-primary)"), showarrow=False,
                )],
            )
            render_chart(fig_donut, key="fig_donut_L9288", use_container_width=True)

    # ─── TAB 2: LIVE RESPONSE ────────────────────────────────
    with arch_tabs[1]:
        # Control bar
        st.markdown('<div class="viz-control-bar">', unsafe_allow_html=True)
        ccol1, ccol2, ccol3, ccol4, ccol5, ccol6 = st.columns(
            [1, 1, 1.2, 1, 0.8, 1.5])
        with ccol1:
            if st.button("▶ Start", key="viz_start", use_container_width=True,
                         disabled=st.session_state.viz_running):
                st.session_state.viz_sim = SimulationSession(
                    target_incidents=st.session_state.viz_target,
                    seed=42,
                )
                st.session_state.viz_sim.start()
                st.session_state.viz_running = True
                st.session_state.viz_paused = False
                st.session_state.viz_incidents = []
                st.session_state.viz_tick = 0
                st.session_state.viz_started = True
                st.rerun()
        with ccol2:
            if st.button("⏸ Pause", key="viz_pause", use_container_width=True,
                         disabled=not st.session_state.viz_running or st.session_state.viz_paused):
                if st.session_state.viz_sim:
                    st.session_state.viz_sim.pause()
                st.session_state.viz_paused = True
                st.rerun()
        with ccol3:
            if st.button("▶ Resume", key="viz_resume", use_container_width=True,
                         disabled=not st.session_state.viz_paused):
                if st.session_state.viz_sim:
                    st.session_state.viz_sim.resume()
                st.session_state.viz_paused = False
                st.rerun()
        with ccol4:
            if st.button("⏹ Stop", key="viz_stop", use_container_width=True,
                         disabled=not st.session_state.viz_running):
                if st.session_state.viz_sim:
                    st.session_state.viz_sim.stop()
                st.session_state.viz_running = False
                st.session_state.viz_paused = False
                st.rerun()
        with ccol5:
            if st.button("↺ Reset", key="viz_reset", use_container_width=True):
                st.session_state.viz_sim = None
                st.session_state.viz_running = False
                st.session_state.viz_paused = False
                st.session_state.viz_incidents = []
                st.session_state.viz_tick = 0
                st.session_state.viz_started = False
                st.rerun()
        with ccol6:
            st.session_state.viz_scenario = st.selectbox(
                "Scenario", ["quick_drill", "critical_hours", "night_shift",
                             "multi_station_cascade", "weather_event", "shift_simulation"],
                label_visibility="collapsed",
                key="viz_scenario_sel",
                disabled=st.session_state.viz_running,
            )
        st.html('</div>')

        # Simulation tick
        sim = st.session_state.viz_sim
        if st.session_state.viz_running and sim and not st.session_state.viz_paused:
            for _ in range(min(st.session_state.viz_rate, 5)):
                inc = sim.generate_single()
                if inc:
                    sim.assign_incident(inc)
                    if st.session_state.viz_tick % 3 == 0 and inc.status == "assigned":
                        sim.resolve_incident(inc, success=True)
                    st.session_state.viz_incidents.append(inc)
                    st.session_state.viz_tick += 1
                if len(st.session_state.viz_incidents) >= st.session_state.viz_target:
                    sim.stop()
                    st.session_state.viz_running = False
                    break
            import time
            time.sleep(0.3)
            st.rerun()

        # KPI strip
        sim_data = None
        if sim:
            try:
                sim_data = sim.to_dataframe()
            except Exception:
                sim_data = pd.DataFrame()
        total_inc = len(st.session_state.viz_incidents)
        resolved = sum(
            1 for i in st.session_state.viz_incidents if i.status == "resolved")
        failed = sum(
            1 for i in st.session_state.viz_incidents if i.status == "failed")
        critical = sum(
            1 for i in st.session_state.viz_incidents if i.severity == "CRITICAL")
        active = sum(1 for i in st.session_state.viz_incidents if i.status in (
            "pending", "assigned"))
        avg_resp = 0.0
        resp_times = [
            i.resolution_time_min for i in st.session_state.viz_incidents if i.resolution_time_min > 0]
        if resp_times:
            avg_resp = sum(resp_times) / len(resp_times)
        success_rate = (resolved / total_inc * 100) if total_inc > 0 else 0

        kpi_cols = st.columns(6)
        kpi_data = [
            ("Total", str(total_inc), "#d4a030"),
            ("Active", str(active), "var(--color-warning)"),
            ("Resolved", str(resolved), "#0d9488"),
            ("Failed", str(failed), "var(--color-danger)"),
            ("Avg Resp", f"{avg_resp:.1f}m", "#0d9488"),
            ("Success", f"{success_rate:.0f}%", "#d4a030"),
        ]
        for i, (klabel, kval, kcolor) in enumerate(kpi_data):
            with kpi_cols[i]:
                st.markdown(
                    f'<div class="viz-kpi-card">'
                    f'<div class="viz-kpi-value" style="color:{kcolor};">{kval}</div>'
                    f'<div class="viz-kpi-label">{klabel}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        # Main content: feed + team panel
        feed_col, team_col = st.columns([1.5, 1])
        with feed_col:
            st.markdown(
                '<div class="viz-sub-title">Incident Feed</div>', unsafe_allow_html=True)
            feed_html = '<div class="viz-feed-container">'
            for inc in reversed(st.session_state.viz_incidents[-30:]):
                sev = inc.severity
                sts = inc.status
                sev_label = {"CRITICAL": "🔴", "WARNING": "🟡",
                             "INFO": "🔵"}.get(sev, "⚪")
                sts_label = sts.upper()
                feed_html += f'<div class="viz-incident-card severity-{sev} status-{sts}">'
                feed_html += f'<div class="viz-incident-time">{sev_label}</div>'
                feed_html += f'<div class="viz-incident-body">'
                feed_html += f'<div class="viz-incident-type">{inc.incident_type} @ {inc.station}</div>'
                feed_html += f'<div class="viz-incident-desc">{inc.description[:60]}</div>'
                feed_html += f'</div>'
                feed_html += f'<div class="viz-incident-persona">{inc.assigned_persona or "—"}</div>'
                feed_html += f'<div class="viz-incident-status">{sts_label}</div>'
                feed_html += f'</div>'
            feed_html += '</div>'
            st.markdown(feed_html, unsafe_allow_html=True)

        with team_col:
            st.markdown('<div class="viz-sub-title">Team Status</div>',
                        unsafe_allow_html=True)
            personas = get_simulation_personas() if not sim else sim.personas
            for p in personas:
                load_pct = min(p.current_assigned / 3.0 * 100,
                               100) if hasattr(p, "current_assigned") else 0
                fatigue = getattr(p, "fatigue", 0)
                fat_color = "var(--color-emerald)" if fatigue < 30 else (
                    "var(--color-warning)" if fatigue < 60 else "var(--color-danger)")
                bar_color = "#d4a030" if load_pct < 50 else (
                    "var(--color-warning)" if load_pct < 80 else "var(--color-danger)")
                sr = getattr(p, "success_rate", 100)
                st.markdown(
                    f'<div class="viz-persona-card">'
                    f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                    f'<div><div class="viz-persona-name">{p.name}</div>'
                    f'<div class="viz-persona-role">{p.role}</div></div>'
                    f'<div style="display:flex;gap:6px;align-items:center;">'
                    f'<span style="font-size:0.55rem;color:{fat_color};font-weight:600;">{fatigue:.0f}%</span>'
                    f'<span style="font-size:0.55rem;color:var(--text-muted);">{sr:.0f}%</span>'
                    f'</div></div>'
                    f'<div class="viz-persona-load">'
                    f'<div class="viz-persona-load-bar" style="width:{load_pct}%;background:{bar_color};"></div>'
                    f'</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        # Live charts
        st.markdown(
            '<div class="viz-section-header"><div class="viz-section-title">Live Analytics</div></div>', unsafe_allow_html=True)
        chart_cols = st.columns(3)
        if st.session_state.viz_incidents:
            df_inc = pd.DataFrame([{"severity": i.severity, "status": i.status,
                                    "response_time": i.response_time_min,
                                    "persona": i.assigned_persona or "Unassigned"}
                                   for i in st.session_state.viz_incidents])
            with chart_cols[0]:
                sev_counts = df_inc["severity"].value_counts().reindex(
                    ["CRITICAL", "WARNING", "INFO"], fill_value=0)
                fig_sev = go.Figure(data=[go.Pie(
                    labels=sev_counts.index.tolist(),
                    values=sev_counts.values.tolist(),
                    marker=dict(colors=["var(--color-danger)", "var(--color-warning)", "#d4a030"]),
                    hole=0.5,
                    textinfo="label+percent",
                    textfont=dict(size=10, color="var(--text-primary)"),
                )])
                fig_sev.update_layout(
                    template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=10, r=10, t=30, b=10), height=220,
                    title=dict(text="Severity Distribution",
                               font=dict(size=11, color="var(--text-secondary)")),
                    showlegend=False,
                )
                render_chart(fig_sev, key="fig_sev_L9492", use_container_width=True)
            with chart_cols[1]:
                status_counts = df_inc["status"].value_counts()
                fig_st = go.Figure(data=[go.Bar(
                    x=status_counts.index.tolist(),
                    y=status_counts.values.tolist(),
                    marker=dict(
                        color=["#0d9488", "var(--color-warning)", "var(--color-danger)", "#d4a030"]),
                )])
                fig_st.update_layout(
                    template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=10, r=10, t=30, b=10), height=220,
                    title=dict(text="Outcome Breakdown",
                               font=dict(size=11, color="var(--text-secondary)")),
                    xaxis=dict(showgrid=False, title=""),
                    yaxis=dict(showgrid=True,
                               gridcolor="rgba(148,163,184,0.1)", title=""),
                )
                render_chart(fig_st, key="fig_st_L9510", use_container_width=True)
            with chart_cols[2]:
                pcounts = df_inc["persona"].value_counts().head(8)
                fig_per = go.Figure(data=[go.Bar(
                    x=pcounts.values.tolist(),
                    y=pcounts.index.tolist(),
                    orientation="h",
                    marker=dict(color="#d4a030"),
                )])
                fig_per.update_layout(
                    template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=10, r=10, t=30, b=10), height=220,
                    title=dict(text="Persona Workload",
                               font=dict(size=11, color="var(--text-secondary)")),
                    xaxis=dict(showgrid=True,
                               gridcolor="rgba(148,163,184,0.1)", title=""),
                    yaxis=dict(showgrid=False, title=""),
                )
                render_chart(fig_per, key="fig_per_L9528", use_container_width=True)
        else:
            for c in chart_cols:
                c.markdown(
                    '<div class="viz-empty-state">'
                    '▶ Start a simulation to see live charts</div>',
                    unsafe_allow_html=True,
                )

        # Session summary
        if st.session_state.viz_started and not st.session_state.viz_running and sim:
            st.markdown(
                '<div class="viz-section-header"><div class="viz-section-title">Session Summary</div></div>', unsafe_allow_html=True)
            try:
                sim_df = sim.to_dataframe()
                if not sim_df.empty:
                    st.dataframe(sim_df[["id", "station", "incident_type", "severity", "status",
                                         "assigned_persona", "response_time_min"]].tail(10),
                                 use_container_width=True, hide_index=True)
            except Exception:
                pass

        # Response Time Trend Chart
        if st.session_state.viz_incidents and resp_times:
            st.markdown('<div class="viz-section-header"><div class="viz-section-title">Live Analytics <span class="viz-section-muted">— Response Time &amp; Team Metrics</span></div></div>', unsafe_allow_html=True)
            rt_cols = st.columns(2)
            with rt_cols[0]:
                fig_rt = go.Figure()
                cum_times = []
                cum_sum = 0
                for i, inc in enumerate(st.session_state.viz_incidents):
                    if inc.resolution_time_min > 0:
                        cum_sum = inc.resolution_time_min
                        cum_times.append((i, inc.resolution_time_min))
                if cum_times:
                    x_vals, y_vals = zip(*cum_times)
                    fig_rt.add_trace(go.Scatter(
                        x=x_vals, y=y_vals, mode="lines+markers",
                        name="Response Time",
                        line=dict(color="#0d9488", width=2, shape="spline"),
                        marker=dict(size=5, color="#0d9488",
                                    line=dict(width=1, color="rgba(255,255,255,0.3)")),
                        fill="tozeroy", fillcolor="rgba(13,148,136,0.08)",))
                    fig_rt.add_hline(
                        y=sum(y_vals)/len(y_vals),
                        line=dict(color="rgba(239,68,68,0.4)",
                                  width=1, dash="dash"),
                        annotation_text=f"Avg: {sum(y_vals)/len(y_vals):.2f}m",
                        annotation_font=dict(size=9, color="var(--color-danger)"),
                    )
                fig_rt.update_layout(
                    template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=10, r=10, t=30, b=10), height=220,
                    title=dict(text="Response Time by Incident",
                               font=dict(size=11, color="var(--text-secondary)")),
                    xaxis=dict(title="", showgrid=False),
                    yaxis=dict(title="Minutes", showgrid=True,
                               gridcolor="rgba(148,163,184,0.08)"),
                    hovermode="x unified",
                )
                render_chart(fig_rt, key="fig_rt_L9588", use_container_width=True)

            with rt_cols[1]:
                # Persona Fatigue Scorecard (horizontal bar)
                fat_data = [{"persona": p.name, "fatigue": getattr(p, "fatigue", 0),
                             "load": getattr(p, "current_assigned", 0),
                             "role": p.role[:12]} for p in personas]
                fat_data.sort(key=lambda x: x["fatigue"], reverse=True)
                fat_df = pd.DataFrame(fat_data)
                fig_fat = go.Figure()
                for _, row in fat_df.iterrows():
                    fcol = "var(--color-emerald)" if row["fatigue"] < 30 else (
                        "var(--color-warning)" if row["fatigue"] < 60 else "var(--color-danger)")
                    fig_fat.add_trace(go.Bar(
                        x=[row["fatigue"]], y=[row["persona"]],
                        orientation="h", name=row["persona"],
                        marker=dict(color=fcol),
                        showlegend=False,
                    ))
                fig_fat.update_layout(
                    template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=10, r=10, t=30, b=10), height=220,
                    title=dict(text="Team Fatigue Levels",
                               font=dict(size=11, color="var(--text-secondary)")),
                    xaxis=dict(title="Fatigue %", range=[0, 100], showgrid=True,
                               gridcolor="rgba(148,163,184,0.08)", tickfont=dict(size=9)),
                    yaxis=dict(title="", showgrid=False,
                               tickfont=dict(size=8)),
                    barmode="overlay",
                )
                render_chart(fig_fat, key="fig_fat_L9618", use_container_width=True)

        # Incident Timeline (Gantt-style) & Competency Heatmap
        if st.session_state.viz_incidents:
            tl_cols = st.columns([1.3, 1])
            with tl_cols[0]:
                tl_data = [{"id": i.id[-6:], "station": i.station.split()[0],
                            "type": i.incident_type, "severity": i.severity,
                            "idx": idx, "duration": max(i.resolution_time_min, 0.5),
                            "color": {"CRITICAL": "var(--color-danger)", "WARNING": "var(--color-warning)", "INFO": "#d4a030"}.get(i.severity, "var(--text-muted)")}
                           for idx, i in enumerate(st.session_state.viz_incidents[-25:])]
                tl_df = pd.DataFrame(tl_data)
                fig_tl = go.Figure()
                for _, row in tl_df.iterrows():
                    fig_tl.add_trace(go.Bar(
                        x=[row["duration"]], y=[f"#{row['idx']}"],
                        orientation="h", base=0,
                        marker=dict(color=row["color"], line=dict(width=0)),
                        showlegend=False,
                        width=0.7,
                    ))
                fig_tl.update_layout(
                    template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=10, r=10, t=30, b=10), height=220,
                    title=dict(text="Incident Timeline (duration)",
                               font=dict(size=11, color="var(--text-secondary)")),
                    xaxis=dict(title="Minutes", showgrid=True,
                               gridcolor="rgba(148,163,184,0.08)"),
                    yaxis=dict(title="", showgrid=False, autorange="reversed"),
                    barmode="overlay",
                )
                render_chart(fig_tl, key="fig_tl_L9649", use_container_width=True)

            with tl_cols[1]:
                # Competency Heatmap
                if sim and hasattr(sim, "competency_scores"):
                    try:
                        cs = sim.competency_scores
                        if cs:
                            chm_data = [{"Persona": c.persona_name.split()[0],
                                         "Speed": c.speed_score, "Accuracy": c.accuracy_score,
                                         "Critical": c.critical_score, "Specialty": c.specialty_score,
                                         "Escalation": c.escalation_score, "Balance": c.balance_score}
                                        for c in cs]
                            chm_df = pd.DataFrame(chm_data)
                            dims = ["Speed", "Accuracy", "Critical",
                                    "Specialty", "Escalation", "Balance"]
                            z_vals = chm_df[dims].values.T.tolist()
                            fig_chm = go.Figure(data=go.Heatmap(
                                z=z_vals,
                                x=chm_df["Persona"].tolist(),
                                y=dims,
                                colorscale="plasma",
                                zmin=0, zmax=100,
                                text=[[f"{v:.0f}" for v in row]
                                      for row in z_vals],
                                texttemplate="%{text}",
                                textfont=dict(size=8, color="#f8fafc"),))
                            fig_chm.update_layout(
                                template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                margin=dict(l=10, r=10, t=30, b=10), height=220,
                                title=dict(text="Competency Matrix",
                                           font=dict(size=11, color="var(--text-secondary)")),
                                xaxis=dict(tickfont=dict(
                                    size=7), tickangle=-30),
                                yaxis=dict(tickfont=dict(size=8)),
                            )
                            render_chart(fig_chm, key="fig_chm_L9685", use_container_width=True)
                    except Exception:
                        pass

    # ─── TAB 3: VULNERABILITY SCAN ──────────────────────────
    with arch_tabs[2]:
        sim_metrics = {}
        root_causes = {}
        if sim and hasattr(sim, "metrics") and sim.metrics:
            sim_metrics = sim.metrics
            root_causes = sim_metrics.get("root_causes", {})

        tech_loops, oper_loops = analyze_loopholes(
            {"metrics": sim_metrics} if sim_metrics else None
        )

        # Summary
        vuln_summary = [
            ("Critical", sum(1 for l in tech_loops +
             oper_loops if l.severity == "critical"), "var(--color-danger)"),
            ("High", sum(1 for l in tech_loops +
             oper_loops if l.severity == "high"), "var(--color-warning)"),
            ("Medium", sum(1 for l in tech_loops +
             oper_loops if l.severity == "medium"), "#d4a030"),
            ("Low", sum(1 for l in tech_loops +
             oper_loops if l.severity == "low"), "var(--text-muted)"),
        ]
        vcols = st.columns(4)
        for vi, (vlabel, vcount, vcolor) in enumerate(vuln_summary):
            with vcols[vi]:
                st.markdown(
                    f'<div class="viz-kpi-card">'
                    f'<div class="viz-kpi-value" style="color:{vcolor};font-size:1.3rem;">{vcount}</div>'
                    f'<div class="viz-kpi-label">{vlabel}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        st.markdown(
            '<div class="viz-section-header"><div class="viz-section-title">Root Cause Analysis</div></div>', unsafe_allow_html=True)
        rc_cols = st.columns(2)
        with rc_cols[0]:
            if root_causes:
                rc_df = pd.DataFrame(sorted(root_causes.items(), key=lambda x: x[1], reverse=True),
                                     columns=["Root Cause", "Count"])
                fig_rc = go.Figure(data=[go.Bar(
                    x=rc_df["Count"].tolist(),
                    y=rc_df["Root Cause"].tolist(),
                    orientation="h",
                    marker=dict(color=["var(--color-danger)", "var(--color-warning)",
                                "#d4a030", "#0d9488", "var(--text-muted)"]),
                )])
                fig_rc.update_layout(
                    template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=10, r=10, t=10, b=10), height=250,
                    xaxis=dict(showgrid=True,
                               gridcolor="rgba(148,163,184,0.1)", title=""),
                    yaxis=dict(showgrid=False, title=""),
                )
                render_chart(fig_rc, key="fig_rc_L9744", use_container_width=True)
            else:
                st.markdown(
                    '<div class="viz-empty-state">Run a Live Response simulation to see root cause analysis</div>', unsafe_allow_html=True)
        with rc_cols[1]:
            tech_count = len(tech_loops)
            st.markdown(
                '<div class="glass-panel">'
                '<div class="viz-vuln-header">'
                '<span class="viz-vuln-title">Technical Gaps</span>'
                f'<span class="section-badge section-badge-err">{tech_count} total</span>'
                '</div>',
                unsafe_allow_html=True,
            )
            for tl in tech_loops[:4]:
                icon = {"critical": "🔴", "high": "🟠",
                        "medium": "🟡", "low": "🔵"}.get(tl.severity, "⚪")
                st.markdown(
                    f'<div class="viz-vuln-card">'
                    f'<div class="viz-vuln-icon">{icon}</div>'
                    f'<div class="viz-vuln-body">'
                    f'<div class="viz-vuln-title">{tl.title}</div>'
                    f'<div class="viz-vuln-desc">{tl.description[:80]}</div>'
                    f'<div class="viz-vuln-impact">{tl.impact}</div>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )
            st.html('</div>')

        st.markdown(
            '<div class="gradient-divider"></div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="viz-section-header"><div class="viz-section-title">Operational Gaps</div></div>', unsafe_allow_html=True)
        oper_count = len(oper_loops)
        st.markdown(
            '<div class="glass-panel">'
            '<div class="viz-vuln-header">'
            '<span class="viz-vuln-title">Operational Gaps</span>'
            f'<span class="section-badge section-badge-warn">{oper_count} total</span>'
            '</div>',
            unsafe_allow_html=True,
        )
        for ol in oper_loops[:5]:
            icon = {"critical": "🔴", "high": "🟠",
                    "medium": "🟡", "low": "🔵"}.get(ol.severity, "⚪")
            st.markdown(
                f'<div class="viz-vuln-card">'
                f'<div class="viz-vuln-icon">{icon}</div>'
                f'<div class="viz-vuln-body">'
                f'<div class="viz-vuln-title">{ol.title}</div>'
                f'<div class="viz-vuln-desc">{ol.description[:90]}</div>'
                f'<div class="viz-vuln-impact">Affected: {ol.affected_persona or ol.location}</div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )
        st.html('</div>')

        # Station vulnerability scores
        st.markdown(
            '<div class="viz-section-header"><div class="viz-section-title">Station Vulnerability Heatmap</div></div>', unsafe_allow_html=True)
        svuln = get_station_vulnerability_scores()
        sv_df = pd.DataFrame(svuln)
        fig_sv = go.Figure(data=go.Heatmap(
            z=[sv_df["score"].tolist()],
            x=sv_df["station"].tolist(),
            y=["Vulnerability Score"],
            colorscale="oranges",
            text=[sv_df["score"].tolist()],
            texttemplate="%{text}",
            textfont=dict(size=9, color="#f8fafc"),))
        fig_sv.update_layout(
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=10, b=10), height=100,
            xaxis=dict(tickangle=-45, tickfont=dict(size=8)),
            yaxis=dict(visible=False),
        )
        render_chart(fig_sv, key="fig_sv_L9823", use_container_width=True)

        # Vulnerability Category Distribution & Risk Matrix
        st.markdown('<div class="viz-section-header"><div class="viz-section-title">Risk Analysis <span class="viz-section-muted">— Category Breakdown &amp; Impact Assessment</span></div></div>', unsafe_allow_html=True)
        vc_cols = st.columns(2)
        with vc_cols[0]:
            all_loops = tech_loops + oper_loops
            cat_counts = {}
            for l in all_loops:
                cat = l.type.capitalize()
                cat_counts[cat] = cat_counts.get(cat, 0) + 1
            if cat_counts:
                cat_df = pd.DataFrame([{"Category": k, "Count": v}
                                      for k, v in cat_counts.items()])
                fig_vcat = go.Figure(data=[go.Pie(
                    labels=cat_df["Category"].tolist(),
                    values=cat_df["Count"].tolist(),
                    marker=dict(
                        colors=["var(--color-danger)", "var(--color-warning)", "#d4a030", "#0d9488"]),
                    hole=0.5,
                    textinfo="label+percent",
                    textfont=dict(size=11, color="var(--text-primary)"),
                    pull=[0.05, 0],
                )])
                fig_vcat.update_layout(
                    template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=10, r=10, t=30, b=10), height=260,
                    title=dict(text="Vulnerability Categories",
                               font=dict(size=11, color="var(--text-secondary)")),
                    showlegend=False,
                )
                render_chart(fig_vcat, key="fig_vcat_L9854", use_container_width=True)

        with vc_cols[1]:
            # Risk Impact vs Likelihood Bubble Chart
            risk_data = [
                {"gap": "Single Controller Failure", "impact": 95,
                    "likelihood": 30, "severity": "critical"},
                {"gap": "No DR Plan", "impact": 90,
                    "likelihood": 15, "severity": "high"},
                {"gap": "Latency Spikes", "impact": 70,
                    "likelihood": 65, "severity": "high"},
                {"gap": "Legacy Gateways", "impact": 85,
                    "likelihood": 25, "severity": "medium"},
                {"gap": "Alert Fatigue", "impact": 50,
                    "likelihood": 80, "severity": "low"},
                {"gap": "Fatigue-Driven Errors", "impact": 75,
                    "likelihood": 70, "severity": "critical"},
                {"gap": "Night Understaffing", "impact": 65,
                    "likelihood": 55, "severity": "medium"},
                {"gap": "Knowledge Silos", "impact": 60,
                    "likelihood": 60, "severity": "high"},
                {"gap": "Weather Protocol Gap", "impact": 55,
                    "likelihood": 40, "severity": "medium"},
                {"gap": "Escalation Ambiguity", "impact": 40,
                    "likelihood": 45, "severity": "low"},
            ]
            rd_df = pd.DataFrame(risk_data)
            sev_colors = {"critical": "var(--color-danger)", "high": "var(--color-warning)",
                          "medium": "#d4a030", "low": "var(--text-muted)"}
            sev_order = {"critical": 3, "high": 2, "medium": 1, "low": 0}
            rd_df["size"] = rd_df["impact"] * rd_df["likelihood"] / 10
            fig_risk = go.Figure()
            for sev in ["critical", "high", "medium", "low"]:
                subset = rd_df[rd_df["severity"] == sev]
                if not subset.empty:
                    fig_risk.add_trace(go.Scatter(
                        x=subset["likelihood"], y=subset["impact"],
                        mode="markers+text",
                        marker=dict(size=subset["size"].clip(8, 40).tolist(),
                                    color=sev_colors[sev],
                                    line=dict(
                                        width=1, color="rgba(255,255,255,0.3)"),
                                    sizemode="area",
                                    sizeref=2.*max(subset["size"])/(40.**2),
                                    sizemin=8),
                        text=subset["gap"].str[:20].tolist(),
                        textposition="middle center",
                        textfont=dict(size=7, color="#f8fafc"),
                        name=sev.capitalize(),))
            fig_risk.add_vline(x=50, line=dict(
                color="rgba(255,255,255,0.15)", width=1, dash="dash"))
            fig_risk.add_hline(y=50, line=dict(
                color="rgba(255,255,255,0.15)", width=1, dash="dash"))
            fig_risk.add_annotation(x=25, y=90, text="HIGH IMPACT", showarrow=False,
                                    font=dict(size=8, color="rgba(239,68,68,0.3)"))
            fig_risk.add_annotation(x=75, y=90, text="CRITICAL ZONE", showarrow=False,
                                    font=dict(size=8, color="rgba(239,68,68,0.5)"))
            fig_risk.update_layout(
                template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=10, r=10, t=30, b=10), height=260,
                title=dict(text="Risk: Impact vs Likelihood",
                           font=dict(size=11, color="var(--text-secondary)")),
                xaxis=dict(title="Likelihood %", range=[0, 100], showgrid=True,
                           gridcolor="rgba(148,163,184,0.08)", tickfont=dict(size=9)),
                yaxis=dict(title="Impact %", range=[0, 100], showgrid=True,
                           gridcolor="rgba(148,163,184,0.08)", tickfont=dict(size=9)),
                hovermode="closest",
                legend=dict(font=dict(size=10, color="var(--text-secondary)"),
                            orientation="h", y=1.08),
            )
            render_chart(fig_risk, key="fig_risk_L9924", use_container_width=True)

        # Historical Vulnerability Trend (simulated)
        st.markdown('<div class="viz-section-header"><div class="viz-section-title">Vulnerability Discovery Trend <span class="viz-section-muted">— simulated quarterly view</span></div></div>', unsafe_allow_html=True)
        vtrend = [
            {"quarter": "Q1 2025", "critical": 5,
                "high": 8, "medium": 12, "low": 18},
            {"quarter": "Q2 2025", "critical": 7,
                "high": 11, "medium": 15, "low": 22},
            {"quarter": "Q3 2025", "critical": 4,
                "high": 9, "medium": 10, "low": 16},
            {"quarter": "Q4 2025", "critical": 3,
                "high": 6, "medium": 8, "low": 14},
            {"quarter": "Q1 2026", "critical": 2,
                "high": 4, "medium": 6, "low": 10},
        ]
        vtrend_df = pd.DataFrame(vtrend)
        fig_vt = go.Figure()
        for col, color, label in [("critical", "var(--color-danger)", "Critical"), ("high", "var(--color-warning)", "High"),
                                  ("medium", "#d4a030", "Medium"), ("low", "var(--text-muted)", "Low")]:
            fig_vt.add_trace(go.Scatter(
                x=vtrend_df["quarter"], y=vtrend_df[col],
                mode="lines+markers", name=label,
                line=dict(width=2, shape="spline", color=color),
                marker=dict(size=6, color=color),
                fill="tonexty", fillcolor=f"rgba{tuple(int(color.removeprefix('#')[i:i+2], 16) for i in (0, 2, 4)) + (0.05,)}" if color.startswith("#") else "rgba(212,160,48,0.05)", hovertemplate=f"{label}: %{{y}}<extra></extra>",
            ))
        fig_vt.update_layout(
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=10, b=10), height=200,
            xaxis=dict(title="", showgrid=True,
                       gridcolor="rgba(148,163,184,0.06)"),
            yaxis=dict(title="Count", showgrid=True,
                       gridcolor="rgba(148,163,184,0.08)"),
            hovermode="x unified",
            legend=dict(font=dict(size=10, color="var(--text-secondary)"),
                        orientation="h", y=1.15),
        )
        render_chart(fig_vt, key="fig_vt_L9962", use_container_width=True)

    # ─── TAB 4: INTELLIGENCE ────────────────────────────────
    with arch_tabs[3]:
        personas_data = get_simulation_personas() if not sim else sim.personas
        recs = generate_recommendations(
            metrics=sim_metrics if sim_metrics else None,
            root_causes=root_causes if root_causes else None,
            personas=personas_data if st.session_state.viz_started else None,
        )

        st.markdown(
            '<div class="viz-section-header"><div class="viz-section-title">AI-Generated Recommendations</div></div>', unsafe_allow_html=True)

        priority_labels = {"critical": "🔴 Critical",
                           "high": "🟠 High", "medium": "🟡 Medium", "info": "🔵 Info"}
        sev_border = {
            "critical": "var(--color-danger)", "high": "var(--color-warning)",
            "medium": "#d4a030", "info": "#3b82f6",
        }
        for rec in recs[:8]:
            border_color = sev_border.get(rec.priority, "var(--text-muted)")
            st.markdown(
                f'<div class="glass-card" style="border-left:3px solid {border_color};padding:14px 18px;">'
                f'<div class="glass-label" style="margin-bottom:6px;">'
                f'{priority_labels.get(rec.priority, "⚪")} {rec.title}</div>'
                f'<div class="glass-value counter-animate" style="font-size:0.85rem;margin-bottom:8px;">{rec.description}</div>'
                f'<div>'
                f'<span class="glass-label" style="color:#d4a030;margin-right:8px;">{rec.area}</span>'
                f'<span class="glass-label" style="color:#0d9488;margin-right:8px;">{rec.impact[:40]}</span>'
                f'<span class="glass-label" style="color:var(--color-warning);">{rec.actionable[:50]}</span>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        if st.session_state.viz_started and sim:
            st.markdown(
                '<div class="viz-section-header"><div class="viz-section-title">Competency Scores</div></div>', unsafe_allow_html=True)
            try:
                comp_scores = sim.competency_scores
                if comp_scores:
                    comp_df = pd.DataFrame([{
                        "Persona": cs.persona_name,
                        "Speed": cs.speed_score,
                        "Accuracy": cs.accuracy_score,
                        "Critical": cs.critical_score,
                        "Specialty": cs.specialty_score,
                        "Escalation": cs.escalation_score,
                        "Balance": cs.balance_score,
                        "Overall": cs.overall_score,
                    } for cs in comp_scores])
                    if not comp_df.empty:
                        top_personas = comp_df.nlargest(5, "Overall")
                        fig_radar = go.Figure()
                        for _, row in top_personas.iterrows():
                            categories = [
                                "Speed", "Accuracy", "Critical", "Specialty", "Escalation", "Balance"]
                            values = [row[c]
                                      for c in categories] + [row[categories[0]]]
                            fig_radar.add_trace(go.Scatterpolar(
                                r=values,
                                theta=categories + [categories[0]],
                                fill="toself",
                                name=row["Persona"],
                                opacity=0.7,
                            ))
                        fig_radar.update_layout(
                            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            margin=dict(l=40, r=40, t=10, b=10), height=350,
                            polar=dict(
                                radialaxis=dict(visible=True, range=[0, 100],
                                                gridcolor="rgba(148,163,184,0.15)"),
                                bgcolor="rgba(0,0,0,0)",
                                gridshape="circular",
                            ),
                            showlegend=True,
                            legend=dict(font=dict(size=10, color="var(--text-secondary)")),
                        )
                        render_chart(fig_radar, key="fig_radar_L10042", use_container_width=True)
            except Exception:
                pass

        # Impact vs Effort Matrix
        st.markdown('<div class="viz-section-header"><div class="viz-section-title">Strategic Analysis <span class="viz-section-muted">— Priority Matrix &amp; Trends</span></div></div>', unsafe_allow_html=True)
        ie_cols = st.columns(2)
        with ie_cols[0]:
            ie_data = [
                {"rec": "DR Plan", "impact": 85,
                    "effort": 20, "priority": "critical"},
                {"rec": "Edge Processing", "impact": 70,
                    "effort": 35, "priority": "high"},
                {"rec": "Fatigue Mgmt", "impact": 75,
                    "effort": 15, "priority": "critical"},
                {"rec": "Redundant Ctrl", "impact": 90,
                    "effort": 45, "priority": "critical"},
                {"rec": "Cross-Training", "impact": 60,
                    "effort": 25, "priority": "high"},
                {"rec": "Legacy Upgrade", "impact": 55,
                    "effort": 40, "priority": "medium"},
                {"rec": "Alert Intel", "impact": 50,
                    "effort": 30, "priority": "medium"},
                {"rec": "Weather Protocol", "impact": 45,
                    "effort": 10, "priority": "info"},
            ]
            ie_df = pd.DataFrame(ie_data)
            pri_colors = {"critical": "var(--color-danger)", "high": "var(--color-warning)",
                          "medium": "#d4a030", "info": "var(--text-muted)"}
            fig_ie = go.Figure()
            for pri in ["critical", "high", "medium", "info"]:
                subset = ie_df[ie_df["priority"] == pri]
                if not subset.empty:
                    fig_ie.add_trace(go.Scatter(
                        x=subset["effort"], y=subset["impact"],
                        mode="markers+text",
                        marker=dict(size=22, color=pri_colors[pri],
                                    line=dict(width=1.5, color="rgba(255,255,255,0.2)")),
                        text=subset["rec"].str[:12].tolist(),
                        textposition="middle center",
                        textfont=dict(size=7, color="#f8fafc"),
                        name=pri.capitalize(),))
            fig_ie.add_vline(x=30, line=dict(
                color="rgba(255,255,255,0.12)", width=1, dash="dash"))
            fig_ie.add_hline(y=65, line=dict(
                color="rgba(255,255,255,0.12)", width=1, dash="dash"))
            fig_ie.add_annotation(x=15, y=85, text="QUICK WINS", showarrow=False,
                                  font=dict(size=8, color="rgba(16,185,129,0.4)"))
            fig_ie.add_annotation(x=50, y=85, text="STRATEGIC", showarrow=False,
                                  font=dict(size=8, color="rgba(59,130,246,0.4)"))
            fig_ie.update_layout(
                template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=10, r=10, t=30, b=10), height=270,
                title=dict(text="Impact vs Effort Matrix",
                           font=dict(size=11, color="var(--text-secondary)")),
                xaxis=dict(title="Effort %", range=[0, 60], showgrid=True,
                           gridcolor="rgba(148,163,184,0.08)", tickfont=dict(size=9)),
                yaxis=dict(title="Impact %", range=[30, 100], showgrid=True,
                           gridcolor="rgba(148,163,184,0.08)", tickfont=dict(size=9)),
                hovermode="closest",
                legend=dict(font=dict(size=10, color="var(--text-secondary)"),
                            orientation="h", y=1.08),
            )
            render_chart(fig_ie, key="fig_ie_L10105", use_container_width=True)

        with ie_cols[1]:
            # Improvement Area Trend (simulated across sessions)
            impr_trend = [
                {"session": 1, "Communication": 45, "Response Time": 30, "Escalation": 55,
                 "Coordination": 40, "Technical": 60},
                {"session": 2, "Communication": 50, "Response Time": 38, "Escalation": 52,
                 "Coordination": 45, "Technical": 58},
                {"session": 3, "Communication": 58, "Response Time": 45, "Escalation": 48,
                 "Coordination": 52, "Technical": 55},
                {"session": 4, "Communication": 65, "Response Time": 55, "Escalation": 42,
                 "Coordination": 60, "Technical": 50},
                {"session": 5, "Communication": 72, "Response Time": 62, "Escalation": 38,
                 "Coordination": 68, "Technical": 45},
            ]
            impr_df = pd.DataFrame(impr_trend)
            impr_colors = {"Communication": "#d4a030", "Response Time": "var(--color-danger)",
                           "Escalation": "var(--color-warning)", "Coordination": "#0d9488", "Technical": "#e8b84b"}
            fig_impr = go.Figure()
            for col, color in impr_colors.items():
                fig_impr.add_trace(go.Scatter(
                    x=impr_df["session"], y=impr_df[col],
                    mode="lines+markers", name=col,
                    line=dict(width=2, shape="spline", color=color),
                    marker=dict(size=5, color=color),
                    hovertemplate=f"{col}: %{{y}}<extra></extra>",
                ))
            fig_impr.update_layout(
                template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=10, r=10, t=30, b=10), height=270,
                title=dict(text="Improvement Areas Over Sessions",
                           font=dict(size=11, color="var(--text-secondary)")),
                xaxis=dict(title="Session #", dtick=1, showgrid=True,
                           gridcolor="rgba(148,163,184,0.06)"),
                yaxis=dict(title="Score", range=[
                           25, 80], showgrid=True, gridcolor="rgba(148,163,184,0.08)"),
                hovermode="x unified",
                legend=dict(font=dict(size=10, color="var(--text-secondary)"),
                            orientation="h", y=1.12),
            )
            render_chart(fig_impr, key="fig_impr_L10146", use_container_width=True)

        # Weakness Distribution
        st.markdown(
            '<div class="viz-section-header"><div class="viz-section-title">Team Weakness Profile</div></div>', unsafe_allow_html=True)
        weak_data = [
            {"area": "Speed", "gap": 35, "personas_affected": 8},
            {"area": "Specialty Match", "gap": 28, "personas_affected": 6},
            {"area": "Balance", "gap": 22, "personas_affected": 5},
            {"area": "Critical Handling", "gap": 18, "personas_affected": 4},
            {"area": "Accuracy", "gap": 12, "personas_affected": 3},
            {"area": "Escalation Control", "gap": 8, "personas_affected": 2},
        ]
        wd_df = pd.DataFrame(weak_data)
        fig_wd = go.Figure()
        fig_wd.add_trace(go.Bar(
            x=wd_df["gap"], y=wd_df["area"],
            orientation="h",
            marker=dict(color=wd_df["gap"].tolist(), colorscale="ylorrd_r",
                        cmin=0, cmax=40,
                        line=dict(width=0)),
            text=wd_df["gap"].apply(lambda x: f"{x}% gap"),
            textposition="outside",
            textfont=dict(size=9, color="var(--text-secondary)"),customdata=wd_df["personas_affected"].tolist(),
            showlegend=False,
        ))
        fig_wd.add_vline(x=20, line=dict(color="rgba(239,68,68,0.3)", width=1, dash="dash"),
                         annotation_text="Threshold", annotation_font=dict(size=8, color="rgba(239,68,68,0.5)"))
        fig_wd.update_layout(
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=60, t=10, b=10), height=220,
            xaxis=dict(title="Performance Gap %", range=[0, 45], showgrid=True,
                       gridcolor="rgba(148,163,184,0.06)", tickfont=dict(size=9)),
            yaxis=dict(title="", showgrid=False, tickfont=dict(size=9)),
        )
        render_chart(fig_wd, key="fig_wd_L10181", use_container_width=True)

        # Export section
        st.markdown(
            '<div class="viz-section-header"><div class="viz-section-title">Export &amp; Reports</div></div>', unsafe_allow_html=True)
        exp_cols = st.columns(3)
        with exp_cols[0]:
            if st.button("📄 Download PDF Report", use_container_width=True,
                         disabled=not st.session_state.viz_started):
                if sim:
                    try:
                        from reports.pdf_generator import generate_simulation_report
                        session_data = {
                            "session_id": f"SIM-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                            "metrics": sim.metrics if hasattr(sim, "metrics") else {},
                            "narrative": f"Training simulation completed with {total_inc} incidents. "
                                         f"Success rate: {success_rate:.0f}%.",
                            "severity_counts": {"CRITICAL": critical,
                                                "WARNING": total_inc - critical - (total_inc - critical - sum(1 for i in st.session_state.viz_incidents if i.severity == "INFO")),
                                                "INFO": sum(1 for i in st.session_state.viz_incidents if i.severity == "INFO")},
                            "personas": [{"name": p.name, "role": p.role,
                                          "assigned": getattr(p, "assigned_count", 0),
                                          "resolved": getattr(p, "resolved_count", 0),
                                          "failed": getattr(p, "assigned_count", 0) - getattr(p, "resolved_count", 0),
                                          "success_rate": getattr(p, "success_rate_computed", 100)}
                                         for p in personas_data],
                            "incidents": [{"timestamp": str(i.timestamp), "severity": i.severity,
                                           "incident_type": i.incident_type, "station": i.station,
                                           "assigned_persona": i.assigned_persona or "—", "status": i.status}
                                          for i in st.session_state.viz_incidents[:50]],
                            "leadership_assessment": "Team performance demonstrates strong operational capability. "
                                                     "Recommend targeted training for identified weakness areas.",
                        }
                        pdf_bytes = generate_simulation_report(session_data)
                        st.download_button(
                            "Save PDF",
                            data=pdf_bytes,
                            file_name=f"simulation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                        )
                    except Exception as e:
                        st.error(f"PDF generation failed: {e}")
        with exp_cols[1]:
            if st.button("📊 Export CSV", use_container_width=True,
                         disabled=not st.session_state.viz_started):
                if st.session_state.viz_incidents:
                    export_df = pd.DataFrame([{
                        "timestamp": i.timestamp, "station": i.station,
                        "type": i.incident_type, "severity": i.severity,
                        "status": i.status, "assigned_to": i.assigned_persona or "",
                        "response_time_min": i.response_time_min,
                    } for i in st.session_state.viz_incidents])
                    csv_data = convert_to_csv(export_df)
                    st.download_button(
                        "Save CSV",
                        data=csv_data,
                        file_name=f"incident_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
        with exp_cols[2]:
            st.markdown(
                f'<div class="viz-stat-card">'
                f'<div class="viz-label-card">Sessions Run</div>'
                f'<div class="viz-stat-value">'
                f'{"1" if st.session_state.viz_started else "0"}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

st.html('</div>')
