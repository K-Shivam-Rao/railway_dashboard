import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from pathlib import Path
import sys
import subprocess
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.dashboard.parsers import run_pytest_json, parse_coverage_data, get_test_files_summary, get_coverage_report

# ============================================================
# DESIGN SYSTEM - Dark Theme
# ============================================================
COLORS = {
    "primary": "#6366f1",
    "primary_light": "#818cf8",
    "secondary": "#8b5cf6",
    "success": "#10b981",
    "warning": "#f59e0b",
    "error": "#ef4444",
    "info": "#3b82f6",
    "bg_dark": "#0f172a",
    "bg_card": "#1e293b",
    "bg_surface": "#334155",
    "text_primary": "#f8fafc",
    "text_secondary": "#94a3b8",
    "text_muted": "#64748b",
    "border": "#475569",
}

st.set_page_config(page_title="TestVision Pro", page_icon="🚂", layout="wide", initial_sidebar_state="expanded")

# ============================================================
# STYLED COMPONENTS
# ============================================================
def metric_card(value, label, color="primary", icon=""):
    color_map = {
        "primary": COLORS["primary"], "success": COLORS["success"],
        "warning": COLORS["warning"], "error": COLORS["error"], "info": COLORS["info"],
    }
    accent = color_map.get(color, COLORS["primary"])
    st.markdown(f"""
    <div style="background: {COLORS['bg_card']}; border: 1px solid {COLORS['border']}; border-left: 4px solid {accent}; border-radius: 12px; padding: 1.25rem;">
        <div style="font-size: 2rem; font-weight: 700; color: {COLORS['text_primary']}; line-height: 1.2;">{icon} {value}</div>
        <div style="font-size: 0.75rem; font-weight: 600; color: {COLORS['text_secondary']}; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.5rem;">{label}</div>
    </div>
    """, unsafe_allow_html=True)

def section_header(title):
    st.markdown(f"""
    <div style="margin: 1.5rem 0 1rem 0; padding-bottom: 0.75rem; border-bottom: 1px solid {COLORS['border']};">
        <h2 style="margin: 0; font-size: 1.25rem; font-weight: 600; color: {COLORS['text_primary']};">{title}</h2>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# CUSTOM CSS
# ============================================================
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    * {{ font-family: 'Inter', sans-serif; }}
    .stApp {{ background: {COLORS['bg_dark']}; color: {COLORS['text_primary']}; }}
    .main-header {{ background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%); padding: 2rem; border-radius: 16px; margin-bottom: 1.5rem; box-shadow: 0 8px 32px rgba(99, 102, 241, 0.3); }}
    .main-header h1 {{ color: white; font-size: 2rem; font-weight: 700; margin: 0; }}
    .main-header p {{ color: rgba(255,255,255,0.85); font-size: 1rem; margin-top: 0.5rem; }}
    section[data-testid="stSidebar"] {{ background: {COLORS['bg_card']}; border-right: 1px solid {COLORS['border']}; }}
    .stTabs [data-baseweb="tab-list"] {{ gap: 8px; background: {COLORS['bg_card']}; padding: 8px; border-radius: 12px; }}
    .stTabs [data-baseweb="tab"] {{ height: 44px; padding: 0 20px; background: {COLORS['bg_surface']}; border-radius: 8px; font-weight: 500; color: {COLORS['text_secondary']}; border: none; }}
    .stTabs [aria-selected="true"] {{ background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%) !important; color: white !important; }}
    .stButton > button {{ background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%); color: white; border: none; border-radius: 8px; font-weight: 600; padding: 0.6rem 1.5rem; }}
    .stButton > button:hover {{ transform: translateY(-1px); box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4); }}
    [data-testid="stMetricValue"] {{ font-size: 1.75rem; font-weight: 700; }}
    [data-testid="stMetricLabel"] {{ font-size: 0.8rem; color: {COLORS['text_secondary']}; }}
    [data-testid="stDataFrame"] {{ border: 1px solid {COLORS['border']}; border-radius: 12px; }}
    .stProgress > div > div > div {{ background: {COLORS['primary']}; }}
    .stAlert {{ background: {COLORS['bg_card']}; border: 1px solid {COLORS['border']}; border-radius: 8px; }}
    hr {{ border-color: {COLORS['border']}; }}
    footer {{ text-align: center; padding: 2rem; color: {COLORS['text_muted']}; font-size: 0.85rem; border-top: 1px solid {COLORS['border']}; margin-top: 2rem; }}
</style>
""", unsafe_allow_html=True)

# ============================================================
# HEADER
# ============================================================
st.markdown(f"""
<div class="main-header">
    <h1>TestVision Pro</h1>
    <p>Beautiful test analytics for Railway Dashboard</p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("### Controls")
    if st.button("Run Tests", type="primary", use_container_width=True):
        with st.spinner("Running tests..."):
            run_pytest_json()
            st.success("Done!")
            st.rerun()
    st.markdown("---")
    
    json_file = Path(__file__).parent.parent.parent / "tests" / "dashboard" / "pytest_results.json"
    if json_file.exists():
        with open(json_file) as f:
            data = json.load(f)
            summary = data.get("summary", {})
            total = summary.get("total", 0)
            passed = summary.get("passed", 0)
            failed = summary.get("failed", 0)
            pass_rate = (passed / total * 100) if total > 0 else 0
            st.metric("Total Tests", total)
            st.metric("Passed", passed)
            st.metric("Failed", failed)
            st.progress(pass_rate / 100)
            st.markdown(f'<p style="text-align: center; font-size: 1.5rem; font-weight: 700; color: {COLORS["success"] if pass_rate >= 80 else COLORS["warning"]}">{pass_rate:.1f}%</p>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("**About**")
    st.caption("TestVision Pro v1.0\nBeautiful test insights")

# ============================================================
# MAIN TABS
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Test Results", "Coverage", "Performance"])

# ----------------------------------------------------------
# TAB 1: OVERVIEW
# ----------------------------------------------------------
with tab1:
    section_header("Test Overview")
    
    json_file = Path(__file__).parent.parent.parent / "tests" / "dashboard" / "pytest_results.json"
    if json_file.exists():
        with open(json_file) as f:
            data = json.load(f)
            summary = data.get("summary", {})
            total = summary.get("total", 0)
            passed = summary.get("passed", 0)
            failed = summary.get("failed", 0)
            skipped = summary.get("skipped", 0)
            pass_rate = (passed / total * 100) if total > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            with col1: metric_card(passed, "Passed", "success")
            with col2: metric_card(failed, "Failed", "error")
            with col3: metric_card(skipped, "Skipped", "warning")
            with col4: metric_card(f"{pass_rate:.1f}%", "Pass Rate", "primary")
            
            st.markdown("---")
            
            # Two main charts
            col1, col2 = st.columns(2)
            
            with col1:
                section_header("Pass Rate")
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number", value=pass_rate, domain={"x": [0, 1], "y": [0, 1]},
                    gauge={
                        "axis": {"range": [0, 100], "tickcolor": COLORS["text_muted"]},
                        "bar": {"color": COLORS["primary"]},
                        "bgcolor": COLORS["bg_surface"], "borderwidth": 0,
                        "steps": [
                            {"range": [0, 60], "color": COLORS["error"]},
                            {"range": [60, 80], "color": COLORS["warning"]},
                            {"range": [80, 100], "color": COLORS["success"]},
                        ],
                    }
                ))
                fig_gauge.update_layout(height=250, font={"color": COLORS["text_secondary"]}, paper_bgcolor="rgba(0,0,0,0)", margin={"l": 20, "r": 20, "t": 20, "b": 20})
                st.plotly_chart(fig_gauge, use_container_width=True)
            
            with col2:
                section_header("Distribution")
                fig_pie = go.Figure(data=[go.Pie(
                    labels=["Passed", "Failed", "Skipped"],
                    values=[passed, failed, skipped],
                    hole=0.5,
                    marker={"colors": [COLORS["success"], COLORS["error"], COLORS["warning"]], "line": {"color": COLORS["bg_card"], "width": 2}},
                    textinfo="label+percent", textfont={"size": 13},
                )])
                fig_pie.update_layout(height=250, showlegend=True, legend={"orientation": "h", "y": -0.1}, font={"color": COLORS["text_secondary"]}, paper_bgcolor="rgba(0,0,0,0)", margin={"l": 20, "r": 20, "t": 20, "b": 40})
                st.plotly_chart(fig_pie, use_container_width=True)
            
            st.markdown("---")
            
            # NEW: Tests by Module bar chart
            section_header("Tests by Module")
            test_results = []
            for test in data.get("tests", []):
                test_results.append({
                    "Module": test.get("nodeid", "").split("::")[0].replace("tests/", "").replace("test_", "").replace(".py", ""),
                    "Status": test.get("outcome", "unknown"),
                })
            
            df_mod = pd.DataFrame(test_results)
            if not df_mod.empty:
                mod_summary = df_mod.groupby(["Module", "Status"]).size().unstack(fill_value=0).reset_index()
                
                fig_mod = go.Figure()
                for status in ["passed", "failed", "skipped"]:
                    if status in mod_summary.columns:
                        color = {"passed": COLORS["success"], "failed": COLORS["error"], "skipped": COLORS["warning"]}[status]
                        fig_mod.add_trace(go.Bar(x=mod_summary["Module"], y=mod_summary[status], name=status.title(), marker_color=color))
                
                fig_mod.update_layout(barmode="group", font={"color": COLORS["text_secondary"]}, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=350, legend={"orientation": "h", "y": 1.1}, margin={"l": 20, "r": 20, "t": 40, "b": 20})
                st.plotly_chart(fig_mod, use_container_width=True)
            
            st.markdown("---")
            
            # Coverage section
            section_header("Coverage Overview")
            coverage_data = parse_coverage_data()
            if "error" not in coverage_data:
                cov_percent = coverage_data.get("percent", 0)
                covered = coverage_data.get("covered", 0)
                total_lines = coverage_data.get("total", 0)
                
                col1, col2, col3 = st.columns(3)
                with col1: metric_card(f"{covered:,}", "Lines Covered", "success")
                with col2: metric_card(f"{total_lines:,}", "Total Lines", "info")
                with col3: metric_card(f"{cov_percent:.1f}%", "Coverage", "primary")
                
                fig_cov = go.Figure(go.Indicator(
                    mode="gauge+number", value=cov_percent, domain={"x": [0, 1], "y": [0, 1]},
                    title={"text": "Code Coverage", "font": {"size": 16}},
                    gauge={
                        "axis": {"range": [0, 100]},
                        "bar": {"color": COLORS["success"]},
                        "bgcolor": COLORS["bg_surface"], "borderwidth": 0,
                        "steps": [
                            {"range": [0, 60], "color": COLORS["error"]},
                            {"range": [60, 80], "color": COLORS["warning"]},
                            {"range": [80, 100], "color": COLORS["success"]},
                        ],
                    }
                ))
                fig_cov.update_layout(height=280, font={"color": COLORS["text_secondary"]}, paper_bgcolor="rgba(0,0,0,0)", margin={"l": 20, "r": 20, "t": 40, "b": 20})
                st.plotly_chart(fig_cov, use_container_width=True)
            else:
                st.warning("No coverage data. Run: python -m pytest --cov --cov-report=json")

# ----------------------------------------------------------
# TAB 2: TEST RESULTS
# ----------------------------------------------------------
with tab2:
    section_header("Test Results")
    
    json_file = Path(__file__).parent.parent.parent / "tests" / "dashboard" / "pytest_results.json"
    if json_file.exists():
        with open(json_file) as f:
            data = json.load(f)
            
            if "tests" in data:
                test_results = []
                for test in data["tests"]:
                    test_results.append({
                        "Test": test.get("nodeid", "").split("::")[-1],
                        "Module": test.get("nodeid", "").split("::")[0].replace("tests/", ""),
                        "Status": test.get("outcome", "unknown"),
                        "Duration (s)": round(test.get("call", {}).get("duration", 0), 4) if "call" in test else 0,
                    })
                
                df = pd.DataFrame(test_results)
                
                # Filters
                col1, col2 = st.columns(2)
                with col1:
                    statuses = df["Status"].unique().tolist()
                    selected_status = st.multiselect("Status", statuses, default=statuses)
                with col2:
                    files = df["Module"].unique().tolist()
                    selected_files = st.multiselect("Module", files, default=files)
                
                filtered_df = df[df["Status"].isin(selected_status) & df["Module"].isin(selected_files)]
                
                # Summary metrics
                col1, col2, col3 = st.columns(3)
                with col1: st.metric("Tests", len(filtered_df))
                with col2: st.metric("Avg Duration", f"{filtered_df['Duration (s)'].mean():.4f}s")
                with col3:
                    pr = (filtered_df[filtered_df['Status']=='passed'].shape[0] / len(filtered_df) * 100) if len(filtered_df) > 0 else 0
                    st.metric("Pass Rate", f"{pr:.1f}%")
                
                # NEW: Module distribution pie
                col1, col2 = st.columns(2)
                
                with col1:
                    section_header("Tests by Module")
                    mod_counts = filtered_df["Module"].value_counts()
                    fig_mod_pie = go.Figure(data=[go.Pie(
                        labels=mod_counts.index, values=mod_counts.values, hole=0.4,
                        marker={"colors": [COLORS["primary"], COLORS["secondary"], COLORS["info"], COLORS["success"], COLORS["warning"], COLORS["error"]]},
                    )])
                    fig_mod_pie.update_layout(height=300, font={"color": COLORS["text_secondary"]}, paper_bgcolor="rgba(0,0,0,0)", margin={"l": 20, "r": 20, "t": 20, "b": 20})
                    st.plotly_chart(fig_mod_pie, use_container_width=True)
                
                with col2:
                    section_header("Status Summary")
                    status_counts = filtered_df["Status"].value_counts()
                    fig_status = go.Figure(data=[go.Bar(
                        x=status_counts.index, y=status_counts.values,
                        marker_color=[COLORS["success"], COLORS["error"], COLORS["warning"]][:len(status_counts)],
                    )])
                    fig_status.update_layout(height=300, font={"color": COLORS["text_secondary"]}, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig_status, use_container_width=True)
                
                st.markdown("---")
                
                # Data table
                section_header("All Tests")
                def style_status(val):
                    if val == "passed": return f"color: {COLORS['success']}; font-weight: 600"
                    elif val == "failed": return f"color: {COLORS['error']}; font-weight: 600"
                    elif val == "skipped": return f"color: {COLORS['warning']}; font-weight: 600"
                    return ""
                
                st.dataframe(
                    filtered_df.style.map(style_status, subset=["Status"]),
                    use_container_width=True, height=400,
                    column_config={
                        "Test": st.column_config.TextColumn("Test", width="large"),
                        "Module": st.column_config.TextColumn("Module", width="medium"),
                        "Status": st.column_config.TextColumn("Status", width="small"),
                        "Duration (s)": st.column_config.NumberColumn("Duration", format="%.4fs"),
                    }
                )
                
                if st.button("Export CSV"):
                    csv = filtered_df.to_csv(index=False)
                    st.download_button("Download", csv, "test_results.csv", "text/csv")

# ----------------------------------------------------------
# TAB 3: COVERAGE
# ----------------------------------------------------------
with tab3:
    section_header("Coverage Analysis")
    
    coverage_data = parse_coverage_data()
    if "error" not in coverage_data:
        cov_percent = coverage_data.get("percent", 0)
        covered = coverage_data.get("covered", 0)
        total_lines = coverage_data.get("total", 0)
        
        col1, col2, col3 = st.columns(3)
        with col1: metric_card(f"{covered:,}", "Covered", "success")
        with col2: metric_card(f"{total_lines:,}", "Total", "info")
        with col3: metric_card(f"{cov_percent:.1f}%", "Coverage", "primary")
        
        st.markdown("---")
        
        # Module breakdown charts
        section_header("By Module")
        
        coverage_report = get_coverage_report()
        if coverage_report and "error" not in coverage_report:
            modules = []
            for module, stats in coverage_report.items():
                total = stats.get("total", 1)
                executed = stats.get("executed", 0)
                pct = (executed / total * 100) if total > 0 else 0
                modules.append({
                    "Module": module, "Covered": executed,
                    "Missing": stats.get("missing", 0), "Total": total, "Coverage %": pct,
                })
            
            df_mod = pd.DataFrame(modules)
            
            # Stacked bar chart
            col1, col2 = st.columns(2)
            
            with col1:
                section_header("Lines by Module")
                fig_bar = go.Figure()
                fig_bar.add_trace(go.Bar(x=df_mod["Module"], y=df_mod["Covered"], name="Covered", marker_color=COLORS["success"]))
                fig_bar.add_trace(go.Bar(x=df_mod["Module"], y=df_mod["Missing"], name="Missing", marker_color=COLORS["error"]))
                fig_bar.update_layout(barmode="stack", font={"color": COLORS["text_secondary"]}, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=350, legend={"orientation": "h", "y": 1.1})
                st.plotly_chart(fig_bar, use_container_width=True)
            
            with col2:
                section_header("Coverage %")
                fig_hbar = px.bar(df_mod, y="Module", x="Coverage %", orientation="h",
                                  color="Coverage %",
                                  color_continuous_scale=["#ef4444", "#f59e0b", "#10b981"],
                                  range_x=[0, 100])
                fig_hbar.update_layout(height=350, font={"color": COLORS["text_secondary"]}, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_hbar, use_container_width=True)
            
            st.markdown("---")
            
            # Table with style
            section_header("Detailed Coverage")
            def style_cov(val):
                if isinstance(val, (int, float)):
                    if val >= 80: return f"color: {COLORS['success']}"
                    elif val >= 60: return f"color: {COLORS['warning']}"
                    else: return f"color: {COLORS['error']}"
                return ""
            
            st.dataframe(
                df_mod.style.map(style_cov, subset=["Coverage %"]),
                use_container_width=True,
                column_config={
                    "Module": st.column_config.TextColumn(),
                    "Covered": st.column_config.NumberColumn(),
                    "Missing": st.column_config.NumberColumn(),
                    "Coverage %": st.column_config.NumberColumn(format="%.1f%%"),
                }
            )
            
            # NEW: Coverage treemap
            section_header("Coverage Treemap")
            fig_tree = px.treemap(df_mod, path=["Module"], values="Total",
                                  color="Coverage %",
                                  color_continuous_scale=["#ef4444", "#f59e0b", "#10b981"])
            fig_tree.update_layout(height=300, font={"color": COLORS["text_secondary"]}, paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_tree, use_container_width=True)
    else:
        st.warning("No coverage data. Run: python -m pytest --cov --cov-report=json")

# ----------------------------------------------------------
# TAB 4: PERFORMANCE
# ----------------------------------------------------------
with tab4:
    section_header("Performance Analytics")
    
    json_file = Path(__file__).parent.parent.parent / "tests" / "dashboard" / "pytest_results.json"
    if json_file.exists():
        with open(json_file) as f:
            data = json.load(f)
            
            if "tests" in data:
                perf_data = []
                for test in data["tests"]:
                    if "call" in test:
                        perf_data.append({
                            "Test": test.get("nodeid", "").split("::")[-1],
                            "Duration (s)": test["call"]["duration"],
                            "Status": test.get("outcome", "unknown"),
                        })
                
                if perf_data:
                    df_perf = pd.DataFrame(perf_data).sort_values("Duration (s)", ascending=False)
                    
                    # Stats
                    col1, col2, col3, col4 = st.columns(4)
                    with col1: st.metric("Mean", f"{df_perf['Duration (s)'].mean():.4f}s")
                    with col2: st.metric("Median", f"{df_perf['Duration (s)'].median():.4f}s")
                    with col3: st.metric("Max", f"{df_perf['Duration (s)'].max():.4f}s")
                    with col4: st.metric("Min", f"{df_perf['Duration (s)'].min():.4f}s")
                    
                    st.markdown("---")
                    
                    # Performance charts
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        section_header("Duration Distribution")
                        fig_hist = px.histogram(df_perf, x="Duration (s)", nbins=30, color_discrete_sequence=[COLORS["primary"]])
                        fig_hist.update_layout(height=350, font={"color": COLORS["text_secondary"]}, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                        st.plotly_chart(fig_hist, use_container_width=True)
                    
                    with col2:
                        section_header("Slowest Tests")
                        fig_slow = px.bar(df_perf.head(15), x="Duration (s)", y="Test", color="Status",
                                          orientation="h",
                                          color_discrete_map={"passed": COLORS["success"], "failed": COLORS["error"], "skipped": COLORS["warning"]})
                        fig_slow.update_layout(height=350, font={"color": COLORS["text_secondary"]}, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", yaxis={"categoryorder": "total ascending"})
                        st.plotly_chart(fig_slow, use_container_width=True)
                    
                    st.markdown("---")
                    
                    # NEW: Box plot and fastest tests
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        section_header("Duration Box Plot")
                        fig_box = px.box(df_perf, y="Duration (s)", color="Status",
                                         color_discrete_map={"passed": COLORS["success"], "failed": COLORS["error"], "skipped": COLORS["warning"]})
                        fig_box.update_layout(height=300, font={"color": COLORS["text_secondary"]}, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                        st.plotly_chart(fig_box, use_container_width=True)
                    
                    with col2:
                        section_header("Fastest Tests")
                        df_fast = df_perf.sort_values("Duration (s)").head(15)
                        fig_fast = px.bar(df_fast, x="Duration (s)", y="Test", orientation="h", color_discrete_sequence=[COLORS["success"]])
                        fig_fast.update_layout(height=300, font={"color": COLORS["text_secondary"]}, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", yaxis={"categoryorder": "total ascending"})
                        st.plotly_chart(fig_fast, use_container_width=True)

# ============================================================
# FOOTER
# ============================================================
st.markdown(f"""
<footer>
    <p>TestVision Pro | Railway Dashboard</p>
    <p style="color: {COLORS['text_muted']}">Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
</footer>
""", unsafe_allow_html=True)