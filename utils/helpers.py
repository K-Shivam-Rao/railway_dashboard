import streamlit as st
import pandas as pd


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
    return f"~{int(round(value))}/10"


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
