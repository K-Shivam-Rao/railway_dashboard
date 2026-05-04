import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from data.loader import load_and_transform_data, load_data_polars, transform_data_fast
from utils.exceptions import DataLoadError, DataValidationError, ConfigurationError
from core.logic import (
    # Analytics functions
    get_metrics,
    get_psd_analytics,
    get_network_summary,
    get_maintenance_forecast,
    get_passenger_heatmap,
    get_incident_log,
    get_leadership_data,
    get_tech_stack,
    # Financial model
    SaaSModelConfig,
    run_simulation,
    print_summary,
    visualize_results,
    visualize_dashboard_1,
    visualize_dashboard_2,
    visualize_comparison,
    # OOP classes
    StationAnalytics,
    FinancialModel,
    CustomerSegmenter,
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
    visualize_comparison,
)
from utils.helpers import (
    format_euro,
    get_status_color,
    format_number,
    format_score,
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
import cartopy.crs as ccrs
import cartopy.feature as cfeature


# ═══════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════
def format_euro(value):
    if value >= 1e6:
        return f"~€{value / 1e6:.1f}M"
    elif value >= 1e3:
        return f"~€{value / 1e3:.0f}K"
    return f"~€{value:.0f}"


def get_status_color(value, threshold_high, threshold_low):
    if value >= threshold_high:
        return "#10b981"
    elif value >= threshold_low:
        return "#f59e0b"
    return "#ef4444"


def format_number(value):
    if value >= 1e3:
        return f"~{int(value)}"
    return f"~{int(value)}"


def format_score(value):
    if value is None:
        return "N/A"
    return f"~{int(round(value))}/10"


# ═══════════════════════════════════════════════════
# CSV EXPORT UTILITY
# ═══════════════════════════════════════════
def convert_to_csv(df):
    """Convert DataFrame to CSV for download."""
    return df.to_csv(index=False).encode("utf-8")


def show_loading_spinner(text="Loading data..."):
    """Context manager for showing loading state."""
    return st.spinner(text)


# ═══════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════
st.set_page_config(
    layout="wide",
    page_title="SicherGleis Pro | BahnSetu",
    page_icon="🛡️",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════
if "current_station" not in st.session_state:
    st.session_state.current_station = "Berlin Hauptbahnhof"
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "ops"
if "selected_operator" not in st.session_state:
    st.session_state.selected_operator = None

# ═══════════════════════════════════════════════════
# CSS — MODERN CLEAN DASHBOARD
# ═══════════════════════════════════════════════════
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

    /* ═══════════════════════════════════════════════════ */
    /* ROOT VARIABLES - Modern Clean Palette */
    /* ═══════════════════════════════════════════════════ */
    :root {
        /* Colors - Cool sophisticated palette */
        --bg-primary: #0b0f1a;
        --bg-secondary: #111827;
        --bg-tertiary: #1a2332;
        --bg-card: rgba(26, 35, 50, 0.6);
        --bg-card-hover: rgba(35, 48, 68, 0.7);
        --bg-elevated: rgba(30, 41, 59, 0.8);

        --border-subtle: rgba(148, 163, 184, 0.1);
        --border-default: rgba(148, 163, 184, 0.2);
        --border-active: rgba(59, 130, 246, 0.5);
        --border-color: rgba(148, 163, 184, 0.15);
        --border-glow: rgba(59, 130, 246, 0.3);

        --text-primary: #f1f5f9;
        --text-secondary: #cbd5e1;
        --text-tertiary: #94a3b8;
        --text-muted: #64748b;

        --accent-primary: #3b82f6;
        --accent-secondary: #60a5fa;
        --accent-tertiary: #93c5fd;
        --accent-blue: #3b82f6;
        --accent-cyan: #06b6d4;

        --status-ok: #10b981;
        --status-warning: #f59e0b;
        --status-error: #ef4444;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;

        /* Gradient definitions (simplified) */
        --gradient-primary: linear-gradient(135deg, #3b82f6, #06b6d4);
        --gradient-glass: rgba(255, 255, 255, 0.03);

        /* Shadows - Clean and minimal */
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.15);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.2), 0 2px 4px -1px rgba(0, 0, 0, 0.1);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.25), 0 4px 6px -2px rgba(0, 0, 0, 0.15);
        --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.2), 0 10px 10px -5px rgba(0, 0, 0, 0.1);

        /* Transitions */
        --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
        --transition-base: 250ms cubic-bezier(0.4, 0, 0.2, 1);
        --transition-slow: 350ms cubic-bezier(0.4, 0, 0.2, 1);

        /* Spacing scale */
        --space-xs: 4px;
        --space-sm: 8px;
        --space-md: 12px;
        --space-lg: 16px;
        --space-xl: 24px;
        --space-2xl: 32px;

        /* Border radius */
        --radius-sm: 6px;
        --radius-md: 10px;
        --radius-lg: 14px;
        --radius-xl: 18px;
    }

    /* ═══════════════════════════════════════════════════ */
    /* BASE STYLES */
    /* ═══════════════════════════════════════════════════ */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        background: var(--bg-primary) !important;
        color: var(--text-primary);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        font-size: 14px;
        line-height: 1.6;
        letter-spacing: -0.01em;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }

    /* Smooth scrolling */
    html {
        scroll-behavior: smooth;
    }

    /* ═══════════════════════════════════════════════════ */
    /* SIDEBAR - Clean & Minimal */
    /* ═══════════════════════════════════════════════════ */
    [data-testid="stSidebar"] {
        background: var(--bg-elevated) !important;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-right: 1px solid var(--border-subtle);
        box-shadow: 4px 0 24px rgba(0, 0, 0, 0.3);
        padding: var(--space-lg) var(--space-md);
    }

    /* Sidebar Brand */
    .sidebar-brand {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: var(--space-md) 0;
        margin-bottom: var(--space-xl);
    }

    .brand-icon {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 40px;
        height: 40px;
        background: linear-gradient(135deg, var(--accent-primary), var(--accent-tertiary));
        border-radius: var(--radius-md);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    }

    .brand-icon svg {
        width: 20px;
        height: 20px;
        color: white;
    }

    .brand-info {
        display: flex;
        flex-direction: column;
        gap: 2px;
    }

    .brand-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--text-primary);
        letter-spacing: -0.02em;
        margin: 0;
    }

    .brand-subtitle {
        font-size: 0.75rem;
        font-weight: 500;
        color: var(--text-tertiary);
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin: 0;
    }

    /* Sidebar Status Card */
    .sidebar-status {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        padding: var(--space-md);
        margin: 0 0 var(--space-xl) 0;
        display: flex;
        align-items: center;
        gap: var(--space-md);
        transition: var(--transition-base);
    }

    .sidebar-status:hover {
        background: var(--bg-card-hover);
        border-color: var(--border-default);
    }

    .status-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        flex-shrink: 0;
        box-shadow: 0 0 8px currentColor;
    }

    .status-dot.ok { background: var(--status-ok); color: var(--status-ok); }
    .status-dot.warning { background: var(--status-warning); color: var(--status-warning); }
    .status-dot.error { background: var(--status-error); color: var(--status-error); }

    .status-text {
        display: flex;
        flex-direction: column;
        gap: 2px;
        flex: 1;
    }

    .status-label {
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .status-desc {
        font-size: 0.7rem;
        color: var(--text-tertiary);
        font-weight: 500;
    }

    /* Section Labels */
    .sidebar-section {
        margin: var(--space-xl) 0 var(--space-md) 0;
    }

    .section-label {
        font-size: 0.7rem;
        font-weight: 700;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: var(--space-sm);
        display: flex;
        align-items: center;
        gap: var(--space-sm);
        padding: 0 0 0 var(--space-sm);
    }

    .section-label::before {
        content: '';
        width: 3px;
        height: 10px;
        background: var(--accent-primary);
        border-radius: 2px;
        opacity: 0.7;
    }

    /* Navigation Buttons - Clean Style */
    .nav-button {
        width: 100% !important;
        background: transparent !important;
        border: 1px solid transparent !important;
        color: var(--text-secondary) !important;
        padding: var(--space-md) var(--space-md) !important;
        border-radius: var(--radius-md) !important;
        margin-bottom: var(--space-xs) !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
        display: flex !important;
        align-items: center !important;
        gap: var(--space-md) !important;
        justify-content: flex-start !important;
        transition: var(--transition-base) !important;
        position: relative !important;
        overflow: hidden !important;
        text-align: left !important;
    }

    .nav-button:hover {
        background: var(--bg-card) !important;
        border-color: var(--border-subtle) !important;
        color: var(--text-primary) !important;
        transform: translateX(4px);
    }

    .nav-button.active {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(6, 182, 212, 0.08)) !important;
        border-color: rgba(59, 130, 246, 0.4) !important;
        color: var(--text-primary) !important;
        font-weight: 600 !important;
    }

    .nav-button.active::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 3px;
        background: var(--accent-primary);
        border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
        box-shadow: 0 0 8px rgba(59, 130, 246, 0.4);
    }

    .nav-icon {
        font-size: 1rem;
        width: 20px;
        text-align: center;
        flex-shrink: 0;
    }

    .nav-text {
        display: flex;
        flex-direction: column;
        gap: 1px;
    }

    .nav-label-text {
        font-size: 0.875rem;
        font-weight: 500;
    }

    .nav-sublabel {
        font-size: 0.65rem;
        color: var(--text-muted);
        font-weight: 400;
        letter-spacing: 0.02em;
    }

    /* Divider */
    .divider {
        height: 1px;
        background: var(--border-subtle);
        margin: var(--space-xl) 0;
    }

    /* Sidebar Footer */
    .sidebar-footer {
        margin-top: auto;
        padding: var(--space-md);
        border-top: 1px solid var(--border-subtle);
        font-size: 0.7rem;
        color: var(--text-muted);
        text-align: center;
    }

    .footer-brand {
        font-weight: 600;
        color: var(--text-tertiary);
        margin-bottom: 2px;
    }

    .footer-version {
        font-size: 0.6rem;
        color: var(--text-muted);
        opacity: 0.7;
        font-family: 'JetBrains Mono', monospace;
    }
    [data-testid="stSidebar"]::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background: linear-gradient(180deg,
            rgba(59, 130, 246, 0.03) 0%,
            transparent 30%,
            transparent 70%,
            rgba(6, 182, 212, 0.02) 100%);
        pointer-events: none;
        z-index: 0;
    }
    [data-testid="stSidebar"]::after {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; height: 2px;
        background: var(--gradient-primary);
        opacity: 0.6;
        pointer-events: none;
        z-index: 1;
    }

    /* ── Sidebar Brand Header ── */
    .sidebar-brand {
        padding: 14px 12px;
        margin: -12px -12px 12px -12px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }
    .brand-title {
        font-size: 1rem; font-weight: 600; letter-spacing: 0.02em;
        color: var(--text-primary); display: flex; align-items: center; gap: 8px;
        font-family: 'Space Grotesk', sans-serif;
    }
    .brand-title svg {
        width: 18px; height: 18px;
        color: var(--accent-blue);
        flex-shrink: 0;
    }
    .brand-tagline {
        font-size: 0.7rem; font-family: 'JetBrains Mono', monospace;
        color: var(--text-muted); margin-top: 6px; letter-spacing: 1.5px;
        text-transform: uppercase;
        opacity: 0.8;
        font-weight: 500;
    }

    /* ── System Status Indicator - Clean & Elegant ── */
    .system-status-indicator {
        display: flex; align-items: center; gap: 12px;
        padding: 12px 14px;
        background: rgba(17, 24, 39, 0.5);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.06);
        margin: 0 0 20px 0;
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
    }
    .system-status-indicator:hover {
        background: rgba(30, 41, 59, 0.5);
        border-color: rgba(255, 255, 255, 0.1);
    }
    .status-icon-section {
        position: relative;
        flex-shrink: 0;
    }
    .status-icon-large {
        width: 32px; height: 32px;
        display: flex; align-items: center; justify-content: center;
        border-radius: 50%;
        background: rgba(59, 130, 246, 0.1);
        border: 1px solid rgba(59, 130, 246, 0.3);
    }
    .status-icon-large svg {
        width: 16px; height: 16px;
        color: var(--accent-blue);
    }
    .system-status-indicator.status-normal .status-icon-large {
        background: rgba(16, 185, 129, 0.1);
        border-color: rgba(16, 185, 129, 0.3);
    }
    .system-status-indicator.status-normal .status-icon-large svg {
        color: var(--success);
    }
    .system-status-indicator.status-warning .status-icon-large {
        background: rgba(245, 158, 11, 0.1);
        border-color: rgba(245, 158, 11, 0.3);
    }
    .system-status-indicator.status-warning .status-icon-large svg {
        color: var(--warning);
    }
    .system-status-indicator.status-alert .status-icon-large {
        background: rgba(239, 68, 68, 0.1);
        border-color: rgba(239, 68, 68, 0.3);
    }
    .system-status-indicator.status-alert .status-icon-large svg {
        color: var(--danger);
    }
    .status-content {
        flex: 1;
    }
    .status-label-main {
        font-size: 0.75rem; font-weight: 700; letter-spacing: 0.05em;
        text-transform: uppercase; color: var(--text-primary);
        font-family: 'JetBrains Mono', monospace;
    }
    .status-label-sub {
        font-size: 0.625rem; color: var(--text-muted);
        margin-top: 2px; letter-spacing: 0.02em;
    }

    /* ── Section Headers ── */
    .section-header-modern {
        display: flex; align-items: center; justify-content: space-between;
        margin: 24px 0 12px 0;
        padding: 0 4px;
    }
    .section-title {
        font-size: 0.6875rem; font-weight: 700; letter-spacing: 2px;
        text-transform: uppercase; color: var(--text-secondary);
        font-family: 'JetBrains Mono', monospace;
        display: flex; align-items: center; gap: 8px;
    }
    .section-title::before {
        content: '';
        width: 3px; height: 11px;
        background: var(--gradient-primary);
        border-radius: 2px;
        box-shadow: 0 0 8px rgba(59, 130, 246, 0.4);
    }

    /* ── Navigation Divider ── */
    .nav-divider {
        height: 1px;
        background: linear-gradient(90deg,
            transparent 0%,
            rgba(30, 41, 59, 0.6) 30%,
            rgba(30, 41, 59, 0.6) 70%,
            transparent 100%);
        margin: 20px 0;
        position: relative;
    }
    .nav-divider::after {
        content: '';
        position: absolute;
        top: 0; left: 50%; transform: translateX(-50%);
        width: 30px; height: 1px;
        background: var(--gradient-primary);
        opacity: 0.5;
    }

    /* ── Sidebar Footer ── */
    .sidebar-footer {
        font-size: 0.625rem; color: var(--text-muted); text-align: center;
        padding: 14px 12px; font-family: 'JetBrains Mono';
        border-top: 1px solid rgba(255, 255, 255, 0.05);
        margin-top: 20px;
        opacity: 0.6;
        position: relative;
        background: rgba(17, 24, 39, 0.4);
        border-radius: 10px 10px 0 0;
    }
    .footer-version {
        font-size: 0.5625rem;
        margin-top: 4px;
        opacity: 0.7;
    }

    /* ── Sidebar Buttons - Pill Style ── */
    [data-testid="stSidebar"] .stButton > button {
        width: 100%; border: 1px solid transparent;
        background: rgba(30, 41, 59, 0.3);
        color: var(--text-secondary);
        text-align: left; padding: 11px 16px;
        border-radius: 10px; margin-bottom: 6px;
        font-weight: 500; font-size: 0.875rem;
        transition: all 0.2s ease;
        display: flex; align-items: center; gap: 12px;
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(4px);
        border: 1px solid rgba(255, 255, 255, 0.04);
    }
    [data-testid="stSidebar"] .stButton > button::before {
        content: '';
        position: absolute; left: 0; top: 0;
        width: 4px; height: 100%;
        background: var(--gradient-primary);
        transform: translateX(-100%);
        transition: var(--transition);
        border-radius: 0 4px 4px 0;
    }

    /* ── Sidebar Nav Labels ── */
    .nav-label {
        font-size: 0.6875rem; font-weight: 700; letter-spacing: 2.5px;
        text-transform: uppercase; color: var(--text-muted);
        margin: 28px 0 12px 4px;
        display: flex; align-items: center; gap: 8px;
        position: relative;
    }
    .nav-label::before {
        content: '';
        width: 6px; height: 6px;
        background: var(--gradient-primary);
        border-radius: 50%;
        box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
        transition: var(--transition);
    }
    .nav-label:hover::before {
        transform: scale(1.3);
        box-shadow: 0 0 14px rgba(59, 130, 246, 0.7);
    }
    .nav-divider {
        height: 1px;
        background: linear-gradient(90deg,
            transparent 0%,
            var(--border-color) 20%,
            var(--border-color) 80%,
            transparent 100%);
        margin: 24px 0;
        position: relative;
    }
    .nav-divider::after {
        content: '';
        position: absolute;
        top: 0; left: 50%; transform: translateX(-50%);
        width: 40px; height: 1px;
        background: var(--gradient-primary);
        opacity: 0.6;
    }
    .sidebar-footer {
        font-size: 0.6875rem; color: var(--text-muted); text-align: center;
        padding: 16px; font-family: 'JetBrains Mono';
        border-top: 1px solid var(--border-color);
        margin-top: 24px;
        opacity: 0.7;
        position: relative;
        background: var(--bg-card);
        backdrop-filter: blur(10px);
        border-radius: 12px 12px 0 0;
    }

    /* ── Sidebar Buttons ── */
    [data-testid="stSidebar"] .stButton > button {
        width: 100%; border: 1px solid transparent;
        background: transparent; color: var(--text-secondary);
        text-align: left; padding: 12px 16px;
        border-radius: 10px; margin-bottom: 6px;
        font-weight: 500; font-size: 0.875rem;
        transition: var(--transition);
        display: flex; align-items: center; gap: 12px;
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(4px);
    }
    [data-testid="stSidebar"] .stButton > button::before {
        content: '';
        position: absolute; left: 0; top: 0;
        width: 4px; height: 100%;
        background: var(--gradient-primary);
        transform: translateX(-100%);
        transition: var(--transition);
        border-radius: 0 4px 4px 0;
    }
    [data-testid="stSidebar"] .stButton > button::after {
        content: '';
        position: absolute; inset: 0;
        background: var(--gradient-glass);
        opacity: 0;
        transition: var(--transition);
        border-radius: 10px;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(59, 130, 246, 0.1) !important;
        border-color: rgba(59, 130, 246, 0.3) !important;
        color: var(--text-primary) !important;
        transform: translateX(4px);
        box-shadow: 0 4px 16px rgba(59, 130, 246, 0.15);
    }
    [data-testid="stSidebar"] .stButton > button:hover::before {
        transform: translateX(0);
    }
    [data-testid="stSidebar"] .stButton > button:hover::after {
        opacity: 1;
    }
    [data-testid="stSidebar"] .stButton > button:active {
        transform: translateX(2px);
    }
    [data-testid="stSidebar"] .stButton > button:focus {
        outline: none;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
    }

    /* ── Enhanced Sidebar Buttons ── */
    [data-testid="stSidebar"] .stButton > button[kind="secondary"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-secondary) !important;
        padding: 11px 14px !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
        display: flex !important;
        align-items: center !important;
        gap: 10px !important;
        transition: var(--transition) !important;
        backdrop-filter: blur(8px);
        position: relative;
        overflow: hidden;
    }
    [data-testid="stSidebar"] .stButton > button[kind="secondary"]::before {
        content: '';
        position: absolute;
        inset: 0;
        background: var(--gradient-glass);
        opacity: 0;
        transition: var(--transition);
        border-radius: 10px;
    }
    [data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
        background: var(--bg-card-hover) !important;
        border-color: rgba(59, 130, 246, 0.4) !important;
        color: var(--text-primary) !important;
        transform: translateX(4px) !important;
        box-shadow: 0 4px 16px rgba(59, 130, 246, 0.12), 0 0 0 1px rgba(59, 130, 246, 0.1) inset !important;
    }
    [data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover::before {
        opacity: 1;
    }
    [data-testid="stSidebar"] .stButton > button[kind="secondary"]:active {
        transform: translateX(2px) !important;
    }

    /* ── Primary/Action Buttons ── */
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: rgba(59, 130, 246, 0.12) !important;
        border: 1px solid rgba(59, 130, 246, 0.3) !important;
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.2), 0 2px 8px rgba(59, 130, 246, 0.1);
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
        background: rgba(59, 130, 246, 0.18) !important;
        border-color: rgba(59, 130, 246, 0.5) !important;
        box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.3), 0 4px 12px rgba(59, 130, 246, 0.2);
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"]:active {
        transform: translateX(2px) !important;
    }

    /* ── Enhanced Sidebar Features ── */

    /* Quick Stats Card */
    .quick-stats-card {
        background: var(--gradient-glass);
        backdrop-filter: blur(16px) saturate(150%);
        border: 1px solid var(--border-color);
        border-radius: 14px;
        padding: 18px;
        margin: 0 0 24px 0;
        box-shadow: var(--shadow-md);
        position: relative;
        overflow: hidden;
    }
    .quick-stats-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; height: 2px;
        background: var(--gradient-primary);
        opacity: 0.7;
    }
    .quick-stats-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid var(--border-color);
    }
    .quick-stats-title {
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: var(--text-muted);
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 10px;
    }
    .stat-item {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 10px;
        padding: 12px;
        transition: var(--transition);
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(8px);
    }
    .stat-item::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; height: 2px;
        background: var(--gradient-primary);
        opacity: 0;
        transition: var(--transition);
    }
    .stat-item:hover {
        background: var(--bg-card-hover);
        border-color: rgba(59, 130, 246, 0.4);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
    }
    .stat-item:hover::before {
        opacity: 1;
    }
    .stat-label {
        font-size: 0.6rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        color: var(--text-muted);
        margin-bottom: 4px;
    }
    .stat-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1rem;
        font-weight: 700;
        color: var(--text-primary);
    }
    .stat-value.green { color: var(--success); }
    .stat-value.yellow { color: var(--warning); }
    .stat-value.red { color: var(--danger); }

    /* Station Search */
    .station-search {
        position: relative;
        margin-bottom: 20px;
    }
    .search-icon {
        position: absolute;
        left: 14px;
        top: 50%;
        transform: translateY(-50%);
        color: var(--text-muted);
        font-size: 0.875rem;
        z-index: 2;
        transition: var(--transition);
    }
    .station-search:hover .search-icon {
        color: var(--accent-blue);
    }
    [data-testid="stTextInput"] input {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
        color: var(--text-primary) !important;
        padding: 10px 12px 10px 38px !important;
        font-size: 0.875rem !important;
        font-family: 'Inter', sans-serif !important;
        transition: var(--transition) !important;
        backdrop-filter: blur(8px);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    [data-testid="stTextInput"] input:focus {
        border-color: var(--accent-blue) !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2), 0 4px 12px rgba(59, 130, 246, 0.1) !important;
        outline: none !important;
        background: var(--bg-card-hover) !important;
    }
    [data-testid="stTextInput"] input::placeholder {
        color: var(--text-muted) !important;
        opacity: 0.6;
    }

    /* Enhanced Station List */
    .station-list {
        max-height: 280px;
        overflow-y: auto;
        margin: 0 -8px;
        padding: 0 8px;
        scrollbar-width: thin;
        scrollbar-color: var(--border-glow) transparent;
    }
    .station-list::-webkit-scrollbar {
        width: 6px;
    }
    .station-list::-webkit-scrollbar-track {
        background: transparent;
    }
    .station-list::-webkit-scrollbar-thumb {
        background: var(--border-glow);
        border-radius: 3px;
    }
    .station-list::-webkit-scrollbar-thumb:hover {
        background: var(--text-muted);
    }
    .station-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 14px;
        border-radius: 10px;
        margin-bottom: 6px;
        transition: var(--transition);
        cursor: pointer;
        border: 1px solid transparent;
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(4px);
    }
    .station-item::before {
        content: '';
        position: absolute;
        inset: 0;
        background: var(--gradient-glass);
        opacity: 0;
        transition: var(--transition);
        border-radius: 10px;
    }
    .station-item:hover {
        background: rgba(59, 130, 246, 0.08);
        border-color: rgba(59, 130, 246, 0.3);
        transform: translateX(4px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
    }
    .station-item:hover::before {
        opacity: 1;
    }
    .station-item.active {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(6, 182, 212, 0.1) 100%);
        border-color: rgba(59, 130, 246, 0.5);
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.15);
        transform: translateX(4px);
    }
    .station-item.active::before {
        opacity: 1;
    }
    .station-icon {
        width: 32px;
        height: 32px;
        border-radius: 8px;
        background: rgba(59, 130, 246, 0.15);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.875rem;
        color: var(--accent-blue);
        flex-shrink: 0;
        border: 1px solid var(--border-color);
        transition: var(--transition);
    }
    .station-item:hover .station-icon {
        border-color: rgba(59, 130, 246, 0.4);
        box-shadow: 0 0 12px rgba(59, 130, 246, 0.2);
    }
    .station-item.active .station-icon {
        background: var(--accent-blue);
        color: white;
        border-color: var(--accent-blue);
        box-shadow: 0 0 16px rgba(59, 130, 246, 0.4);
    }
    .station-info {
        flex: 1;
        min-width: 0;
    }
    .station-name {
        font-size: 0.875rem;
        font-weight: 500;
        color: var(--text-primary);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .station-status {
        font-size: 0.65rem;
        color: var(--text-muted);
        font-family: 'JetBrains Mono', monospace;
    }
    .station-badge {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        flex-shrink: 0;
    }
    .station-badge.online { background: var(--success); box-shadow: 0 0 4px var(--success); }
    .station-badge.alert { background: var(--danger); box-shadow: 0 0 4px var(--danger); }
    .station-badge.warning { background: var(--warning); box-shadow: 0 0 4px var(--warning); }

    /* Quick Actions */
    .quick-actions {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 8px;
        margin: 16px 0;
    }
    .quick-action-btn {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
        padding: 12px !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        gap: 6px !important;
        transition: var(--transition) !important;
        min-height: auto !important;
        position: relative !important;
        overflow: hidden !important;
    }
    .quick-action-btn:hover {
        background: var(--bg-card-hover) !important;
        border-color: var(--accent-blue) !important;
        transform: translateY(-2px) !important;
        box-shadow: var(--shadow-md) !important;
    }
    .quick-action-btn::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: var(--gradient-primary);
        transform: scaleX(0);
        transition: var(--transition);
    }
    .quick-action-btn:hover::before {
        transform: scaleX(1);
    }
    .action-icon {
        width: 24px;
        height: 24px;
        color: var(--accent-blue);
    }
    .action-label {
        font-size: 0.65rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        color: var(--text-secondary);
        text-transform: uppercase;
    }

    /* Enhanced Module Navigation */
    .module-nav {
        display: flex;
        flex-direction: column;
        gap: 8px;
        margin: 12px 0;
    }
    .module-item {
        display: flex;
        align-items: center;
        gap: 14px;
        padding: 14px 16px;
        border-radius: 12px;
        border: 1px solid transparent;
        transition: var(--transition);
        cursor: pointer;
        background: var(--bg-card);
        backdrop-filter: blur(12px);
        position: relative;
        overflow: hidden;
    }
    .module-item::before {
        content: '';
        position: absolute;
        inset: 0;
        background: var(--gradient-glass);
        opacity: 0;
        transition: var(--transition);
        border-radius: 12px;
    }
    .module-item:hover {
        background: var(--bg-card-hover);
        border-color: rgba(59, 130, 246, 0.3);
        transform: translateX(6px);
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.12);
    }
    .module-item:hover::before {
        opacity: 1;
    }
    .module-item.active {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.18) 0%, rgba(6, 182, 212, 0.12) 100%);
        border-color: rgba(59, 130, 246, 0.5);
        box-shadow: 0 0 24px rgba(59, 130, 246, 0.2), 0 4px 12px rgba(0, 0, 0, 0.2);
        transform: translateX(6px);
    }
    .module-item.active::before {
        opacity: 1;
    }
    .module-icon {
        width: 36px;
        height: 36px;
        border-radius: 10px;
        background: var(--bg-card);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.125rem;
        border: 1px solid var(--border-color);
        transition: var(--transition);
        flex-shrink: 0;
    }
    .module-item:hover .module-icon {
        border-color: rgba(59, 130, 246, 0.4);
        box-shadow: 0 0 16px rgba(59, 130, 246, 0.2);
        transform: scale(1.05);
    }
    .module-item.active .module-icon {
        background: var(--gradient-primary);
        color: white;
        border-color: transparent;
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.4);
        transform: scale(1.08);
    }
    .module-info {
        flex: 1;
    }
    .module-name {
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--text-primary);
        line-height: 1.2;
    }
    .module-desc {
        font-size: 0.65rem;
        color: var(--text-muted);
        margin-top: 2px;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Sidebar Footer Enhancement */
    .sidebar-footer {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 14px;
        padding: 16px;
        margin: 24px -24px 0 -24px;
        text-align: center;
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(16px);
        box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.2);
    }
    .sidebar-footer::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: var(--gradient-primary);
        opacity: 0.7;
    }
    .sidebar-footer::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--border-color), transparent);
    }
    .footer-brand {
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--text-secondary);
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
    }
    .footer-version {
        font-size: 0.625rem;
        color: var(--text-muted);
        font-family: 'JetBrains Mono', monospace;
        opacity: 0.6;
        letter-spacing: 0.5px;
    }
    .footer-links {
        display: flex;
        justify-content: center;
        gap: 16px;
        margin-top: 8px;
    }
    .footer-link {
        font-size: 0.625rem;
        color: var(--text-muted);
        text-decoration: none;
        transition: var(--transition);
        opacity: 0.7;
    }
    .footer-link:hover {
        color: var(--accent-blue);
        opacity: 1;
    }

    /* ═══════════════════════════════════════════════════ */
    /* STATUS INDICATOR - Clean & Modern */
    /* ═══════════════════════════════════════════════════ */
    .system-status-indicator {
        display: flex;
        align-items: center;
        gap: var(--space-md);
        padding: var(--space-md) var(--space-lg);
        border-radius: var(--radius-lg);
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        margin: 0 0 var(--space-xl) 0;
        transition: var(--transition-base);
        position: relative;
        overflow: hidden;
    }

    .system-status-indicator::before {
        content: '';
        position: absolute;
        inset: 0;
        background: var(--gradient-glass);
        opacity: 0;
        transition: var(--transition-base);
        border-radius: var(--radius-lg);
    }

    .system-status-indicator:hover {
        border-color: var(--border-default);
        background: var(--bg-card-hover);
    }

    .system-status-indicator:hover::before {
        opacity: 1;
    }

    .status-indicator-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        flex-shrink: 0;
        transition: var(--transition-base);
        box-shadow: 0 0 10px currentColor;
    }

    .status-indicator-dot.ok {
        background: var(--status-ok);
        color: var(--status-ok);
    }

    .status-indicator-dot.warning {
        background: var(--status-warning);
        color: var(--status-warning);
        animation: pulse-warning 2s ease-in-out infinite;
    }

    .status-indicator-dot.error {
        background: var(--status-error);
        color: var(--status-error);
        animation: pulse-error 1.5s ease-in-out infinite;
    }

    @keyframes pulse-warning {
        0%, 100% { box-shadow: 0 0 4px currentColor; }
        50% { box-shadow: 0 0 12px currentColor, 0 0 20px currentColor; }
    }

    @keyframes pulse-error {
        0%, 100% { box-shadow: 0 0 4px currentColor; transform: scale(1); }
        50% { box-shadow: 0 0 14px currentColor, 0 0 24px currentColor; transform: scale(1.05); }
    }

    .status-indicator-text {
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 1px;
        position: relative;
        z-index: 1;
    }

    .status-indicator-label {
        font-size: 0.8125rem;
        font-weight: 700;
        color: var(--text-primary);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .status-indicator-desc {
        font-size: 0.7rem;
        color: var(--text-tertiary);
        font-weight: 500;
        letter-spacing: 0.02em;
    }
        80% {
            opacity: 0.1;
        }
        100% {
            transform: translate(-50%, -50%) scale(2.5);
            opacity: 0;
        }
    }

    /* Status text - centered */
    .system-status-indicator .status-content {
        position: relative;
        z-index: 2;
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        flex: 1;
        min-width: 0;
    }

    .system-status-indicator .status-label-main {
        font-size: 0.875rem;
        font-weight: 700;
        font-family: 'Space Grotesk', 'JetBrains Mono', monospace;
        letter-spacing: 1.5px;
        text-transform: uppercase;
    }

    .system-status-indicator .status-label-sub {
        font-size: 0.65rem;
        font-weight: 500;
        font-family: 'Inter', sans-serif;
        letter-spacing: 0.5px;
        opacity: 0.7;
        margin-top: 2px;
    }

    /* Variations */
    .system-status-indicator.status-normal {
        background: linear-gradient(
            135deg,
            rgba(16, 185, 129, 0.12) 0%,
            rgba(16, 185, 129, 0.05) 100%
        );
        border-color: rgba(16, 185, 129, 0.4);
        box-shadow: 0 4px 16px rgba(16, 185, 129, 0.12);
    }

    .system-status-indicator.status-normal .status-label-main {
        color: #34d399;
        text-shadow: 0 0 12px rgba(52, 211, 153, 0.4);
    }

    .system-status-indicator.status-normal .status-ring-pulse {
        color: #34d399;
        animation-delay: 0s;
    }

    .status-normal .status-icon-large svg {
        color: #34d399;
    }

    /* ═══════════════════════════════════════════════════ */
    /* STATUS INDICATOR COLORS - Subtle variations */
    /* ═══════════════════════════════════════════════════ */
    .system-status-indicator.status-normal {
        background: rgba(16, 185, 129, 0.08);
        border-color: rgba(16, 185, 129, 0.2);
    }

    .system-status-indicator.status-normal .status-indicator-dot {
        box-shadow: 0 0 8px var(--status-ok);
    }

    .system-status-indicator.status-warning {
        background: rgba(245, 158, 11, 0.08);
        border-color: rgba(245, 158, 11, 0.2);
    }

    .system-status-indicator.status-warning .status-indicator-label {
        color: var(--status-warning);
    }

    .system-status-indicator.status-alert {
        background: rgba(239, 68, 68, 0.08);
        border-color: rgba(239, 68, 68, 0.2);
    }

    .system-status-indicator.status-alert .status-indicator-label {
        color: var(--status-error);
    }

    .system-status-indicator.status-alert .status-text {
        color: #f87171;
        text-shadow: 0 0 8px rgba(248, 113, 113, 0.4);
    }

    .system-status-indicator.status-alert .status-dot-ring {
        color: #f87171;
        animation-delay: 0s;
    }

    @keyframes sidebar-alert-glow {
        0%, 100% {
            box-shadow: 0 2px 12px rgba(239, 68, 68, 0.12);
        }
        50% {
            box-shadow: 0 3px 16px rgba(239, 68, 68, 0.22);
        }
    }

    .status-text {
        font-size: 0.75rem;
        font-weight: 700;
        font-family: 'Space Grotesk', 'JetBrains Mono', monospace;
        letter-spacing: 1px;
        text-transform: uppercase;
        position: relative;
        z-index: 1;
    }

    /* Section Enhancements */
    .section-header-modern {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin: 20px 0 12px 0;
        padding: 0 4px;
    }
    .section-title {
        font-size: 0.65rem;
        font-weight: 700;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: var(--text-muted);
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .section-count {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 999px;
        padding: 2px 8px;
        font-size: 0.65rem;
        font-family: 'JetBrains Mono', monospace;
        color: var(--text-secondary);
    }

    /* Responsive adjustments for sidebar */
    @media (max-width: 768px) {
        [data-testid="stSidebar"] {
            width: 100% !important;
            max-width: 100% !important;
        }
        .quick-actions {
            grid-template-columns: repeat(2, 1fr);
            gap: 6px;
        }
        .stats-grid {
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
        }
        .module-item {
            padding: 12px 14px;
            gap: 12px;
        }
        .module-icon {
            width: 32px;
            height: 32px;
            font-size: 1rem;
        }
        .station-item {
            padding: 10px 12px;
            gap: 10px;
        }
        .station-icon {
            width: 28px;
            height: 28px;
            font-size: 0.75rem;
        }
        .brand-title {
            font-size: 1.375rem;
        }
        .sidebar-brand {
            padding: 24px 20px 20px;
            margin: -20px -20px 20px -20px;
        }
    }
    
    @media (max-width: 480px) {
        [data-testid="stSidebar"] {
            padding-bottom: 20px;
        }
        .quick-actions {
            grid-template-columns: repeat(2, 1fr);
        }
        .stats-grid {
            grid-template-columns: repeat(2, 1fr);
        }
        .module-item {
            padding: 10px 12px;
            gap: 10px;
        }
        .module-icon {
            width: 28px;
            height: 28px;
            font-size: 0.875rem;
        }
        .station-item {
            padding: 8px 10px;
            gap: 8px;
        }
        .station-icon {
            width: 28px;
            height: 28px;
            font-size: 0.75rem;
        }
    }

    /* ── Main Header ── */
    /* ═══════════════════════════════════════════════════ */
    /* MAIN HEADER - Clean & Modern */
    /* ═══════════════════════════════════════════════════ */
    .main-header {
        background: var(--bg-card);
        backdrop-filter: blur(16px);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        padding: var(--space-xl) var(--space-2xl);
        margin-bottom: var(--space-xl);
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: var(--shadow-md);
        position: relative;
    }

    .main-header::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; height: 3px;
        background: linear-gradient(90deg, var(--accent-primary), var(--accent-tertiary));
        border-radius: var(--radius-lg) var(--radius-lg) 0 0;
        opacity: 0.8;
    }

    .header-left {
        display: flex;
        flex-direction: column;
        gap: var(--space-sm);
    }

    .station-title {
        font-size: 1.75rem;
        font-weight: 700;
        color: var(--text-primary);
        margin: 0;
        letter-spacing: -0.02em;
        line-height: 1.2;
    }

    .station-sub {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        color: var(--text-tertiary);
        letter-spacing: 0.1em;
        display: flex;
        align-items: center;
        gap: var(--space-sm);
        margin-top: var(--space-xs);
    }

    .station-sub::before {
        content: '●';
        color: var(--accent-primary);
        font-size: 0.5rem;
        opacity: 0.7;
    }

    /* ═══════════════════════════════════════════════════ */
    /* STATUS BADGE - Clean Modern */
    /* ═══════════════════════════════════════════════════ */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: var(--space-sm);
        padding: var(--space-sm) var(--space-lg);
        border-radius: var(--radius-xl);
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        transition: var(--transition-base);
        border: 1px solid;
        backdrop-filter: blur(12px);
        cursor: default;
    }

    .status-badge.normal {
        background: rgba(16, 185, 129, 0.12);
        border-color: rgba(16, 185, 129, 0.3);
        color: var(--status-ok);
    }

    .status-badge.warning {
        background: rgba(245, 158, 11, 0.12);
        border-color: rgba(245, 158, 11, 0.3);
        color: var(--status-warning);
    }

    .status-badge.alert {
        background: rgba(239, 68, 68, 0.12);
        border-color: rgba(239, 68, 68, 0.3);
        color: var(--status-error);
    }

    .status-icon {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 18px;
        height: 18px;
    }

    .status-icon svg {
        width: 16px;
        height: 16px;
        stroke-width: 2.5;
    }

    /* Status Icon Container */
    .status-icon {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 20px;
        height: 20px;
        position: relative;
    }

    .status-icon svg {
        width: 18px;
        height: 18px;
        position: relative;
        z-index: 2;
        filter: drop-shadow(0 0 4px currentColor);
    }

    /* Animated ring pulse effect */
    .status-icon-ring {
        position: absolute;
        top: 50%; left: 50%;
        transform: translate(-50%, -50%);
        width: 100%;
        height: 100%;
        border-radius: 50%;
        border: 2px solid currentColor;
        opacity: 0;
        animation: ring-pulse 2s ease-out infinite;
    }

    @keyframes ring-pulse {
        0% {
            transform: translate(-50%, -50%) scale(0.8);
            opacity: 0.8;
        }
        100% {
            transform: translate(-50%, -50%) scale(2);
            opacity: 0;
        }
    }

    /* Status Variations */
    .status-normal {
        background: linear-gradient(
            135deg,
            rgba(16, 185, 129, 0.18) 0%,
            rgba(16, 185, 129, 0.08) 100%
        );
        border-color: rgba(16, 185, 129, 0.6);
        color: #34d399;
        box-shadow:
            0 4px 24px rgba(16, 185, 129, 0.18),
            inset 0 1px 0 rgba(255,255,255,0.1),
            0 0 0 1px rgba(16, 185, 129, 0.1) inset;
    }

    .status-normal:hover {
        background: linear-gradient(
            135deg,
            rgba(16, 185, 129, 0.25) 0%,
            rgba(16, 185, 129, 0.12) 100%
        );
        border-color: rgba(16, 185, 129, 0.8);
        box-shadow:
            0 6px 32px rgba(16, 185, 129, 0.28),
            inset 0 1px 0 rgba(255,255,255,0.15),
            0 0 0 1px rgba(16, 185, 129, 0.15) inset;
        transform: translateY(-1px) scale(1.02);
    }

    .status-normal .status-icon-ring {
        color: #34d399;
        animation-delay: 0s;
    }

    .status-warning {
        background: linear-gradient(
            135deg,
            rgba(245, 158, 11, 0.18) 0%,
            rgba(245, 158, 11, 0.08) 100%
        );
        border-color: rgba(245, 158, 11, 0.6);
        color: #fbbf24;
        box-shadow:
            0 4px 24px rgba(245, 158, 11, 0.18),
            inset 0 1px 0 rgba(255,255,255,0.1),
            0 0 0 1px rgba(245, 158, 11, 0.1) inset;
    }

    .status-warning:hover {
        background: linear-gradient(
            135deg,
            rgba(245, 158, 11, 0.25) 0%,
            rgba(245, 158, 11, 0.12) 100%
        );
        border-color: rgba(245, 158, 11, 0.8);
        box-shadow:
            0 6px 32px rgba(245, 158, 11, 0.28),
            inset 0 1px 0 rgba(255,255,255,0.15),
            0 0 0 1px rgba(245, 158, 11, 0.15) inset;
        transform: translateY(-1px) scale(1.02);
    }

    .status-warning .status-icon-ring {
        color: #fbbf24;
        animation-delay: 0.6s;
    }

    .status-alert {
        background: linear-gradient(
            135deg,
            rgba(239, 68, 68, 0.2) 0%,
            rgba(239, 68, 68, 0.08) 100%
        );
        border-color: rgba(239, 68, 68, 0.65);
        color: #f87171;
        box-shadow:
            0 4px 24px rgba(239, 68, 68, 0.22),
            inset 0 1px 0 rgba(255,255,255,0.1),
            0 0 0 1px rgba(239, 68, 68, 0.12) inset;
        animation: alert-glow 2s ease-in-out infinite;
    }

    .status-alert:hover {
        background: linear-gradient(
            135deg,
            rgba(239, 68, 68, 0.28) 0%,
            rgba(239, 68, 68, 0.14) 100%
        );
        border-color: rgba(239, 68, 68, 0.9);
        box-shadow:
            0 6px 32px rgba(239, 68, 68, 0.35),
            inset 0 1px 0 rgba(255,255,255,0.15),
            0 0 0 1px rgba(239, 68, 68, 0.18) inset;
        transform: translateY(-1px) scale(1.02);
        animation: none;
    }

    .status-alert .status-icon-ring {
        color: #f87171;
        animation-delay: 0s;
    }

    @keyframes alert-glow {
        0%, 100% {
            box-shadow:
                0 4px 24px rgba(239, 68, 68, 0.22),
                inset 0 1px 0 rgba(255,255,255,0.1),
                0 0 0 1px rgba(239, 68, 68, 0.12) inset;
        }
        50% {
            box-shadow:
                0 6px 32px rgba(239, 68, 68, 0.35),
                inset 0 1px 0 rgba(255,255,255,0.15),
                0 0 0 1px rgba(239, 68, 68, 0.2) inset;
        }
    }

    /* ── Metric Cards ── */
    /* ═══════════════════════════════════════════════════ */
    /* METRIC CARDS - Clean & Modern */
    /* ═══════════════════════════════════════════════════ */
    .metric-card {
        background: var(--bg-card);
        backdrop-filter: blur(12px);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        padding: var(--space-xl);
        position: relative;
        transition: var(--transition-base);
        box-shadow: var(--shadow-md);
        cursor: default;
        overflow: hidden;
    }

    .metric-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; height: 2px;
        background: var(--accent-primary);
        opacity: 0.6;
        transition: var(--transition-base);
    }

    .metric-card:hover {
        background: var(--bg-card-hover);
        border-color: var(--border-default);
        transform: translateY(-4px);
        box-shadow: var(--shadow-lg);
    }

    .metric-card:hover::before {
        opacity: 1;
    }

    .metric-card.alert::before {
        background: var(--status-error);
    }

    .metric-card.warn::before {
        background: var(--status-warning);
    }

    .metric-card.green::before {
        background: var(--status-ok);
    }

    .metric-title {
        font-size: 0.6875rem;
        font-weight: 600;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        color: var(--text-tertiary);
        margin-bottom: var(--space-md);
        display: flex;
        align-items: center;
        gap: var(--space-xs);
    }

    .metric-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2rem;
        font-weight: 700;
        color: var(--text-primary);
        line-height: 1.1;
        margin-bottom: var(--space-xs);
        letter-spacing: -0.02em;
    }

    .metric-sub {
        font-size: 0.7rem;
        color: var(--text-muted);
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: 0.02em;
        display: flex;
        align-items: center;
        gap: 6px;
        opacity: 0.7;
    }

    /* ═══════════════════════════════════════════════════ */
    /* KPI STRIP - Professional Dashboard */
    /* ═══════════════════════════════════════════════════ */
    .kpi-strip {
        display: flex;
        gap: 12px;
        padding: 16px 0;
        margin-bottom: 8px;
    }
    .kpi-card {
        flex: 1;
        background: linear-gradient(145deg, rgba(30,41,59,0.8) 0%, rgba(15,23,42,0.9) 100%);
        border: 1px solid rgba(59,130,246,0.2);
        border-radius: 12px;
        padding: 16px 18px;
        display: flex;
        align-items: center;
        gap: 14px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        border-color: rgba(59,130,246,0.4);
        box-shadow: 0 8px 24px rgba(59,130,246,0.15);
    }
    .kpi-card.green { border-left: 3px solid #10b981; }
    .kpi-card.warn { border-left: 3px solid #f59e0b; }
    .kpi-card.alert { border-left: 3px solid #ef4444; }
    .kpi-icon {
        width: 40px;
        height: 40px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
        background: rgba(59,130,246,0.15);
        color: #3b82f6;
    }
    .kpi-card.green .kpi-icon { background: rgba(16,185,129,0.15); color: #10b981; }
    .kpi-card.warn .kpi-icon { background: rgba(245,158,11,0.15); color: #f59e0b; }
    .kpi-card.alert .kpi-icon { background: rgba(239,68,68,0.15); color: #ef4444; }
    .kpi-body { flex: 1; }
    .kpi-label {
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #64748b;
        margin-bottom: 2px;
    }
    .kpi-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.5rem;
        font-weight: 700;
        color: #f8fafc;
        line-height: 1.2;
    }
    .kpi-sub {
        font-size: 0.65rem;
        color: #64748b;
        margin-top: 2px;
    }

    /* ═══════════════════════════════════════════════════ */
    /* PANELS - Professional Container */
    /* ═══════════════════════════════════════════════════ */
    .panel {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: 16px;
        overflow: hidden;
        box-shadow: var(--shadow-md);
        margin-bottom: 16px;
    }
    .panel-header {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 16px 20px;
        background: var(--bg-tertiary);
        border-bottom: 1px solid var(--border-subtle);
    }
    .panel-icon {
        font-size: 1.3rem;
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(59,130,246,0.2);
        border-radius: 8px;
    }
    .panel-title {
        font-size: 1rem;
        font-weight: 700;
        color: #f8fafc;
        flex: 1;
        letter-spacing: -0.01em;
    }
    .panel-badge {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: #fff;
        font-size: 0.65rem;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 20px;
        letter-spacing: 0.1em;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    .panel-content {
        padding: 16px 20px;
    }

    /* ═══════════════════════════════════════════════════ */
    /* SECTION HEADINGS - Clean & Elegant */
    /* ═══════════════════════════════════════════════════ */
    .section-heading {
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--text-primary);
        letter-spacing: -0.02em;
        margin-bottom: var(--space-lg);
        display: flex;
        align-items: center;
        gap: var(--space-sm);
        padding-bottom: var(--space-md);
        border-bottom: 1px solid var(--border-subtle);
        position: relative;
    }

    .section-heading::before {
        content: '';
        position: absolute;
        bottom: -1px;
        left: 0;
        width: 60px;
        height: 2px;
        background: var(--accent-primary);
        border-radius: 1px;
    }

    /* ═══════════════════════════════════════════════════ */
    /* CARDS & CONTAINERS - Unified Style */
    /* ═══════════════════════════════════════════════════ */
    .card, .psd-container {
        background: var(--bg-card);
        backdrop-filter: blur(12px);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        padding: var(--space-xl);
        margin-bottom: var(--space-lg);
        box-shadow: var(--shadow-md);
        position: relative;
        overflow: hidden;
        transition: var(--transition-base);
    }

    .card:hover, .psd-container:hover {
        background: var(--bg-card-hover);
        border-color: var(--border-default);
        box-shadow: var(--shadow-lg);
    }

    .psd-container {
        padding: var(--space-2xl);
        margin-bottom: var(--space-xl);
    }

    .psd-container::before {
        content: '';
        position: absolute;
        inset: 0;
        background: radial-gradient(circle at top left, rgba(6, 182, 212, 0.05), transparent 50%);
        pointer-events: none;
    }

    .platform-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.812rem;
        color: var(--text-secondary);
        margin-bottom: 18px;
        font-weight: 600;
        letter-spacing: 0.02em;
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
    /* ═══════════════════════════════════════════════════ */
    /* DATA TABLES - Clean Modern */
    /* ═══════════════════════════════════════════════════ */
    [data-testid="stDataFrame"] {
        border: 1px solid var(--border-subtle) !important;
        border-radius: var(--radius-lg) !important;
        overflow: hidden !important;
        box-shadow: var(--shadow-md);
    }

    [data-testid="stDataFrame"] table {
        background: transparent !important;
    }

    [data-testid="stDataFrame"] th {
        background: var(--bg-tertiary) !important;
        color: var(--text-secondary) !important;
        font-weight: 600 !important;
        border-bottom: 1px solid var(--border-subtle) !important;
        font-size: 0.75rem !important;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        padding: var(--space-md) var(--space-lg) !important;
    }

    [data-testid="stDataFrame"] td {
        border-bottom: 1px solid var(--border-subtle) !important;
        color: var(--text-primary) !important;
        font-size: 0.875rem !important;
        padding: var(--space-md) var(--space-lg) !important;
    }

    [data-testid="stDataFrame"] tr:hover {
        background: var(--bg-card-hover) !important;
    }

    [data-testid="stDataFrame"] tr:last-child td {
        border-bottom: none;
    }

    /* Incident rows */
    .incident-row {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        padding: var(--space-lg);
        margin-bottom: var(--space-sm);
        display: flex;
        gap: var(--space-lg);
        align-items: center;
        transition: var(--transition-base);
        box-shadow: var(--shadow-sm);
    }

    .incident-row:hover {
        border-color: var(--accent-primary);
        box-shadow: var(--shadow-md);
        transform: translateX(4px);
    }

    .incident-row.critical { border-left: 3px solid var(--status-error); }
    .incident-row.warning { border-left: 3px solid var(--status-warning); }

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

    /* Team Cards */
    .team-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: var(--space-lg);
    }

    .team-card {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        padding: var(--space-xl);
        display: flex;
        gap: var(--space-lg);
        align-items: flex-start;
        transition: var(--transition-base);
        box-shadow: var(--shadow-md);
    }

    .team-card:hover {
        border-color: var(--accent-primary);
        transform: translateY(-4px);
        box-shadow: var(--shadow-lg);
    }

    .team-avatar img {
        width: 64px;
        height: 64px;
        border-radius: var(--radius-md);
        object-fit: cover;
        border: 2px solid var(--accent-primary);
    }

    .team-role {
        color: var(--accent-primary);
        font-size: 0.7rem;
        font-weight: 600;
        margin: 2px 0 8px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .team-name {
        color: var(--text-primary);
        font-weight: 700;
        font-size: 1rem;
        margin-bottom: 6px;
    }

    .team-desc {
        color: var(--text-secondary);
        font-size: 0.875rem;
        line-height: 1.6;
    }

    /* Tech Stack Rows */
    .tech-row {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        padding: var(--space-lg);
        margin-bottom: var(--space-sm);
        display: grid;
        grid-template-columns: 120px 1fr;
        gap: var(--space-lg);
        align-items: center;
        transition: var(--transition-base);
        box-shadow: var(--shadow-sm);
    }

    .tech-row:hover {
        border-color: var(--accent-primary);
        box-shadow: var(--shadow-md);
        transform: translateX(4px);
    }

    .tech-layer {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        color: var(--accent-tertiary);
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-weight: 600;
    }

    .tech-name {
        font-weight: 600;
        color: var(--text-primary);
        font-size: 0.9rem;
        margin-bottom: 4px;
    }

    .tech-detail {
        color: var(--text-tertiary);
        font-size: 0.8rem;
    }

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

    /* ── Performance Optimizations ── */
    [data-testid="stSidebar"] .stButton > button,
    [data-testid="stSidebar"] .stButton > button[kind="secondary"],
    .station-item,
    .module-item,
    .stat-item,
    .quick-action-btn {
        will-change: transform, box-shadow;
        transform: translateZ(0);
    }
    
    /* GPU acceleration for animations */
    @keyframes pulse-glow {
        0%, 100% { opacity: 0.4; transform: scale(1) translateZ(0); }
        50% { opacity: 0.8; transform: scale(1.15) translateZ(0); }
    }
    
    /* Smooth scrolling performance */
    html {
        scroll-behavior: smooth;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }
    
    /* Optimize scroll performance */
    .station-list {
        -webkit-overflow-scrolling: touch;
        scroll-behavior: smooth;
    }
    
    /* Reduce paint operations */
    [data-testid="stSidebar"] {
        contain: layout style paint;
    }

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
""",
    unsafe_allow_html=True,
)

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
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: #3b82f6;">
                <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                <path d="M2 17l10 5 10-5"/>
                <path d="M2 12l10 5 10-5"/>
            </svg>
            SicherGleis
        </div>
        <div class="brand-tagline">BahnSetu Pro</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # ── System Status Indicator (Sidebar) with Icons ──
    sidebar_icons = {
        "NORMAL": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>',
        "WARNING": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
        "ALERT": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>',
    }

    # Subtitle based on status
    status_subtitle = {
        "NORMAL": "All systems operational",
        "WARNING": "Attention required",
        "ALERT": "Immediate attention needed",
    }

    st.markdown(
        f"""
    <div class="system-status-indicator status-{sys_status.lower()}">
        <div class="status-icon-section">
            <div class="status-ring-pulse"></div>
            <div class="status-icon-large">
                {sidebar_icons[sys_status]}
            </div>
        </div>
        <div class="status-content">
            <div class="status-label-main">{sys_status}</div>
            <div class="status-label-sub">{status_subtitle[sys_status]}</div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="nav-divider"></div>', unsafe_allow_html=True)

    # ── TestVision Pro Button ──
    st.markdown("### 🧪 Test Analytics")
    st.markdown(
        '<a href="http://localhost:8502" target="_blank">'
        '<button style="background:linear-gradient(135deg,#3b82f6,#06b6d4);color:white;padding:12px 24px;border:none;border-radius:10px;font-weight:600;cursor:pointer;width:100%;">'
        '🚀 Open TestVision Pro'
        '</button></a>',
        unsafe_allow_html=True
    )
    st.caption("Test insights dashboard (port 8502)")

    # ── Station Selection (Modern Dropdown) ──
    st.markdown(
        """
        <style>
        .station-select-wrapper {
            margin-bottom: 16px;
        }
        .station-select-label {
            font-size: 0.65rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 1.5px;
            margin-bottom: 8px;
            font-weight: 600;
            display: block;
        }
        </style>
        <div class="station-select-wrapper">
            <div class="station-select-label">Select Station</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Get current station index
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

    # Show quick station info
    st.markdown(
        f"""
        <div style="background:var(--bg-card);border:1px solid var(--border-color);border-radius:10px;padding:12px;margin-top:12px;">
            <div style="font-size:0.6rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">Active Station</div>
            <div style="font-size:0.9rem;font-weight:600;color:var(--text-primary);">{st.session_state.current_station}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="nav-divider"></div>', unsafe_allow_html=True)

    # ── Modules ──
    st.markdown(
        '<div class="section-header-modern"><div class="section-title">Modules</div></div>',
        unsafe_allow_html=True,
    )

    modules = [
        ("ops", "📡 Live Operations"),
        ("forecast", "📈 Predictive Analytics"),
        ("incidents", "🚨 Incident Log"),
        ("network", "🌐 Network Overview"),
        ("financial", "💹 Financial Model"),
        ("customer", "👥 Customer Segments"),
        ("portfolio", "📁 Operator Portfolio"),
        ("kpi", "📊 KPI Dashboard"),
        ("company", "🏢 Company & Team"),
    ]
    for key, label in modules:
        is_active = st.session_state.active_tab == key
        if st.button(
            label=label,
            key=f"tab_{key}",
            type="primary" if is_active else "secondary",
            use_container_width=True,
        ):
            st.session_state.active_tab = key
            st.rerun()

    st.markdown('<div class="nav-divider"></div>', unsafe_allow_html=True)

    # ── Footer ──
    st.markdown(
        """
    <div class="sidebar-footer">
        <div style="font-size:0.7rem;color:var(--text-secondary);font-weight:600;margin-bottom:4px;">
            ⚡ BahnSetu GmbH
        </div>
        <div class="footer-version">v2.1.81 | © 2025</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

# ═══════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════
current_station = st.session_state.get("current_station", "Hauptbahnhof")
try:
    gates_total, gates_active, p_total, alerts, avg_sync, warnings, _ = get_metrics(
        df, current_station
    )
except:
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
            op_row = customer_df[customer_df["customer_id"] == selected_op_id]
            if not op_row.empty:
                display_title = op_row.iloc[0]["customer_name"]
        except:
            pass
elif active_tab == "kpi":
    display_title = "KPI Dashboard"
    display_sub = "KEY PERFORMANCE INDICATORS // OVERVIEW"
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
                "train": str(row.train) if pd.notna(row.train) and row.train else "",
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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Space+Grotesk:wght@400;500;600;700;800&display=swap');

/* ── CSS VARIABLES & THEME ───────────────────────────────────────────── */
:root {
  --bg-primary: #060c1a;
  --bg-secondary: #0a1221;
  --bg-glass: rgba(255, 255, 255, 0.03);
  --bg-glass-hover: rgba(30, 41, 59, 0.8);
  --border-color: rgba(30, 41, 59, 0.6);
  --border-glow: rgba(59, 130, 246, 0.3);
  --text-primary: #f8fafc;
  --text-secondary: #cbd5e1;
  --text-muted: #64748b;
  --accent-blue: #3b82f6;
  --accent-cyan: #06b6d4;
  --accent-teal: #14b8a6;
  --accent-purple: #8b5cf6;
  --success: #10b981;
  --warning: #f59e0b;
  --danger: #ef4444;
  --glass-border: rgba(255, 255, 255, 0.15);
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.2), 0 1px 3px 0 rgba(0, 0, 0, 0.1);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.15);
  --shadow-lg: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
  --shadow-glow: 0 0 20px rgba(59, 130, 246, 0.15);
}
/* Global typography tweaks for cleaner, higher-contrast UI */
body {
  font-family: Inter, system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif;
  color: var(--text-primary);
  background: var(--bg-primary);
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: 'Space Grotesk', sans-serif;
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
    #f59e0b 0px,
    #f59e0b 16px,
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
  background: #f59e0b;
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
  animation: wheel-spin 0.8s linear infinite;
}

.wheel.slow-spin {
  animation: wheel-spin 1.5s linear infinite;
}

@keyframes wheel-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
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
  border-color: #10b981;
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
  border-color: #ef4444;
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
    #ef4444 50%,
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
  background: linear-gradient(90deg, #10b981, #059669);
  box-shadow: 0 0 10px rgba(16, 185, 129, 0.8);
}

.led-jm {
  background: linear-gradient(90deg, #ef4444, #dc2626);
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
      <div class="bldgs" id="bg${idx}"></div>
      <div class="plat-floor"></div>
      <div class="edge-strip"></div>
      <div class="track" id="tr${idx}"></div>
      <div class="train-wrap" id="tw${idx}"></div>
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
    const cw=loco?128:108, ch=loco?62:52;
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


# ═══════════════════════════════════════════════════
# ── TAB: LIVE OPERATIONS ──────────────────────────
# ═══════════════════════════════════════════════════
if active_tab == "ops":
    # ── KPI Row ──
    st.markdown('<div class="kpi-strip">', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    kpis = [
        (c1, "PSD Gates", f"{gates_active}/{gates_total}", "Active Systems", ""),
        (
            c2,
            "Sync Efficiency",
            f"{avg_sync}%",
            "Door Alignment",
            "green" if avg_sync >= 85 else "warn",
        ),
        (c3, "Passenger Flow", f"{p_total:,}", "On Platform", ""),
        (
            c4,
            "Critical Alerts",
            str(alerts),
            "Immediate Action",
            "alert" if alerts > 0 else "green",
        ),
        (
            c5,
            "Warnings",
            str(warnings),
            "Under Observation",
            "warn" if warnings > 0 else "green",
        ),
    ]
    for col, title, val, sub, cls in kpis:
        with col:
            st.markdown(
                f"""
            <div class="kpi-card {cls}">
                <div class="kpi-icon">{("&#9888;" if cls == "alert" else "&#10003;" if cls == "green" else "&#9888;" if cls == "warn" else "&#9679;")}</div>
                <div class="kpi-body">
                    <div class="kpi-label">{title}</div>
                    <div class="kpi-value">{val}</div>
                    <div class="kpi-sub">{sub}</div>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Main Split ──
    left, right = st.columns([65, 35])

    with left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown(
            '<div class="panel-header">'
            '<span class="panel-icon">&#128646;</span>'
            '<span class="panel-title">Live Platform Simulation</span>'
            "</div>",
            unsafe_allow_html=True,
        )

        station_data = df[df["station"] == current_station].copy()
        num_platforms = station_data["platform"].nunique()
        anim_html = build_train_animation(current_station, station_data)
        anim_height = num_platforms * 295 + 60
        components.html(anim_html, height=anim_height, scrolling=False)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown(
            '<div class="panel-header">'
            '<span class="panel-icon">&#128202;</span>'
            '<span class="panel-title">Sensor Analytics</span>'
            "</div>",
            unsafe_allow_html=True,
        )

        cycles_df, temp_df = get_psd_analytics(current_station)

        fig_temp = go.Figure()
        fig_temp.add_trace(
            go.Scatter(
                x=temp_df["Hour"],
                y=temp_df["Avg Temp (°C)"],
                mode="lines+markers",
                line=dict(color="#ef4444", width=2, shape="spline"),
                marker=dict(size=5, color="#ef4444"),
                fill="tozeroy",
                fillcolor="rgba(239,68,68,0.08)",
                name="Temp (°C)",
            )
        )
        fig_temp.add_hline(
            y=45,
            line_dash="dot",
            line_color="#f97316",
            annotation_text="Warning",
            annotation_font_color="#f97316",
        )
        fig_temp.update_layout(
            height=320,
            margin=dict(l=0, r=0, b=24, t=8),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94a3b8", family="Inter", size=10),
            yaxis=dict(
                gridcolor="rgba(30,41,59,0.5)",
                zeroline=False,
                tickfont=dict(size=9, color="#94a3b8"),
            ),
            xaxis=dict(
                gridcolor="rgba(30,41,59,0.5)", tickfont=dict(size=9, color="#94a3b8")
            ),
            showlegend=False,
            hovermode="x unified",
            hoverlabel=dict(
                bgcolor="rgba(17,24,39,0.98)",
                bordercolor="#3b82f6",
                font_color="#f1f5f9",
                font_size=10,
            ),
        )
        st.markdown('<div class="panel-content">', unsafe_allow_html=True)
        st.plotly_chart(fig_temp, use_container_width=True)

        fig_cycles = px.bar(cycles_df, x="Hour", y="Door Cycles")
        fig_cycles.update_traces(
            marker_color="#3b82f6",
            marker_line_width=0,
            hovertemplate="<b>Hour</b>: %{x}<br><b>Cycles</b>: %{y}<extra></extra>",
        )
        fig_cycles.update_layout(
            height=320,
            margin=dict(l=0, r=0, b=24, t=8),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94a3b8", family="Inter", size=10),
            yaxis=dict(
                gridcolor="rgba(30,41,59,0.5)",
                zeroline=False,
                tickfont=dict(size=9, color="#94a3b8"),
            ),
            xaxis=dict(
                gridcolor="rgba(30,41,59,0.5)", tickfont=dict(size=9, color="#94a3b8")
            ),
            showlegend=False,
            hovermode="x unified",
            hoverlabel=dict(
                bgcolor="rgba(17,24,39,0.98)",
                bordercolor="#3b82f6",
                font_color="#f1f5f9",
                font_size=10,
            ),
        )
        st.plotly_chart(fig_cycles, use_container_width=True)
        st.markdown("</div></div>", unsafe_allow_html=True)

    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

    # ── Sensor Logs ──
    st.markdown(
        '<div class="section-heading animate-fade-in">Detailed Sensor Logs</div>',
        unsafe_allow_html=True,
    )

    def color_temp(val):
        """Color-code temperature cells without matplotlib."""
        if val > 45:
            return "background-color: #7f1d1d; color: #fca5a5; font-weight:700"
        elif val > 35:
            return "background-color: #78350f; color: #fcd34d; font-weight:600"
        elif val > 28:
            return "background-color: #1c3a1c; color: #86efac"
        return ""

    def color_risk(val):
        """Color-code risk score cells without matplotlib."""
        if val >= 70:
            return "background-color: #7f1d1d; color: #fca5a5; font-weight:700"
        elif val >= 40:
            return "background-color: #78350f; color: #fcd34d; font-weight:600"
        elif val >= 20:
            return "background-color: #1c3a1c; color: #86efac"
        return ""

    def color_status(val):
        """Color-code maintenance status cells."""
        colors = {
            "CRITICAL": "color: #ef4444; font-weight:700",
            "WARNING": "color: #f59e0b; font-weight:600",
            "MONITOR": "color: #60a5fa",
            "OPTIMAL": "color: #10b981",
        }
        return colors.get(val, "")

    display_cols = [
        "platform",
        "gate_id",
        "train",
        "door_state",
        "sensor_temp",
        "sensor_vib",
        "sync_score",
        "risk_score",
        "maintenance_status",
        "people",
    ]
    styled = (
        station_data[display_cols]
        .sort_values(["platform", "gate_id"])
        .style.map(color_temp, subset=["sensor_temp"])
        .map(color_risk, subset=["risk_score"])
        .map(color_status, subset=["maintenance_status"])
        .format(
            {
                "sensor_temp": "{:.1f}°C",
                "sensor_vib": "{:.2f} mm/s",
                "sync_score": "{}%",
                "risk_score": "{}/100",
            }
        )
    )
    st.dataframe(styled, use_container_width=True, hide_index=True)

    # Export button for ops sensor logs
    ops_csv = convert_to_csv(
        station_data[display_cols].sort_values(["platform", "gate_id"])
    )
    st.download_button(
        "📥 Export Sensor Logs (CSV)",
        data=ops_csv,
        file_name=f"station_sensor_logs_{current_station.replace(' ', '_')}.csv",
        mime="text/csv",
    )


# ═══════════════════════════════════════════════════
# ── TAB: NETWORK OVERVIEW ─────────────────────────
# ═══════════════════════════════════════════════════
elif active_tab == "network":
    with st.spinner("Loading network data..."):
        net = get_network_summary(df)

    # ── Network KPIs ──
    st.markdown('<div class="kpi-strip">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    kpis_net = [
        (
            c1,
            "Network Gates",
            f"{net['total_gates']}",
            f"Across {len(stations)} Stations",
            "",
        ),
        (c2, "Optimal Gates", f"{net['optimal_count']}", "Running Normally", "green"),
        (
            c3,
            "Network Alerts",
            f"{net['critical_count']}",
            "Critical Incidents",
            "alert",
        ),
        (c4, "Total Passengers", f"{net['total_people']:,}", "On All Platforms", ""),
    ]
    for col, title, val, sub, cls in kpis_net:
        with col:
            st.markdown(
                f"""
            <div class="kpi-card {cls}">
                <div class="kpi-icon">{("&#128270;" if cls == "" else "&#10003;" if cls == "green" else "&#9888;" if cls == "alert" else "&#9679;")}</div>
                <div class="kpi-body">
                    <div class="kpi-label">{title}</div>
                    <div class="kpi-value">{val}</div>
                    <div class="kpi-sub">{sub}</div>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Business Network Map (Germany) ──
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown(
        '<div class="panel-header">'
        '<span class="panel-icon">&#127760;</span>'
        '<span class="panel-title">Business Network Map - Germany</span>'
        "</div>",
        unsafe_allow_html=True,
    )

    # Phase summary cards
    try:
        map_df = get_business_map_data()

        st.markdown(
            """
        <style>
        .phase-summary {display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap;}
        .phase-card {flex: 1; min-width: 140px; background: rgba(255,255,255,0.03);
                     border: 1px solid rgba(255,255,255,0.08); border-radius: 8px;
                     padding: 12px 16px; display: flex; align-items: center; gap: 10px;}
        .phase-dot {width: 10px; height: 10px; border-radius: 50%;}
        .phase-label {font-size: 13px; color: #94a3b8;}
        .phase-count {font-size: 20px; font-weight: 700; color: #fff; margin-left: auto;}
        </style>
        """,
            unsafe_allow_html=True,
        )

        summary_html = '<div class="phase-summary">'
        for label, color in [
            ("Established", "#3b82f6"),
            ("Present", "#06b6d4"),
            ("Expanding", "#f59e0b"),
            ("Future", "#10b981"),
        ]:
            cnt = len(map_df[map_df["status"] == label])
            summary_html += f"""
            <div class="phase-card">
                <div class="phase-dot" style="background:{color};box-shadow:0 0 10px {color}80;"></div>
                <span class="phase-label">{label}</span>
                <span class="phase-count">{cnt}</span>
            </div>"""
        summary_html += "</div>"
        st.markdown(summary_html, unsafe_allow_html=True)

        # Phase configuration
        phase_colors = {
            "Established": "#3b82f6",
            "Present": "#06b6d4",
            "Expanding": "#f59e0b",
            "Future": "#10b981",
        }

        # Pre-render all maps once and cache aggressively for instant loading
        @st.cache_data(show_spinner=False, ttl=3600)
        def create_all_maps_cached():
            import io
            import matplotlib.pyplot as plt
            from matplotlib.patches import Circle
            from matplotlib.collections import PatchCollection

            phases = ["Established", "Present", "Expanding", "Future"]
            # More vibrant, realistic colors
            colors = {
                "Established": "#22d3ee",  # Bright cyan
                "Present": "#818cf8",  # Indigo
                "Expanding": "#fcd34d",  # Amber gold
                "Future": "#34d399",  # Emerald green
            }
            map_figs = {}

            for phase in phases:
                phase_df = map_df[map_df["status"] == phase]
                color = colors[phase]

                # High quality figure
                fig, ax = plt.subplots(
                    figsize=(7, 6),
                    dpi=150,
                    subplot_kw=dict(projection=ccrs.PlateCarree()),
                )
                ax.set_facecolor("#080c16")

                ax.set_extent([5.8, 15.2, 47.1, 55.2], crs=ccrs.PlateCarree())

                # Realistic terrain colors - darker, richer
                ax.add_feature(cfeature.LAND, facecolor="#162a4d", edgecolor="none")
                ax.add_feature(cfeature.OCEAN, facecolor="#080c16")
                ax.add_feature(
                    cfeature.COASTLINE, edgecolor="#22d3ee", linewidth=0.5, alpha=0.7
                )
                ax.add_feature(
                    cfeature.BORDERS, edgecolor="#4b5563", linewidth=0.4, alpha=0.6
                )
                ax.add_feature(
                    cfeature.LAKES, facecolor="#0f172a", edgecolor="none", alpha=0.5
                )
                ax.add_feature(
                    cfeature.RIVERS, edgecolor="#1e40af", linewidth=0.6, alpha=0.4
                )

                # Glow effect markers - larger and more visible
                sizes = {
                    "Established": 200,
                    "Present": 170,
                    "Expanding": 140,
                    "Future": 110,
                }
                s = sizes.get(phase, 80)

                if len(phase_df) > 0:
                    # Outer glow (larger, transparent)
                    ax.scatter(
                        phase_df["lon"],
                        phase_df["lat"],
                        s=s * 1.8,
                        c=color,
                        alpha=0.25,
                        edgecolors="none",
                        transform=ccrs.Geodetic(),
                        zorder=3,
                    )
                    # Middle glow
                    ax.scatter(
                        phase_df["lon"],
                        phase_df["lat"],
                        s=s * 1.4,
                        c=color,
                        alpha=0.4,
                        edgecolors="none",
                        transform=ccrs.Geodetic(),
                        zorder=4,
                    )
                    # Main marker
                    ax.scatter(
                        phase_df["lon"],
                        phase_df["lat"],
                        s=s,
                        c=color,
                        alpha=1.0,
                        edgecolors="white",
                        linewidths=1.2,
                        transform=ccrs.Geodetic(),
                        zorder=6,
                    )
                    # Bright center
                    ax.scatter(
                        phase_df["lon"],
                        phase_df["lat"],
                        s=s * 0.3,
                        c="white",
                        alpha=0.9,
                        edgecolors="none",
                        transform=ccrs.Geodetic(),
                        zorder=7,
                    )

                    # Station labels with better styling
                    for _, row in phase_df.iterrows():
                        name = (
                            row["station"]
                            .replace(" Hbf", "")
                            .replace(" (Main)", "")
                            .replace(" Hauptbahnhof", "")
                        )
                        ax.annotate(
                            name,
                            (row["lon"], row["lat"]),
                            xytext=(8, 8),
                            textcoords="offset points",
                            fontsize=8,
                            color="#f8fafc",
                            fontweight="bold",
                            fontfamily="sans-serif",
                            bbox=dict(
                                boxstyle="round,pad=0.3",
                                facecolor="#1e293b",
                                edgecolor=color,
                                alpha=0.95,
                                linewidth=1,
                            ),
                            annotation_clip=False,
                            zorder=10,
                        )

                try:
                    ax.outline_patch.set_visible(False)
                except:
                    pass
                try:
                    ax.spines["geo"].set_visible(False)
                except:
                    pass
                ax.set_xticks([])
                ax.set_yticks([])
                ax.tick_params(axis="both", length=0)
                fig.patch.set_facecolor("#080c16")
                fig.patch.set_alpha(0)

                # Save as high-quality PNG
                buf = io.BytesIO()
                fig.savefig(
                    buf,
                    format="png",
                    bbox_inches="tight",
                    pad_inches=0.15,
                    facecolor="#080c16",
                    dpi=150,
                )
                buf.seek(0)
                map_figs[phase] = buf.getvalue()
                plt.close(fig)

            return map_figs

        # Show skeleton while loading (first time only)
        with st.spinner("Loading maps..."):
            all_maps = create_all_maps_cached()

        from PIL import Image
        import io

        st.markdown(
            """
            <style>
            .map-panel {background: #0a0f1a; border: 1px solid rgba(59,130,246,0.2); border-radius: 10px; padding: 8px; margin-bottom: 14px;}
            .map-header {background: rgba(15,23,42,0.98); padding: 8px 12px; display: flex; align-items: center; justify-content: space-between; border-radius: 6px; margin-bottom: 6px;}
            .map-title {font-size: 11px; font-weight: 600; color: #e2e8f0; text-transform: uppercase; letter-spacing: 0.8px;}
            .map-count {background: rgba(59,130,246,0.3); color: #60a5fa; padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: 700;}
            .map-img {width: 100%; border-radius: 6px;}
            .skeleton {background: linear-gradient(90deg, #1e293b 25%, #334155 50%, #1e293b 75%); background-size: 200% 100%; animation: skeleton-loading 1.5s infinite;}
            @keyframes skeleton-loading {0% {background-position: 200% 0;} 100% {background-position: -200% 0;}}
            </style>
            """,
            unsafe_allow_html=True,
        )

        phase_order = ["Established", "Present", "Expanding", "Future"]
        col_left, col_right = st.columns(2)

        for idx, phase in enumerate(phase_order):
            phase_df = map_df[map_df["status"] == phase]
            color = phase_colors[phase]
            station_count = len(phase_df)

            col = col_left if idx < 2 else col_right

            with col:
                st.markdown(
                    f"""
                    <div class="map-panel">
                        <div class="map-header" style="border-left: 3px solid {color};">
                            <span class="map-title" style="color: {color};">{phase}</span>
                            <span class="map-count">{station_count}</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                # Load from cached bytes - instant!
                img = Image.open(io.BytesIO(all_maps[phase]))
                st.image(img, use_container_width=True, output_format="PNG")

    except Exception as e:
        st.error(f"Could not load business map: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Main Content Grid ──
    left, right = st.columns([55, 45])

    with left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown(
            '<div class="panel-header">'
            '<span class="panel-icon">&#128202;</span>'
            '<span class="panel-title">Station Performance Matrix</span>'
            "</div>"
            '<div class="panel-content">',
            unsafe_allow_html=True,
        )
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

        # Export station performance matrix
        matrix_csv = convert_to_csv(net["station_summary"])
        st.download_button(
            "📥 Export Station Matrix (CSV)",
            data=matrix_csv,
            file_name="station_performance_matrix.csv",
            mime="text/csv",
        )
        st.markdown("</div></div>", unsafe_allow_html=True)

        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown(
            '<div class="panel-header">'
            '<span class="panel-icon">&#128100;</span>'
            '<span class="panel-title">Passengers by Station</span>'
            "</div>"
            '<div class="panel-content">',
            unsafe_allow_html=True,
        )
        fig_pass = px.bar(
            net["station_summary"].sort_values("Passengers", ascending=True),
            x="Passengers",
            y="Station",
            orientation="h",
            color="Avg Risk",
            color_continuous_scale=["#10b981", "#f59e0b", "#ef4444"],
            range_color=[0, 100],
            title="",
        )
        fig_pass.update_layout(
            height=320,
            margin=dict(l=0, r=0, b=20, t=10),
            paper_bgcolor="rgba(10, 14, 23, 0)",
            plot_bgcolor="rgba(10, 14, 23, 0)",
            font=dict(color="#94a3b8", family="Inter", size=11),
            yaxis=dict(gridcolor="rgba(30, 41, 59, 0.3)", tickfont=dict(size=10)),
            xaxis=dict(gridcolor="rgba(30, 41, 59, 0.3)", tickfont=dict(size=10)),
            coloraxis_colorbar=dict(
                title=dict(text="Risk", font=dict(color="#94a3b8", size=10)),
                tickfont=dict(color="#94a3b8", size=9),
                thickness=6,
                len=0.7,
            ),
            hovermode="y unified",
            hoverlabel=dict(
                bgcolor="rgba(17, 24, 39, 0.95)",
                bordercolor="#3b82f6",
                font_color="#f1f5f9",
                font_size=11,
            ),
        )
        fig_pass.update_traces(
            hovertemplate="<b>Station</b>: %{y}<br><b>Passengers</b>: %{x:,}<br><b>Avg Risk</b>: ~%{customdata[0]:.0f}/100<extra></extra>",
            customdata=net["station_summary"][["Avg Risk"]].values,
        )
        st.plotly_chart(fig_pass, use_container_width=True)
        st.markdown("</div></div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown(
            '<div class="panel-header">'
            '<span class="panel-icon">&#9881;</span>'
            '<span class="panel-title">Maintenance Status</span>'
            "</div>"
            '<div class="panel-content">',
            unsafe_allow_html=True,
        )
        color_map = {
            "OPTIMAL": "#10b981",
            "MONITOR": "#60a5fa",
            "WARNING": "#f59e0b",
            "CRITICAL": "#ef4444",
        }
        fig_pie = px.pie(
            net["status_dist"],
            names="maintenance_status",
            values="Count",
            color="maintenance_status",
            color_discrete_map=color_map,
            hole=0.5,
        )
        fig_pie.update_layout(
            height=300,
            margin=dict(l=5, r=5, b=5, t=5),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94a3b8", family="Inter", size=9),
            showlegend=True,
            hoverlabel=dict(
                bgcolor="rgba(17, 24, 39, 0.95)",
                bordercolor="#3b82f6",
                font_color="#f1f5f9",
                font_size=10,
            ),
        )
        fig_pie.update_traces(
            textposition="inside",
            textinfo="percent",
            textfont_size=8,
            textfont_color="#f1f5f9",
            marker_line_color="rgba(30, 41, 59, 0.3)",
            marker_line_width=1,
            hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>",
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        st.markdown("</div></div>", unsafe_allow_html=True)

        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown(
            '<div class="panel-header">'
            '<span class="panel-icon">&#128642;</span>'
            '<span class="panel-title">Train Types</span>'
            "</div>"
            '<div class="panel-content">',
            unsafe_allow_html=True,
        )
        if not net["train_type_dist"].empty:
            train_colors = px.colors.qualitative.Set3
            fig_train = px.pie(
                net["train_type_dist"], names="train_type", values="Count", hole=0.5
            )
            fig_train.update_layout(
                height=300,
                margin=dict(l=5, r=5, b=5, t=5),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94a3b8", family="Inter", size=9),
                showlegend=True,
                hoverlabel=dict(
                    bgcolor="rgba(17, 24, 39, 0.95)",
                    bordercolor="#3b82f6",
                    font_color="#f1f5f9",
                    font_size=10,
                ),
            )
            fig_train.update_traces(
                textposition="inside",
                textinfo="percent",
                textfont_size=8,
                textfont_color="#f1f5f9",
                marker_line_color="rgba(30, 41, 59, 0.3)",
                marker_line_width=1,
                hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percentage: ~%{percent:.0%}<extra></extra>",
            )
            st.plotly_chart(fig_train, use_container_width=True)
        else:
            st.markdown(
                '<div style="text-align: center; color: #64748b; font-size: 0.8rem; padding: 20px;">No train type data available</div>',
                unsafe_allow_html=True,
            )
        st.markdown("</div></div>", unsafe_allow_html=True)

        # Door State Distribution
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown(
            '<div class="panel-header">'
            '<span class="panel-icon">&#128682;</span>'
            '<span class="panel-title">Door State Distribution</span>'
            "</div>"
            '<div class="panel-content">',
            unsafe_allow_html=True,
        )
        door_color = {
            "closed": "#1565c0",
            "open": "#10b981",
            "jammed": "#ef4444",
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
        fig_door.update_layout(
            height=320,
            margin=dict(l=0, r=0, b=30, t=10),
            paper_bgcolor="rgba(10, 14, 23, 0)",
            plot_bgcolor="rgba(10, 14, 23, 0)",
            font=dict(color="#64748b", family="Inter", size=10),
            yaxis=dict(
                gridcolor="rgba(30, 41, 59, 0.4)",
                tickfont=dict(size=9, color="#94a3b8"),
                title="",
            ),
            xaxis=dict(
                gridcolor="rgba(30, 41, 59, 0.4)",
                tickfont=dict(size=9, color="#94a3b8"),
                title="",
                categoryorder="array",
                categoryarray=["closed", "open", "closing", "jammed"],
            ),
            showlegend=True,
            hovermode="x unified",
            hoverlabel=dict(
                bgcolor="rgba(17, 24, 39, 0.95)",
                bordercolor="#3b82f6",
                font_color="#f1f5f9",
                font_size=10,
            ),
        )
        fig_door.update_traces(
            hovertemplate="<b>State</b>: %{x}<br><b>Count</b>: %{y}<extra></extra>"
        )
        st.plotly_chart(fig_door, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Operator Performance
        if not net["operator_stats"].empty:
            st.markdown(
                '<div class="section-heading">Operator Performance</div>',
                unsafe_allow_html=True,
            )

            # Use styled dataframe for better rendering compatibility
            op_display = net["operator_stats"].copy()
            op_display = op_display.rename(
                columns={"Avg Sync %": "Sync %", "Avg Risk": "Risk"}
            )

            def style_sync(val):
                if val >= 85:
                    return "color: #10b981; font-weight: 600;"
                elif val >= 70:
                    return "color: #f59e0b; font-weight: 600;"
                else:
                    return "color: #ef4444; font-weight: 600;"

            def style_risk(val):
                if val <= 20:
                    return "color: #10b981; font-weight: 600;"
                elif val <= 40:
                    return "color: #f59e0b; font-weight: 600;"
                else:
                    return "color: #ef4444; font-weight: 600;"

            styled_op = (
                op_display.style.format({"Sync %": "{:.1f}%", "Risk": "{:.1f}"})
                .map(style_sync, subset=["Sync %"])
                .map(style_risk, subset=["Risk"])
            )
            st.dataframe(styled_op, use_container_width=True, hide_index=True)

            # Export operator stats
            op_csv = convert_to_csv(net["operator_stats"])
            st.download_button(
                "📥 Export Operator Stats (CSV)",
                data=op_csv,
                file_name="network_operator_stats.csv",
                mime="text/csv",
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Network Health Metrics
        st.markdown(
            '<div class="section-heading">Network Health</div>', unsafe_allow_html=True
        )
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.markdown(
                f'<div style="background: rgba(26, 35, 50, 0.4); border-radius: 8px; padding: 12px; text-align: center; border: 1px solid rgba(148, 163, 184, 0.1);"><div style="font-size: 0.7rem; color: #94a3b8; margin-bottom: 4px;">Sync Score</div><div style="font-size: 1.2rem; font-weight: 700; color: #3b82f6;">{net["network_sync"]}%</div></div>',
                unsafe_allow_html=True,
            )
        with col_b:
            st.markdown(
                f'<div style="background: rgba(26, 35, 50, 0.4); border-radius: 8px; padding: 12px; text-align: center; border: 1px solid rgba(148, 163, 184, 0.1);"><div style="font-size: 0.7rem; color: #94a3b8; margin-bottom: 4px;">Avg Risk</div><div style="font-size: 1.2rem; font-weight: 700; color: #f59e0b;">{net["network_risk"]}/100</div></div>',
                unsafe_allow_html=True,
            )
        with col_c:
            health_color = (
                "#10b981"
                if net["network_health"] >= 80
                else "#f59e0b"
                if net["network_health"] >= 60
                else "#ef4444"
            )
            st.markdown(
                f'<div style="background: rgba(26, 35, 50, 0.4); border-radius: 8px; padding: 12px; text-align: center; border: 1px solid rgba(148, 163, 184, 0.1);"><div style="font-size: 0.7rem; color: #94a3b8; margin-bottom: 4px;">Health Score</div><div style="font-size: 1.2rem; font-weight: 700; color: {health_color};">{net["network_health"]}</div></div>',
                unsafe_allow_html=True,
            )


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
            '<div class="panel-content" style="text-align:center;padding:40px;color:#64748b;">'
            "✓ No active incidents. All systems operating normally."
            "</div></div>",
            unsafe_allow_html=True,
        )
    else:
        crit = (incidents["Severity"].str.contains("CRITICAL")).sum()
        warn = (incidents["Severity"].str.contains("WARNING")).sum()

        st.markdown('<div class="kpi-strip">', unsafe_allow_html=True)
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
        st.markdown("</div>", unsafe_allow_html=True)

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
            border_col = "#ef4444" if cls == "critical" else "#f59e0b"
            st.markdown(
                f"""
            <div class="incident-row {cls}" style="border-left-color:{border_col};">
                <div style="font-family:'JetBrains Mono'; font-size:0.75rem; color:#64748b; min-width:50px;">{row["Time"]}</div>
                <div style="min-width:70px;font-weight:600;color:{"#ef4444" if "CRITICAL" in row["Severity"] else "#f59e0b"};">{row["Severity"]}</div>
                <div style="font-size:0.78rem; color:#94a3b8; min-width:100px;">{row["Station"][:14]}…</div>
                <div style="font-size:0.78rem; color:#e2e8f0; flex:1;">{row["Description"]}</div>
                <div style="font-family:'JetBrains Mono'; font-size:0.72rem; color:#64748b;">
                    {row["Temp (°C)"]}°C | {row["Vibration"]} mm/s
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )
        st.markdown("</div></div>", unsafe_allow_html=True)

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
        st.markdown("</div></div>", unsafe_allow_html=True)

        # ── Enhanced Analytics Sections ──
        st.markdown(
            '<div class="section-heading">Incident Analytics</div>',
            unsafe_allow_html=True,
        )

        col_inc1, col_inc2 = st.columns(2)

        with col_inc1:
            st.markdown(
                '<div style="font-size:0.85rem;font-weight:600;color:#94a3b8;margin-bottom:10px;">Incidents by Station</div>',
                unsafe_allow_html=True,
            )
            station_counts = incidents.groupby("Station").size().reset_index(name="Count")
            fig_station = px.bar(
                station_counts,
                x="Station",
                y="Count",
                color="Count",
                color_continuous_scale=["#0d47a1", "#0288d1", "#00b4d8"],
                text="Count",
            )
            fig_station.update_layout(
                height=250,
                margin=dict(l=20, r=20, b=40, t=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94a3b8", size=10),
                xaxis=dict(tickfont=dict(size=9, color="#94a3b8")),
                yaxis=dict(tickfont=dict(size=9, color="#94a3b8")),
                coloraxis_colorbar=dict(
                    title=dict(text="Count", font=dict(color="#94a3b8", size=10)),
                    tickfont=dict(color="#94a3b8", size=9),
                ),
            )
            fig_station.update_traces(textposition="outside", marker_line_width=0)
            st.plotly_chart(fig_station, use_container_width=True)

        with col_inc2:
            st.markdown(
                '<div style="font-size:0.85rem;font-weight:600;color:#94a3b8;margin-bottom:10px;">Severity Distribution</div>',
                unsafe_allow_html=True,
            )
            severity_counts = incidents["Severity"].value_counts().reset_index()
            severity_counts.columns = ["Severity", "Count"]
            fig_severity = px.pie(
                severity_counts,
                values="Count",
                names="Severity",
                color_discrete_sequence=["#ef4444", "#f59e0b"],
                hole=0.5,
            )
            fig_severity.update_layout(
                height=250,
                margin=dict(l=20, r=20, b=20, t=20),
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94a3b8", size=10),
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.1,
                    xanchor="center",
                    x=0.5,
                    font=dict(color="#94a3b8", size=9),
                ),
            )
            fig_severity.update_traces(
                textinfo="percent+label",
                hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>",
            )
            st.plotly_chart(fig_severity, use_container_width=True)

        col_inc3, col_inc4 = st.columns(2)

        with col_inc3:
            st.markdown(
                '<div style="font-size:0.85rem;font-weight:600;color:#94a3b8;margin-bottom:10px;margin-top:20px;">Incidents by Hour</div>',
                unsafe_allow_html=True,
            )
            incidents["Hour"] = incidents["Time"].str.split(":").str[0].astype(int)
            hour_counts = incidents.groupby("Hour").size().reset_index(name="Count")
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
            fig_hour.update_layout(
                height=220,
                margin=dict(l=20, r=20, b=40, t=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94a3b8", size=10),
                xaxis=dict(
                    tickmode="linear",
                    tick0=0,
                    dtick=2,
                    tickfont=dict(size=9, color="#94a3b8"),
                    title=dict(text="Hour", font=dict(color="#94a3b8", size=10)),
                ),
                yaxis=dict(tickfont=dict(size=9, color="#94a3b8")),
                hovermode="x unified",
            )
            fig_hour.update_traces(
                hovertemplate="<b>Hour</b>: %{x}:00<br><b>Incidents</b>: %{y}<extra></extra>"
            )
            st.plotly_chart(fig_hour, use_container_width=True)

        with col_inc4:
            st.markdown(
                '<div style="font-size:0.85rem;font-weight:600;color:#94a3b8;margin-bottom:10px;margin-top:20px;">Platform Distribution</div>',
                unsafe_allow_html=True,
            )
            platform_counts = incidents.groupby("Platform").size().reset_index(name="Count")
            fig_platform = px.bar(
                platform_counts,
                x="Platform",
                y="Count",
                color="Count",
                color_continuous_scale=["#10b981", "#34d399", "#6ee7b7"],
                text="Count",
            )
            fig_platform.update_layout(
                height=220,
                margin=dict(l=20, r=20, b=40, t=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94a3b8", size=10),
                xaxis=dict(tickfont=dict(size=9, color="#94a3b8")),
                yaxis=dict(tickfont=dict(size=9, color="#94a3b8")),
            )
            fig_platform.update_traces(textposition="outside", marker_line_width=0)
            st.plotly_chart(fig_platform, use_container_width=True)

        st.markdown(
            '<div style="font-size:0.85rem;font-weight:600;color:#94a3b8;margin-bottom:10px;margin-top:20px;">Temperature vs Incidents</div>',
            unsafe_allow_html=True,
        )
        fig_temp_scatter = px.scatter(
            incidents,
            x="Temp (°C)",
            y="Vibration",
            color="Severity",
            color_discrete_map={"🔴 CRITICAL": "#ef4444", "🟡 WARNING": "#f59e0b"},
            size_max=12,
            hover_data={"Gate": True, "Station": True, "Description": True},
        )
        fig_temp_scatter.update_layout(
            height=280,
            margin=dict(l=20, r=20, b=40, t=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94a3b8", size=10),
            xaxis=dict(
                title=dict(text="Temperature (°C)", font=dict(color="#94a3b8", size=11)),
                tickfont=dict(size=9, color="#94a3b8"),
                gridcolor="rgba(30,41,59,0.5)",
            ),
            yaxis=dict(
                title=dict(text="Vibration (mm/s)", font=dict(color="#94a3b8", size=11)),
                tickfont=dict(size=9, color="#94a3b8"),
                gridcolor="rgba(30,41,59,0.5)",
            ),
            legend=dict(
                title=dict(text="Severity", font=dict(color="#94a3b8")),
                font=dict(color="#94a3b8", size=9),
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
            ),
        )
        st.plotly_chart(fig_temp_scatter, use_container_width=True)


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
        '<div style="font-size:0.9rem;font-weight:600;color:#94a3b8;margin:10px 0 15px 0;">Network Risk Forecast by Station</div>',
        unsafe_allow_html=True,
    )

    station_risk_forecast = df.groupby("station")["risk_score"].mean().reset_index()
    station_risk_forecast = station_risk_forecast.sort_values("risk_score", ascending=False)

    fig_forecast = px.bar(
        station_risk_forecast,
        x="station",
        y="risk_score",
        color="risk_score",
        color_continuous_scale=["#10b981", "#f59e0b", "#ef4444"],
        range_color=[0, 100],
        text="risk_score",
    )
    fig_forecast.update_layout(
        height=320,
        margin=dict(l=20, r=20, b=50, t=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8", size=10),
        xaxis=dict(
            tickfont=dict(size=9, color="#94a3b8"),
            title=dict(text="Station", font=dict(color="#94a3b8", size=11)),
        ),
        yaxis=dict(
            tickfont=dict(size=10, color="#94a3b8"),
            title=dict(text="Avg Risk Score", font=dict(color="#94a3b8", size=11)),
            range=[0, 100],
        ),
        coloraxis_colorbar=dict(
            title=dict(text="Risk", font=dict(color="#94a3b8", size=10)),
            tickfont=dict(color="#94a3b8", size=9),
        ),
    )
    fig_forecast.update_traces(textposition="outside", marker_line_width=0)
    st.plotly_chart(fig_forecast, use_container_width=True)

    col_heat, col_sync = st.columns([2, 1])

    with col_heat:
        st.markdown(
            '<div style="font-size:0.9rem;font-weight:600;color:#94a3b8;margin:20px 0 10px 0;">Passenger Flow by Station</div>',
            unsafe_allow_html=True,
        )
        station_passengers = df.groupby("station")["people"].sum().reset_index()
        station_passengers = station_passengers.sort_values("people", ascending=False)

        fig_passengers = px.bar(
            station_passengers,
            x="station",
            y="people",
            color="people",
            color_continuous_scale=["#0d47a1", "#0288d1", "#00b4d8"],
            text="people",
        )
        fig_passengers.update_layout(
            height=320,
            margin=dict(l=20, r=20, b=50, t=20),
            paper_bgcolor="rgba(10, 14, 23, 0)",
            plot_bgcolor="rgba(10, 14, 23, 0)",
            font=dict(color="#94a3b8", size=10),
            xaxis=dict(
                tickfont=dict(size=9, color="#94a3b8"),
                title=dict(text="Station", font=dict(color="#94a3b8", size=11)),
            ),
            yaxis=dict(
                tickfont=dict(size=10, color="#94a3b8"),
                title=dict(text="Total Passengers", font=dict(color="#94a3b8", size=11)),
            ),
            coloraxis_colorbar=dict(
                title=dict(text="Passengers", font=dict(color="#94a3b8", size=10)),
                tickfont=dict(color="#94a3b8", size=9),
            ),
        )
        fig_passengers.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig_passengers, use_container_width=True)

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
                        "line": {"color": "#10b981", "width": 3},
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
                number={"suffix": "%", "font": {"color": "#e2e8f0", "size": 30}},
            )
        )
        fig_gauge.update_layout(
            height=320,
            margin=dict(l=40, r=40, b=40, t=50),
            paper_bgcolor="rgba(10, 14, 23, 0)",
            font=dict(color="#94a3b8", family="Inter", size=11),
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

        st.markdown(
            '<div style="font-size:0.8rem;color:#94a3b8;text-align:center;margin-top:10px;">Sync Score by Station</div>',
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
            color_continuous_scale=["#ef4444", "#f59e0b", "#10b981"],
            range_color=[0, 100],
        )
        fig_sync_bar.update_layout(
            height=180,
            margin=dict(l=10, r=10, b=30, t=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94a3b8", size=9),
            yaxis=dict(tickfont=dict(size=8, color="#94a3b8"), title=""),
            xaxis=dict(tickfont=dict(size=9, color="#94a3b8"), title="Sync Score", range=[0, 100]),
        )
        st.plotly_chart(fig_sync_bar, use_container_width=True)

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
        color_continuous_scale=["#10b981", "#f59e0b", "#ef4444"],
        range_color=[0, 100],
        labels={"risk_score": "Risk Score", "gate_id": "Gate", "station": "Station"},
        hover_data={"platform": True},
    )
    fig_risk.update_layout(
        height=300,
        margin=dict(l=10, r=10, b=40, t=20),
        paper_bgcolor="rgba(10, 14, 23, 0)",
        plot_bgcolor="rgba(10, 14, 23, 0)",
        font=dict(color="#94a3b8", family="Inter", size=11),
        yaxis=dict(
            gridcolor="rgba(30, 41, 59, 0.6)",
            tickfont=dict(size=10, color="#94a3b8"),
            title="",
        ),
        xaxis=dict(
            gridcolor="rgba(30, 41, 59, 0.6)",
            tickfont=dict(size=10, color="#94a3b8"),
            title="Risk Score",
            range=[0, 100],
        ),
        coloraxis_colorbar=dict(
            title=dict(text="Risk", font=dict(color="#94a3b8", size=10)),
            tickfont=dict(color="#94a3b8", size=9),
            thickness=6,
            len=0.7,
        ),
        hovermode="y unified",
        hoverlabel=dict(
            bgcolor="rgba(17, 24, 39, 0.95)",
            bordercolor="#ef4444",
            font_color="#f1f5f9",
            font_size=11,
        ),
    )
    fig_risk.update_traces(
        hovertemplate="<b>Gate</b>: %{y}<br><b>Risk Score</b>: ~%{x:.0f}/100<extra></extra>",
        marker_line_width=0,
    )
    st.plotly_chart(fig_risk, use_container_width=True)
    st.markdown("</div></div>", unsafe_allow_html=True)

    # Export network risk data
    station_risk_export = df.groupby("station").agg({
        "risk_score": "mean",
        "sync_score": "mean",
        "people": "sum",
        "gate_id": "count"
    }).reset_index()
    station_risk_export.columns = ["Station", "Avg_Risk", "Avg_Sync", "Total_Passengers", "Gate_Count"]
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
            '<div style="font-size:0.85rem;font-weight:600;color:#94a3b8;margin-bottom:10px;">Door Cycles by Hour</div>',
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
        fig_cycles.update_layout(
            height=280,
            margin=dict(l=20, r=20, b=40, t=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94a3b8", size=10),
            xaxis=dict(tickfont=dict(size=9, color="#94a3b8")),
            yaxis=dict(tickfont=dict(size=9, color="#94a3b8")),
        )
        fig_cycles.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig_cycles, use_container_width=True)

    with col_psd2:
        st.markdown(
            '<div style="font-size:0.85rem;font-weight:600;color:#94a3b8;margin-bottom:10px;">Average Temperature by Hour</div>',
            unsafe_allow_html=True,
        )
        fig_temp_psd = go.Figure()
        fig_temp_psd.add_trace(
            go.Scatter(
                x=temp_df["Hour"],
                y=temp_df["Avg Temp (°C)"],
                mode="lines+markers",
                line=dict(color="#ef4444", width=2.5, shape="spline"),
                marker=dict(size=6, color="#ef4444"),
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
        fig_temp_psd.update_layout(
            height=280,
            margin=dict(l=20, r=20, b=40, t=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94a3b8", size=10),
            xaxis=dict(tickfont=dict(size=9, color="#94a3b8")),
            yaxis=dict(
                tickfont=dict(size=9, color="#94a3b8"),
                gridcolor="rgba(30,41,59,0.5)",
                title=dict(text="Temp (°C)", font=dict(color="#94a3b8", size=10)),
            ),
            showlegend=False,
            hovermode="x unified",
        )
        fig_temp_psd.update_traces(
            hovertemplate="<b>Hour</b>: %{x}<br><b>Temp</b>: %{y}°C<extra></extra>"
        )
        st.plotly_chart(fig_temp_psd, use_container_width=True)

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
        (all_stations_data["risk_score"] >= 40) & (all_stations_data["risk_score"] < 70)
    ].sort_values("risk_score", ascending=False)

    if not high_risk_gates.empty:
        st.markdown(
            '<div style="font-size:0.9rem;font-weight:600;color:#ef4444;margin:16px 0 10px 0;">🔴 Critical Risk Gates - Immediate Action Required (Network-wide)</div>',
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
            <div style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);border-radius:8px;padding:12px;margin-bottom:10px;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                    <span style="font-weight:600;color:#fca5a5;font-size:0.95rem;">Gate {gate['gate_id']} @ {station_name[:20]}</span>
                    <span style="background:rgba(239,68,68,0.2);color:#fca5a5;padding:2px 8px;border-radius:4px;font-size:0.75rem;font-weight:600;">Risk: {int(gate['risk_score'])}%</span>
                </div>
                <div style="font-size:0.8rem;color:#94a3b8;margin-bottom:6px;">
                    <span style="margin-right:15px;">🔧 Status: {main_status}</span>
                    <span style="margin-right:15px;">📡 Sync: {sync_score}%</span>
                    <span>🌡️ Temp: {temp}°C</span>
                </div>
                <div style="font-size:0.85rem;color:#f97316;font-weight:500;">→ {rec}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

    if not medium_risk_gates.empty:
        st.markdown(
            '<div style="font-size:0.9rem;font-weight:600;color:#f59e0b;margin:16px 0 10px 0;">🟡 Medium Risk Gates - Schedule Maintenance (Network-wide)</div>',
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
            <div style="background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.3);border-radius:8px;padding:12px;margin-bottom:10px;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                    <span style="font-weight:600;color:#fcd34d;font-size:0.95rem;">Gate {gate['gate_id']} @ {station_name[:20]}</span>
                    <span style="background:rgba(245,158,11,0.2);color:#fcd34d;padding:2px 8px;border-radius:4px;font-size:0.75rem;font-weight:600;">Risk: {int(gate['risk_score'])}%</span>
                </div>
                <div style="font-size:0.8rem;color:#94a3b8;margin-bottom:6px;">
                    <span style="margin-right:15px;">🔧 Status: {main_status}</span>
                    <span style="margin-right:15px;">📡 Sync: {sync_score}%</span>
                </div>
                <div style="font-size:0.85rem;color:#fbbf24;font-weight:500;">→ {rec}</div>
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
                <div style="font-size:0.8rem;color:#94a3b8;margin-bottom:6px;">
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
        <div style="background:linear-gradient(135deg,rgba(239,68,68,0.1) 0%,rgba(239,68,68,0.05) 100%);border:1px solid rgba(239,68,68,0.2);border-radius:12px;padding:16px;text-align:center;">
            <div style="font-size:2rem;font-weight:700;color:#ef4444;">{len(temp_anomalies)}</div>
            <div style="font-size:0.75rem;color:#94a3b8;text-transform:uppercase;letter-spacing:0.5px;">High Temp Anomalies</div>
            <div style="font-size:0.7rem;color:#64748b;margin-top:8px;">> 40°C threshold</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col_anom2:
        st.markdown(
            f"""
        <div style="background:linear-gradient(135deg,rgba(245,158,11,0.1) 0%,rgba(245,158,11,0.05) 100%);border:1px solid rgba(245,158,11,0.2);border-radius:12px;padding:16px;text-align:center;">
            <div style="font-size:2rem;font-weight:700;color:#f59e0b;">{len(vib_anomalies)}</div>
            <div style="font-size:0.75rem;color:#94a3b8;text-transform:uppercase;letter-spacing:0.5px;">Vibration Anomalies</div>
            <div style="font-size:0.7rem;color:#64748b;margin-top:8px;">> 3.0 mm/s threshold</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col_anom3:
        st.markdown(
            f"""
        <div style="background:linear-gradient(135deg,rgba(239,68,68,0.1) 0%,rgba(239,68,68,0.05) 100%);border:1px solid rgba(239,68,68,0.2);border-radius:12px;padding:16px;text-align:center;">
            <div style="font-size:2rem;font-weight:700;color:#ef4444;">{len(sync_anomalies)}</div>
            <div style="font-size:0.75rem;color:#94a3b8;text-transform:uppercase;letter-spacing:0.5px;">Low Sync Anomalies</div>
            <div style="font-size:0.7rem;color:#64748b;margin-top:8px;">< 50% sync score</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    if not temp_anomalies.empty:
        with st.expander("View Temperature Anomaly Details"):
            st.dataframe(
                temp_anomalies[["station", "gate_id", "platform", "sensor_temp", "sync_score"]]
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
                vib_anomalies[["station", "gate_id", "platform", "sensor_vib", "sync_score"]]
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
                sync_anomalies[["station", "gate_id", "platform", "sync_score", "risk_score"]]
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

    station_risk_data = df.groupby("station")["risk_score"].mean().reset_index()
    station_risk_data = station_risk_data.sort_values("risk_score", ascending=False)
    station_risk_data.columns = ["Station", "Avg Risk"]

    fig_station_risk = px.bar(
        station_risk_data,
        x="Station",
        y="Avg Risk",
        color="Avg Risk",
        color_continuous_scale=["#10b981", "#f59e0b", "#ef4444"],
        range_color=[0, 100],
        text="Avg Risk",
    )
    fig_station_risk.update_layout(
        height=280,
        margin=dict(l=20, r=20, b=40, t=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8", size=10),
        xaxis=dict(tickfont=dict(size=9, color="#94a3b8")),
        yaxis=dict(
            tickfont=dict(size=10, color="#94a3b8"),
            title=dict(text="Avg Risk Score", font=dict(color="#94a3b8", size=11)),
            range=[0, 100],
        ),
    )
    fig_station_risk.update_traces(textposition="outside", marker_line_width=0)
    st.plotly_chart(fig_station_risk, use_container_width=True)

    col_trend1, col_trend2 = st.columns(2)

    with col_trend1:
        st.markdown(
            '<div style="font-size:0.85rem;font-weight:600;color:#94a3b8;margin:20px 0 10px 0;">Network Risk Distribution</div>',
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
            color_discrete_sequence=["#10b981", "#f59e0b", "#ef4444"],
            hole=0.5,
        )
        fig_risk_dist.update_layout(
            height=220,
            margin=dict(l=20, r=20, b=20, t=20),
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94a3b8", size=10),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.15,
                xanchor="center",
                x=0.5,
                font=dict(color="#94a3b8", size=9),
            ),
        )
        fig_risk_dist.update_traces(
            textinfo="percent+label",
            hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>",
        )
        st.plotly_chart(fig_risk_dist, use_container_width=True)

    with col_trend2:
        st.markdown(
            '<div style="font-size:0.85rem;font-weight:600;color:#94a3b8;margin:20px 0 10px 0;">Top 5 High Risk Gates</div>',
            unsafe_allow_html=True,
        )
        top_risk_gates = (
            df.nlargest(5, "risk_score")[["gate_id", "station", "risk_score", "maintenance_status"]]
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
    st.markdown(
        f"""
    <div style="text-align:center;margin-top:15px;padding:12px;background:rgba(0,0,0,0.2);border-radius:8px;">
        <span style="font-size:0.9rem;color:#94a3b8;">Network Average Risk Score: </span>
        <span style="font-size:1.1rem;color:{"#10b981" if overall_risk < 40 else "#f59e0b" if overall_risk < 70 else "#ef4444"};font-weight:700;">{overall_risk:.1f}%</span>
    </div>
    """,
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════
# ── TAB: COMPANY & TEAM ───────────────────────────
# ═══════════════════════════════════════════════════
elif active_tab == "financial":
    PLOTLY_DARK = dict(
        plot_bgcolor="rgba(10, 14, 23, 0)",
        paper_bgcolor="rgba(10, 14, 23, 0)",
        font=dict(color="#94a3b8", family="Inter", size=11),
        xaxis=dict(
            gridcolor="rgba(148, 163, 184, 0.1)",
            zeroline=False,
            tickfont=dict(size=10, color="#94a3b8"),
        ),
        yaxis=dict(
            gridcolor="rgba(148, 163, 184, 0.1)",
            zeroline=False,
            tickfont=dict(size=10, color="#94a3b8"),
        ),
        legend=dict(
            bgcolor="rgba(26, 35, 50, 0.8)",
            bordercolor="rgba(148, 163, 184, 0.1)",
            borderwidth=1,
            font=dict(size=10, color="#94a3b8"),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        margin=dict(l=40, r=20, t=80, b=60),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="rgba(26, 35, 50, 0.95)",
            bordercolor="rgba(59, 130, 246, 0.3)",
            font_color="#f1f5f9",
            font_size=11,
        ),
        title_font=dict(size=14, color="#f1f5f9", family="Inter"),
        title_x=0,
        title_y=0.95,
        title_pad=dict(t=10, b=10),
    )

    def fin_fig(layout_extra=None):
        d = dict(**PLOTLY_DARK)
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
        df_base if "Base" in scenario else (df_churn if "High" in scenario else df_base)
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
        (k3, "TOTAL CUSTOMERS", f"{int(final['Total_Customers'])}", "metric-card"),
        (k4, "GROSS MARGIN", f"{final['Gross_Margin_%']:.1f}%", "metric-card green"),
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

    st.markdown("<br>", unsafe_allow_html=True)

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
        fig.update_layout(barmode="relative", title="MRR Movements", **fin_fig())
        st.plotly_chart(fig, use_container_width=True)

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
        st.plotly_chart(fig, use_container_width=True)

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
        st.plotly_chart(fig, use_container_width=True)

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
        st.plotly_chart(fig, use_container_width=True)

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
        st.plotly_chart(fig, use_container_width=True)

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
        st.plotly_chart(fig, use_container_width=True)

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
        st.plotly_chart(fig, use_container_width=True)

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
        st.plotly_chart(fig, use_container_width=True)

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
        st.plotly_chart(fig, use_container_width=True)

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
        st.plotly_chart(fig, use_container_width=True)

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
        st.plotly_chart(fig, use_container_width=True)

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
        st.plotly_chart(fig, use_container_width=True)

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
            for j, (col_name, ylabel, title) in enumerate(compare_pairs[i : i + 2]):
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
                    fig.update_layout(title=title, yaxis_title=ylabel, **fin_fig())
        st.plotly_chart(
            fig,
            config={
                "displaylogo": False,
                "responsive": True,
                "scrollZoom": True,
                "modeBarButtonsToRemove": ["lasso2d", "select2d"],
            },
            use_container_width=True,
        )

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

    st.markdown("</div></div>", unsafe_allow_html=True)

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

    # ── CSS for Customer Tab ──
    st.markdown(
        """
    <style>
    .customer-metric-card {
        background: var(--bg-card);
        border: 1px solid var(--border-default);
        border-radius: 12px;
        padding: 1.25rem;
        transition: all 0.3s ease;
    }
    .customer-metric-card:hover {
        background: var(--bg-card-hover);
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.15);
    }
    .customer-metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--accent-primary);
        margin-bottom: 0.25rem;
    }
    .customer-metric-label {
        font-size: 0.85rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .customer-section-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--text-primary);
        margin: 1.5rem 0 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid var(--border-subtle);
    }
    .segment-champions { color: #10b981; }
    .segment-loyal { color: #3b82f6; }
    .segment-potential { color: #8b5cf6; }
    .segment-risk { color: #f59e0b; }
    .segment-lost { color: #ef4444; }
    .recommendation-card {
        background: var(--bg-tertiary);
        border-left: 3px solid var(--accent-primary);
        padding: 1rem;
        margin-bottom: 0.75rem;
        border-radius: 0 8px 8px 0;
    }
    .recommendation-high { border-left-color: #ef4444; }
    .recommendation-medium { border-left-color: #f59e0b; }
    .recommendation-info { border-left-color: #3b82f6; }
    .viz-metric-card {
        background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-tertiary) 100%);
        border: 1px solid var(--border-default);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    .viz-metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 32px rgba(59, 130, 246, 0.2);
    }
    .viz-metric-icon {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    .viz-metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 0.25rem;
    }
    .viz-metric-label {
        font-size: 0.85rem;
        color: var(--text-tertiary);
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .viz-metric-sub {
        font-size: 0.75rem;
        color: var(--text-muted);
        margin-top: 0.25rem;
    }
    .section-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: var(--text-primary);
        margin: 1.5rem 0 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .heatmap-cell {
        padding: 0.75rem;
        text-align: center;
        border-radius: 8px;
        font-weight: 600;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

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
            <div class="viz-metric-value">{format_number(insights["total_psd_units"])}</div>
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
        '<div class="section-title">📊 RFM Segment Distribution</div>',
        unsafe_allow_html=True,
    )

    col_left, col_right = st.columns([2, 1])
    with col_left:
        segment_counts = rfm_df["rfm_segment"].value_counts().reset_index()
        segment_counts.columns = ["Segment", "Count"]

        segment_colors = {
            "Strategic Partners": "#10b981",
            "Key Accounts": "#3b82f6",
            "Growth Potential": "#8b5cf6",
            "At Risk": "#f59e0b",
            "Dormant": "#ef4444",
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
        fig_rfm.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#cbd5e1",
            showlegend=False,
            hovermode="x unified",
        )
        fig_rfm.update_traces(textposition="outside")
        st.plotly_chart(fig_rfm, use_container_width=True)

    with col_right:
        segment_pct = segment_counts.copy()
        segment_pct["Percentage"] = (
            segment_pct["Count"] / segment_pct["Count"].sum() * 100
        ).astype(int)
        segment_pct["Display"] = (
            segment_pct["Segment"] + ": ~" + segment_pct["Percentage"].astype(str) + "%"
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
        fig_pie.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#cbd5e1",
            showlegend=True,
            legend=dict(
                orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5
            ),
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown(
        '<div class="section-title">📈 RFM Score Breakdown by Segment</div>',
        unsafe_allow_html=True,
    )

    def highlight_rfm(val, max_val=5):
        ratio = val / max_val
        if ratio >= 0.8:
            return "background-color: rgba(16, 185, 129, 0.3); color: #10b981"
        elif ratio >= 0.6:
            return "background-color: rgba(59, 130, 246, 0.3); color: #3b82f6"
        elif ratio >= 0.4:
            return "background-color: rgba(245, 158, 11, 0.3); color: #f59e0b"
        else:
            return "background-color: rgba(239, 68, 68, 0.3); color: #ef4444"

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
        rfm_summary = pd.DataFrame(columns=["Segment", "Avg Recency", "Avg Frequency", "Avg Monetary", "Avg Platforms", "Avg Contract (€)"])

    if not rfm_summary.empty:
        st.dataframe(
            rfm_summary.style.applymap(
                highlight_rfm, subset=["Avg Recency", "Avg Frequency", "Avg Monetary"]
            ),
            use_container_width=True,
            hide_index=True,
        )

    # Additional visualizations
    st.markdown(
        '<div class="section-title">📊 Contract Value by Operator Type</div>',
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
        fig_type.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#cbd5e1",
            showlegend=False,
        )
        fig_type.update_traces(textposition="outside")
        st.plotly_chart(fig_type, use_container_width=True)

    with col_extra2:
        fig_type_psd = px.bar(
            type_value,
            x="Operator Type",
            y="PSD Units",
            color="Operator Type",
            title="PSD Units by Operator Type",
            text="PSD Units",
        )
        fig_type_psd.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#cbd5e1",
            showlegend=False,
        )
        fig_type_psd.update_traces(textposition="outside")
        st.plotly_chart(fig_type_psd, use_container_width=True)

    # Tier distribution
    st.markdown(
        '<div class="section-title">🏆 Contract Tier Distribution</div>',
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
        tier_value.columns = ["Tier", "Total Contract (€)", "PSD Units", "Count"]

        tier_colors_map = {
            "Platinum": "#e5e7eb",
            "Gold": "#fbbf24",
            "Silver": "#94a3b8",
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
        fig_tier_bar.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#cbd5e1",
            showlegend=False,
            xaxis_title="Contract Tier",
        )
        fig_tier_bar.update_traces(textposition="outside")
        st.plotly_chart(fig_tier_bar, use_container_width=True)

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
        fig_tier_donut.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#cbd5e1",
            showlegend=True,
            legend=dict(
                orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5
            ),
        )
        st.plotly_chart(fig_tier_donut, use_container_width=True)

    st.markdown(
        '<div class="section-title">📈 RFM Score Distribution</div>',
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
        fig_rfm_hist.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#cbd5e1",
            showlegend=False,
        )
        st.plotly_chart(fig_rfm_hist, use_container_width=True)

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
        fig_scatter.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#cbd5e1",
            showlegend=True,
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown(
        '<div class="section-title">⭐ High-Value Accounts Ranking</div>',
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
        "Strategic": "#10b981",
        "Preferred": "#fbbf24",
        "Important": "#94a3b8",
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
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "Tier: %{color}<br>"
            "Value Score: ~%{x}<br>"
            "Contract: %{customdata[0]}<br>"
            "PSD Units: %{customdata[1]}<br>"
            "Type: %{customdata[2]}<extra></extra>"
        ),
        textposition="outside",
    )
    fig_hv.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#cbd5e1",
        yaxis_title="",
        xaxis_title="Value Score",
        showlegend=True,
        legend=dict(
            orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5
        ),
        height=500,
        margin=dict(l=20, r=20, t=50, b=80),
    )
    st.plotly_chart(fig_hv, use_container_width=True)

    col_hv1, col_hv2 = st.columns(2)
    with col_hv1:
        st.markdown("**Value Tier Distribution**", unsafe_allow_html=True)
        tier_counts = high_value_df["value_tier"].value_counts()
        tier_df = pd.DataFrame({"Tier": tier_counts.index, "Count": tier_counts.values})

        fig_tier = px.pie(
            tier_df,
            values="Count",
            names="Tier",
            color="Tier",
            color_discrete_map=tier_colors,
            hole=0.4,
            title="Account Tier Breakdown",
        )
        fig_tier.update_traces(
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>Count: %{value}<br>~%{percent:.0%}<extra></extra>",
        )
        fig_tier.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#cbd5e1",
            showlegend=True,
            height=350,
        )
        st.plotly_chart(fig_tier, use_container_width=True)

    with col_hv2:
        st.markdown("**Top 5 by Contract Value**", unsafe_allow_html=True)
        top5_value = high_value_df.nlargest(5, "total_contract_value_eur")[
            ["customer_name", "operator_type", "total_contract_value_eur", "psd_units"]
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
        '<div class="section-title">💡 Business Insights & Recommendations</div>',
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
                <span style="color: {"#ef4444" if insights["risk_rate"] > 20 else "#10b981"}; font-weight: 600;">~{int(insights["risk_rate"])}%</span>
            </div>
            <div style="display: flex; justify-content: space-between; padding: 0.5rem; background: var(--bg-tertiary); border-radius: 8px;">
                <span style="color: var(--text-secondary);">At-Risk Accounts</span>
                <span style="color: #f59e0b; font-weight: 600;">{insights["at_risk_count"]} (~{int(insights["at_risk_pct"])}%)</span>
            </div>
            <div style="display: flex; justify-content: space-between; padding: 0.5rem; background: var(--bg-tertiary); border-radius: 8px;">
                <span style="color: var(--text-secondary);">Strategic Partners</span>
                <span style="color: #10b981; font-weight: 600;">{insights["strategic_count"]} (~{int(insights["strategic_pct"])}%)</span>
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
        '<div class="section-title">💚 Renewal & Health Signals</div>',
        unsafe_allow_html=True,
    )

    # Health Summary Cards
    col_h1, col_h2, col_h3, col_h4 = st.columns(4)
    with col_h1:
        health_color = (
            "#10b981"
            if health_summary["avg_health_score"] >= 70
            else ("#f59e0b" if health_summary["avg_health_score"] >= 50 else "#ef4444")
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
        <div class="viz-metric-card" style="border-left: 4px solid #ef4444;">
            <div class="viz-metric-icon">🔴</div>
            <div class="viz-metric-value" style="color: #ef4444;">{health_summary["critical_count"]}</div>
            <div class="viz-metric-label">Critical Health</div>
            <div class="viz-metric-sub">Needs Immediate Attention</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col_h3:
        st.markdown(
            f"""
        <div class="viz-metric-card" style="border-left: 4px solid #f59e0b;">
            <div class="viz-metric-icon">⚠️</div>
            <div class="viz-metric-value" style="color: #f59e0b;">{health_summary["at_risk_high"]}</div>
            <div class="viz-metric-label">High Risk Accounts</div>
            <div class="viz-metric-sub">{format_euro(health_summary["contract_value_at_risk"])} at risk</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col_h4:
        renewal_color = (
            "#ef4444" if health_summary["renewal_critical"] > 0 else "#10b981"
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
        st.markdown("**📅 Upcoming Renewals (Next 90 Days)**", unsafe_allow_html=True)
        upcoming_renewals = renewal_df[renewal_df["days_to_renewal"] <= 90].copy()

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
                    return "background-color: rgba(239, 68, 68, 0.3); color: #ef4444"
                elif urgency == "Urgent (<60d)":
                    return "background-color: rgba(245, 158, 11, 0.3); color: #f59e0b"
                return "background-color: rgba(59, 130, 246, 0.3); color: #3b82f6"

            st.dataframe(
                display_renewals.style.applymap(urgency_color, subset=["Urgency"]),
                use_container_width=True,
                hide_index=True,
                height=300,
            )
        else:
            st.info("No renewals in the next 90 days")

    with col_r2:
        st.markdown("**🔴 At-Risk Accounts**", unsafe_allow_html=True)
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
                    return "background-color: rgba(239, 68, 68, 0.3); color: #ef4444"
                return "background-color: rgba(245, 158, 11, 0.3); color: #f59e0b"

            st.dataframe(
                risk_table.style.applymap(risk_color, subset=["Risk Level"]),
                use_container_width=True,
                hide_index=True,
                height=300,
            )
        else:
            st.info("No at-risk accounts identified")

    # Health Score Distribution
    st.markdown("**📊 Health Score Distribution**", unsafe_allow_html=True)
    col_health1, col_health2 = st.columns(2)

    with col_health1:
        health_dist = (
            health_df.groupby("health_status")["customer_id"].count().reset_index()
        )
        health_dist.columns = ["Status", "Count"]

        status_colors = {
            "Healthy": "#10b981",
            "Attention": "#f59e0b",
            "Critical": "#ef4444",
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
        fig_health.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#cbd5e1",
        )
        st.plotly_chart(fig_health, use_container_width=True)

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
        fig_health_bar.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#cbd5e1",
            xaxis_tickangle=-45,
            yaxis_title="Health Score",
            coloraxis=dict(colorscale="RdYlGn", cmin=0, cmax=100),
        )
        fig_health_bar.update_traces(textposition="outside")
        st.plotly_chart(fig_health_bar, use_container_width=True)

    # Upcoming Renewal Value
    st.markdown("**💰 Upcoming Renewal Value**", unsafe_allow_html=True)
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
        '<div class="section-title">📋 All Railway Operators Data</div>',
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

elif active_tab == "portfolio":
    # ── PORTFOLIO VIEW: OPERATOR DRILL-DOWN ──
    st.markdown(
        """
        <style>
        /* Portfolio-specific styles */
        .operator-profile-card {
            background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-tertiary) 100%);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 24px;
            position: relative;
            overflow: hidden;
        }
        .operator-profile-card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; height: 3px;
            background: linear-gradient(90deg, var(--accent-primary), var(--accent-cyan));
        }
        .profile-header {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            margin-bottom: 20px;
        }
        .operator-title {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-primary);
            margin: 0 0 4px 0;
        }
        .operator-subtitle {
            font-size: 0.85rem;
            color: var(--text-tertiary);
            font-family: 'JetBrains Mono', monospace;
        }
        .health-badge {
            padding: 8px 16px;
            border-radius: 999px;
            font-weight: 600;
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .health-badge.healthy { background: rgba(16,185,129,0.15); color: #10b981; border: 1px solid rgba(16,185,129,0.3); }
        .health-badge.attention { background: rgba(245,158,11,0.15); color: #f59e0b; border: 1px solid rgba(245,158,11,0.3); }
        .health-badge.critical { background: rgba(239,68,68,0.15); color: #ef4444; border: 1px solid rgba(239,68,68,0.3); }
        .profile-metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 16px;
            margin-top: 20px;
        }
        .profile-metric {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 14px;
        }
        .profile-metric-label {
            font-size: 0.7rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }
        .profile-metric-value {
            font-size: 1.3rem;
            font-weight: 700;
            color: var(--text-primary);
            font-family: 'JetBrains Mono', monospace;
        }
        .section-header {
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--text-primary);
            margin: 24px 0 16px 0;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--border-color);
        }
        .data-table {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 16px;
        }
        .timeline-item {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 14px 16px;
            margin-bottom: 10px;
            transition: all 0.2s ease;
        }
        .timeline-item:hover {
            border-color: var(--accent-blue);
            transform: translateX(4px);
        }
        .timeline-date {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.75rem;
            color: var(--accent-cyan);
            margin-bottom: 4px;
        }
        .timeline-type {
            font-weight: 600;
            font-size: 0.9rem;
            color: var(--text-primary);
            margin-bottom: 6px;
        }
        .timeline-outcome {
            font-size: 0.85rem;
            color: var(--text-secondary);
            line-height: 1.5;
        }
        .quick-action-btn {
            background: var(--bg-card) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 10px !important;
            padding: 16px !important;
            text-align: left !important;
            transition: all 0.2s ease !important;
        }
        .quick-action-btn:hover {
            border-color: var(--accent-blue) !important;
            background: var(--bg-card-hover) !important;
        }
        /* Gauge chart container */
        .gauge-container {
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 10px 0;
        }
        .benchmark-bar {
            height: 8px;
            background: linear-gradient(90deg, #ef4444 0%, #f59e0b 50%, #10b981 100%);
            border-radius: 4px;
            margin: 8px 0;
            position: relative;
        }
        .benchmark-marker {
            position: absolute;
            top: -4px;
            width: 3px;
            height: 16px;
            background: #fff;
            border: 1px solid #000;
            border-radius: 1px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ── Load Operator Data ──
    try:
        customer_df = get_customer_data()
    except Exception as e:
        st.error(f"Failed to load operator data: {e}")
        st.stop()

    # ── Operator Selection (Inline) ──
    st.markdown(
        """
        <style>
        .operator-select-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 20px;
        }
        .operator-select-label {
            font-size: 0.7rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
            font-weight: 600;
        }
        </style>
        <div class="operator-select-card">
            <div class="operator-select-label">Select Operator</div>
        </div>
        """,
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
        selected_operator_label = st.selectbox(
            "Select an operator to view details",
            options=option_labels,
            index=current_index,
            key="operator_selector",
        )

        selected_operator_id = option_to_id[selected_operator_label]
        if st.session_state.selected_operator != selected_operator_id:
            st.session_state.selected_operator = selected_operator_id
            st.rerun()
    else:
        st.info("No customer data available")
        selected_operator_id = None

    if not selected_operator_id:
        st.stop()

    # Quick stats for selected operator
    selected_op = customer_df[customer_df["customer_id"] == selected_operator_id].iloc[
        0
    ]
    col_quick1, col_quick2, col_quick3 = st.columns(3)
    with col_quick1:
        st.markdown(
            f"""
            <div style="background:var(--bg-card);border:1px solid var(--border-color);border-radius:10px;padding:14px;text-align:center;">
                <div style="font-size:0.65rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">Satisfaction</div>
                <div style="font-size:1.4rem;font-weight:700;color:var(--text-primary);">{selected_op["satisfaction_score"]}/10</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_quick2:
        st.markdown(
            f"""
            <div style="background:var(--bg-card);border:1px solid var(--border-color);border-radius:10px;padding:14px;text-align:center;">
                <div style="font-size:0.65rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">PSD Units</div>
                <div style="font-size:1.4rem;font-weight:700;color:var(--text-primary);">{selected_op["psd_units"]:,}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_quick3:
        st.markdown(
            f"""
            <div style="background:var(--bg-card);border:1px solid var(--border-color);border-radius:10px;padding:14px;text-align:center;">
                <div style="font-size:0.65rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">Contract Value</div>
                <div style="font-size:1.4rem;font-weight:700;color:var(--text-primary);">{format_euro(selected_op["total_contract_value_eur"])}</div>
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
                '<div class="section-header">Health Score Trend (12mo)</div>',
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
                fig_health.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#cbd5e1",
                    height=320,
                    yaxis_range=[0, 100],
                    shapes=[
                        dict(
                            type="line",
                            y0=70,
                            y1=70,
                            x0=0,
                            x1=1,
                            line=dict(color="#10b981", dash="dash", width=1),
                        ),
                        dict(
                            type="line",
                            y0=50,
                            y1=50,
                            x0=0,
                            x1=1,
                            line=dict(color="#f59e0b", dash="dash", width=1),
                        ),
                        dict(
                            type="line",
                            y0=30,
                            y1=30,
                            x0=0,
                            x1=1,
                            line=dict(color="#ef4444", dash="dash", width=1),
                        ),
                    ],
                )
                st.plotly_chart(fig_health, use_container_width=True)
            else:
                st.info("No health trend data available.")

            st.markdown(
                '<div class="section-header">Support Ticket Volume Trend</div>',
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
                fig_tickets.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#cbd5e1",
                    height=320,
                    showlegend=False,
                )
                st.plotly_chart(fig_tickets, use_container_width=True)
            else:
                st.info("No ticket trend data available.")

        with col2:
            st.markdown(
                '<div class="section-header">Monthly Activity Summary</div>',
                unsafe_allow_html=True,
            )
            monthly_df = get_operator_monthly_stats(selected_operator_id, months_back=6)
            if not monthly_df.empty:
                st.dataframe(monthly_df, use_container_width=True, hide_index=True)

                # Activity chart
                fig_activity = px.bar(
                    monthly_df,
                    x="Month",
                    y=["Projects Completed", "Tickets Opened", "Engagements"],
                    title="Monthly Activity",
                    barmode="group",
                )
                fig_activity.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#cbd5e1",
                    height=300,
                )
                st.plotly_chart(fig_activity, use_container_width=True)
            else:
                st.info("No monthly activity data.")

    # ── HISTORY TAB ──
    with tabs[1]:
        st.markdown(
            '<div class="section-header">Project History & Installations</div>',
            unsafe_allow_html=True,
        )
        history_df = get_operator_history(selected_operator_id)
        if not history_df.empty:
            # Statistics row
            total_projects = len(history_df)
            total_psd = int(history_df["psd_installed"].sum())
            avg_project_value = history_df["project_value_eur"].mean()
            completed_psd = int(
                history_df[history_df["status"] == "Completed"]["psd_installed"].sum()
            )

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Projects", total_projects)
            with col2:
                st.metric("Total PSDs", total_psd)
            with col3:
                st.metric("Avg Project Value", f"€{avg_project_value / 1e3:.0f}K")
            with col4:
                st.metric(
                    "Completion Rate",
                    f"{(len(history_df[history_df['status'] == 'Completed']) / total_projects * 100):.0f}%",
                )

            # Project timeline Gantt chart
            st.markdown(
                '<div class="section-header">Project Timeline (Gantt)</div>',
                unsafe_allow_html=True,
            )

            # Prepare Gantt data
            gantt_data = history_df.copy()
            gantt_data["start_date"] = pd.to_datetime(gantt_data["start_date"])
            gantt_data["end_date"] = pd.to_datetime(gantt_data["end_date"])

            # Color by status
            status_colors = {
                "Completed": "#10b981",
                "In Progress": "#3b82f6",
                "Planned": "#f59e0b",
            }
            gantt_data["color"] = gantt_data["status"].map(status_colors)

            fig_gantt = px.timeline(
                gantt_data,
                x_start="start_date",
                x_end="end_date",
                y="project_name",
                color="status",
                color_discrete_map=status_colors,
                hover_data=["psd_installed", "project_value_eur", "completion_pct"],
            )
            fig_gantt.update_yaxes(autorange="reversed")
            fig_gantt.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#cbd5e1",
                height=400,
                xaxis_title="Timeline",
                yaxis_title="Projects",
            )
            st.plotly_chart(fig_gantt, use_container_width=True)

            # Project status breakdown
            st.markdown(
                '<div class="section-header">Project Status Distribution</div>',
                unsafe_allow_html=True,
            )
            col1, col2 = st.columns([1, 1])

            with col1:
                status_counts = history_df["status"].value_counts().reset_index()
                status_counts.columns = ["Status", "Count"]
                fig_status = px.bar(
                    status_counts,
                    x="Status",
                    y="Count",
                    color="Status",
                    color_discrete_map={
                        "Completed": "#10b981",
                        "In Progress": "#3b82f6",
                        "Planned": "#f59e0b",
                    },
                )
                fig_status.update_layout(
                    showlegend=False,
                    height=300,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig_status, use_container_width=True)

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
                fig_psd.update_layout(
                    showlegend=False,
                    height=300,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig_psd, use_container_width=True)

            # Full data table
            st.markdown(
                '<div class="section-header">Detailed Project Data</div>',
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
            st.dataframe(display_history, use_container_width=True, hide_index=True)
        else:
            st.info("No project history available.")

    # ── HEALTH TAB ──
    with tabs[2]:
        support_df = get_support_tickets(selected_operator_id, limit=100)
        timeline_df = get_engagement_timeline(selected_operator_id, months_back=12)

        # KPI row
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            open_tickets = (
                len(support_df[support_df["status"].isin(["Open", "In Progress"])])
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
                '<div class="section-header">Ticket Volume Trend (6mo)</div>',
                unsafe_allow_html=True,
            )
            ticket_trend = get_support_ticket_trend(selected_operator_id, months_back=6)
            if not ticket_trend.empty:
                fig_trend = px.area(
                    ticket_trend,
                    x="Month",
                    y="Tickets",
                    title="Monthly Ticket Volume",
                    color_discrete_sequence=["rgba(59, 130, 246, 0.3)"],
                )
                fig_trend.update_layout(
                    height=320,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#cbd5e1",
                )
                st.plotly_chart(fig_trend, use_container_width=True)

            col1, col2 = st.columns(2)

            with col1:
                st.markdown(
                    '<div class="section-header">Tickets by Category</div>',
                    unsafe_allow_html=True,
                )
                cat_data = support_df["category"].value_counts().reset_index()
                cat_data.columns = ["Category", "Count"]
                fig_cat = px.pie(cat_data, values="Count", names="Category", hole=0.4)
                fig_cat.update_layout(
                    height=300,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#cbd5e1",
                    showlegend=True,
                )
                st.plotly_chart(fig_cat, use_container_width=True)

            with col2:
                st.markdown(
                    '<div class="section-header">Tickets by Priority</div>',
                    unsafe_allow_html=True,
                )
                pri_data = support_df["priority"].value_counts().reset_index()
                pri_data.columns = ["Priority", "Count"]
                priority_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
                pri_data["order"] = pri_data["Priority"].map(priority_order)
                pri_data = pri_data.sort_values("order").drop("order", axis=1)
                pri_colors = {
                    "Critical": "#ef4444",
                    "High": "#f59e0b",
                    "Medium": "#3b82f6",
                    "Low": "#10b981",
                }
                fig_pri = px.bar(
                    pri_data,
                    x="Priority",
                    y="Count",
                    color="Priority",
                    color_discrete_map=pri_colors,
                )
                fig_pri.update_layout(
                    height=300,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#cbd5e1",
                    showlegend=False,
                )
                st.plotly_chart(fig_pri, use_container_width=True)

            # Resolution time analysis
            st.markdown(
                '<div class="section-header">Resolution Time Analysis</div>',
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
                    resolved_tickets.groupby("priority")["resolution_time_hours"]
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
                fig_res.update_layout(
                    height=300,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#cbd5e1",
                    showlegend=False,
                )
                st.plotly_chart(fig_res, use_container_width=True)

            # Recent tickets table
            st.markdown(
                '<div class="section-header">Recent Tickets</div>',
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
            '<div class="section-header">Engagement & Relationship Timeline</div>',
            unsafe_allow_html=True,
        )
        timeline_df = get_engagement_timeline(selected_operator_id, months_back=12)
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
            '<div class="section-header">Contract Financials</div>',
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
            '<div class="section-header">Revenue Projections (12-Month)</div>',
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
            fig_proj.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#cbd5e1",
                height=300,
            )
            st.plotly_chart(fig_proj, use_container_width=True)
        else:
            st.info("No financial projections available.")

        st.markdown(
            '<div class="section-header">Contract Amendments History</div>',
            unsafe_allow_html=True,
        )
        amendments_df = get_contract_amendments(selected_operator_id, customer_df)
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
                total_amendments_value = amendments_df["financial_impact_eur"].sum()
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
                    amendments_df.groupby("amendment_type")["financial_impact_eur"]
                    .sum()
                    .reset_index()
                )
                amend_by_type.columns = ["Type", "Total Impact (€)"]
                fig_amend = px.bar(amend_by_type, x="Type", y="Total Impact (€)")
                fig_amend.update_layout(
                    height=320,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#cbd5e1",
                    showlegend=False,
                )
                st.plotly_chart(fig_amend, use_container_width=True)
        else:
            st.info("No contract amendments found.")

        # Project financial summary
        st.markdown(
            '<div class="section-header">Project Financial Summary</div>',
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
                    labels={"total_value": "Total Value (€)", "status": "Status"},
                )
                fig_value.update_layout(
                    height=300,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#cbd5e1",
                    showlegend=False,
                )
                st.plotly_chart(fig_value, use_container_width=True)

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
                st.dataframe(display_summary, use_container_width=True, hide_index=True)

    # ── HEALTH TAB ── (already enhanced above) ──

    # ── QUICK ACTIONS TAB ──
    with tabs[4]:
        st.markdown(
            '<div class="section-header">Quick Actions</div>', unsafe_allow_html=True
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
            '<div class="section-header">Notes & Actions</div>', unsafe_allow_html=True
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
            '<div class="section-header">Quick Benchmark (by Tier)</div>',
            unsafe_allow_html=True,
        )
        benchmark = get_operator_comparison_benchmarks(selected_operator_id)
        if benchmark and "percentiles" in benchmark:
            pcts = benchmark["percentiles"]
            tier_stats = next((item for item in benchmark.get("tier_benchmarks", []) if item.get("tier") == profile.get("tier")), {})
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
        """
        <style>
        /* ═══ CLEAN KPI DASHBOARD ═══ */
        .kpi-hero {
            text-align: center;
            padding: 1.5rem 1rem;
            margin-bottom: 2rem;
            background: linear-gradient(135deg, rgba(0,192,255,0.08) 0%, rgba(0,255,136,0.04) 100%);
            border-radius: 16px;
            border: 1px solid rgba(0,192,255,0.15);
        }
        .kpi-hero h1 {
            font-size: 1.8rem;
            background: linear-gradient(90deg, #00c0ff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.3rem;
            font-weight: 700;
        }
        .kpi-hero p {
            color: #6b7a94;
            font-size: 0.9rem;
        }
        
        /* Clean Card Base */
        .glass-card {
            background: linear-gradient(145deg, rgba(30,40,55,0.95) 0%, rgba(18,25,38,0.98) 100%);
            border: 1px solid rgba(0,192,255,0.1);
            border-radius: 12px;
            padding: 1.25rem;
            transition: all 0.3s ease;
        }
        .glass-card:hover {
            border-color: rgba(0,192,255,0.25);
            box-shadow: 0 8px 24px rgba(0,192,255,0.12);
        }
        
        /* Hero Score Card */
        .hero-card {
            background: linear-gradient(145deg, rgba(0,192,255,0.12) 0%, rgba(0,255,136,0.06) 100%);
            border: 1px solid rgba(0,192,255,0.2);
            border-radius: 16px;
            padding: 1.5rem;
            text-align: center;
        }
        
        /* Value Styling */
        .glass-value {
            font-size: 1.75rem;
            font-weight: 700;
            background: linear-gradient(135deg, #00c0ff 0%, #00ff88 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.2rem;
            line-height: 1.2;
        }
        .glass-value-lg {
            font-size: 2.2rem;
        }
        .glass-label {
            font-size: 0.7rem;
            color: #5a6a85;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }
        .glass-trend {
            font-size: 0.65rem;
            margin-top: 0.5rem;
            padding: 3px 8px;
            border-radius: 12px;
            display: inline-flex;
            align-items: center;
            gap: 3px;
            font-weight: 600;
        }
        .trend-up { background: rgba(0,255,136,0.12); color: #00ff88; }
        .trend-down { background: rgba(245,101,101,0.12); color: #f56565; }
        .trend-neutral { background: rgba(100,116,139,0.12); color: #64748b; }
        
        /* Section Headers */
        .kpi-section-header {
            font-size: 1.1rem;
            font-weight: 600;
            color: #e8ecf4;
            margin: 1.5rem 0 0.75rem;
            padding: 0.6rem 0.8rem;
            background: linear-gradient(90deg, rgba(0,192,255,0.15), transparent);
            border-left: 3px solid #00c0ff;
            border-radius: 0 8px 8px 0;
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }
        .kpi-section-header .icon {
            font-size: 1.2rem;
        }
        
        /* Section Subheader */
        .kpi-sub-header {
            font-size: 0.85rem;
            font-weight: 500;
            color: #8ba3c7;
            margin: 1rem 0 0.5rem;
            padding-left: 0.5rem;
            border-left: 2px solid rgba(0,192,255,0.3);
        }
        
        /* Grid Layouts */
        .kpi-grid-4 {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 0.75rem;
            margin-bottom: 1rem;
        }
        .kpi-grid-3 {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 0.75rem;
            margin-bottom: 1rem;
        }
        .kpi-grid-2 {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 0.75rem;
            margin-bottom: 1rem;
        }
        
        /* Chart Container */
        .chart-container {
            background: rgba(18,25,38,0.6);
            border: 1px solid rgba(0,192,255,0.08);
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 0.75rem;
        }
        
        /* Chart Title */
        .chart-title {
            font-size: 0.8rem;
            font-weight: 600;
            color: #00c0ff;
            margin-bottom: 0.5rem;
            text-align: center;
        }
        
        /* Gap between sections */
        .section-gap {
            height: 1rem;
        }
        
        /* Responsive */
        @media (max-width: 1200px) {
            .kpi-grid-4 { grid-template-columns: repeat(2, 1fr); }
            .kpi-grid-3 { grid-template-columns: repeat(2, 1fr); }
        }
        @media (max-width: 768px) {
            .kpi-grid-4, .kpi-grid-3, .kpi-grid-2 { grid-template-columns: 1fr; }
        }
        </style>
        
        <div class="kpi-hero">
            <h1>KPI Dashboard</h1>
            <p>Business performance overview</p>
        </div>
        """,
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
    is_weekend = ops_df["is_weekend"].sum() if "is_weekend" in ops_df.columns else 2

    # Historical trends
    hist_trend = None
    try:
        hist_trend = get_historical_trends(ops_df, days_back=7)
    except:
        pass

    # Maintenance forecast
    maint_forecast = None
    if stations.shape[0] > 0:
        try:
            maint_forecast = get_maintenance_forecast(stations[0])
        except:
            pass

    st.markdown(
        '<div class="kpi-section-header"><span class="icon">🚂</span> Operations</div>',
        unsafe_allow_html=True,
    )

    # Core metrics - simplified to 4 key cards
    st.markdown(
        f"""
        <div class="kpi-grid-4">
            <div class="glass-card">
                <div class="glass-value">{total_stations}</div>
                <div class="glass-label">Active Stations</div>
                <div class="glass-trend trend-up">Operational</div>
            </div>
            <div class="glass-card">
                <div class="glass-value">{total_gates:,}</div>
                <div class="glass-label">PSD Gates</div>
                <div class="glass-trend trend-up">{total_active} Active</div>
            </div>
            <div class="glass-card">
                <div class="glass-value">{avg_sync:.1f}%</div>
                <div class="glass-label">Sync Efficiency</div>
                <div class="glass-trend {"trend-up" if avg_sync >= 85 else "trend-neutral"}">Target: 85%</div>
            </div>
            <div class="glass-card">
                <div class="glass-value">{avg_risk:.1f}</div>
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
                plot_bgcolor="rgba(0,0,0,0.3)",
                font=dict(color="#8ba3c7"),
                title=dict(font=dict(size=14, color="#00c0ff")),
                margin=dict(l=20, r=20, t=40, b=30),
                height=320,
            )
            st.plotly_chart(fig_energy, use_container_width=True)

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
                    plot_bgcolor="rgba(0,0,0,0.2)",
                    font=dict(color="#8ba3c7"),
                    title=dict(font=dict(size=14, color="#00c0ff")),
                    margin=dict(l=20, r=20, t=40, b=20),
                    height=320,
                )
                st.plotly_chart(fig_hist, use_container_width=True)
            else:
                st.markdown(
                    """
                    <div class="glass-card" style="height: 250px; display: flex; flex-direction: column; justify-content: center; align-items: center;">
                        <div class="glass-value" style="background: linear-gradient(90deg, #64748b, #8ba3c7); -webkit-background-clip: text;">📈</div>
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
                    <div class="glass-value" style="background: linear-gradient(90deg, #64748b, #8ba3c7); -webkit-background-clip: text;">📈</div>
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
                plot_bgcolor="rgba(255,215,0,0.1)",
                font=dict(color="#8ba3c7"),
                title=dict(font=dict(size=14, color="#ffd700")),
                margin=dict(l=20, r=20, t=40, b=20),
                height=320,
            )
            fig_forecast.update_traces(fill="tozeroy", line=dict(width=3))
            st.plotly_chart(fig_forecast, use_container_width=True)
        with col_maint2:
            if "Predicted Risk %" in maint_forecast.columns:
                avg_forecast_risk = maint_forecast["Predicted Risk %"].mean()
                st.markdown(
                    f"""
                    <div class="glass-card" style="height: 250px; display: flex; flex-direction: column; justify-content: center; align-items: center;">
                        <div class="glass-value glass-value-lg">{avg_forecast_risk:.1f}%</div>
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
        st.plotly_chart(fig_treemap, use_container_width=True)

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
            font=dict(color="#8ba3c7", size=12),
            height=320,
            margin=dict(l=30, r=30, t=40, b=30),
        )
        st.plotly_chart(fig_gauge_sync, use_container_width=True)

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
                        {"range": [50, 100], "color": "rgba(245,101,101,0.15)"},
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
            font=dict(color="#8ba3c7", size=12),
            height=320,
            margin=dict(l=30, r=30, t=40, b=30),
        )
        st.plotly_chart(fig_gauge_risk, use_container_width=True)

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
            font=dict(color="#8ba3c7"),
            title=dict(font=dict(size=13, color="#00c0ff")),
            height=320,
            margin=dict(l=10, r=10, t=30, b=10),
        )
        st.plotly_chart(fig_door, use_container_width=True)

    with col_d2:
        maint_counts = ops_df["maintenance_status"].value_counts().reset_index()
        maint_counts.columns = ["Status", "Count"]
        fig_maint_bar = px.bar(
            maint_counts,
            y="Status",
            x="Count",
            orientation="h",
            title="Maintenance",
            color="Status",
            color_discrete_sequence=["#00ff88", "#00c0ff", "#ffd700", "#f56565"],
        )
        fig_maint_bar.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0.2)",
            font=dict(color="#8ba3c7"),
            title=dict(font=dict(size=13, color="#00c0ff")),
            height=320,
            yaxis=dict(categoryorder="total ascending"),
        )
        st.plotly_chart(fig_maint_bar, use_container_width=True)

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
                <div class="glass-card">
                    <div class="glass-value">${mrr:,.0f}</div>
                    <div class="glass-label">Monthly Revenue</div>
                    <div class="glass-trend trend-up">↑ {growth_rate:.1f}% MoM</div>
                </div>
                <div class="glass-card">
                    <div class="glass-value">${arr:,.0f}</div>
                    <div class="glass-label">Annual Revenue</div>
                    <div class="glass-trend {"trend-up" if arr >= 600000 else "trend-neutral"}">Target: $2M</div>
                </div>
                <div class="glass-card">
                    <div class="glass-value">${expansion_rev:,.0f}</div>
                    <div class="glass-label">Expansion Revenue</div>
                    <div class="glass-trend trend-up">◆ Upsells</div>
                </div>
                <div class="glass-card">
                    <div class="glass-value">${revenue_per_cust:,.0f}</div>
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
                <div class="glass-card">
                    <div class="glass-value">${ltv:,.0f}</div>
                    <div class="glass-label">Customer LTV</div>
                    <div class="glass-trend trend-up">LTV:CAC {ltv_cac_ratio:.1f}x</div>
                </div>
                <div class="glass-card">
                    <div class="glass-value" style="background: linear-gradient(90deg, #ffd700, #ffaa00); -webkit-background-clip: text;">{gross_margin:.1f}%</div>
                    <div class="glass-label">Gross Margin</div>
                    <div class="glass-trend {"trend-up" if gross_margin >= 70 else "trend-neutral"}">Target: &gt;70%</div>
                </div>
                <div class="glass-card">
                    <div class="glass-value">${net_revenue:,.0f}</div>
                    <div class="glass-label">Net Revenue</div>
                    <div class="glass-trend trend-up">◆ After Costs</div>
                </div>
                <div class="glass-card">
                    <div class="glass-value">${burn_rate:,}</div>
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
                <div class="glass-card">
                    <div class="glass-value">${cac}</div>
                    <div class="glass-label">CAC</div>
                    <div class="glass-trend trend-up">Payback: {payback_period:.0f}mo</div>
                </div>
                <div class="glass-card">
                    <div class="glass-value">{payback_period:.0f}</div>
                    <div class="glass-label">CAC Payback</div>
                    <div class="glass-trend {"trend-up" if payback_period <= 12 else "trend-neutral"}">Target: &lt;12mo</div>
                </div>
                <div class="glass-card">
                    <div class="glass-value">{runway:.0f}</div>
                    <div class="glass-label">Runway (Months)</div>
                    <div class="glass-trend {"trend-up" if runway >= 18 else "trend-neutral"}">◆ Cash Reserve</div>
                </div>
                <div class="glass-card">
                    <div class="glass-value" style="background: linear-gradient(90deg, #f56565, #ed8936); -webkit-background-clip: text;">{churn_rate:.1f}%</div>
                    <div class="glass-label">Churn Rate</div>
                    <div class="glass-trend {"trend-down" if churn_rate > 5 else "trend-up"}">Target: &lt;5%</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Key Financial Charts
        st.markdown('<div class="kpi-sub-header">Trends</div>', unsafe_allow_html=True)
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            fig_mrr = px.area(
                df_fin,
                x="Month",
                y="MRR",
                title="Revenue (MRR)",
                color_discrete_sequence=["#00c0ff"],
            )
            fig_mrr.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,192,255,0.1)",
                font=dict(color="#8ba3c7"),
                title=dict(font=dict(size=13, color="#00c0ff")),
                margin=dict(l=20, r=20, t=30, b=20),
                height=300,
            )
            fig_mrr.update_traces(line=dict(width=2))
            st.plotly_chart(fig_mrr, use_container_width=True)

        with col_f2:
            fig_cust = px.line(
                df_fin,
                x="Month",
                y="Total_Customers",
                title="Customers",
                color_discrete_sequence=["#00ff88"],
            )
            fig_cust.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,255,136,0.1)",
                font=dict(color="#8ba3c7"),
                title=dict(font=dict(size=13, color="#00ff88")),
                margin=dict(l=20, r=20, t=30, b=20),
                height=300,
            )
            fig_cust.update_traces(line=dict(width=2))
            st.plotly_chart(fig_cust, use_container_width=True)

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
                font=dict(color="#8ba3c7"),
                title=dict(
                    text="Revenue Waterfall", font=dict(size=13, color="#00c0ff")
                ),
                height=300,
                showlegend=False,
                margin=dict(l=10, r=10, t=30, b=10),
            )
            st.plotly_chart(fig_waterfall, use_container_width=True)

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
                color_discrete_sequence=["#00c0ff", "#00ff88", "#ffd700", "#8b5cf6"],
            )
            fig_mix.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0.2)",
                font=dict(color="#8ba3c7"),
                title=dict(font=dict(size=13, color="#00c0ff")),
                height=300,
            )
            st.plotly_chart(fig_mix, use_container_width=True)
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
                at_risk[at_risk["risk_level"].isin(["High Risk", "Medium Risk"])]
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
            <div class="glass-card">
                <div class="glass-value">{total_customers}</div>
                <div class="glass-label">Total Customers</div>
                <div class="glass-trend trend-up">◆ Active</div>
            </div>
            <div class="glass-card">
                <div class="glass-value" style="background: linear-gradient(90deg, #f56565, #ed8936); -webkit-background-clip: text;">{at_risk_count}</div>
                <div class="glass-label">At-Risk</div>
                <div class="glass-trend {"trend-down" if at_risk_count > 3 else "trend-up"}">{"Needs Attention" if at_risk_count > 3 else "Healthy"}</div>
            </div>
            <div class="glass-card">
                <div class="glass-value">${renewal_value:,.0f}</div>
                <div class="glass-label">Renewal Value</div>
                <div class="glass-trend trend-up">Next 180 Days</div>
            </div>
            <div class="glass-card">
                <div class="glass-value" style="background: linear-gradient(90deg, #00c0ff, #00ff88); -webkit-background-clip: text;">{avg_health:.0f}</div>
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
            <div class="glass-card">
                <div class="glass-value">{nps_score}</div>
                <div class="glass-label">NPS Score</div>
                <div class="glass-trend {"trend-up" if nps_score >= 50 else "trend-neutral"}">◆ Industry: 41</div>
            </div>
            <div class="glass-card">
                <div class="glass-value">{avg_ticket_res:.1f}h</div>
                <div class="glass-label">Avg Ticket Res.</div>
                <div class="glass-trend {"trend_up" if avg_ticket_res <= 4 else "trend-neutral"}">Target: &lt;4h</div>
            </div>
            <div class="glass-card">
                <div class="glass-value">{contract_renewal_rate:.0f}%</div>
                <div class="glass-label">Renewal Rate</div>
                <div class="glass-trend trend-up">◆ Contract Health</div>
            </div>
            <div class="glass-card">
                <div class="glass-value">{premium_cust}</div>
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
            <div class="glass-card">
                <div class="glass-value" style="background: linear-gradient(90deg, #00ff88, #00c0ff); -webkit-background-clip: text;">{seg_counts.get("Strategic Partners", 8)}</div>
                <div class="glass-label">Strategic Partners</div>
                <div class="glass-trend trend-up">◆ Top Tier</div>
            </div>
            <div class="glass-card">
                <div class="glass-value">{seg_counts.get("Key Accounts", seg_counts.get("Potential", 15))}</div>
                <div class="glass-label">Key Accounts</div>
                <div class="glass-trend trend-up">Growth Ready</div>
            </div>
            <div class="glass-card">
                <div class="glass-value">{seg_counts.get("Growth Potential", seg_counts.get("Loyal", 20))}</div>
                <div class="glass-label">Growth Potential</div>
                <div class="glass-trend trend-up">Stable Base</div>
            </div>
            <div class="glass-card">
                <div class="glass-value">{seg_counts.get("At Risk", seg_counts.get("Churned", 5))}</div>
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
                    font=dict(color="#8ba3c7"),
                    title=dict(font=dict(size=13, color="#00c0ff")),
                    margin=dict(l=10, r=10, t=30, b=10),
                    height=320,
                )
                st.plotly_chart(fig_seg, use_container_width=True)

        with col_c2:
            if "segment" in rfm_data.columns and "recency" in rfm_data.columns:
                fig_rfm = px.scatter(
                    rfm_data,
                    x="recency",
                    y="monetary",
                    size="frequency",
                    color="segment",
                    title="RFM Analysis",
                    color_discrete_map=colors_map,
                    size_max=30,
                )
                fig_rfm.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0.3)",
                    font=dict(color="#8ba3c7"),
                    title=dict(font=dict(size=13, color="#00c0ff")),
                    margin=dict(l=10, r=10, t=30, b=10),
                    height=320,
                )
                st.plotly_chart(fig_rfm, use_container_width=True)

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
        color_discrete_sequence=["#00c0ff", "#00ff88", "#ffd700", "#f56565", "#8b5cf6"],
    )
    fig_cust_funnel.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#8ba3c7"),
        title=dict(font=dict(size=13, color="#00c0ff")),
        margin=dict(l=10, r=10, t=30, b=10),
        height=300,
    )
    st.plotly_chart(fig_cust_funnel, use_container_width=True)

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
            color_discrete_sequence=["#00ff88", "#00c0ff", "#ffd700", "#f56565"],
        )
        fig_sat.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0.2)",
            font=dict(color="#8ba3c7"),
            title=dict(font=dict(size=13, color="#00c0ff")),
            height=300,
        )
        st.plotly_chart(fig_sat, use_container_width=True)

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
            plot_bgcolor="rgba(0,0,0,0.2)",
            font=dict(color="#8ba3c7"),
            title=dict(font=dict(size=13, color="#00c0ff")),
            height=300,
        )
        st.plotly_chart(fig_renewal_cal, use_container_width=True)

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
                <div class="glass-value glass-value-lg">{overall_score:.0f}</div>
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
                <div class="glass-value glass-value-lg" style="background: linear-gradient(90deg, #00ff88, #00c0ff); -webkit-background-clip: text;">{total_stations}</div>
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
                <div class="glass-value glass-value-lg" style="background: linear-gradient(90deg, #ffd700, #ffaa00); -webkit-background-clip: text;">${arr:,.0f}</div>
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
                f"${mrr:,.0f}",
                f"${arr:,.0f}",
                f"${ltv:,.0f}",
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

elif active_tab == "company":
    # ── Modern Glassmorphism Company Profile CSS ──
    st.markdown(
        """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');
    
    /* Main Company Profile Styles */
    .company-section {
        font-family: 'Inter', -apple-system, sans-serif;
    }
    
    /* Hero Section */
    .hero-section {
        background: linear-gradient(135deg, rgba(30, 60, 114, 0.95), rgba(42, 82, 152, 0.9));
        border-radius: 20px;
        padding: 2.5rem;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(0, 192, 255, 0.2);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    .hero-section::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -20%;
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, rgba(0, 192, 255, 0.15), transparent 70%);
        pointer-events: none;
    }
    .hero-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.2rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }
    .hero-subtitle {
        font-size: 1.1rem;
        color: rgba(204, 231, 255, 0.9);
        margin-bottom: 1rem;
    }
    .hero-tagline {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: rgba(0, 192, 255, 0.15);
        padding: 0.5rem 1rem;
        border-radius: 20px;
        color: #00c0ff;
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    /* Metrics Dashboard */
    .metrics-dashboard {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin-bottom: 2rem;
    }
    @media (max-width: 768px) {
        .metrics-dashboard { grid-template-columns: repeat(2, 1fr); }
    }
    .metric-card {
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-4px);
        background: rgba(255, 255, 255, 0.12);
        border-color: rgba(0, 192, 255, 0.3);
        box-shadow: 0 12px 24px rgba(0, 192, 255, 0.15);
    }
    .metric-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }
    .metric-value {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.8rem;
        font-weight: 700;
        color: #ffffff;
        line-height: 1.2;
    }
    .metric-label {
        font-size: 0.8rem;
        color: rgba(204, 231, 255, 0.7);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 0.25rem;
    }
    
    /* Section Headers */
    .section-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin: 2rem 0 1.25rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    .section-icon {
        font-size: 1.5rem;
    }
    .section-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.3rem;
        font-weight: 600;
        color: #ffffff;
    }
    
    /* Glass Cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.06);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 18px;
        padding: 1.75rem;
        margin-bottom: 1.25rem;
        transition: all 0.3s ease;
    }
    .glass-card:hover {
        background: rgba(255, 255, 255, 0.1);
        border-color: rgba(0, 192, 255, 0.2);
    }
    .glass-card h3 {
        color: #00c0ff;
        font-size: 1.15rem;
        font-weight: 600;
        margin-bottom: 0.75rem;
    }
    .glass-card p {
        color: rgba(255, 255, 255, 0.85);
        font-size: 0.95rem;
        line-height: 1.65;
    }
    
    /* Service Cards */
    .services-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 1rem;
        margin-bottom: 1.5rem;
    }
    .service-card {
        background: linear-gradient(135deg, rgba(30, 60, 114, 0.6), rgba(42, 82, 152, 0.5));
        border: 1px solid rgba(0, 192, 255, 0.15);
        border-radius: 16px;
        padding: 1.5rem;
        transition: all 0.3s ease;
    }
    .service-card:hover {
        transform: translateY(-5px);
        border-color: rgba(0, 192, 255, 0.4);
        box-shadow: 0 12px 28px rgba(0, 192, 255, 0.2);
    }
    .service-icon {
        font-size: 2rem;
        margin-bottom: 0.75rem;
    }
    .service-title {
        font-size: 1.05rem;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 0.5rem;
    }
    .service-desc {
        font-size: 0.85rem;
        color: rgba(204, 231, 255, 0.8);
        line-height: 1.5;
    }
    .service-features {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 0.75rem;
    }
    .feature-tag {
        background: rgba(0, 192, 255, 0.15);
        color: #00c0ff;
        padding: 0.3rem 0.65rem;
        border-radius: 12px;
        font-size: 0.7rem;
        font-weight: 500;
    }
    
    /* Team Grid */
    .team-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 1.25rem;
        margin-bottom: 2rem;
    }
    .team-card {
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    .team-card:hover {
        transform: translateY(-5px);
        background: rgba(255, 255, 255, 0.1);
        border-color: rgba(0, 192, 255, 0.3);
    }
    .team-avatar {
        width: 80px;
        height: 80px;
        border-radius: 50%;
        margin: 0 auto 1rem;
        border: 3px solid rgba(0, 192, 255, 0.3);
        overflow: hidden;
    }
    .team-avatar img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .team-name {
        font-size: 1rem;
        font-weight: 600;
        color: #ffffff;
    }
    .team-role {
        font-size: 0.8rem;
        color: #00c0ff;
        margin-bottom: 0.5rem;
    }
    .team-desc {
        font-size: 0.8rem;
        color: rgba(204, 231, 255, 0.75);
    }
    
    /* Award Cards */
    .awards-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1rem;
    }
    .award-card {
        background: linear-gradient(135deg, rgba(255, 215, 0, 0.1), rgba(255, 215, 0, 0.05));
        border: 1px solid rgba(255, 215, 0, 0.3);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
    }
    .award-icon {
        font-size: 2.5rem;
        margin-bottom: 0.75rem;
    }
    .award-title {
        font-size: 1rem;
        font-weight: 600;
        color: #ffd700;
    }
    .award-org {
        font-size: 0.8rem;
        color: rgba(255, 215, 0, 0.8);
    }
    
    /* Partners Section */
    .partners-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 1rem;
        margin-bottom: 1.5rem;
    }
    .partner-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .partner-logo {
        font-size: 1.2rem;
        font-weight: 600;
        color: rgba(204, 231, 255, 0.8);
    }
    
    /* Stats Row */
    .stats-row {
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
        margin: 1rem 0;
    }
    .stat-item {
        flex: 1 1 45%;
        background: rgba(255, 255, 255, 0.04);
        border-radius: 12px;
        padding: 1rem;
    }
    .stat-label {
        font-size: 0.75rem;
        color: rgba(204, 231, 255, 0.6);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .stat-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #ffffff;
    }
    
    /* Chart Containers */
    .chart-container {
        background: rgba(255, 255, 255, 0.04);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }
    
    /* Timeline */
    .timeline {
        position: relative;
        padding-left: 2rem;
    }
    .timeline::before {
        content: '';
        position: absolute;
        left: 0.5rem;
        top: 0;
        bottom: 0;
        width: 2px;
        background: linear-gradient(to bottom, #00c0ff, #ffd700);
    }
    .timeline-item {
        position: relative;
        padding-bottom: 1.5rem;
    }
    .timeline-item::before {
        content: '';
        position: absolute;
        left: -1.65rem;
        top: 0.3rem;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: #00c0ff;
        border: 2px solid rgba(0, 192, 255, 0.3);
    }
    .timeline-date {
        font-size: 0.75rem;
        color: #00c0ff;
        font-weight: 600;
    }
    .timeline-title {
        font-size: 0.95rem;
        color: #ffffff;
        font-weight: 500;
        margin: 0.25rem 0;
    }
    
    /* Old styles cleanup */
    .main { background: linear-gradient(135deg, #1E3C72, #2A5298); }
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="company-section">', unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════
    # HERO SECTION
    # ═══════════════════════════════════════════════════
    st.markdown(
        """
    <div class="hero-section">
        <div class="hero-title">SicherGleis GmbH</div>
        <div class="hero-subtitle">Precision Railway Safety Systems</div>
        <div class="hero-tagline">
            <span>🛡️</span>
            <span>Suraksha (Safety-First) + German Engineering Excellence</span>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # ═══════════════════════════════════════════════════
    # COMPANY METRICS DASHBOARD
    # ═══════════════════════════════════════════════════
    st.markdown(
        '<div class="section-header"><span class="section-icon">📊</span><span class="section-title">Company Impact</span></div>',
        unsafe_allow_html=True,
    )

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.markdown(
            """
        <div class="metric-card">
            <div class="metric-icon">🚉</div>
            <div class="metric-value">127</div>
            <div class="metric-label">Stations Deployed</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col_m2:
        st.markdown(
            """
        <div class="metric-card">
            <div class="metric-icon">🚪</div>
            <div class="metric-value">2,450</div>
            <div class="metric-label">PSD Units Installed</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col_m3:
        st.markdown(
            """
        <div class="metric-card">
            <div class="metric-icon">🌍</div>
            <div class="metric-value">5</div>
            <div class="metric-label">Countries</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col_m4:
        st.markdown(
            """
        <div class="metric-card">
            <div class="metric-icon">👥</div>
            <div class="metric-value">14</div>
            <div class="metric-label">Team Members</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # ═══════════════════════════════════════════════════
    # ABOUT SECTION
    # ═══════════════════════════════════════════════════
    st.markdown(
        '<div class="section-header"><span class="section-icon">🏢</span><span class="section-title">About Us</span></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
    <div class="glass-card">
        <h3>Core Concept</h3>
        <p>SicherGleis delivers precision-engineered Platform Screen Door (PSD) systems that unite 
        <strong>Suraksha</strong> (safety-first philosophy) with German engineering excellence to create 
        safe, intelligent, and future-ready urban rail infrastructure.</p>
        <p>Our systems actively prevent platform edge incidents, optimize boarding flow, and enable predictive 
        maintenance — all in real time.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
    <div class="glass-card">
        <h3>Market & Vision</h3>
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
                <div class="stat-label">System Uptime</div>
                <div class="stat-value">99.97%</div>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # ═══════════════════════════════════════════════════
    # SERVICES SECTION
    # ═══════════════════════════════════════════════════
    st.markdown(
        '<div class="section-header"><span class="section-icon">🛠️</span><span class="section-title">Our Services</span></div>',
        unsafe_allow_html=True,
    )

    services_data = [
        {
            "icon": "🚪",
            "title": "Platform Screen Door (PSD) Systems",
            "description": "Advanced PSD systems with smart sensors, automated gate synchronization, and real-time monitoring.",
            "features": ["Door State Detection", "Temp & Vibration", "Passenger Flow", "Train Sync"],
        },
        {
            "icon": "🔮",
            "title": "Predictive Maintenance Analytics",
            "description": "AI-powered system forecasting potential failures before they occur.",
            "features": ["7-Day Risk Forecast", "Multi-Factor Scoring", "Auto Alerts", "Status Classification"],
        },
        {
            "icon": "📊",
            "title": "Real-Time Operations Dashboard",
            "description": "Comprehensive dashboard for monitoring station operations in real-time.",
            "features": ["Live Monitoring", "Incident Logging", "Network Overview", "Mobile Ready"],
        },
        {
            "icon": "👥",
            "title": "Customer Business Intelligence",
            "description": "RFM-based segmentation, contract health scoring, and renewal forecasting.",
            "features": ["RFM Analysis", "At-Risk Detection", "Renewal Forecasting", "Portfolio Management"],
},
    ]

    services_html = '<div class="services-grid">'
    for svc in services_data:
        features_tags = "".join([f'<span class="feature-tag">{f}</span>' for f in svc["features"]])
        services_html += f"""
        <div class="service-card">
            <div class="service-icon">{svc["icon"]}</div>
            <div class="service-title">{svc["title"]}</div>
            <div class="service-desc">{svc["description"]}</div>
            <div class="service-features">{features_tags}</div>
        </div>"""
    services_html += "</div>"
    st.markdown(services_html, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════
    # CHARTS SECTION
    # ═══════════════════════════════════════════════════
    st.markdown(
        '<div class="section-header"><span class="section-icon">📈</span><span class="section-title">Performance Metrics</span></div>',
        unsafe_allow_html=True,
    )

    col_c1, col_c2 = st.columns(2)
    with col_c1:
        stations_data = pd.DataFrame({
            "Region": ["Berlin", "Munich", "Vienna", "Zurich", "Frankfurt"],
            "Stations": [45, 32, 28, 15, 7],
        })
        fig_stations = px.bar(
            stations_data,
            x="Region",
            y="Stations",
            title="Stations by Region",
            color_discrete_sequence=["#00c0ff"],
        )
        fig_stations.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,192,255,0.1)",
            font=dict(color="#8ba3c7"),
            title=dict(font=dict(size=14, color="#00c0ff")),
            margin=dict(l=20, r=20, t=40, b=20),
            height=280,
        )
        st.plotly_chart(fig_stations, use_container_width=True)

    with col_c2:
        service_breakdown = pd.DataFrame({
            "Service": ["PSD Systems", "Analytics", "Dashboard", "BI Tools"],
            "Revenue": [45, 25, 20, 10],
        })
        fig_service = px.pie(
            service_breakdown,
            values="Revenue",
            names="Service",
            title="Revenue by Service (%)",
            color_discrete_sequence=["#00c0ff", "#00ff88", "#ffd700", "#f56565"],
        )
        fig_service.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0, 0, 0)",
            font=dict(color="#8ba3c7"),
            title=dict(font=dict(size=14, color="#00c0ff")),
            margin=dict(l=20, r=20, t=40, b=20),
            height=280,
        )
        st.plotly_chart(fig_service, use_container_width=True)

    # Second row of charts
    col_c3, col_c4 = st.columns(2)
    with col_c3:
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
        revenue_data = pd.DataFrame({
            "Month": months * 2,
            "Revenue": [120, 145, 180, 210, 195, 230, 280, 320, 350, 380, 420, 450],
            "Type": ["Actual"] * 6 + ["Projected"] * 6,
        })
        fig_rev = px.line(
            revenue_data,
            x="Month",
            y="Revenue",
            title="Revenue Trajectory (€K)",
            color="Type",
            color_discrete_map={"Actual": "#00c0ff", "Projected": "#ffd700"},
        )
        fig_rev.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,192,255,0.05)",
            font=dict(color="#8ba3c7"),
            title=dict(font=dict(size=14, color="#00c0ff")),
            margin=dict(l=20, r=20, t=40, b=20),
            height=280,
        )
        st.plotly_chart(fig_rev, use_container_width=True)

    with col_c4:
        kpi_scores = pd.DataFrame({
            "KPI": ["Uptime", "Safety", "Satisfaction", "Efficiency"],
            "Score": [99.7, 98.2, 94.5, 91.8],
        })
        fig_kpi = px.bar(
            kpi_scores,
            x="KPI",
            y="Score",
            title="Key Performance Indicators",
            color_discrete_sequence=["#00ff88"],
        )
        fig_kpi.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,255,136,0.1)",
            font=dict(color="#8ba3c7"),
            title=dict(font=dict(size=14, color="#00ff88")),
            margin=dict(l=20, r=20, t=40, b=20),
            height=280,
            yaxis_range=[0, 100],
        )
        st.plotly_chart(fig_kpi, use_container_width=True)

    # ═══════════════════════════════════════════════════
    # AWARDS & CERTIFICATIONS
    # ═══════════════════════════════════════════════════
    st.markdown(
        '<div class="section-header"><span class="section-icon">🏆</span><span class="section-title">Awards & Certifications</span></div>',
        unsafe_allow_html=True,
    )

    awards_data = [
        {"icon": "🥇", "title": "Innovation in Urban Transit", "org": "UITP 2024"},
        {"icon": "🔒", "title": "ISO 27001 Certified", "org": "Information Security"},
        {"icon": "🌿", "title": "EcoRail Excellence Award", "org": "German Transport Forum"},
        {"icon": "⭐", "title": "Best PSD Solution Provider", "org": "Smart City Expo"},
    ]

    awards_html = '<div class="awards-grid">'
    for award in awards_data:
        awards_html += f"""
        <div class="award-card">
            <div class="award-icon">{award["icon"]}</div>
            <div class="award-title">{award["title"]}</div>
            <div class="award-org">{award["org"]}</div>
        </div>"""
    awards_html += "</div>"
    st.markdown(awards_html, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════
    # PARTNERS
    # ═══════════════════════════════════════════
    st.markdown(
        '<div class="section-header"><span class="section-icon">🤝</span><span class="section-title">Partners & Clients</span></div>',
        unsafe_allow_html=True,
    )

    partners = [
        {"name": "DB Station&Service", "logo": "🚂"},
        {"name": "S-Bahn Berlin", "logo": "🚇"},
        {"name": "BVG Berlin", "logo": "🚌"},
        {"name": "MVV Munich", "logo": "🚆"},
        {"name": "Wiener Linien", "logo": "🚊"},
        {"name": "Indian Metro", "logo": "🚈"},
    ]

    partners_html = '<div class="partners-grid">'
    for partner in partners:
        partners_html += f"""
        <div class="partner-card">
            <div class="partner-logo">{partner["logo"]} {partner["name"]}</div>
        </div>"""
    partners_html += "</div>"
    st.markdown(partners_html, unsafe_allow_html=True)

    # Close section
    st.markdown("</div>", unsafe_allow_html=True)

    # ═════════════════════════════════════════════════
    # Leadership Team - Clickable Cards
    st.markdown(
        '<div class="section-header"><span class="section-icon">👥</span><span class="section-title">Leadership Team</span></div>',
        unsafe_allow_html=True,
    )
    
    if "team_selected" not in st.session_state:
        st.session_state.team_selected = None
    
    team = get_leadership_data()
    team_cols = st.columns(len(team))
    
    for i, member in enumerate(team):
        with team_cols[i]:
            img_url = member.get("img") or f"https://ui-avatars.com/api/?name={member['name'].replace(' ', '+')}&background=1a365d&color=fff&size=120"
            
            if st.session_state.team_selected == member["name"]:
                st.image(img_url, width=100)
                st.markdown(f"**{member['name']}**")
                st.caption(member["role"])
                if st.button("Close", key=f"close_{i}"):
                    st.session_state.team_selected = None
                    st.rerun()
            else:
                if st.button(f"{member['name']}\n{member['role']}", key=f"btn_{i}"):
                    st.session_state.team_selected = member["name"]
                    st.rerun()
                st.image(img_url, width=60)

    # Show expanded details if someone selected
    if st.session_state.team_selected:
        member = next(m for m in team if m["name"] == st.session_state.team_selected)
        img_url = member.get("img") or f"https://ui-avatars.com/api/?name={member['name'].replace(' ', '+')}&background=1a365d&color=fff&size=200"
        
        st.markdown("---")
        
        col_l, col_r = st.columns([1, 2])
        with col_l:
            st.image(img_url, width=200)
            st.markdown(f"**{member.get('email', '')}**")
            linkedin = member.get('linkedin', '#')
            if linkedin != '#':
                st.markdown(f"[LinkedIn 🔗]({linkedin})")
        
        with col_r:
            st.markdown(f"### {member['name']}")
            st.markdown(f"**{member['role']}**")
            
            st.markdown(f"_{member.get('desc', '')}_")
            
            st.markdown("---")
            st.markdown("**Experience:**")
            st.caption(member.get('experience', ''))
            
            st.markdown("**Education:**")
            st.caption(member.get('education', ''))
            
            st.markdown("**Specialization:**")
            st.caption(member.get('specialization', ''))
            
            st.markdown("---")
            st.markdown("**Achievements:**")
            for ach in member.get('achievements', []):
                st.markdown(f"• {ach}")
            
            st.markdown("---")
            quote = member.get('quote', '')
            st.markdown(f"> *\"{quote}\"*")

    # ═════════════════════════════════════════════════
    # DOWNLOAD PDF REPORT
    # ═════════════════════════════════════════════════
    st.markdown(
        '<div class="section-header"><span class="section-icon">📥</span><span class="section-title">Company Profile Report</span></div>',
        unsafe_allow_html=True,
    )
    
    col_rep1, col_rep2 = st.columns([2, 1])
    with col_rep1:
        st.markdown(
            """
        <div class="glass-card">
            <h3>PDF Report for Prospective Clients</h3>
            <p>Download our comprehensive company profile report featuring services, case studies, leadership team, and contact information.</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
    
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
    st.markdown("</div>", unsafe_allow_html=True)
