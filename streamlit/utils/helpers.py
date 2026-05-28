import pandas as pd
import streamlit as st


def format_euro(value):
    """Format Euro values with compact notation."""
    if value is None:
        return "—"
    if abs(value) >= 1e9:
        return f"~€{value / 1e9:.1f}B"
    elif abs(value) >= 1e6:
        return f"~€{value / 1e6:.1f}M"
    elif abs(value) >= 1e3:
        return f"~€{value / 1e3:.1f}K"
    return f"~€{value:,.0f}"


def get_status_color(value, threshold_high, threshold_low):
    if value >= threshold_high:
        return "#10b981"
    elif value >= threshold_low:
        return "#f59e0b"
    return "#ef4444"


def smart_format(value):
    """Smart number formatting: full for small, compact for large.
    < 1000: full number with commas (e.g. 842)
    >= 1000: compact notation (e.g. 1.2K)
    >= 1M: compact with M (e.g. 3.4M)
    >= 1B: compact with B (e.g. 2.1B)

    Accepts numeric values or string-convertible types. Returns str
    representation for dict/list types to avoid TypeError/crashes.
    """
    if value is None:
        return "—"
    if isinstance(value, dict):
        return str({k: smart_format(v) if isinstance(v, (int, float)) else v for k, v in value.items()})
    if isinstance(value, (list, tuple, set)):
        return str([smart_format(v) if isinstance(v, (int, float)) else v for v in value])
    if isinstance(value, (int, float)):
        if abs(value) >= 1e9:
            return f"{value / 1e9:.1f}B"
        if abs(value) >= 1e6:
            return f"{value / 1e6:.1f}M"
        if abs(value) >= 1e3:
            return f"{value / 1e3:.1f}K"
        return f"{value:,.0f}"
    return str(value)


def format_compact(value):
    """Always use compact notation, no tildes."""
    if value is None:
        return "—"
    if abs(value) >= 1e9:
        return f"{value / 1e9:.1f}B"
    if abs(value) >= 1e6:
        return f"{value / 1e6:.1f}M"
    if abs(value) >= 1e3:
        return f"{value / 1e3:.1f}K"
    return f"{value:,.0f}"


def format_full(value):
    """Full number with comma separators.
    Accepts numeric values or string-convertible types. Returns str representation
    for non-numeric types to avoid TypeError."""
    if value is None:
        return "—"
    if isinstance(value, (int, float)):
        return f"{value:,.0f}"
    if isinstance(value, dict):
        return str({k: format_full(v) if isinstance(v, (int, float)) else v for k, v in value.items()})
    return str(value)


def format_score(value):
    return f"{int(round(value))}/10"


def convert_to_csv(df):
    """Convert DataFrame to CSV for download."""
    return df.to_csv(index=False).encode("utf-8")


def show_loading_spinner(text="Loading data..."):
    """Context manager for showing loading state."""
    return st.spinner(text)


def format_breakeven(month):
    """Helper function to format breakeven month display."""
    if pd.notna(month):
        return f"Month {int(month)}"
    return "Not achieved"
