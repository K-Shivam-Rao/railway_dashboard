"""Chart export utilities — PNG image and CSV data download helpers.

Provides a single ``render_chart()`` function that wraps ``st.plotly_chart``
with compact export buttons (PNG via Plotly's ``to_image``, CSV via trace data
extraction). Also exposes ``extract_chart_data`` and ``chart_to_csv`` for
standalone use.
"""

import io
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from utils.helpers import convert_to_csv


# ── Public API ────────────────────────────────────────────────────────────

# Auto-incrementing counter to guarantee unique internal Streamlit keys.
# This prevents StreamlitDuplicateElementKey errors even if the same
# ``key`` value is passed to multiple ``render_chart`` calls.
_chart_key_counter: int = 0


def _next_key_suffix() -> str:
    """Return a unique numeric suffix for internal Streamlit keys."""
    global _chart_key_counter
    _chart_key_counter += 1
    return f"_auto{_chart_key_counter}"


def render_chart(
    fig,
    key: str,
    title: str | None = None,
    *,
    use_container_width: bool = True,
    enable_png: bool = True,
    enable_csv: bool = True,
    png_scale: int = 2,
    png_width: int = 1200,
    csv_filename: str | None = None,
    png_filename: str | None = None,
) -> None:
    """Render a Plotly figure with compact PNG / CSV export buttons below it.

    Parameters
    ----------
    fig : go.Figure
        The Plotly figure to display.
    key : str
        Descriptive key for identifying the chart (used as a base for internal
        Streamlit widget keys; an auto-incrementing suffix guarantees uniqueness).
    title : str, optional
        Optional heading shown above the chart.
    use_container_width : bool
        Passed through to ``st.plotly_chart``.
    enable_png : bool
        Show a PNG download button.
    enable_csv : bool
        Show a CSV data download button.
    png_scale : int
        Resolution multiplier for the PNG export (2 = Retina).
    png_width : int
        Pixel width for the exported PNG.
    csv_filename : str, optional
        Override auto-generated CSV filename.
    png_filename : str, optional
        Override auto-generated PNG filename.
    """
    anchor = key.replace(" ", "_").replace(".", "_")
    # Guarantee unique internal keys via auto-incrementing suffix
    unique_suffix = _next_key_suffix()
    internal_anchor = f"{anchor}{unique_suffix}"

    # Optional title
    if title:
        st.html(f"<div class='chart-export-title'>{title}</div>")

    # Render the chart with a modebar that only shows the camera
    _render_figure(fig, internal_anchor, use_container_width)

    # Export toolbar
    _render_toolbar(
        fig=fig,
        anchor=internal_anchor,
        enable_png=enable_png,
        enable_csv=enable_csv,
        png_scale=png_scale,
        png_width=png_width,
        csv_filename=csv_filename,
        png_filename=png_filename,
    )


# ── Trace data extraction ─────────────────────────────────────────────────


def extract_chart_data(fig: go.Figure) -> pd.DataFrame:
    """Extract visible trace data from a Plotly figure into a DataFrame.

    Works with most common trace types (scatter, bar, pie, heatmap, etc.).
    Uses ``getattr`` for attribute access so non-cartesian trace types
    (indicator, table, sankey, etc.) are safely skipped.

    Pie traces produce ``label`` / ``value`` columns; cartesian traces
    produce ``x`` / ``y`` / ``name`` / ``label``.
    """
    rows: list[dict] = []
    for trace in fig.data:
        if not _trace_visible(trace):
            continue
        if trace.type == "pie":
            labels = list(trace.labels) if trace.labels is not None else []
            values = list(trace.values) if trace.values is not None else []
            for label, value in zip(labels, values):
                rows.append({"label": label, "value": value, "series": trace.name or ""})
        else:
            # Use getattr for safety — indicator, table, sankey, etc.
            # don't have .x/.y and should be skipped gracefully.
            xs = _iter(getattr(trace, "x", None))
            ys = _iter(getattr(trace, "y", None))
            if not xs and not ys:
                continue  # skip non-cartesian traces
            texts = _iter(getattr(trace, "text", None))
            labels = _iter(getattr(trace, "hovertext", None))
            series = trace.name or ""
            max_len = max(len(xs), len(ys), 1)
            for i in range(max_len):
                rows.append({
                    "x": xs[i] if i < len(xs) else None,
                    "y": ys[i] if i < len(ys) else None,
                    "text": texts[i] if i < len(texts) else None,
                    "label": labels[i] if i < len(labels) else None,
                    "series": series,
                })
    return pd.DataFrame(rows)


def chart_to_csv(fig: go.Figure) -> bytes:
    """Convert trace data from a Plotly figure to CSV bytes."""
    df = extract_chart_data(fig)
    if df.empty:
        return b""
    return convert_to_csv(df)


# ── Internal helpers ──────────────────────────────────────────────────────


_PLOTLY_EXPORT_CONFIG = {
    "displayModeBar": True,
    "modeBarButtonsToRemove": [
        "zoom2d", "pan2d", "select2d", "lasso2d",
        "zoomIn2d", "zoomOut2d", "autoScale2d", "resetScale2d",
        "hoverClosestCartesian", "hoverCompareCartesian",
        "toggleSpikelines", "resetViews",
    ],
    "modeBarButtonsToAdd": [],
    "displaylogo": False,
    "responsive": True,
    "scrollZoom": True,
}


def _render_figure(fig: go.Figure, anchor: str, use_container_width: bool) -> None:
    """Render the main Plotly figure."""
    st.plotly_chart(
        fig,
        use_container_width=use_container_width,
        config=_PLOTLY_EXPORT_CONFIG,
        key=f"chart_{anchor}",
    )


def _render_toolbar(
    fig: go.Figure,
    anchor: str,
    enable_png: bool,
    enable_csv: bool,
    png_scale: int,
    png_width: int,
    csv_filename: str | None,
    png_filename: str | None,
) -> None:
    """Render a compact export button bar below the chart."""
    actions = []

    if enable_csv:
        try:
            csv_bytes = chart_to_csv(fig)
            if csv_bytes:
                fname = csv_filename or f"chart_data_{anchor}.csv"
                actions.append(("CSV", csv_bytes, fname, "text/csv"))
        except Exception:
            pass  # silently skip CSV if data extraction fails

    if enable_png:
        try:
            png_bytes = fig.to_image(
                format="png",
                width=png_width,
                scale=png_scale,
            )
            fname = png_filename or f"chart_{anchor}.png"
            actions.append(("PNG", png_bytes, fname, "image/png"))
        except Exception:
            pass  # silently skip if export fails

    if not actions:
        return

    cols = st.columns([max(1, 6 - len(actions) * 2)] + [2] * len(actions))
    _label_for = {"PNG": "📷 PNG", "CSV": "📊 CSV"}

    for col_idx, (fmt, data, fname, mime) in enumerate(actions):
        ci = col_idx + 1  # offset by spacer column
        with cols[ci]:
            st.download_button(
                label=_label_for.get(fmt, fmt),
                data=data,
                file_name=fname,
                mime=mime,
                key=f"dl_{anchor}_{fmt.lower()}",
                use_container_width=True,
                help=f"Download as {fmt}",
            )


def _trace_visible(trace) -> bool:
    """Check whether a trace is visible (not explicitly hidden)."""
    return trace.visible is None or trace.visible is True or trace.visible == "True"


def _iter(v):
    """Safely iterate over a Plotly array attribute (handles lists, tuples,
    numpy arrays, pandas Series, and scalars)."""
    if v is None:
        return []
    # Built-in sequence types
    if isinstance(v, (list, tuple)):
        return list(v)
    # Array-like (numpy, pandas, etc.) — convertible via list()
    try:
        return list(v)
    except TypeError:
        # Scalar value — wrap in a single-element list
        return [v]
