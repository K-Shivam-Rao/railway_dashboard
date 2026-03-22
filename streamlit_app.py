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
# CSS — MODERN CLEAN DASHBOARD
# ═══════════════════════════════════════════════════
st.markdown("""
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

        --text-primary: #f1f5f9;
        --text-secondary: #cbd5e1;
        --text-tertiary: #94a3b8;
        --text-muted: #64748b;

        --accent-primary: #3b82f6;
        --accent-secondary: #60a5fa;
        --accent-tertiary: #93c5fd;

        --status-ok: #10b981;
        --status-warning: #f59e0b;
        --status-error: #ef4444;

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
        background: linear-gradient(180deg, rgba(15,23,42,0.95) 0%, rgba(6,12,26,0.98) 100%);
        border: 1px solid rgba(59,130,246,0.15);
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        margin-bottom: 16px;
    }
    .panel-header {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 16px 20px;
        background: linear-gradient(90deg, rgba(59,130,246,0.12) 0%, rgba(6,182,212,0.08) 100%);
        border-bottom: 1px solid rgba(59,130,246,0.15);
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
    # Get current station for status
    current_station_sidebar = st.session_state.current_station
    gates_total, gates_active, p_total, alerts, avg_sync, warnings, _ = get_metrics(df, current_station_sidebar)
    sys_status = "NORMAL" if alerts == 0 and warnings == 0 else ("ALERT" if alerts > 0 else "WARNING")

    # ── Brand Header ──
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
    </div>
    """, unsafe_allow_html=True)

    # ── System Status Indicator (Sidebar) with Icons ──
    sidebar_icons = {
        "NORMAL": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>',
        "WARNING": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
        "ALERT": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>'
    }

    # Subtitle based on status
    status_subtitle = {
        "NORMAL": "All systems operational",
        "WARNING": "Attention required",
        "ALERT": "Immediate attention needed"
    }

    st.markdown(f"""
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
    """, unsafe_allow_html=True)

    st.markdown('<div class="nav-divider"></div>', unsafe_allow_html=True)

    # ── Stations ──
    st.markdown('<div class="section-header-modern"><div class="section-title">Stations</div></div>', unsafe_allow_html=True)

    for s in stations:
        is_active = s == st.session_state.current_station
        if st.button(
            label=s,
            key=f"nav_{s.replace(' ', '_').replace('.', '_')}",
            type="primary" if is_active else "secondary",
            use_container_width=True
        ):
            st.session_state.current_station = s
            st.session_state.active_tab = 'ops'
            st.rerun()

    st.markdown('<div class="nav-divider"></div>', unsafe_allow_html=True)

    # ── Modules ──
    st.markdown('<div class="section-header-modern"><div class="section-title">Modules</div></div>', unsafe_allow_html=True)

    modules = [
        ('ops', '📡 Live Operations'),
        ('network', '🌐 Network Overview'),
        ('incidents', '🚨 Incident Log'),
        ('forecast', '📈 Predictive Analytics'),
        ('financial', '💹 Financial Model'),
        ('company', '🏢 Company & Team'),
    ]
    for key, label in modules:
        is_active = st.session_state.active_tab == key
        if st.button(
            label=label,
            key=f"tab_{key}",
            type="primary" if is_active else "secondary",
            use_container_width=True
        ):
            st.session_state.active_tab = key
            st.rerun()

    st.markdown('<div class="nav-divider"></div>', unsafe_allow_html=True)

    # ── Footer ──
    st.markdown("""
    <div class="sidebar-footer">
        <div style="font-size:0.7rem;color:var(--text-secondary);font-weight:600;margin-bottom:4px;">
            ⚡ BahnSetu GmbH
        </div>
        <div class="footer-version">v2.1.81 | © 2025</div>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════
current_station = st.session_state.current_station
gates_total, gates_active, p_total, alerts, avg_sync, warnings, _ = get_metrics(
    df, current_station)
active_tab = st.session_state.active_tab

sys_status = "NORMAL" if alerts == 0 and warnings == 0 else (
    "ALERT" if alerts > 0 else "WARNING")
badge_cls = f"status-{sys_status.lower()}"

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

# Define status icons (SVG strings without extra whitespace)
status_icons = {
    "NORMAL": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>',
    "WARNING": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
    "ALERT": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>'
}

icon_html = f'<div class="status-icon">{status_icons[sys_status]}<div class="status-icon-ring"></div></div>'

st.markdown(f"""
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
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════
# TRAIN ANIMATION HTML BUILDER - MODERN PREMIUM EDITION
# ════════════════════════════════════════════════════
@st.cache_data(ttl=60, show_spinner=False)
def build_train_animation(station_name, station_df):
    """Build a sophisticated HTML/JS animation with modern visuals and realistic train movement."""
    platforms_data = []
    station_df = station_df.copy()

    grouped = station_df.groupby('platform')

    for platform, plat_df in sorted(grouped, key=lambda x: x[0]):
        gates = []
        train_types_found = []

        for row in plat_df.itertuples(index=False):
            gate_data = {
                "id": row.gate_id,
                "state": row.door_state,
                "train": str(row.train) if pd.notna(row.train) and row.train else "",
                "train_type": str(row.train_type) if 'train_type' in row._fields and pd.notna(row.train_type) else "ICE",
                "operator": str(row.operator) if 'operator' in row._fields and pd.notna(row.operator) else "DB",
                "destination": str(row.destination) if 'destination' in row._fields and pd.notna(row.destination) else "Unknown",
                "temp": float(row.sensor_temp),
                "vib": float(row.sensor_vib),
                "risk": int(row.risk_score) if 'risk_score' in row._fields else 0,
                "status": row.maintenance_status if 'maintenance_status' in row._fields else "OPTIMAL",
                "people": int(row.people),
                "capacity": int(row.capacity) if 'capacity' in row._fields else 400,
                "door_position": str(row.door_position) if 'door_position' in row._fields else "middle",
                "signal_status": str(row.signal_status) if 'signal_status' in row._fields else "green",
                "track_number": int(row.track_number) if 'track_number' in row._fields else 1,
            }
            gates.append(gate_data)
            if gate_data["train"] and gate_data["train_type"] not in train_types_found:
                train_types_found.append(gate_data["train_type"])

        # Determine primary train type for animation
        primary_train_type = train_types_found[0] if train_types_found else "ICE"
        train_name = next((g["train"] for g in gates if g["train"]),
                         f"{primary_train_type} {abs(hash(platform)) % 900 + 100}")

        platforms_data.append({
            "platform": platform,
            "gates": gates,
            "train_name": train_name,
            "train_type": primary_train_type,
        })

    platforms_json = json.dumps(platforms_data)

    # Build the HTML with an embedded JS animation engine - MODERN PREMIUM EDITION
    html = """<!DOCTYPE html>
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
    return html


# ═══════════════════════════════════════════════════
# ── TAB: LIVE OPERATIONS ──────────────────────────
# ═══════════════════════════════════════════════════
if active_tab == 'ops':

    # ── KPI Row ──
    st.markdown('<div class="kpi-strip">', unsafe_allow_html=True)
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
            <div class="kpi-card {cls}">
                <div class="kpi-icon">{('&#9888;' if cls=='alert' else '&#10003;' if cls=='green' else '&#9888;' if cls=='warn' else '&#9679;')}</div>
                <div class="kpi-body">
                    <div class="kpi-label">{title}</div>
                    <div class="kpi-value">{val}</div>
                    <div class="kpi-sub">{sub}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Main Split ──
    left, right = st.columns([65, 35])

    with left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-header">'
                    '<span class="panel-icon">&#128646;</span>'
                    '<span class="panel-title">Live Platform Simulation</span>'
                    '</div>', unsafe_allow_html=True)

        station_data = get_station_data_cached(current_station, df)
        num_platforms = station_data['platform'].nunique()
        anim_html = build_train_animation(current_station, station_data)
        anim_height = num_platforms * 295 + 60
        components.html(anim_html, height=anim_height, scrolling=False)
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-header">'
                    '<span class="panel-icon">&#128202;</span>'
                    '<span class="panel-title">Sensor Analytics</span>'
                    '</div>', unsafe_allow_html=True)

        cycles_df, temp_df = get_psd_analytics_cached(current_station)

        fig_temp = go.Figure()
        fig_temp.add_trace(go.Scatter(
            x=temp_df["Hour"], y=temp_df["Avg Temp (°C)"],
            mode='lines+markers',
            line=dict(color='#ef4444', width=2, shape='spline'),
            marker=dict(size=5, color='#ef4444'),
            fill='tozeroy',
            fillcolor='rgba(239,68,68,0.08)',
            name="Temp (°C)"
        ))
        fig_temp.add_hline(y=45, line_dash="dot", line_color="#f97316",
                           annotation_text="Warning", annotation_font_color="#f97316")
        fig_temp.update_layout(
            height=190,
            margin=dict(l=0, r=0, b=24, t=8),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#94a3b8", family="Inter", size=10),
            yaxis=dict(
                gridcolor='rgba(30,41,59,0.5)',
                zeroline=False,
                tickfont=dict(size=9, color="#94a3b8")
            ),
            xaxis=dict(
                gridcolor='rgba(30,41,59,0.5)',
                tickfont=dict(size=9, color="#94a3b8")
            ),
            showlegend=False,
            hovermode='x unified',
            hoverlabel=dict(
                bgcolor='rgba(17,24,39,0.98)',
                bordercolor='#3b82f6',
                font_color='#f1f5f9',
                font_size=10
            )
        )
        st.markdown('<div class="panel-content">', unsafe_allow_html=True)
        st.plotly_chart(fig_temp, use_container_width=True)

        fig_cycles = px.bar(cycles_df, x="Hour", y="Door Cycles")
        fig_cycles.update_traces(
            marker_color='#3b82f6',
            marker_line_width=0,
            hovertemplate='<b>Hour</b>: %{x}<br><b>Cycles</b>: %{y}<extra></extra>'
        )
        fig_cycles.update_layout(
            height=155,
            margin=dict(l=0, r=0, b=24, t=8),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#94a3b8", family="Inter", size=10),
            yaxis=dict(
                gridcolor='rgba(30,41,59,0.5)',
                zeroline=False,
                tickfont=dict(size=9, color="#94a3b8")
            ),
            xaxis=dict(
                gridcolor='rgba(30,41,59,0.5)',
                tickfont=dict(size=9, color="#94a3b8")
            ),
            showlegend=False,
            hovermode='x unified',
            hoverlabel=dict(
                bgcolor='rgba(17,24,39,0.98)',
                bordercolor='#3b82f6',
                font_color='#f1f5f9',
                font_size=10
            )
        )
        st.plotly_chart(fig_cycles, use_container_width=True)
        st.markdown('</div></div>', unsafe_allow_html=True)

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
    st.markdown('<div class="kpi-strip">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    kpis_net = [
        (c1, "Network Gates", f"{net['total_gates']}", f"Across {len(stations)} Stations", ""),
        (c2, "Optimal Gates", f"{net['optimal_count']}", "Running Normally", "green"),
        (c3, "Network Alerts", f"{net['critical_count']}", "Critical Incidents", "alert"),
        (c4, "Total Passengers", f"{net['total_people']:,}", "On All Platforms", ""),
    ]
    for col, title, val, sub, cls in kpis_net:
        with col:
            st.markdown(f"""
            <div class="kpi-card {cls}">
                <div class="kpi-icon">{('&#128270;' if cls=='' else '&#10003;' if cls=='green' else '&#9888;' if cls=='alert' else '&#9679;')}</div>
                <div class="kpi-body">
                    <div class="kpi-label">{title}</div>
                    <div class="kpi-value">{val}</div>
                    <div class="kpi-sub">{sub}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Main Content Grid ──
    left, right = st.columns([55, 45])

    with left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-header">'
                    '<span class="panel-icon">&#128202;</span>'
                    '<span class="panel-title">Station Performance Matrix</span>'
                    '</div>'
                    '<div class="panel-content">', unsafe_allow_html=True)
        styled_net = (
            net['station_summary']
            .style
            .background_gradient(subset=['Avg Sync %'], cmap='Blues', vmin=0, vmax=100)
            .background_gradient(subset=['Avg Risk'], cmap='RdYlGn_r', vmin=0, vmax=100)
            .format({'Avg Sync %': "{}%", 'Avg Risk': "{:.1f}/100", 'Passengers': "{:,}"})
        )
        st.dataframe(styled_net, use_container_width=True, hide_index=True)
        st.markdown('</div></div>', unsafe_allow_html=True)

        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-header">'
                    '<span class="panel-icon">&#128100;</span>'
                    '<span class="panel-title">Passengers by Station</span>'
                    '</div>'
                    '<div class="panel-content">', unsafe_allow_html=True)
        fig_pass = px.bar(
            net['station_summary'].sort_values('Passengers', ascending=True),
            x='Passengers', y='Station', orientation='h',
            color='Avg Risk',
            color_continuous_scale=['#10b981', '#f59e0b', '#ef4444'],
            range_color=[0, 100],
            title=""
        )
        fig_pass.update_layout(
            height=280,
            margin=dict(l=0, r=0, b=20, t=10),
            paper_bgcolor='rgba(10, 14, 23, 0)',
            plot_bgcolor='rgba(10, 14, 23, 0)',
            font=dict(color="#94a3b8", family="Inter", size=11),
            yaxis=dict(
                gridcolor='rgba(30, 41, 59, 0.3)',
                tickfont=dict(size=10)
            ),
            xaxis=dict(
                gridcolor='rgba(30, 41, 59, 0.3)',
                tickfont=dict(size=10)
            ),
            coloraxis_colorbar=dict(
                title=dict(
                    text="Risk",
                    font=dict(color="#94a3b8", size=10)
                ),
                tickfont=dict(color="#94a3b8", size=9),
                thickness=6,
                len=0.7
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
        st.markdown('</div></div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-header">'
                    '<span class="panel-icon">&#9881;</span>'
                    '<span class="panel-title">Maintenance Status</span>'
                    '</div>'
                    '<div class="panel-content">', unsafe_allow_html=True)
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
            hole=0.5
        )
        fig_pie.update_layout(
            height=180,
            margin=dict(l=5, r=5, b=5, t=5),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#94a3b8", family="Inter", size=9),
            showlegend=True,
            hoverlabel=dict(
                bgcolor='rgba(17, 24, 39, 0.95)',
                bordercolor='#3b82f6',
                font_color='#f1f5f9',
                font_size=10
            )
        )
        fig_pie.update_traces(
            textposition='inside',
            textinfo='percent',
            textfont_size=8,
            textfont_color='#f1f5f9',
            marker_line_color='rgba(30, 41, 59, 0.3)',
            marker_line_width=1,
            hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        st.markdown('</div></div>', unsafe_allow_html=True)

        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-header">'
                    '<span class="panel-icon">&#128642;</span>'
                    '<span class="panel-title">Train Types</span>'
                    '</div>'
                    '<div class="panel-content">', unsafe_allow_html=True)
        if not net['train_type_dist'].empty:
            train_colors = px.colors.qualitative.Set3
            fig_train = px.pie(
                net['train_type_dist'],
                names='train_type',
                values='Count',
                hole=0.5
            )
            fig_train.update_layout(
                height=180,
                margin=dict(l=5, r=5, b=5, t=5),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#94a3b8", family="Inter", size=9),
                showlegend=True,
                hoverlabel=dict(
                    bgcolor='rgba(17, 24, 39, 0.95)',
                    bordercolor='#3b82f6',
                    font_color='#f1f5f9',
                    font_size=10
                )
            )
            fig_train.update_traces(
                textposition='inside',
                textinfo='percent',
                textfont_size=8,
                textfont_color='#f1f5f9',
                marker_line_color='rgba(30, 41, 59, 0.3)',
                marker_line_width=1,
                hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
            )
            st.plotly_chart(fig_train, use_container_width=True)
        else:
            st.markdown('<div style="text-align: center; color: #64748b; font-size: 0.8rem; padding: 20px;">No train type data available</div>', unsafe_allow_html=True)
        st.markdown('</div></div>', unsafe_allow_html=True)

        # Door State Distribution
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-header">'
                    '<span class="panel-icon">&#128682;</span>'
                    '<span class="panel-title">Door State Distribution</span>'
                    '</div>'
                    '<div class="panel-content">', unsafe_allow_html=True)
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
            height=200,
            margin=dict(l=0, r=0, b=30, t=10),
            paper_bgcolor='rgba(10, 14, 23, 0)',
            plot_bgcolor='rgba(10, 14, 23, 0)',
            font=dict(color="#64748b", family="Inter", size=10),
            yaxis=dict(
                gridcolor='rgba(30, 41, 59, 0.4)',
                tickfont=dict(size=9, color="#94a3b8"),
                title=''
            ),
            xaxis=dict(
                gridcolor='rgba(30, 41, 59, 0.4)',
                tickfont=dict(size=9, color="#94a3b8"),
                title='',
                categoryorder='array',
                categoryarray=['closed', 'open', 'closing', 'jammed']
            ),
            showlegend=True,
            hovermode='x unified',
            hoverlabel=dict(
                bgcolor='rgba(17, 24, 39, 0.95)',
                bordercolor='#3b82f6',
                font_color='#f1f5f9',
                font_size=10
            )
        )
        fig_door.update_traces(
            hovertemplate='<b>State</b>: %{x}<br><b>Count</b>: %{y}<extra></extra>'
        )
        st.plotly_chart(fig_door, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Operator Performance
        if not net['operator_stats'].empty:
            st.markdown(
                '<div class="section-heading">Operator Performance</div>', unsafe_allow_html=True)

            # Use styled dataframe for better rendering compatibility
            op_display = net['operator_stats'].copy()
            op_display = op_display.rename(columns={'Avg Sync %': 'Sync %', 'Avg Risk': 'Risk'})

            def style_sync(val):
                if val >= 85: return 'color: #10b981; font-weight: 600;'
                elif val >= 70: return 'color: #f59e0b; font-weight: 600;'
                else: return 'color: #ef4444; font-weight: 600;'

            def style_risk(val):
                if val <= 20: return 'color: #10b981; font-weight: 600;'
                elif val <= 40: return 'color: #f59e0b; font-weight: 600;'
                else: return 'color: #ef4444; font-weight: 600;'

            styled_op = (op_display.style
                        .format({'Sync %': '{:.1f}%', 'Risk': '{:.1f}'})
                        .map(style_sync, subset=['Sync %'])
                        .map(style_risk, subset=['Risk']))
            st.dataframe(styled_op, use_container_width=True, hide_index=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Network Health Metrics
        st.markdown(
            '<div class="section-heading">Network Health</div>', unsafe_allow_html=True)
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.markdown(f'<div style="background: rgba(26, 35, 50, 0.4); border-radius: 8px; padding: 12px; text-align: center; border: 1px solid rgba(148, 163, 184, 0.1);"><div style="font-size: 0.7rem; color: #94a3b8; margin-bottom: 4px;">Sync Score</div><div style="font-size: 1.2rem; font-weight: 700; color: #3b82f6;">{net["network_sync"]}%</div></div>', unsafe_allow_html=True)
        with col_b:
            st.markdown(f'<div style="background: rgba(26, 35, 50, 0.4); border-radius: 8px; padding: 12px; text-align: center; border: 1px solid rgba(148, 163, 184, 0.1);"><div style="font-size: 0.7rem; color: #94a3b8; margin-bottom: 4px;">Avg Risk</div><div style="font-size: 1.2rem; font-weight: 700; color: #f59e0b;">{net["network_risk"]}/100</div></div>', unsafe_allow_html=True)
        with col_c:
            health_color = '#10b981' if net['network_health'] >= 80 else '#f59e0b' if net['network_health'] >= 60 else '#ef4444'
            st.markdown(f'<div style="background: rgba(26, 35, 50, 0.4); border-radius: 8px; padding: 12px; text-align: center; border: 1px solid rgba(148, 163, 184, 0.1);"><div style="font-size: 0.7rem; color: #94a3b8; margin-bottom: 4px;">Health Score</div><div style="font-size: 1.2rem; font-weight: 700; color: {health_color};">{net["network_health"]}</div></div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════
# ── TAB: INCIDENT LOG ─────────────────────────────
# ═══════════════════════════════════════════════════
elif active_tab == 'incidents':
    incidents = get_incident_log_cached(df)

    if incidents.empty:
        st.markdown('<div class="panel">'
                    '<div class="panel-header">'
                    '<span class="panel-icon">&#10003;</span>'
                    '<span class="panel-title">Active Incidents — All Stations</span>'
                    '</div>'
                    '<div class="panel-content" style="text-align:center;padding:40px;color:#64748b;">'
                    '✓ No active incidents. All systems operating normally.'
                    '</div></div>', unsafe_allow_html=True)
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
                st.markdown(f"""
                <div class="kpi-card {cls}">
                    <div class="kpi-icon">{('&#9888;' if cls=='alert' else '&#9888;' if cls=='warn' else '&#9679;')}</div>
                    <div class="kpi-body">
                        <div class="kpi-label">{title}</div>
                        <div class="kpi-value">{val}</div>
                        <div class="kpi-sub">{sub}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-header">'
                    '<span class="panel-icon">&#128680;</span>'
                    '<span class="panel-title">Incident List</span>'
                    '</div>'
                    '<div class="panel-content">', unsafe_allow_html=True)
        
        for _, row in incidents.iterrows():
            cls = "critical" if "CRITICAL" in row["Severity"] else "warning"
            border_col = "#ef4444" if cls == "critical" else "#f59e0b"
            st.markdown(f"""
            <div class="incident-row {cls}" style="border-left-color:{border_col};">
                <div style="font-family:'JetBrains Mono'; font-size:0.75rem; color:#64748b; min-width:50px;">{row['Time']}</div>
                <div style="min-width:70px;font-weight:600;color:{'#ef4444' if 'CRITICAL' in row['Severity'] else '#f59e0b'};">{row['Severity']}</div>
                <div style="font-size:0.78rem; color:#94a3b8; min-width:100px;">{row['Station'][:14]}…</div>
                <div style="font-size:0.78rem; color:#e2e8f0; flex:1;">{row['Description']}</div>
                <div style="font-family:'JetBrains Mono'; font-size:0.72rem; color:#64748b;">
                    {row['Temp (°C)']}°C | {row['Vibration']} mm/s
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div></div>', unsafe_allow_html=True)

        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-header">'
                    '<span class="panel-icon">&#128202;</span>'
                    '<span class="panel-title">Incident Detail Table</span>'
                    '</div>'
                    '<div class="panel-content">', unsafe_allow_html=True)
        st.dataframe(incidents, use_container_width=True, hide_index=True)
        st.markdown('</div></div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════
# ── TAB: PREDICTIVE ANALYTICS ─────────────────────
# ═══════════════════════════════════════════════════
elif active_tab == 'forecast':
    forecast_df = get_maintenance_forecast_cached(current_station)

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-header">'
                '<span class="panel-icon">&#128200;</span>'
                '<span class="panel-title">Predictive Analytics — ' + current_station + '</span>'
                '</div>'
                '<div class="panel-content">', unsafe_allow_html=True)

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
        height=300, margin=dict(l=0, r=0, b=50, t=30),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#64748b", family="Inter", size=11),
        yaxis=dict(
            gridcolor='rgba(30, 41, 59, 0.6)',
            range=[0, 100],
            title=dict(text='Risk %', font=dict(size=12, color="#94a3b8")),
            tickfont=dict(size=10, color="#94a3b8"),
        ),
        xaxis=dict(
            gridcolor='rgba(30, 41, 59, 0.6)',
            tickfont=dict(size=10, color="#94a3b8")
        ),
        showlegend=True,
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

    col_heat, col_sync = st.columns([2, 1])

    with col_heat:
        st.markdown('<div style="font-size:0.9rem;font-weight:600;color:#94a3b8;margin:20px 0 10px 0;">Weekly Passenger Flow Heatmap</div>', unsafe_allow_html=True)
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
                title=dict(text='Hour of Day', font=dict(size=12, color="#94a3b8")),
            ),
            yaxis=dict(
                tickfont=dict(size=10, color="#94a3b8"),
                title=dict(text='Day of Week', font=dict(size=12, color="#94a3b8")),
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
        coloraxis_colorbar=dict(
            title=dict(
                text="Risk",
                font=dict(color="#94a3b8", size=10)
            ),
            tickfont=dict(color="#94a3b8", size=9),
            thickness=6,
            len=0.7
        ),
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
    st.markdown('</div></div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════
# ── TAB: COMPANY & TEAM ───────────────────────────
# ═══════════════════════════════════════════════════
elif active_tab == 'financial':
    from data_source import get_financial_model_data

    PLOTLY_DARK = dict(
        plot_bgcolor='rgba(10, 14, 23, 0)',
        paper_bgcolor='rgba(10, 14, 23, 0)',
        font=dict(color='#94a3b8', family='Inter', size=11),
        xaxis=dict(
            gridcolor='rgba(148, 163, 184, 0.1)',
            zeroline=False,
            tickfont=dict(size=10, color='#94a3b8')
        ),
        yaxis=dict(
            gridcolor='rgba(148, 163, 184, 0.1)',
            zeroline=False,
            tickfont=dict(size=10, color='#94a3b8')
        ),
        legend=dict(
            bgcolor='rgba(26, 35, 50, 0.8)',
            bordercolor='rgba(148, 163, 184, 0.1)',
            borderwidth=1,
            font=dict(size=10, color='#94a3b8'),
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        margin=dict(l=40, r=20, t=80, b=60),
        hovermode='x unified',
        hoverlabel=dict(
            bgcolor='rgba(26, 35, 50, 0.95)',
            bordercolor='rgba(59, 130, 246, 0.3)',
            font_color='#f1f5f9',
            font_size=11
        ),
        title_font=dict(size=14, color='#f1f5f9', family='Inter'),
        title_x=0,
        title_y=0.95,
        title_pad=dict(t=10, b=10)
    )

    def fin_fig(layout_extra=None):
        d = dict(**PLOTLY_DARK)
        if layout_extra:
            d.update(layout_extra)
        return d

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-header">'
                '<span class="panel-icon">&#9881;</span>'
                '<span class="panel-title">Financial Model</span>'
                '</div>'
                '<div class="panel-content">', unsafe_allow_html=True)
    
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
    st.markdown('</div></div>', unsafe_allow_html=True)

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

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-header">'
                '<span class="panel-icon">&#127970;</span>'
                '<span class="panel-title">Company & Team</span>'
                '</div>'
                '<div class="panel-content">', unsafe_allow_html=True)

    st.markdown('<div class="section-heading" style="font-size:1.2rem;margin:0 0 16px 0;">About SicherGleis GmbH</div>', unsafe_allow_html=True)
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

    st.markdown('<div class="section-heading" style="font-size:1.2rem;margin:24px 0 16px 0;">Leadership Team</div>', unsafe_allow_html=True)
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
    st.markdown('</div></div>', unsafe_allow_html=True)
