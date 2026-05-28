_BASE_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#c4c2d2", size=13, family="Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"),
    hovermode="x unified",
    hoverlabel=dict(
        bgcolor="rgba(10,15,36,0.92)",
        bordercolor="rgba(148,163,184,0.25)",
        font=dict(color="#f1f0f5", size=13, family="Inter, sans-serif"),
    ),
    # ── Legend: dark glass panel, right-aligned, readable ──
    legend=dict(
        x=0.98,
        y=0.98,
        xanchor="right",
        yanchor="top",
        bgcolor="rgba(10,15,36,0.75)",
        bordercolor="rgba(148,163,184,0.15)",
        borderwidth=1,
        font=dict(color="#c4c2d2", size=12, family="Inter, sans-serif"),
        title=dict(font=dict(color="#f1f0f5", size=12, family="Inter, sans-serif")),
        itemclick="toggleothers",
        itemdoubleclick="toggle",
        tracegroupgap=4,
    ),
    # ── Spacious margins — chart needs breathing room ──
    margin=dict(l=60, r=24, t=50, b=50, pad=4),
    # ── Colorbar: thin, well-positioned, readable ──
    coloraxis_colorbar=dict(
        thickness=10,
        len=0.55,
        x=1.015,
        tickfont=dict(size=11, color="#c4c2d2"),
        title=dict(font=dict(size=11, color="#c4c2d2")),
    ),
)


def style_chart(fig, **kwargs):
    fig.update_layout(**_BASE_LAYOUT)
    fig.update_xaxes(
        gridcolor="rgba(255,255,255,0.06)",
        zeroline=False,
        zerolinecolor="rgba(255,255,255,0.08)",
        showline=False,
        automargin=True,
        tickfont=dict(color="#848298", size=12, family="Inter, sans-serif"),
        title=dict(font=dict(color="#c4c2d2", size=13, family="Inter, sans-serif")),
    )
    fig.update_yaxes(
        gridcolor="rgba(255,255,255,0.06)",
        zeroline=False,
        zerolinecolor="rgba(255,255,255,0.08)",
        showline=False,
        automargin=True,
        tickfont=dict(color="#848298", size=12, family="Inter, sans-serif"),
        title=dict(font=dict(color="#c4c2d2", size=13, family="Inter, sans-serif")),
    )
    if kwargs:
        layout_kwargs = dict(kwargs)
        if "legend" in layout_kwargs and layout_kwargs["legend"] is False:
            layout_kwargs["showlegend"] = False
            del layout_kwargs["legend"]
        elif "legend" in layout_kwargs and layout_kwargs["legend"] is True:
            layout_kwargs["showlegend"] = True
            del layout_kwargs["legend"]
        if "hovermode" in layout_kwargs:
            # Allow explicit hovermode override
            pass
        fig.update_layout(**layout_kwargs)
    return fig


def style_pie(fig, title=None, height=None):
    # Apply base layout first, then override pie-specific settings
    fig.update_layout(**_BASE_LAYOUT)
    fig.update_layout(
        dragmode=False,
        showlegend=True,
        margin=dict(t=title and 50 or 20, b=20, l=20, r=100),
        hovermode="closest",
        legend=dict(
            x=1.02,
            y=0.5,
            xanchor="left",
            yanchor="middle",
            bgcolor="rgba(10,15,36,0.7)",
            bordercolor="rgba(148,163,184,0.12)",
            borderwidth=1,
            font=dict(color="#c4c2d2", size=12),
            itemclick=False,
            itemdoubleclick=False,
        ),
    )
    if height is not None:
        fig.update_layout(height=height)
    fig.update_traces(
        marker=dict(line=dict(color="rgba(15,21,40,0.4)", width=2)),
        hovertemplate="<b>%{label}</b><br>"
                       "Count: %{value}<br>"
                       "Share: %{percent}<extra></extra>",
        textfont=dict(color="#f1f0f5", size=12, family="Inter, sans-serif"),
    )
    # Pie-only properties applied via selector to avoid ``ValueError``
    # on non-pie trace types (e.g. Scatter in tests).
    fig.update_traces(
        selector=dict(type="pie"),
        insidetextfont=dict(color="#f1f0f5", size=12, family="Inter, sans-serif"),
    )
    if title:
        fig.add_annotation(
            x=0.02, y=1.05, xref="paper", yref="paper",
            text=f"<b>{title}</b>",
            showarrow=False, font=dict(size=15, color="#f1f0f5", family="Inter, sans-serif"),
            xanchor="left",
        )
    return fig


def style_indicator(fig, height=400):
    style_chart(fig)
    fig.update_layout(height=height)
    return fig


def style_df(df, **css):
    try:
        return df.style
    except Exception:
        return df


COLOR_SCHEMES = {
    "status_reverse": ["#ef4444", "#f59e0b", "#10b981"],
    "blue": ["#1e3a5f", "#2563eb", "#3b82f6", "#60a5fa", "#93c5fd"],
    "teal": ["#134e4a", "#0d9488", "#06b6d4", "#22d3ee", "#67e8f9"],
    "amber": ["#78350f", "#d97706", "#f59e0b", "#fbbf24", "#fcd34d"],
    "fuchsia": ["#4a044e", "#a21caf", "#d946ef", "#e879f9", "#f5d0fe"],
    "kpi": ["#f59e0b", "#d946ef", "#06b6d4"],
    "aurora": ["#f59e0b", "#d946ef", "#06b6d4", "#3b82f6", "#10b981"],
    "status_continuous": [[0, "#ef4444"], [0.5, "#f59e0b"], [1, "#10b981"]],
}
