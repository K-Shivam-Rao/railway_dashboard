"""TestVision Dashboard — comprehensive test analytics with 16 chart types.

Run:
    streamlit run streamlit/tests/dashboard/main.py
"""
from __future__ import annotations

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TestVision Dashboard",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Helpers ───────────────────────────────────────────────────────────────────


def lighten_hex(hex_color: str, amount: float = 0.3) -> str:
    """Lighten a hex colour by *amount* (0 = unchanged, 1 = white)."""
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    r = min(255, int(r + (255 - r) * amount))
    g = min(255, int(g + (255 - g) * amount))
    b = min(255, int(b + (255 - b) * amount))
    return f"#{r:02x}{g:02x}{b:02x}"


# ── Data loading ──────────────────────────────────────────────────────────────


@st.cache_data(ttl=60)
def load_test_data() -> dict:
    """Load pytest JSON results, falling back to synthetic data."""
    json_paths = [
        Path("pytest_results.json"),
        Path("tests/dashboard/pytest_results.json"),
        Path(__file__).parent / "pytest_results.json",
    ]
    for p in json_paths:
        if p.exists() and p.stat().st_size > 10:
            try:
                raw = json.loads(p.read_text())
                return _parse_pytest_json(raw)
            except Exception:
                continue
    return _generate_sample_data()


def _parse_pytest_json(raw: dict) -> dict:
    """Parse a pytest-json-report payload into our internal format."""
    tests = []
    for report in raw.get("tests", []):
        duration = report.get("call", {}).get("duration", 0) or 0
        tests.append(
            {
                "nodeid": report.get("nodeid", ""),
                "status": report.get("outcome", "passed"),
                "duration": duration,
                "module": _extract_module(report.get("nodeid", "")),
            }
        )

    summary = raw.get("summary", {})
    passed = summary.get("passed", 0) or 0
    failed = summary.get("failed", 0) or 0
    skipped = summary.get("skipped", 0) or 0
    error = summary.get("error", 0) or 0
    total = passed + failed + skipped + error

    return {
        "tests": tests,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "error": error,
            "pass_rate": round(passed / total * 100, 1) if total else 0,
            "duration": round(sum(t["duration"] for t in tests), 3),
        },
    }


def _extract_module(nodeid: str) -> str:
    """Extract the top-level module name from a nodeid."""
    parts = nodeid.split("::")[0].replace("\\", "/").split("/")
    return parts[0] if parts else "unknown"


def _generate_sample_data() -> dict:
    """Generate rich synthetic test data for visualisation."""
    random.seed(42)

    modules = [
        "core/logic",
        "data/loader",
        "data/sample_data",
        "utils/helpers",
        "reports/pdf_gen",
        "tests/integration",
        "tests/edge_cases",
        "tests/simulation",
    ]
    test_names = [
        "test_pass_rate", "test_anomaly_detection", "test_metrics",
        "test_budget_calc", "test_customer_seg", "test_rfm_analysis",
        "test_contract_health", "test_renewal_forecast", "test_simulation_run",
        "test_data_load", "test_network_summary", "test_incident_log",
        "test_station_ops", "test_predictive_maintenance", "test_pdf_generation",
        "test_edge_empty", "test_edge_null", "test_edge_large",
        "test_integration_flow", "test_simulation_scenario",
    ]

    tests = []
    for mod in modules:
        for name in random.sample(test_names, random.randint(2, 5)):
            rng = random.random()
            if rng < 0.72:
                status = "passed"
            elif rng < 0.85:
                status = "failed"
            elif rng < 0.94:
                status = "skipped"
            else:
                status = "error"
            duration = round(random.uniform(0.005, 3.5), 4)
            tests.append(
                {
                    "nodeid": f"{mod}/test_{name}.py::{name}",
                    "status": status,
                    "duration": duration,
                    "module": mod,
                }
            )

    # Add some very slow tests
    for _ in range(5):
        mod = random.choice(modules)
        tests.append(
            {
                "nodeid": f"{mod}/test_slow.py::test_slow_{_}",
                "status": "passed",
                "duration": round(random.uniform(5.0, 18.0), 4),
                "module": mod,
            }
        )

    df = pd.DataFrame(tests)
    passed = (df["status"] == "passed").sum()
    failed = (df["status"] == "failed").sum()
    skipped = (df["status"] == "skipped").sum()
    error = (df["status"] == "error").sum()
    total = len(df)

    return {
        "tests": tests,
        "summary": {
            "total": total,
            "passed": int(passed),
            "failed": int(failed),
            "skipped": int(skipped),
            "error": int(error),
            "pass_rate": round(passed / total * 100, 1) if total else 0,
            "duration": round(df["duration"].sum(), 3),
        },
    }


def _build_dataframes(data: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Build test, module, and time-series DataFrames."""
    df_tests = pd.DataFrame(data["tests"])
    df_tests["module_short"] = df_tests["module"].apply(lambda m: m.split("/")[-1])

    # Per-module aggregates
    df_mod = df_tests.groupby("module").agg(
        total=("status", "count"),
        passed=("status", lambda s: (s == "passed").sum()),
        failed=("status", lambda s: (s == "failed").sum()),
        skipped=("status", lambda s: (s == "skipped").sum()),
        error=("status", lambda s: (s == "error").sum()),
        avg_duration=("duration", "mean"),
        max_duration=("duration", "max"),
        total_duration=("duration", "sum"),
    ).reset_index()
    df_mod["pass_rate"] = (df_mod["passed"] / df_mod["total"] * 100).round(1)
    df_mod["module_short"] = df_mod["module"].apply(lambda m: m.split("/")[-1])
    df_mod = df_mod.sort_values("pass_rate")

    # Synthetic time-series (last 30 days)
    base_date = datetime.now() - timedelta(days=30)
    rows = []
    for d in range(30):
        day = base_date + timedelta(days=d)
        base = 80 + d * 0.3 + random.uniform(-3, 3)
        rows.append(
            {
                "date": day.strftime("%Y-%m-%d"),
                "pass_rate": round(min(100, base), 1),
                "tests_run": random.randint(200, 280),
                "avg_duration": round(random.uniform(0.08, 0.35), 3),
            }
        )
    df_ts = pd.DataFrame(rows)

    return df_tests, df_mod, df_ts


# ── Chart builders ────────────────────────────────────────────────────────────


def chart_gauge(pass_rate: float) -> go.Figure:
    """1. Gauge / indicator chart — overall pass rate."""
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=pass_rate,
            title={"text": "Pass Rate"},
            delta={"reference": 90, "increasing": {"color": "#00cc96"}},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#00cc96" if pass_rate >= 90 else "#ffa15a"},
                "steps": [
                    {"range": [0, 60], "color": "#ff4d4f20"},
                    {"range": [60, 80], "color": "#ffa15a20"},
                    {"range": [80, 95], "color": "#00cc9620"},
                    {"range": [95, 100], "color": "#00cc9640"},
                ],
                "threshold": {
                    "line": {"color": "white", "width": 4},
                    "thickness": 0.75,
                    "value": pass_rate,
                },
            },
        )
    )
    fig.update_layout(height=300, margin=dict(t=40, b=0, l=0, r=0))
    return fig


def chart_donut(data: dict) -> go.Figure:
    """2. Donut/pie chart — test status distribution."""
    labels = ["Passed", "Failed", "Skipped", "Error"]
    values = [
        data["summary"]["passed"],
        data["summary"]["failed"],
        data["summary"]["skipped"],
        data["summary"]["error"],
    ]
    colors = ["#00cc96", "#ff4d4f", "#ffa15a", "#ab8ce4"]
    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.5,
            marker=dict(colors=colors, line=dict(color="#1e1e2e", width=2)),
            textinfo="label+percent",
            textfont=dict(size=13),
        )
    )
    fig.update_layout(
        height=320,
        margin=dict(t=30, b=0, l=0, r=0),
        showlegend=False,
    )
    return fig


def chart_module_coverage(df_mod: pd.DataFrame) -> go.Figure:
    """3. Horizontal bar chart — module coverage %."""
    df = df_mod.sort_values("pass_rate")
    fig = go.Figure(
        go.Bar(
            x=df["pass_rate"],
            y=df["module_short"],
            orientation="h",
            marker=dict(
                color=df["pass_rate"],
                colorscale=[
                    [0, "#ff4d4f"],
                    [0.5, "#ffa15a"],
                    [0.8, "#00cc96"],
                    [1, "#00cc96"],
                ],
                line=dict(color="#1e1e2e", width=1),
            ),
            text=df["pass_rate"].apply(lambda v: f"{v:.1f}%"),
            textposition="outside",
        )
    )
    fig.update_layout(
        title="Module Pass Rate",
        height=400,
        xaxis=dict(range=[0, 105], title="Pass Rate (%)"),
        yaxis=dict(title=""),
        margin=dict(l=120, r=40, t=40, b=20),
    )
    return fig


def chart_coverage_trend(df_ts: pd.DataFrame) -> go.Figure:
    """4. Line chart — pass rate trend over time."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df_ts["date"],
            y=df_ts["pass_rate"],
            mode="lines+markers",
            line=dict(color="#00cc96", width=3, shape="spline"),
            marker=dict(size=6, color="#00cc96", line=dict(width=1, color="white")),
            fill="tozeroy",
            fillcolor="rgba(0, 204, 150, 0.12)",
            name="Pass Rate",
        )
    )
    fig.add_hline(
        y=90,
        line_dash="dash",
        line_color="#ffa15a",
        annotation_text="Target 90%",
        annotation_position="bottom right",
    )
    fig.update_layout(
        title="Pass Rate Trend (30 days)",
        height=350,
        xaxis=dict(title=""),
        yaxis=dict(range=[70, 100], title="Pass Rate (%)"),
        margin=dict(t=40, b=30),
        hovermode="x unified",
    )
    return fig


def chart_heatmap(df_tests: pd.DataFrame) -> go.Figure:
    """5. Heatmap — module × test status count."""
    matrix = df_tests.groupby(["module_short", "status"]).size().unstack(fill_value=0)
    for col in ["passed", "failed", "skipped", "error"]:
        if col not in matrix.columns:
            matrix[col] = 0
    matrix = matrix[["passed", "failed", "skipped", "error"]]

    fig = go.Figure(
        go.Heatmap(
            z=matrix.values,
            x=matrix.columns,
            y=matrix.index,
            colorscale="Viridis",
            text=matrix.values,
            texttemplate="%{text}",
            textfont=dict(size=11, color="white"),
            hovertemplate="<b>%{y}</b><br>%{x}: %{z}<extra></extra>",
        )
    )
    fig.update_layout(
        title="Module × Status Heatmap",
        height=350,
        xaxis=dict(title=""),
        yaxis=dict(title=""),
        margin=dict(t=40, b=20),
    )
    return fig


def chart_radar(df_mod: pd.DataFrame) -> go.Figure:
    """6. Radar/polar chart — multi-metric comparison."""
    top4 = df_mod.nlargest(4, "total")
    fig = go.Figure()
    for _, row in top4.iterrows():
        fig.add_trace(
            go.Scatterpolar(
                r=[
                    row["pass_rate"],
                    row["passed"],
                    row["total"] - row["failed"] - row["error"],
                    row["total"],
                    round(1.0 / max(row["avg_duration"], 0.01), 1),
                ],
                theta=["Pass Rate", "Passed Tests", "Clean Tests", "Total Tests", "Speed (1/s)"],
                fill="toself",
                name=row["module_short"],
                opacity=0.7,
            )
        )
    fig.update_layout(
        title="Module Performance Radar",
        height=380,
        polar=dict(
            radialaxis=dict(visible=True, rangemode="nonnegative"),
            bgcolor="rgba(0,0,0,0)",
        ),
        margin=dict(t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25),
    )
    return fig


def chart_treemap(df_tests: pd.DataFrame) -> go.Figure:
    """7. Treemap — test count hierarchy by module + status."""
    df = df_tests.copy()
    df["path"] = df["module"] + "." + df["status"]
    counts = df.groupby(["module", "status"]).size().reset_index(name="count")
    status_color = {"passed": "#00cc96", "failed": "#ff4d4f",
                    "skipped": "#ffa15a", "error": "#ab8ce4"}
    counts["color"] = counts["status"].map(status_color)

    fig = go.Figure(
        go.Treemap(
            labels=counts["module"] + " (" + counts["status"] + ")",
            parents=[""] * len(counts),
            values=counts["count"],
            marker=dict(colors=counts["color"]),
            textinfo="label+value",
            hovertemplate="<b>%{label}</b><br>Count: %{value}<extra></extra>",
        )
    )
    fig.update_layout(
        title="Test Distribution (Treemap)",
        height=380,
        margin=dict(t=40, b=0, l=0, r=0),
    )
    return fig


def chart_scatter(df_tests: pd.DataFrame) -> go.Figure:
    """8. Scatter plot — duration vs. frequency by module."""
    scatter_data = (
        df_tests.groupby("module")
        .agg(avg_duration=("duration", "mean"), count=("status", "count"),
             failed=("status", lambda s: (s == "failed").sum()))
        .reset_index()
    )
    scatter_data["fail_rate"] = (scatter_data["failed"] / scatter_data["count"] * 100).round(1)
    scatter_data["module_short"] = scatter_data["module"].apply(lambda m: m.split("/")[-1])

    fig = go.Figure(
        go.Scatter(
            x=scatter_data["avg_duration"],
            y=scatter_data["count"],
            mode="markers+text",
            marker=dict(
                size=scatter_data["fail_rate"] + 10,
                color=scatter_data["fail_rate"],
                colorscale="RdYlGn_r",
                showscale=True,
                colorbar=dict(title="Fail Rate %"),
                line=dict(width=1, color="white"),
            ),
            text=scatter_data["module_short"],
            textposition="top center",
            hovertemplate=(
                "<b>%{text}</b><br>Avg Duration: %{x:.3f}s<br>"
                "Tests: %{y}<br>Fail Rate: %{marker.size:.1f}%<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        title="Test Duration vs. Count (bubble = fail rate)",
        height=350,
        xaxis=dict(title="Avg Duration (s)"),
        yaxis=dict(title="Test Count"),
        margin=dict(t=40, b=20),
    )
    return fig


def chart_histogram(df_tests: pd.DataFrame) -> go.Figure:
    """9. Histogram — test duration distribution."""
    fig = go.Figure()
    for status, color, name in [
        ("passed", "#00cc96", "Passed"),
        ("failed", "#ff4d4f", "Failed"),
    ]:
        subset = df_tests[df_tests["status"] == status]
        if not subset.empty:
            fig.add_trace(
                go.Histogram(
                    x=subset["duration"],
                    nbinsx=20,
                    name=name,
                    marker=dict(color=color, line=dict(width=0.5, color="#1e1e2e")),
                    opacity=0.7,
                    histnorm="percent",
                )
            )
    fig.update_layout(
        title="Duration Distribution",
        height=320,
        xaxis=dict(title="Duration (s)"),
        yaxis=dict(title="% of Tests"),
        barmode="overlay",
        margin=dict(t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def chart_stacked_bar(df_tests: pd.DataFrame) -> go.Figure:
    """10. Stacked bar — test status by module."""
    crosstab = (
        df_tests.groupby(["module_short", "status"]).size().unstack(fill_value=0)
    )
    for col in ["passed", "failed", "skipped", "error"]:
        if col not in crosstab.columns:
            crosstab[col] = 0
    crosstab = crosstab[["passed", "failed", "skipped", "error"]]

    colors = ["#00cc96", "#ff4d4f", "#ffa15a", "#ab8ce4"]
    fig = go.Figure()
    for i, col in enumerate(crosstab.columns):
        fig.add_trace(
            go.Bar(
                name=col.capitalize(),
                y=crosstab[col],
                x=crosstab.index,
                marker=dict(color=colors[i]),
                text=crosstab[col],
                textposition="inside",
            )
        )
    fig.update_layout(
        title="Test Status by Module",
        barmode="stack",
        height=380,
        xaxis=dict(title=""),
        yaxis=dict(title="Test Count"),
        margin=dict(t=40, b=80),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def chart_area_cumulative(df_tests: pd.DataFrame) -> go.Figure:
    """11. Area chart — cumulative test execution (simulated timeline)."""
    passed_df = df_tests[df_tests["status"] == "passed"].reset_index(drop=True)
    failed_df = df_tests[df_tests["status"] == "failed"].reset_index(drop=True)

    total = len(df_tests)
    timeline = list(range(1, total + 1))

    # Simulate order: mostly passed early, failures later
    passed_cum = [0]
    failed_cum = [0]
    for i in range(total):
        passed_cum.append(passed_cum[-1] + (1 if i < len(passed_df) else 0))
        failed_cum.append(failed_cum[-1] + (1 if i >= len(passed_df) else 0))

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=list(range(len(passed_cum))),
            y=passed_cum,
            fill="tozeroy",
            mode="lines",
            name="Passed",
            line=dict(color="#00cc96", width=2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=list(range(len(failed_cum))),
            y=failed_cum,
            fill="tonexty",
            mode="lines",
            name="Failed",
            line=dict(color="#ff4d4f", width=2),
        )
    )
    fig.update_layout(
        title="Cumulative Test Execution",
        height=320,
        xaxis=dict(title="Test Run Order"),
        yaxis=dict(title="Cumulative Count"),
        margin=dict(t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def chart_sunburst(df_tests: pd.DataFrame) -> go.Figure:
    """12. Sunburst — hierarchical test categories (module → status)."""
    sun_data = (
        df_tests.groupby(["module", "module_short", "status"]).size().reset_index(name="count")
    )
    # Build hierarchy: root → module → status
    modules = sun_data["module_short"].unique()
    labels = []
    parents = []
    values = []
    colors = []

    # Root level
    labels.append("All Tests")
    parents.append("")
    values.append(0)
    colors.append("#636efa")

    # Module level (each module is a child of root)
    for mod in modules:
        mod_count = sun_data[sun_data["module_short"] == mod]["count"].sum()
        labels.append(mod)
        parents.append("All Tests")
        values.append(int(mod_count))
        colors.append("#888")

    # Status level (each status is child of its module)
    status_color = {"passed": "#00cc96", "failed": "#ff4d4f",
                    "skipped": "#ffa15a", "error": "#ab8ce4"}
    for _, row in sun_data.iterrows():
        labels.append(f"{row['module_short']} - {row['status']}")
        parents.append(row["module_short"])
        values.append(int(row["count"]))
        colors.append(status_color.get(row["status"], "#888"))

    fig = go.Figure(
        go.Sunburst(
            labels=labels,
            parents=parents,
            values=values,
            branchvalues="total",
            marker=dict(colors=colors),
            textinfo="label+value",
            hovertemplate="<b>%{label}</b><br>Count: %{value}<extra></extra>",
        )
    )
    fig.update_layout(
        title="Test Categories (Sunburst)",
        height=380,
        margin=dict(t=40, b=0, l=0, r=0),
    )
    return fig


def chart_boxplot(df_tests: pd.DataFrame) -> go.Figure:
    """13. Box plot — duration distribution by module."""
    fig = go.Figure()
    for mod in df_tests["module"].unique():
        subset = df_tests[df_tests["module"] == mod]
        if not subset.empty:
            fig.add_trace(
                go.Box(
                    y=subset["duration"],
                    name=mod.split("/")[-1],
                    boxmean="sd",
                    marker=dict(color="#00cc96"),
                    line=dict(color="#00cc9680"),
                    fillcolor=lighten_hex("#00cc96", 0.85),
                )
            )
    fig.update_layout(
        title="Duration Distribution by Module",
        height=380,
        xaxis=dict(title=""),
        yaxis=dict(title="Duration (s)"),
        margin=dict(t=40, b=60),
        showlegend=False,
    )
    return fig


def chart_funnel() -> go.Figure:
    """14. Funnel chart — test pipeline stages."""
    stages = ["Planned", "Written", "Run", "Passed", "Approved"]
    values = [250, 235, 220, 192, 180]
    fig = go.Figure(
        go.Funnel(
            y=stages,
            x=values,
            textinfo="value+percent initial",
            marker=dict(
                color=["#636efa", "#00cc96", "#ffa15a", "#00cc96", "#ab8ce4"],
                line=dict(width=1, color="white"),
            ),
        )
    )
    fig.update_layout(
        title="Test Pipeline Funnel",
        height=380,
        margin=dict(t=40, b=0, l=0, r=0),
    )
    return fig


def chart_sankey(df_tests: pd.DataFrame) -> go.Figure:
    """15. Sankey diagram — flow from module through status to outcome."""
    mod_status = df_tests.groupby(["module", "status"]).size().reset_index(name="count")
    modules = df_tests["module"].unique().tolist()
    statuses = ["passed", "failed", "skipped", "error"]
    outcomes = ["success", "needs review", "blocked"]

    labels = modules + [s.capitalize() for s in statuses] + outcomes
    label_to_idx = {lbl: i for i, lbl in enumerate(labels)}

    source, target, value = [], [], []
    for _, row in mod_status.iterrows():
        source.append(label_to_idx[row["module"]])
        target.append(label_to_idx[row["status"].capitalize()])
        value.append(int(row["count"]))

    # map status → outcome
    for s in statuses:
        total_s = int(df_tests[df_tests["status"] == s].shape[0])
        s_idx = label_to_idx[s.capitalize()]
        if s == "passed":
            target.append(label_to_idx["success"])
            source.append(s_idx)
            value.append(total_s)
        elif s == "failed":
            for o in ["needs review", "blocked"]:
                target.append(label_to_idx[o])
                source.append(s_idx)
                value.append(total_s // 2)
        else:
            target.append(label_to_idx["needs review"])
            source.append(s_idx)
            value.append(total_s)

    fig = go.Figure(
        go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="#1e1e2e", width=1),
                label=labels,
                color=["#636efa"] * len(modules)
                + ["#00cc96", "#ff4d4f", "#ffa15a", "#ab8ce4"]
                + ["#00cc96", "#ffa15a", "#ff4d4f"],
            ),
            link=dict(
                source=source,
                target=target,
                value=value,
                color=[
                    "rgba(99, 110, 250, 0.3)" for _ in source
                ],
            ),
        )
    )
    fig.update_layout(
        title="Test Flow (Sankey)",
        height=400,
        margin=dict(t=40, b=0, l=0, r=0),
        font=dict(size=11),
    )
    return fig


def chart_violin(df_tests: pd.DataFrame) -> go.Figure:
    """16. Violin plot — duration density by status."""
    fig = go.Figure()
    for status, color in [
        ("passed", "#00cc96"), ("failed", "#ff4d4f"),
        ("skipped", "#ffa15a"), ("error", "#ab8ce4"),
    ]:
        subset = df_tests[df_tests["status"] == status]
        if not subset.empty:
            fig.add_trace(
                go.Violin(
                    y=subset["duration"],
                    name=status.capitalize(),
                    box_visible=True,
                    meanline_visible=True,
                    fillcolor=lighten_hex(color, 0.7),
                    line=dict(color=color, width=1.5),
                    opacity=0.8,
                )
            )
    fig.update_layout(
        title="Duration Density by Status (Violin)",
        height=380,
        yaxis=dict(title="Duration (s)"),
        margin=dict(t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


# ── UI ────────────────────────────────────────────────────────────────────────

st.markdown(
    """
<style>
    /* Dark theme overrides for readability */
    .stApp { background-color: #0e1117; }
    h1, h2, h3 { color: #f0f0f0 !important; }
    .metric-card {
        background: linear-gradient(135deg, #1e1e2e 0%, #2a2a3e 100%);
        border: 1px solid #3a3a4e;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        margin: 8px 0 4px;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .section-header {
        border-bottom: 2px solid #3a3a4e;
        padding-bottom: 8px;
        margin-bottom: 20px;
    }
</style>
""",
    unsafe_allow_html=True,
)

st.title("🧪 TestVision Dashboard")
st.markdown("Comprehensive test analytics with 16 chart types")

# ── Load data ─────────────────────────────────────────────────────────────────
data = load_test_data()
df_tests, df_mod, df_ts = _build_dataframes(data)
summary = data["summary"]

# ── KPI row ───────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.markdown(
        f'<div class="metric-card">'
        f'<div class="metric-label">Total Tests</div>'
        f'<div class="metric-value" style="color:#636efa">{summary["total"]}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
with k2:
    st.markdown(
        f'<div class="metric-card">'
        f'<div class="metric-label">Passed</div>'
        f'<div class="metric-value" style="color:#00cc96">{summary["passed"]}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
with k3:
    st.markdown(
        f'<div class="metric-card">'
        f'<div class="metric-label">Failed</div>'
        f'<div class="metric-value" style="color:#ff4d4f">{summary["failed"]}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
with k4:
    st.markdown(
        f'<div class="metric-card">'
        f'<div class="metric-label">Duration</div>'
        f'<div class="metric-value" style="color:#ffa15a">{summary["duration"]:.1f}s</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
with k5:
    color = "#00cc96" if summary["pass_rate"] >= 90 else "#ffa15a"
    st.markdown(
        f'<div class="metric-card">'
        f'<div class="metric-label">Pass Rate</div>'
        f'<div class="metric-value" style="color:{color}">{summary["pass_rate"]}%</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

# ── Section 1: Overall Metrics ────────────────────────────────────────────────
st.markdown("<h2 class='section-header'>📊 Overall Metrics</h2>", unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(chart_gauge(summary["pass_rate"]), use_container_width=True)
with c2:
    st.plotly_chart(chart_donut(data), use_container_width=True)

# ── Section 2: Module Analysis ────────────────────────────────────────────────
st.markdown("<h2 class='section-header'>📦 Module Analysis</h2>", unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(chart_module_coverage(df_mod), use_container_width=True)
with c2:
    st.plotly_chart(chart_stacked_bar(df_tests), use_container_width=True)

c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(chart_heatmap(df_tests), use_container_width=True)
with c2:
    st.plotly_chart(chart_radar(df_mod), use_container_width=True)

# ── Section 3: Trends & Timing ────────────────────────────────────────────────
st.markdown("<h2 class='section-header'>📈 Trends & Timing</h2>", unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(chart_coverage_trend(df_ts), use_container_width=True)
with c2:
    st.plotly_chart(chart_histogram(df_tests), use_container_width=True)

c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(chart_area_cumulative(df_tests), use_container_width=True)
with c2:
    st.plotly_chart(chart_scatter(df_tests), use_container_width=True)

# ── Section 4: Distributions & Hierarchies ────────────────────────────────────
st.markdown("<h2 class='section-header'>🔬 Distributions & Hierarchies</h2>", unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(chart_treemap(df_tests), use_container_width=True)
with c2:
    st.plotly_chart(chart_sunburst(df_tests), use_container_width=True)

c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(chart_boxplot(df_tests), use_container_width=True)
with c2:
    st.plotly_chart(chart_violin(df_tests), use_container_width=True)

# ── Section 5: Flow & Pipeline ────────────────────────────────────────────────
st.markdown("<h2 class='section-header'>🔄 Flow & Pipeline</h2>", unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(chart_sankey(df_tests), use_container_width=True)
with c2:
    st.plotly_chart(chart_funnel(), use_container_width=True)

# ── Data table ────────────────────────────────────────────────────────────────
with st.expander("📋 Raw Test Data"):
    show_df = df_tests[["nodeid", "status", "duration", "module"]].copy()
    show_df.columns = ["Test", "Status", "Duration (s)", "Module"]
    st.dataframe(show_df, use_container_width=True, height=400)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    f"TestVision Dashboard • {summary['total']} tests • "
    f"{summary['pass_rate']}% pass rate • "
    f"Generated at {datetime.now().strftime('%Y-%m-%d %H:%M')}"
)
