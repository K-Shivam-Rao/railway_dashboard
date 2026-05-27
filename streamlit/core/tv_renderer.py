"""
TotalVision Renderer — Renders the cross-domain intelligence hub in Streamlit.

Integrates with TotalVisionDataEngine (totalvision.py) to display 5-domain
analytics with KPI cards, chart info bars, and a what-if scenario simulator.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import textwrap
from core.totalvision import (
    TotalVisionDataEngine, TotalVisionData,
    STATIONS, DOMAIN_COLORS,
)

# ── Domain icon/short-label map ──
DOMAIN_META = {
    "security":    {"icon": "🛡️", "short": "SEC", "label": "Security & Threat"},
    "sustain":     {"icon": "🌱", "short": "SUS", "label": "Sustainability & Energy"},
    "passenger":   {"icon": "👥", "short": "PAS", "label": "Passenger Experience"},
    "asset":       {"icon": "⚙️", "short": "AST", "label": "Asset Lifecycle & IoT"},
    "climate":     {"icon": "🌤️", "short": "CLM", "label": "Climate Resilience"},
}

DOMAINS = ["security", "sustain", "passenger", "asset", "climate"]


def _make_domain_gauge(value: float, title: str, color: str) -> go.Figure:
    """Create a compact gauge chart for a domain KPI."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={"font": {"size": 24, "color": color, "family": "Clash Display, sans-serif"}, "suffix": ""},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickfont": {"size": 9}},
            "bar": {"color": color, "thickness": 0.4},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 30], "color": "rgba(239,68,68,0.08)"},
                {"range": [30, 60], "color": "rgba(245,158,11,0.08)"},
                {"range": [60, 100], "color": "rgba(16,185,129,0.08)"},
            ],
            "threshold": {
                "line": {"color": color, "width": 2},
                "thickness": 0.6,
                "value": value,
            },
        },
        domain={"x": [0, 1], "y": [0, 1]},
    ))
    fig.update_layout(
        height=140,
        margin=dict(l=20, r=20, t=25, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#94a3b8"},
        title={"text": title, "font": {"size": 11, "color": "#94a3b8"}, "x": 0.5, "y": 0.95},
    )
    return fig


def _make_radar_chart(scores: dict, title: str) -> go.Figure:
    """Create a radar chart for domain scores."""
    categories = [DOMAIN_META[d]["label"].split(" ")[0] for d in DOMAINS]
    values = [scores.get(d, 50) for d in DOMAINS]
    values += values[:1]  # close the loop

    fig = go.Figure(go.Scatterpolar(
        r=values,
        theta=categories + categories[:1],
        fill="toself",
        fillcolor="rgba(245,158,11,0.1)",
        line=dict(color="#f59e0b", width=2),
        hovertemplate="%{theta}: %{r:.1f}<extra></extra>",
    ))
    fig.update_layout(
        height=200,
        margin=dict(l=40, r=40, t=25, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#94a3b8", "size": 9},
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], color="#475569", gridcolor="rgba(255,255,255,0.05)"),
            angularaxis=dict(color="#94a3b8", gridcolor="rgba(255,255,255,0.05)"),
            bgcolor="rgba(0,0,0,0)",
        ),
        showlegend=False,
    )
    return fig


def _make_bar_chart(data: dict, title: str, color: str, height: int = 200) -> go.Figure:
    """Create a horizontal bar chart (e.g., for domain breakdown)."""
    stations = list(data.keys())
    values = list(data.values())
    # Sort by value
    pairs = sorted(zip(values, stations), reverse=True)
    values, stations = zip(*pairs) if pairs else ([], [])

    fig = go.Figure(go.Bar(
        x=list(values),
        y=list(stations),
        orientation="h",
        marker=dict(color=color, opacity=0.7, line=dict(color=color, width=1)),
        hovertemplate="%{y}: %{x:.1f}<extra></extra>",
    ))
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=25, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#94a3b8", "size": 9},
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, color="#64748b", tickfont={"size": 8}),
        showlegend=False,
        bargap=0.3,
    )
    return fig


def _make_all_stations_bar(all_data: dict, domain: str, color: str) -> go.Figure:
    """All-stations ranking bar chart for a domain."""
    scores = {s: all_data[s].score(domain) for s in STATIONS if s in all_data}
    return _make_bar_chart(scores, DOMAIN_META[domain]["label"], color)


def _make_correlation_heatmap(corr_matrix: dict) -> go.Figure:
    """Cross-domain correlation heatmap."""
    domain_labels = ["Sec", "Sus", "Pas", "Ast", "Clm"]
    z = [[corr_matrix.get(d1, {}).get(d2, 0) for d2 in DOMAINS] for d1 in DOMAINS]

    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=domain_labels,
        y=domain_labels,
        colorscale=[[0, "#ef4444"], [0.5, "#1e293b"], [1, "#10b981"]],
        zmid=0,
        zmin=-1,
        zmax=1,
        hovertemplate="<b>%{x} vs %{y}</b><br>Correlation: %{z:+.2f}<extra></extra>",
        showscale=True,
        colorbar=dict(
            title=dict(text="Correlation", font=dict(size=8, color="#94a3b8")),
            tickfont=dict(size=8, color="#94a3b8"),
            outlinewidth=0,
            tickvals=[-1, -0.5, 0, 0.5, 1],
            ticktext=["-1", "-0.5", "0", "+0.5", "+1"],
            x=1.02,
            len=0.7,
        ),
    ))
    fig.update_layout(
        height=240,
        margin=dict(l=10, r=40, t=25, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#94a3b8", "size": 9},
        xaxis=dict(side="bottom", tickfont={"size": 8}, gridcolor="rgba(0,0,0,0)"),
        yaxis=dict(tickfont={"size": 8}, gridcolor="rgba(0,0,0,0)"),
    )
    return fig



# ── New Advanced Chart Functions ─────────────────────────────────────────


def _make_sunburst(all_data: dict) -> go.Figure:
    """Sunburst chart: Domain → Station hierarchy (inner=5 domains, outer=stations)."""
    labels = []
    parents = []
    values = []
    colors = []

    # Compute domain totals (sum of station scores) for correct hierarchy arithmetic
    domain_totals = {}
    for d in DOMAINS:
        dv = [all_data[s].score(d) for s in STATIONS if s in all_data]
        domain_totals[d] = sum(dv) if dv else 0

    root_total = sum(domain_totals.values())

    # Build customdata with average scores for meaningful hover display
    customdata = []
    stations_per_domain = {d: [s for s in STATIONS if s in all_data] for d in DOMAINS}

    # Root: overall network average
    all_station_count = sum(len(v) for v in stations_per_domain.values())
    overall_avg = round(root_total / (len(DOMAINS) * max(all_station_count, 1)), 1)
    labels.append("Network")
    parents.append("")
    values.append(root_total)
    colors.append("rgba(148,163,184,0.15)")
    customdata.append([overall_avg, "Network Avg"])

    for d in DOMAINS:
        meta = DOMAIN_META[d]
        color = DOMAIN_COLORS.get(d, "#94a3b8")
        domain_stations = stations_per_domain[d]
        avg = round(domain_totals[d] / len(domain_stations), 1) if domain_stations else 0

        labels.append(meta["label"].split(" ")[0])
        parents.append("Network")
        values.append(domain_totals[d])
        colors.append(f"{color}cc")
        customdata.append([avg, "Domain Avg"])

        for s in domain_stations:
            short = s.replace(" Hbf", "").replace(" Hauptbahnhof", "")
            labels.append(short)
            parents.append(meta["label"].split(" ")[0])
            values.append(all_data[s].score(d))
            colors.append(f"{color}66")
            customdata.append([round(all_data[s].score(d), 1), "Station"])

    fig = go.Figure(go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        marker=dict(colors=colors, line=dict(color="rgba(0,0,0,0.15)", width=0.5)),
        hovertemplate="<b>%{label}</b><br>Score: %{customdata[0]:.1f}<extra></extra>",
        customdata=customdata,
        branchvalues="total",
        textinfo="label",
        textfont=dict(size=10, color="#e2e8f0"),
    ))

    # Add domain color legend via invisible markers
    for d in DOMAINS:
        fig.add_trace(go.Scatter(
            x=[None], y=[None],
            mode="markers",
            marker=dict(size=10, color=DOMAIN_COLORS.get(d, "#94a3b8")),
            name=DOMAIN_META[d]["short"],
            showlegend=True,
            hoverinfo="skip",
        ))

    fig.update_layout(
        height=350,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#94a3b8", "size": 9},
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.07,
            xanchor="center",
            x=0.5,
            font=dict(size=8, color="#94a3b8"),
            itemclick=False,
            itemdoubleclick=False,
        ),
    )
    return fig


def _make_treemap(all_data: dict) -> go.Figure:
    """Treemap: Station scores broken down by domain."""
    labels = []
    parents = []
    values = []
    colors = []

    for station, tv_data in all_data.items():
        short = station.replace(" Hbf", "").replace(" Hauptbahnhof", "")
        labels.append(short)
        parents.append("")
        values.append(0)
        colors.append("rgba(148,163,184,0.2)")

    for station, tv_data in all_data.items():
        short = station.replace(" Hbf", "").replace(" Hauptbahnhof", "")
        domain_vals = tv_data.scores_dict()
        for d in DOMAINS:
            labels.append(f"{d} — {short}")
            parents.append(short)
            values.append(domain_vals[d])
            colors.append(DOMAIN_COLORS.get(d, "#94a3b8"))

    fig = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        marker=dict(colors=colors, line=dict(color="rgba(0,0,0,0.15)", width=1)),
        hovertemplate="<b>%{label}</b><br>%{parent} — Score: %{value:.1f}<extra></extra>",
        textinfo="label+value",
        textfont=dict(size=9, color="#e2e8f0"),
    ))

    # Add domain color legend via invisible markers
    for d in DOMAINS:
        fig.add_trace(go.Scatter(
            x=[None], y=[None],
            mode="markers",
            marker=dict(size=10, color=DOMAIN_COLORS.get(d, "#94a3b8")),
            name=DOMAIN_META[d]["short"],
            showlegend=True,
            hoverinfo="skip",
        ))

    fig.update_layout(
        height=340,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#94a3b8", "size": 9},
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.07,
            xanchor="center",
            x=0.5,
            font=dict(size=8, color="#94a3b8"),
            itemclick=False,
            itemdoubleclick=False,
        ),
    )
    return fig


def _make_scatter_bubble(all_data: dict, x_domain: str, y_domain: str, size_domain: str) -> go.Figure:
    """Scatter bubble chart: 2 domains as axes, 3rd as bubble size."""
    stations, xs, ys, sizes, labels = [], [], [], [], []
    for station, tv_data in all_data.items():
        scores = tv_data.scores_dict()
        short = station.replace(" Hbf", "").replace(" Hauptbahnhof", "")
        stations.append(station)
        xs.append(scores.get(x_domain, 50))
        ys.append(scores.get(y_domain, 50))
        sizes.append(max(8, scores.get(size_domain, 50) * 0.5))
        labels.append(short)

    fig = go.Figure(go.Scatter(
        x=xs, y=ys,
        mode="markers+text",
        text=labels,
        textposition="top center",
        textfont=dict(size=8, color="#94a3b8"),
        marker=dict(
            size=sizes,
            color=xs,
            colorscale=[[0, "#ef4444"], [0.5, "#f59e0b"], [1, "#10b981"]],
            showscale=True,
            colorbar=dict(
                title=dict(text=DOMAIN_META[x_domain]["short"], font=dict(size=8, color="#94a3b8")),
                tickfont=dict(size=8, color="#94a3b8"),
                outlinewidth=0,
                x=1.02,
                len=0.6,
            ),
            line=dict(color="rgba(255,255,255,0.2)", width=1),
            opacity=0.75,
        ),
        hovertemplate="<b>%{text}</b><br>"
                      + DOMAIN_META[x_domain]["short"] + " (x): %{x:.1f}<br>"
                      + DOMAIN_META[y_domain]["short"] + " (y): %{y:.1f}<br>"
                      + DOMAIN_META[size_domain]["short"] + " (bubble): %{marker.size:.1f}<extra></extra>",
    ))
    fig.update_layout(
        height=350,
        margin=dict(l=10, r=65, t=30, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#94a3b8", "size": 9},
        xaxis=dict(title=DOMAIN_META[x_domain]["label"], gridcolor="rgba(255,255,255,0.04)", color="#64748b", range=[0, 100], tickfont={"size": 8}),
        yaxis=dict(title=DOMAIN_META[y_domain]["label"], gridcolor="rgba(255,255,255,0.04)", color="#64748b", range=[0, 100], tickfont={"size": 8}),
        hovermode="closest",
    )
    return fig


def _make_box_plot(all_data: dict) -> go.Figure:
    """Box plot: Score distribution per domain across all stations."""
    fig = go.Figure()
    for d in DOMAINS:
        scores = [all_data[s].score(d) for s in STATIONS if s in all_data]
        if not scores:
            continue
        arr = np.array(scores)
        stats = [round(np.mean(arr), 1), round(np.median(arr), 1),
                 round(np.percentile(arr, 25), 1), round(np.percentile(arr, 75), 1),
                 round(np.std(arr), 1), len(scores)]
        fig.add_trace(go.Box(
            y=scores,
            name=DOMAIN_META[d]["short"],
            marker_color=DOMAIN_COLORS.get(d, "#94a3b8"),
            boxmean="sd",
            line=dict(width=1.5),
            fillcolor="rgba(255,255,255,0.02)",
            customdata=[stats] * len(scores),
            hovertemplate="<b>%{x}</b><br>"
                          + "Median: %{customdata[1]:.1f}<br>"
                          + "Mean: %{customdata[0]:.1f} ± %{customdata[4]:.1f}<br>"
                          + "Q1–Q3: %{customdata[2]:.1f} – %{customdata[3]:.1f}<br>"
                          + "Count: %{customdata[5]}<extra></extra>",
        ))
    fig.update_layout(
        height=280,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#94a3b8", "size": 9},
        yaxis=dict(title="Score", range=[0, 100], gridcolor="rgba(255,255,255,0.04)", color="#64748b", tickfont={"size": 8}),
        xaxis=dict(color="#64748b", tickfont={"size": 8}),
        showlegend=False,
        hovermode="y unified",
    )
    return fig


def _make_violin_plot(all_data: dict) -> go.Figure:
    """Violin plot: Alternative score distribution view."""
    fig = go.Figure()
    for d in DOMAINS:
        scores = [all_data[s].score(d) for s in STATIONS if s in all_data]
        if not scores:
            continue
        arr = np.array(scores)
        stats = [round(np.mean(arr), 1), round(np.median(arr), 1),
                 round(np.percentile(arr, 25), 1), round(np.percentile(arr, 75), 1),
                 round(np.std(arr), 1), len(scores)]
        fig.add_trace(go.Violin(
            y=scores,
            name=DOMAIN_META[d]["short"],
            marker_color=DOMAIN_COLORS.get(d, "#94a3b8"),
            line=dict(color=DOMAIN_COLORS.get(d, "#94a3b8"), width=1.5),
            fillcolor="rgba(255,255,255,0.02)",
            meanline_visible=True,
            box_visible=True,
            points=False,
            customdata=[stats] * len(scores),
            hovertemplate="<b>%{x}</b><br>"
                          + "Median: %{customdata[1]:.1f}<br>"
                          + "Mean: %{customdata[0]:.1f} ± %{customdata[4]:.1f}<br>"
                          + "Q1–Q3: %{customdata[2]:.1f} – %{customdata[3]:.1f}<br>"
                          + "Count: %{customdata[5]}<extra></extra>",
        ))
    fig.update_layout(
        height=280,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#94a3b8", "size": 9},
        yaxis=dict(title="Score", range=[0, 100], gridcolor="rgba(255,255,255,0.04)", color="#64748b", tickfont={"size": 8}),
        xaxis=dict(color="#64748b", tickfont={"size": 8}),
        showlegend=False,
        hovermode="y unified",
    )
    return fig


def _make_histogram(all_data: dict) -> go.Figure:
    """Histogram: Score frequency distribution across all stations/domains."""
    fig = go.Figure()
    for d in DOMAINS:
        scores = [all_data[s].score(d) for s in STATIONS if s in all_data]
        if not scores:
            continue
        # Compute histogram bins and percentages for richer hover
        counts, bin_edges = np.histogram(scores, bins=10, range=(0, 100))
        total = len(scores)
        pcts = [round(c / total * 100, 1) for c in counts]
        customdata_arr = [[int(counts[i]), pcts[i]] for i in range(len(counts))]

        fig.add_trace(go.Histogram(
            x=scores,
            name=DOMAIN_META[d]["short"],
            marker_color=DOMAIN_COLORS.get(d, "#94a3b8"),
            opacity=0.6,
            nbinsx=10,
            customdata=customdata_arr,
            hovertemplate="<b>" + DOMAIN_META[d]["short"] + "</b><br>"
                          + "Score: %{x:.0f}<br>"
                          + "Count: %{customdata[0]}<br>"
                          + "Share: %{customdata[1]:.1f}%<extra></extra>",
        ))
    fig.update_layout(
        height=280,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#94a3b8", "size": 9},
        barmode="overlay",
        xaxis=dict(title="Score", range=[0, 100], gridcolor="rgba(255,255,255,0.04)", color="#64748b", tickfont={"size": 8}),
        yaxis=dict(title="Frequency", gridcolor="rgba(255,255,255,0.04)", color="#64748b", tickfont={"size": 8}),
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5, font=dict(size=8, color="#94a3b8")),
        hovermode="x unified",
    )
    return fig


def _make_deviation_heatmap(all_data: dict) -> go.Figure:
    """Heatmap: Station × Domain score deviation from network average.
    Green = above avg, Red = below avg — instantly spot under/over performers."""
    # Compute network averages per domain
    domain_avgs = {}
    for d in DOMAINS:
        vals = [all_data[s].score(d) for s in STATIONS if s in all_data]
        domain_avgs[d] = sum(vals) / len(vals) if vals else 50

    # Build deviation matrix: rows=stations, cols=domains
    station_names = [s.replace(" Hbf", "").replace(" Hauptbahnhof", "") for s in STATIONS if s in all_data]
    z_data = []
    for s in STATIONS:
        if s not in all_data:
            continue
        row = [all_data[s].score(d) - domain_avgs[d] for d in DOMAINS]
        z_data.append(row)

    if not z_data:
        return go.Figure()

    fig = go.Figure(go.Heatmap(
        z=z_data,
        x=[DOMAIN_META[d]["short"] for d in DOMAINS],
        y=station_names,
        colorscale=[
            [0.0, "#dc2626"],
            [0.25, "rgba(220,38,38,0.35)"],
            [0.45, "rgba(30,41,59,0.95)"],
            [0.5, "rgba(30,41,59,0.95)"],
            [0.55, "rgba(30,41,59,0.95)"],
            [0.75, "rgba(22,163,74,0.35)"],
            [1.0, "#16a34a"],
        ],
        zmid=0,
        zmin=-25,
        zmax=25,
        text=[[f"{v:+.1f}" for v in row] for row in z_data],
        texttemplate="%{text}",
        textfont=dict(size=8, color="#e2e8f0"),
        hovertemplate="<b>%{y}</b> — %{x}<br>Deviation: %{z:+.1f}<extra></extra>",
        showscale=True,
        colorbar=dict(
            title=dict(text="Deviation", font=dict(size=8, color="#94a3b8")),
            tickfont=dict(size=8, color="#94a3b8"),
            outlinewidth=0,
            tickvals=[-25, -15, -5, 0, 5, 15, 25],
            ticktext=["-25", "-15", "-5", "0", "+5", "+15", "+25"],
            x=1.02,
            len=0.7,
        ),
    ))
    fig.update_layout(
        height=340,
        margin=dict(l=10, r=50, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#94a3b8", "size": 9},
        xaxis=dict(side="bottom", tickfont={"size": 9}, gridcolor="rgba(0,0,0,0)"),
        yaxis=dict(tickfont={"size": 8}, gridcolor="rgba(0,0,0,0)"),
    )
    return fig


def _make_parallel_coords(all_data: dict) -> go.Figure:
    """Parallel coordinates: Multi-dimensional station profiling across all 5 domains.
    Each line = one station, color-coded by overall score.
    Operators can instantly spot stations weak in multiple domains."""
    df_data = []
    for s in STATIONS:
        if s not in all_data:
            continue
        sd = all_data[s].scores_dict()
        overall = sum(sd.get(d, 50) for d in DOMAINS) / len(DOMAINS)
        row = {"station": s.replace(" Hbf", "").replace(" Hauptbahnhof", ""), "overall": overall}
        row.update({DOMAIN_META[d]["short"]: sd.get(d, 50) for d in DOMAINS})
        df_data.append(row)

    if not df_data:
        return go.Figure()

    df = pd.DataFrame(df_data)

    # Sort stations by overall score for cleaner rendering
    df = df.sort_values("overall", ascending=False).reset_index(drop=True)

    dimensions = []
    for d in DOMAINS:
        short = DOMAIN_META[d]["short"]
        dimensions.append(dict(
            label=short,
            values=df[short].tolist(),
            range=[0, 100],
            tickvals=[0, 25, 50, 75, 100],
            ticktext=["0", "25", "50", "75", "100"],
        ))

    fig = go.Figure(go.Parcoords(
        line=dict(
            color=df["overall"].tolist(),
            colorscale=[[0, "#ef4444"], [0.25, "#f59e0b"], [0.5, "#3b82f6"], [0.75, "#10b981"], [1, "#059669"]],
            showscale=True,
            colorbar=dict(
                title=dict(text="Overall Score", font=dict(size=9, color="#94a3b8")),
                tickfont=dict(size=8, color="#94a3b8"),
                outlinewidth=0,
                tickvals=[0, 25, 50, 75, 100],
                x=0.9,
                len=0.6,
            ),
            cmin=0,
            cmax=100,
        ),
        dimensions=dimensions,
        customdata=df[["station", "overall"]].to_numpy(),
        labelfont=dict(color="#e2e8f0", size=11, family="Clash Display, sans-serif"),
        tickfont=dict(color="#94a3b8", size=9),
        rangefont=dict(color="#64748b", size=8),
        unselected=dict(line=dict(color="rgba(148,163,184,0.12)")),
    ))
    fig.update_layout(
        height=380,
        margin=dict(l=50, r=50, t=30, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#94a3b8", "size": 9},
        dragmode="select",
        hovermode="closest",
    )
    return fig


def _make_bullet_chart(scores: dict, targets: dict) -> go.Figure:
    """Bullet chart: Current score vs target for each domain.
    Horizontal bars with three qualitative zones (poor/acceptable/good),
    a dark bar for the current value, and a diamond marker for the target."""
    fig = go.Figure()

    # Qualitative zone backgrounds (stacked)
    for zone_start, zone_end, zone_color, zone_name in [
        (0, 33, "rgba(239,68,68,0.10)", "Poor"),
        (33, 66, "rgba(245,158,11,0.08)", "Fair"),
        (66, 100, "rgba(16,185,129,0.08)", "Good"),
    ]:
        fig.add_trace(go.Bar(
            y=[DOMAIN_META[d]["short"] for d in DOMAINS],
            x=[zone_end - zone_start] * len(DOMAINS),
            base=[zone_start] * len(DOMAINS),
            orientation="h",
            marker=dict(color=zone_color, line=dict(width=0)),
            showlegend=False,
            hoverinfo="skip",
            legendgroup="zone",
        ))

    # Current value bars (semi-transparent dark bars)
    current_vals = [scores.get(d, 50) for d in DOMAINS]
    fig.add_trace(go.Bar(
        y=[DOMAIN_META[d]["short"] for d in DOMAINS],
        x=current_vals,
        base=[0] * len(DOMAINS),
        orientation="h",
        marker=dict(
            color=[DOMAIN_COLORS.get(d, "#94a3b8") for d in DOMAINS],
            opacity=0.45,
            line=dict(color=[DOMAIN_COLORS.get(d, "#94a3b8") for d in DOMAINS], width=2),
        ),
        name="Current",
        hovertemplate="<b>%{y}</b> Current: %{x:.1f}<extra></extra>",
    ))

    # Target markers (diamonds)
    target_vals = [targets.get(d, 75) for d in DOMAINS]
    fig.add_trace(go.Scatter(
        x=target_vals,
        y=[DOMAIN_META[d]["short"] for d in DOMAINS],
        mode="markers",
        name="Target",
        marker=dict(
            symbol="diamond",
            size=12,
            color="#f8fafc",
            line=dict(color="rgba(0,0,0,0.3)", width=2),
        ),
        hovertemplate="<b>%{y}</b> Target: %{x:.1f}<extra></extra>",
    ))

    fig.update_layout(
        height=260,
        margin=dict(l=10, r=30, t=18, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#94a3b8", "size": 9},
        xaxis=dict(
            title="Score",
            range=[0, 100],
            gridcolor="rgba(255,255,255,0.04)",
            color="#64748b",
            tickfont={"size": 8},
            tickvals=[0, 25, 50, 75, 100],
        ),
        yaxis=dict(
            color="#64748b",
            tickfont={"size": 9, "weight": 700},
            autorange="reversed",
        ),
        barmode="overlay",
        bargap=0.4,
        hovermode="y unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5,
            font=dict(size=8, color="#94a3b8"),
        ),
        annotations=[
            dict(
                x=16, y=1.06,
                xref="x", yref="paper",
                text="Poor",
                showarrow=False,
                font=dict(size=7, color="rgba(239,68,68,0.4)"),
            ),
            dict(
                x=50, y=1.02,
                xref="x", yref="paper",
                text="Fair",
                showarrow=False,
                font=dict(size=7, color="rgba(245,158,11,0.4)"),
            ),
            dict(
                x=83, y=1.02,
                xref="x", yref="paper",
                text="Good",
                showarrow=False,
                font=dict(size=7, color="rgba(16,185,129,0.4)"),
            ),
        ],
    )
    return fig


def _render_kpi_row(station_scores: dict, tv_data: TotalVisionData = None):
    """Render 5 domain KPI cards with sub-metrics."""
    cols = st.columns(5)
    for idx, domain in enumerate(DOMAINS):
        meta = DOMAIN_META[domain]
        color = DOMAIN_COLORS.get(domain, "#f59e0b")
        score = station_scores.get(domain, 50)
        trend = "trend-up" if score > 55 else "trend-down"
        trend_arrow = "↑" if score > 55 else "↓"

        # Build sub-metrics from domain data
        sub_metrics = ""
        if tv_data:
            if domain == "security" and hasattr(tv_data, "security"):
                d = tv_data.security
                sub_metrics = textwrap.dedent(f'''\
                <div class="tv-kpi-submetrics">
                  <div class="tv-kpi-submetric"><span class="tv-kpi-submetric-label">Cyber Inc.</span><span class="tv-kpi-submetric-value">{d.incidents_cyber}</span></div>
                  <div class="tv-kpi-submetric"><span class="tv-kpi-submetric-label">Response</span><span class="tv-kpi-submetric-value">{d.avg_response_time:.1f}m</span></div>
                </div>''')
            elif domain == "sustain" and hasattr(tv_data, "sustainability"):
                d = tv_data.sustainability
                sub_metrics = textwrap.dedent(f'''\
                <div class="tv-kpi-submetrics">
                  <div class="tv-kpi-submetric"><span class="tv-kpi-submetric-label">Carbon</span><span class="tv-kpi-submetric-value">{d.carbon_tco2e:.1f}t</span></div>
                  <div class="tv-kpi-submetric"><span class="tv-kpi-submetric-label">Green</span><span class="tv-kpi-submetric-value">{d.green_energy_pct:.0f}%</span></div>
                </div>''')
            elif domain == "passenger" and hasattr(tv_data, "passenger"):
                d = tv_data.passenger
                sub_metrics = textwrap.dedent(f'''\
                <div class="tv-kpi-submetrics">
                  <div class="tv-kpi-submetric"><span class="tv-kpi-submetric-label">Crowding</span><span class="tv-kpi-submetric-value">{d.crowding_index:.0f}%</span></div>
                  <div class="tv-kpi-submetric"><span class="tv-kpi-submetric-label">Dwell</span><span class="tv-kpi-submetric-value">{d.dwell_time_avg:.0f}s</span></div>
                </div>''')
            elif domain == "asset" and hasattr(tv_data, "asset"):
                d = tv_data.asset
                sub_metrics = textwrap.dedent(f'''\
                <div class="tv-kpi-submetrics">
                  <div class="tv-kpi-submetric"><span class="tv-kpi-submetric-label">Backlog</span><span class="tv-kpi-submetric-value">{d.backlog_total}</span></div>
                  <div class="tv-kpi-submetric"><span class="tv-kpi-submetric-label">Sensors</span><span class="tv-kpi-submetric-value">{d.sensor_healthy}/{d.gates_total}</span></div>
                </div>''')
            elif domain == "climate" and hasattr(tv_data, "climate"):
                d = tv_data.climate
                sub_metrics = textwrap.dedent(f'''\
                <div class="tv-kpi-submetrics">
                  <div class="tv-kpi-submetric"><span class="tv-kpi-submetric-label">Flood Risk</span><span class="tv-kpi-submetric-value">{d.flood_risk:.0f}%</span></div>
                  <div class="tv-kpi-submetric"><span class="tv-kpi-submetric-label">Adaptation</span><span class="tv-kpi-submetric-value">{d.adaptation_readiness_pct:.0f}%</span></div>
                </div>''')

        with cols[idx]:
            st.markdown(f"""            <div class="tv-kpi-card-modern tv-{domain}">
              <div class="tv-kpi-header-row">
                <span class="tv-kpi-icon-wrap">
                  <span class="tv-kpi-domain-icon">{meta['icon']}</span>
                  <span class="tv-kpi-domain-label">{meta['short']}</span>
                </span>
                <span class="tv-kpi-trend-badge {trend}">{trend_arrow} {abs(score - 50):.1f}</span>
              </div>
              <div class="tv-kpi-value">{score:.1f}</div>
              <div class="tv-kpi-sub">{meta['label']}</div>
              {sub_metrics}
            </div>
            """, unsafe_allow_html=True)


def _chart_info_bar(domain: str, tv_data: TotalVisionData) -> str:
    """Generate a compact info bar with contextual metrics."""
    meta = DOMAIN_META.get(domain)
    if meta is None:
        return '<div class="tv-chart-info-bar unknown"></div>'
    color = DOMAIN_COLORS.get(domain, "#f59e0b")

    # Get domain-specific metrics
    chips = []
    if domain == "security":
        d = tv_data.security
        chips = [
            ("Threat", f"{d.threat_level:.0f}"),
            ("Cyber Inc.", str(d.incidents_cyber)),
            ("Response", f"{d.avg_response_time:.1f}m"),
        ]
    elif domain == "sustain":
        d = tv_data.sustainability
        chips = [
            ("Energy", f"{d.energy_kwh:.0f} kWh"),
            ("Carbon", f"{d.carbon_tco2e:.2f} t"),
            ("Green", f"{d.green_energy_pct:.0f}%"),
        ]
    elif domain == "passenger":
        d = tv_data.passenger
        chips = [
            ("Satisfaction", f"{d.satisfaction_score:.0f}%"),
            ("Crowding", f"{d.crowding_index:.0f}%"),
            ("Dwell", f"{d.dwell_time_avg:.0f}s"),
        ]
    elif domain == "asset":
        d = tv_data.asset
        chips = [
            ("RUL", f"{d.fleet_rul_pct:.0f}%"),
            ("Backlog", str(d.backlog_total)),
            ("Sensors", f"{d.sensor_healthy}/{d.gates_total}"),
        ]
    elif domain == "climate":
        d = tv_data.climate
        chips = [
            ("Resilience", f"{d.resilience_score:.0f}%"),
            ("Flood Risk", f"{d.flood_risk:.0f}%"),
            ("Adaptation", f"{d.adaptation_readiness_pct:.0f}%"),
        ]

    chip_html = "".join(
        f'<span class="tv-chart-info-chip"><span class="chip-label">{l}</span> <span class="chip-value">{v}</span></span>'
        for l, v in chips
    )
    return f'<div class="tv-chart-info-bar {domain}">{chip_html}</div>'


def render_tv(df: pd.DataFrame = None):
    """
    Main TotalVision renderer — called from app.py.

    Generates all domain data, renders KPI cards, charts with info bars,
    and the what-if scenario simulator.
    """
    st.markdown('<div class="tv-section">', unsafe_allow_html=True)

    # ── Section Header ──
    st.markdown("""
    <div class="tv-section-header">
      <span class="tv-section-icon">🧠</span>
      <div class="tv-section-title">TotalVision — Cross-Domain Intelligence Hub</div>
      <div class="tv-section-subtitle">Security · Sustainability · Passenger · Asset · Climate</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Initialize Engine ──
    engine = TotalVisionDataEngine(df)
    with st.spinner("Generating cross-domain intelligence data..."):
        tv_all = engine.generate_all()
        correlations = engine.correlate(tv_all)
        agg_scores = TotalVisionDataEngine.aggregate_scores(tv_all)

    # ── Station Selector ──
    station_name = st.selectbox(
        "Select Station", STATIONS,
        key="tv_station",
        label_visibility="collapsed",
    )
    tv_data = tv_all.get(station_name, list(tv_all.values())[0])
    station_scores = tv_data.scores_dict()

    # ── Summary Bar ──
    summary_chips = "".join(
        f'<div class="tv-summary-stat"><span class="tv-summary-stat-value" style="color:{DOMAIN_COLORS[d]}">{station_scores[d]:.0f}</span><span class="tv-summary-stat-label">{DOMAIN_META[d]["short"]}</span></div>'
        for d in DOMAINS
    )
    st.markdown(f'<div class="tv-summary-bar">{summary_chips}</div>', unsafe_allow_html=True)

    # ── KPI Row ──
    _render_kpi_row(station_scores, tv_data)

    # ── Charts Row 1: Gauges (5 cols) ──
    st.markdown('<div class="tv-section-heading">Domain Health Gauges</div>', unsafe_allow_html=True)
    cols = st.columns(5)
    for idx, domain in enumerate(DOMAINS):
        with cols[idx]:
            color = DOMAIN_COLORS.get(domain, "#f59e0b")
            gauge = _make_domain_gauge(
                station_scores[domain],
                DOMAIN_META[domain]["label"],
                color,
            )
            st.plotly_chart(gauge, use_container_width=True, key=f"tv_gauge_{domain}")

    # ── Charts Row 2: Radar + Comparison (2 cols) ──
    cols = st.columns(2)
    with cols[0]:
        st.markdown(f'<div class="tv-panel"><div class="tv-panel-header"><div class="tv-panel-title">Score Profile — Network Average</div></div><div class="tv-panel-content">', unsafe_allow_html=True)
        st.markdown(_chart_info_bar("security", tv_data), unsafe_allow_html=True)
        radar = _make_radar_chart(agg_scores, "Score Profile")
        st.plotly_chart(radar, use_container_width=True, key="tv_radar")
        st.markdown('</div></div>', unsafe_allow_html=True)

    with cols[1]:
        # Cross-domain comparison: station vs network average
        fig = go.Figure()
        categories = [DOMAIN_META[d]["short"] for d in DOMAINS]
        station_vals = [station_scores.get(d, 50) for d in DOMAINS]
        avg_vals = [agg_scores.get(d, 50) for d in DOMAINS]

        fig.add_trace(go.Scatterpolar(
            r=station_vals + station_vals[:1],
            theta=categories + categories[:1],
            fill="toself",
            name=station_name,
            fillcolor="rgba(245,158,11,0.12)",
            line=dict(color="#f59e0b", width=2.5),
            hovertemplate="%{theta}: %{r:.1f}<extra>" + station_name + "</extra>",
        ))
        fig.add_trace(go.Scatterpolar(
            r=avg_vals + avg_vals[:1],
            theta=categories + categories[:1],
            fill="toself",
            name="Network Avg",
            fillcolor="rgba(148,163,184,0.08)",
            line=dict(color="#94a3b8", width=2, dash="dot"),
            hovertemplate="%{theta}: %{r:.1f}<extra>Network Avg</extra>",
        ))
        fig.update_layout(
            height=240,
            margin=dict(l=40, r=40, t=25, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={"color": "#94a3b8", "size": 9},
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100], color="#475569", gridcolor="rgba(255,255,255,0.05)"),
                angularaxis=dict(color="#94a3b8", gridcolor="rgba(255,255,255,0.05)"),
                bgcolor="rgba(0,0,0,0)",
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.25,
                xanchor="center",
                x=0.5,
                font=dict(size=9, color="#94a3b8"),
            ),
        )
        st.markdown(f'<div class="tv-panel"><div class="tv-panel-header"><div class="tv-panel-title">Station vs Network Average</div></div><div class="tv-panel-content">', unsafe_allow_html=True)
        st.markdown(_chart_info_bar("passenger", tv_data), unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True, key="tv_compare_radar")
        st.markdown('</div></div>', unsafe_allow_html=True)

    # ── All-Stations Rankings ──
    st.markdown('<div class="tv-section-heading">Station Rankings by Domain</div>', unsafe_allow_html=True)
    cols = st.columns(5)
    for idx, domain in enumerate(DOMAINS):
        with cols[idx]:
            color = DOMAIN_COLORS.get(domain, "#f59e0b")
            st.markdown(f'<div class="tv-panel"><div class="tv-panel-header"><div class="tv-panel-title">{DOMAIN_META[domain]["label"]}</div></div><div class="tv-panel-content">', unsafe_allow_html=True)
            st.markdown(_chart_info_bar(domain, tv_data), unsafe_allow_html=True)
            bar = _make_all_stations_bar(tv_all, domain, color)
            st.plotly_chart(bar, use_container_width=True, key=f"tv_rank_{domain}")
            st.markdown('</div></div>', unsafe_allow_html=True)

    # ── Station Ranking Table ──
    st.markdown('<div class="tv-section-heading">🏆 Station Score Comparison</div>', unsafe_allow_html=True)
    # Build ranking data: for each station, compute overall score = avg of all domains
    ranking_rows = []
    for s in STATIONS:
        if s not in tv_all:
            continue
        sd = tv_all[s].scores_dict()
        overall = sum(sd.get(d, 0) for d in DOMAINS) / len(DOMAINS)
        ranking_rows.append({
            "station": s,
            "overall": round(overall, 1),
            **{d: round(sd.get(d, 0), 1) for d in DOMAINS},
        })
    ranking_rows.sort(key=lambda r: r["overall"], reverse=True)

    # Generate ranking table HTML
    rank_icons = ["🥇", "🥈", "🥉"]
    rows_html = []
    max_score = max((r["overall"] for r in ranking_rows), default=100)
    for i, r in enumerate(ranking_rows[:10]):  # Top 10
        rank = i + 1
        medal = f'<span class="tv-rank-badge gold">{rank_icons[i]}</span>' if i < 3 else f'<span class="tv-rank-number">#{rank}</span>'
        bar_width = max(4, int((r["overall"] / max(max_score, 1)) * 120))
        rows_html.append(f"""<tr>
          <td>{medal}</td>
          <td><strong>{r['station']}</strong></td>
          <td style="font-weight:700;font-family:var(--font-mono);color:var(--text-primary)">{r['overall']}</td>
          {''.join(f'<td style="font-family:var(--font-mono);color:var(--text-secondary)">{r[d]:.0f}</td>' for d in DOMAINS)}
          <td><span class="tv-score-bar" style="width:{bar_width}px;background:linear-gradient(90deg,var(--color-primary),var(--color-secondary))"></span></td>
        </tr>""")

    rows_joined = "\n".join(rows_html)
    table_html = f'''
    <div class="tv-panel">
      <div class="tv-panel-header">
        <div class="tv-panel-title">Top 10 Stations — Overall Score</div>
        <span class="tv-section-badge">Network-wide</span>
      </div>
      <div class="tv-panel-content">
        <div class="tv-rank-table-wrapper">
          <table class="tv-rank-table">
            <thead>
              <tr>
                <th style="width:36px">Rank</th>
                <th>Station</th>
                <th>Overall</th>
                <th>SEC</th><th>SUS</th><th>PAS</th><th>AST</th><th>CLM</th>
                <th>Score</th>
              </tr>
            </thead>
            <tbody>
              {rows_joined}
            </tbody>
          </table>
        </div>
      </div>
    </div>
    '''
    st.markdown(table_html, unsafe_allow_html=True)

    # ── Score Distribution Across Network ──
    st.markdown('<div class="tv-section-heading">📊 Score Distribution Across Network</div>', unsafe_allow_html=True)
    cols = st.columns(3)
    with cols[0]:
        st.markdown(f'<div class="tv-panel"><div class="tv-panel-header"><div class="tv-panel-title">Box Plot — Score Distribution</div></div><div class="tv-panel-content">', unsafe_allow_html=True)
        st.plotly_chart(_make_box_plot(tv_all), use_container_width=True, key="tv_box")
        st.markdown('</div></div>', unsafe_allow_html=True)
    with cols[1]:
        st.markdown(f'<div class="tv-panel"><div class="tv-panel-header"><div class="tv-panel-title">Violin Plot — Density View</div></div><div class="tv-panel-content">', unsafe_allow_html=True)
        st.plotly_chart(_make_violin_plot(tv_all), use_container_width=True, key="tv_violin")
        st.markdown('</div></div>', unsafe_allow_html=True)
    with cols[2]:
        st.markdown(f'<div class="tv-panel"><div class="tv-panel-header"><div class="tv-panel-title">Histogram — Score Frequency</div></div><div class="tv-panel-content">', unsafe_allow_html=True)
        st.plotly_chart(_make_histogram(tv_all), use_container_width=True, key="tv_hist")
        st.markdown('</div></div>', unsafe_allow_html=True)

    # ── Correlation Findings ──
    findings = correlations.get("findings", [])
    if findings:
        st.markdown('<div class="tv-section-heading">🔍 Auto-Discovered Insights</div>', unsafe_allow_html=True)
        for f in findings:
            direction_icon = "📈" if f["direction"] == "positive" else "📉"
            strength_label = f["strength"].upper()
            border_class = "positive" if f["direction"] == "positive" else "negative"

            # Color-code p-value
            p_val = f.get("p_value", 1.0)
            p_confidence = "High" if p_val < 0.05 else "Moderate" if p_val < 0.1 else "Low"

            st.markdown(f"""
            <div class="tv-insight-callout {border_class}">
              <span class="tv-insight-icon">{direction_icon}</span>
              <div class="tv-insight-text">
                <strong>{strength_label} {f['direction'].title()} Correlation</strong> —
                {f['story']}
                <div class="tv-insight-meta">
                  <span class="tv-insight-strength {f['strength']}">{strength_label}</span>
                  <span>r = {f['r_value']:.3f}</span>
                  <span>p = {p_val:.4f}</span>
                  <span>Confidence: {p_confidence}</span>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Advanced Domain Visualizations ──
    st.markdown('<div class="tv-section-heading">🔬 Advanced Domain Visualizations</div>', unsafe_allow_html=True)
    cols = st.columns(3)
    with cols[0]:
        st.markdown(f'<div class="tv-panel"><div class="tv-panel-header"><div class="tv-panel-title">Scatter Bubble — Security vs Asset (size = Climate)</div></div><div class="tv-panel-content">', unsafe_allow_html=True)
        st.plotly_chart(_make_scatter_bubble(tv_all, "security", "asset", "climate"), use_container_width=True, key="tv_bubble")
        st.markdown('</div></div>', unsafe_allow_html=True)
    with cols[1]:
        st.markdown(f'<div class="tv-panel"><div class="tv-panel-header"><div class="tv-panel-title">Treemap — Station Scores by Domain</div></div><div class="tv-panel-content">', unsafe_allow_html=True)
        st.plotly_chart(_make_treemap(tv_all), use_container_width=True, key="tv_treemap")
        st.markdown('</div></div>', unsafe_allow_html=True)
    with cols[2]:
        st.markdown(f'<div class="tv-panel"><div class="tv-panel-header"><div class="tv-panel-title">Sunburst — Domain Hierarchy</div></div><div class="tv-panel-content">', unsafe_allow_html=True)
        st.plotly_chart(_make_sunburst(tv_all), use_container_width=True, key="tv_sunburst")
        st.markdown('</div></div>', unsafe_allow_html=True)

    # Full-width Parallel Coordinates
    st.markdown(f'<div class="tv-panel"><div class="tv-panel-header"><div class="tv-panel-title">🔗 Parallel Coordinates — Multi-Domain Station Profile</div></div><div class="tv-panel-content">', unsafe_allow_html=True)
    st.plotly_chart(_make_parallel_coords(tv_all), use_container_width=True, key="tv_parallel")
    st.markdown('</div></div>', unsafe_allow_html=True)

    # Full-width Deviation Heatmap
    st.markdown(f'<div class="tv-panel"><div class="tv-panel-header"><div class="tv-panel-title">📊 Station Performance vs Network Average</div></div><div class="tv-panel-content">', unsafe_allow_html=True)
    st.plotly_chart(_make_deviation_heatmap(tv_all), use_container_width=True, key="tv_deviation")
    st.markdown('</div></div>', unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════
    # WHAT-IF SCENARIO SIMULATOR
    # ═══════════════════════════════════════════════════════════
    st.markdown("""
    <div class="tv-whatif-section">
      <div class="tv-whatif-header">
        <span class="tv-whatif-header-icon">🔮</span>
        <div class="tv-whatif-header-title">What-If Scenario Simulator</div>
        <div class="tv-whatif-header-sub">Adjust levers to project outcomes</div>
      </div>
      <div class="tv-whatif-body">
    """, unsafe_allow_html=True)

    # Sliders in 2 rows
    row1_c, row2_c = st.columns([1, 1])
    with row1_c:
        invest = st.slider("Investment Level", 0.5, 2.0, 1.0, 0.1, key="tv_wi_invest",
                           help="Overall infrastructure investment multiplier")
        maint = st.slider("Maintenance Cadence", 1, 12, 6, 1, key="tv_wi_maint",
                          help="Months between maintenance cycles")
        green = st.slider("Green Budget", 0.0, 5.0, 1.0, 0.1, key="tv_wi_green",
                          help="Sustainability budget multiplier (× baseline)")
    with row2_c:
        staffing = st.slider("Security Staffing", 50, 200, 100, 10, key="tv_wi_staff",
                             help="Security staffing level %")
        climate_fund = st.slider("Climate Fund", 0.0, 5.0, 1.0, 0.1, key="tv_wi_climate",
                                 help="Climate adaptation fund multiplier (× baseline)")

    params = {
        "investment_level": invest,
        "maintenance_cadence": float(maint),
        "green_budget": green * 1_000_000,
        "security_staffing": float(staffing),
        "climate_fund": climate_fund * 2_000_000,
    }

    projection = engine.project(params, tv_all)
    projected = projection.get("projected_scores", {})
    baseline = projection.get("baseline_scores", {})
    deltas = projection.get("deltas", {})
    timeline = projection.get("timeline", [])

    st.markdown('<div class="tv-whatif-results">', unsafe_allow_html=True)
    for domain in DOMAINS:
        meta = DOMAIN_META[domain]
        color = DOMAIN_COLORS.get(domain, "#f59e0b")
        base = baseline.get(domain, 50)
        proj = projected.get(domain, 50)
        delta = deltas.get(domain, 0)
        delta_class = "positive" if delta >= 0 else "negative"

        # Parse hex to RGB for CSS custom properties
        hex_clean = color.lstrip("#")
        r, g, b = int(hex_clean[0:2], 16), int(hex_clean[2:4], 16), int(hex_clean[4:6], 16)

        bar_pct = min(max(proj, 2), 100)

        st.markdown(f"""
        <div class="tv-whatif-result-card" style="--card-r:{r};--card-g:{g};--card-b:{b};">
          <div class="tv-whatif-result-header">
            <span class="tv-whatif-result-icon">{meta['icon']}</span>
            <span class="tv-whatif-result-label">{meta['short']}</span>
          </div>
          <div class="tv-whatif-result-body">
            <div class="tv-whatif-result-scores">
              <span class="tv-whatif-result-current">{base:.0f}</span>
              <span class="tv-whatif-result-arrow">→</span>
              <span class="tv-whatif-result-projected">{proj:.0f}</span>
            </div>
            <div class="tv-whatif-result-bar">
              <div class="tv-whatif-result-bar-track">
                <div class="tv-whatif-result-bar-fill" style="width:{bar_pct:.0f}%"></div>
              </div>
            </div>
          </div>
          <div class="tv-whatif-result-footer">
            <span class="tv-whatif-result-delta {delta_class}">
              <span class="tv-whatif-delta-arrow">{'↑' if delta >= 0 else '↓'}</span>
              {abs(delta):.1f}
            </span>
            <span class="tv-whatif-result-tag">{'improvement' if delta >= 0 else 'decline'}</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # close whatif-results

    # ── What-If Projection Trend Chart ──
    if timeline:
        st.markdown('<div class="tv-whatif-chart">', unsafe_allow_html=True)
        fig = go.Figure()
        for domain in DOMAINS:
            color = DOMAIN_COLORS.get(domain, "#f59e0b")
            vals = [m.get(domain, 50) for m in timeline]
            fig.add_trace(go.Scatter(
                x=[m["month"] for m in timeline],
                y=vals,
                mode="lines+markers",
                name=DOMAIN_META[domain]["short"],
                line=dict(color=color, width=2.5),
                marker=dict(size=4, color=color),
                hovertemplate="Month %{x}: %{y:.1f}<extra>" + DOMAIN_META[domain]["label"] + "</extra>",
            ))
        fig.update_layout(
            height=220,
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={"color": "#94a3b8", "size": 9},
            xaxis=dict(
                title="Month",
                showgrid=True,
                gridcolor="rgba(255,255,255,0.04)",
                color="#64748b",
                tickfont={"size": 8},
                dtick=3,
            ),
            yaxis=dict(
                title="Score",
                range=[0, 100],
                showgrid=True,
                gridcolor="rgba(255,255,255,0.04)",
                color="#64748b",
                tickfont={"size": 8},
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.35,
                xanchor="center",
                x=0.5,
                font=dict(size=9, color="#94a3b8"),
            ),
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True, key="tv_wi_trend")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div></div>', unsafe_allow_html=True)  # close whatif-body + whatif-section

    # ── Scenario Deep Dive Visuals ──
    st.markdown('<div class="tv-section-heading">🎯 Scenario Deep Dive</div>', unsafe_allow_html=True)

    # Full-width Bullet Chart: station scores vs network targets
    st.markdown(f'<div class="tv-panel"><div class="tv-panel-header"><div class="tv-panel-title">🎯 Bullet Chart — {station_name} vs Network Target</div></div><div class="tv-panel-content">', unsafe_allow_html=True)
    st.plotly_chart(_make_bullet_chart(station_scores, agg_scores), use_container_width=True, key="tv_bullet")
    st.markdown('</div></div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # close tv-section
