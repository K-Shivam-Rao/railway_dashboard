import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from io import BytesIO, StringIO
import base64
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import SaaSModelConfig, run_simulation, visualize_results, visualize_dashboard_1, visualize_dashboard_2, print_summary

st.set_page_config(
    layout="wide",
    page_title="SaaS Financial Dashboard - Backend Simulator",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');
    
    html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        background: #0a0f1e !important;
        color: #e2e8f0;
        font-family: 'Space Grotesk', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #0d1b3e 0%, #0a1628 100%);
        border: 1px solid #1e2d4d;
        border-radius: 14px;
        padding: 22px 28px;
        margin-bottom: 22px;
    }
    .header-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: #e2e8f0;
        margin: 0;
    }
    .header-sub {
        font-family: 'IBM Plex Mono';
        font-size: 0.75rem;
        color: #4a6fa5;
        margin-top: 4px;
    }
    
    .section-heading {
        font-size: 1rem;
        font-weight: 700;
        color: #7ab3d4;
        letter-spacing: 0.5px;
        margin-bottom: 14px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .section-heading::after {
        content: '';
        flex: 1;
        height: 1px;
        background: #1a2d50;
    }
    
    .metric-card {
        background: #0d1b3e;
        border: 1px solid #1e2d4d;
        border-radius: 12px;
        padding: 18px 20px;
        position: relative;
        overflow: hidden;
    }
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #0288d1, #00b4d8);
    }
    .metric-card.green::before {
        background: linear-gradient(90deg, #10b981, #34d399);
    }
    .metric-card.alert::before {
        background: linear-gradient(90deg, #ef4444, #f97316);
    }
    .metric-card.optimistic::before {
        background: linear-gradient(90deg, #10b981, #34d399);
    }
    .metric-card.pessimistic::before {
        background: linear-gradient(90deg, #ef4444, #f97316);
    }
    .metric-card.sensitivity::before {
        background: linear-gradient(90deg, #8b5cf6, #a78bfa);
    }
    .metric-title {
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: #4a6fa5;
        margin-bottom: 10px;
    }
    .metric-value {
        font-family: 'IBM Plex Mono';
        font-size: 1.8rem;
        font-weight: 600;
        color: #e2e8f0;
        line-height: 1;
    }
    .metric-sub {
        font-size: 0.72rem;
        color: #4a6fa5;
        margin-top: 6px;
        font-family: 'IBM Plex Mono';
    }
    
    [data-testid="stDataFrame"] {
        border: 1px solid #1e2d4d !important;
        border-radius: 10px !important;
    }
    
    [data-testid="stExpander"] {
        background: #0d1b3e !important;
        border: 1px solid #1e2d4d !important;
        border-radius: 10px !important;
    }
    
    [data-testid="stSlider"] {
        padding-top: 8px;
    }
    
    .scenario-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.7rem;
        font-family: 'IBM Plex Mono';
        font-weight: 600;
        letter-spacing: 1px;
    }
    .badge-optimistic {
        background: rgba(16,185,129,0.15);
        border: 1px solid #10b981;
        color: #10b981;
    }
    .badge-base {
        background: rgba(41,128,185,0.15);
        border: 1px solid #2980b9;
        color: #2980b9;
    }
    .badge-pessimistic {
        background: rgba(239,68,68,0.15);
        border: 1px solid #e74c3c;
        color: #e74c3c;
    }
    
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #060c1a; }
    ::-webkit-scrollbar-thumb { background: #1e3060; border-radius: 3px; }
    
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    [data-testid="stToolbar"] { display: none; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <div class="header-title">📊 SaaS Financial Dashboard</div>
    <div class="header-sub">BahnSetu Financial Simulator // Real-Time Analysis</div>
</div>
""", unsafe_allow_html=True)

PLOTLY_DARK = dict(
    plot_bgcolor='#0a1221',
    paper_bgcolor='#0a1221',
    font=dict(color='#7ab3d4', family='IBM Plex Mono', size=11),
    xaxis=dict(gridcolor='#1a2d50', zeroline=False),
    yaxis=dict(gridcolor='#1a2d50', zeroline=False),
    legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(size=10)),
    margin=dict(l=50, r=20, t=40, b=40),
)

def fin_fig(layout_extra=None):
    d = dict(**PLOTLY_DARK)
    if layout_extra:
        d.update(layout_extra)
    return d

@st.cache_data(ttl=0, show_spinner=False)
def run_cached_simulation(starting_customers, monthly_growth_rate, churn_rate, price_per_customer, 
                          fixed_costs, variable_cost, cac_simplified, months, scenario_name):
    config = SaaSModelConfig(
        starting_customers=starting_customers,
        monthly_growth_rate=monthly_growth_rate,
        churn_rate=churn_rate,
        price_per_customer=price_per_customer,
        fixed_costs=fixed_costs,
        variable_cost_per_customer=variable_cost,
        cac_simplified=cac_simplified
    )
    return run_simulation(config, months=months)

@st.cache_data(ttl=300, show_spinner=False)
def get_chart_image(_fig_bytes, chart_name):
    return _fig_bytes

def create_matplotlib_chart(x, y_data, title, labels=None, colors_list=None):
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(12, 6), facecolor='#0a1221')
    ax.set_facecolor('#0a1221')
    
    if isinstance(y_data, dict):
        for i, (name, y) in enumerate(y_data.items()):
            y_arr = np.array(y) if hasattr(y, '__iter__') else y
            c = colors_list[i] if colors_list else None
            ax.plot(x, y_arr, marker='o', linewidth=2.5, label=name, markersize=5)
            if c:
                ax.lines[-1].set_color(c)
    else:
        y_arr = np.array(y_data) if hasattr(y_data, '__iter__') else y_data
        ax.plot(x, y_arr, marker='o', linewidth=3, color='#2980b9', markersize=6)
    
    ax.set_xlabel('Month', color='#7ab3d4', fontsize=12, fontweight='bold')
    ax.set_ylabel('Value', color='#7ab3d4', fontsize=12, fontweight='bold')
    ax.set_title(title, color='#e2e8f0', fontsize=16, fontweight='bold', pad=20)
    ax.tick_params(colors='#7ab3d4', labelsize=10)
    ax.grid(True, alpha=0.15, color='#1a2d50', linestyle='-', linewidth=0.5)
    ax.legend(loc='upper left', framealpha=0.9, facecolor='#1a2d50', edgecolor='#2980b9')
    
    if 'Cash' in title or 'Cash Flow' in title:
        ax.axhline(y=0, color='#e74c3c', linestyle='--', alpha=0.8, linewidth=2)
    
    plt.tight_layout()
    
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=150, facecolor='#0a1221', edgecolor='none', bbox_inches='tight', pad_inches=0.3)
    buf.seek(0)
    plt.close()
    return buf.getvalue()

def create_pdf_buffer(
    df_base, df_opt, df_pess, display_cols, scenario_name, starting_customers,
    monthly_growth_rate, churn_rate, price_per_customer, cac_simplified,
    fixed_costs, variable_cost, simulation_months, show_scenarios,
    fig_customers_bytes, fig_mrr_bytes, fig_cash_bytes, fig_ltv_bytes,
    final_sens, breakeven_opt, breakeven_base, breakeven_pess
):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from io import BytesIO
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=0.5*inch, leftMargin=0.5*inch, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, spaceAfter=20, alignment=TA_CENTER, textColor=colors.HexColor('#0d1b3e'))
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, spaceAfter=10, spaceBefore=15, textColor=colors.HexColor('#2980b9'))
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontSize=10, spaceAfter=5)
    
    def format_breakeven(month):
        return f"Month {int(month)}" if pd.notna(month) else "Not achieved"
    
    elements.append(Paragraph("SaaS Financial Simulation Report", title_style))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"Scenario: {scenario_name}", ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=12, alignment=TA_CENTER, textColor=colors.grey)))
    elements.append(Spacer(1, 20))
    
    elements.append(Paragraph("Model Assumptions", heading_style))
    assumptions_data = [
        ["Parameter", "Value"],
        ["Starting Customers", str(starting_customers)],
        ["Monthly Growth Rate", f"{monthly_growth_rate*100:.0f}%"],
        ["Monthly Churn Rate", f"{churn_rate*100:.0f}%"],
        ["Price per Customer", f"${price_per_customer}"],
        ["CAC", f"${cac_simplified}"],
        ["Fixed Costs", f"${fixed_costs:,}/mo"],
        ["Variable Cost", f"${variable_cost}/customer"],
        ["Simulation Period", f"{simulation_months} months"],
    ]
    assumptions_table = Table(assumptions_data, colWidths=[2.5*inch, 2*inch])
    assumptions_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d1b3e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f5f5f5')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(assumptions_table)
    elements.append(Spacer(1, 20))
    
    if show_scenarios:
        elements.append(Paragraph("3-Way Scenario Comparison Summary", heading_style))
        final_opt = df_opt.iloc[-1]
        final_pess = df_pess.iloc[-1]
        final_base = df_base.iloc[-1]
        scenario_summary = [
            ["Metric", "Optimistic", "Base Case", "Pessimistic"],
            ["Final MRR", f"${final_opt['MRR']:,.0f}", f"${final_base['MRR']:,.0f}", f"${final_pess['MRR']:,.0f}"],
            ["Final Customers", str(int(final_opt['Total_Customers'])), str(int(final_base['Total_Customers'])), str(int(final_pess['Total_Customers']))],
            ["Gross Margin", f"{final_opt['Gross_Margin_%']:.1f}%", f"{final_base['Gross_Margin_%']:.1f}%", f"{final_pess['Gross_Margin_%']:.1f}%"],
            ["LTV:CAC", f"{final_opt['LTV_CAC_Ratio']:.2f}x", f"{final_base['LTV_CAC_Ratio']:.2f}x", f"{final_pess['LTV_CAC_Ratio']:.2f}x"],
            ["Break-even Month", format_breakeven(breakeven_opt), format_breakeven(breakeven_base), format_breakeven(breakeven_pess)],
        ]
        scenario_table = Table(scenario_summary, colWidths=[1.5*inch, 1.3*inch, 1.3*inch, 1.3*inch])
        scenario_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d1b3e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (1, 1), (1, -1), colors.HexColor('#d5f5e3')),
            ('BACKGROUND', (2, 1), (2, -1), colors.HexColor('#ebf5fb')),
            ('BACKGROUND', (3, 1), (3, -1), colors.HexColor('#fadbd8')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(scenario_table)
        elements.append(PageBreak())
    
    elements.append(Paragraph("Monthly Simulation Data - Base Case", heading_style))
    table_data = [["Month", "Customers", "MRR", "Costs", "P&L", "Cum. Cash"]]
    for _, row in df_base.iterrows():
        table_data.append([
            str(int(row['Month'])),
            str(int(row['Total_Customers'])),
            f"${row['MRR']:,.0f}",
            f"${row['Total_Costs']:,.0f}",
            f"${row['Profit_Loss']:,.0f}",
            f"${row['Cumulative_Cash']:,.0f}"
        ])
    
    monthly_table = Table(table_data, colWidths=[0.6*inch, 0.9*inch, 1*inch, 1*inch, 0.9*inch, 1.1*inch])
    monthly_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d1b3e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
    ]))
    elements.append(monthly_table)
    elements.append(PageBreak())
    
    elements.append(Paragraph("Charts", heading_style))
    
    for title, img_bytes in [("Customer Growth", fig_customers_bytes), ("MRR Growth", fig_mrr_bytes), 
                              ("Cumulative Cash Flow", fig_cash_bytes), ("LTV/CAC Ratio", fig_ltv_bytes)]:
        elements.append(Paragraph(title, normal_style))
        img_buffer = BytesIO(img_bytes)
        elements.append(Image(img_buffer, width=6*inch, height=3.4*inch))
        elements.append(Spacer(1, 15))
    
    elements.append(Paragraph("Generated by BahnSetu SaaS Financial Dashboard", ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER, textColor=colors.grey)))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

st.markdown('<div class="section-heading">⚙️ Model Configuration</div>', unsafe_allow_html=True)

with st.expander("Configure SaaS Model Parameters", expanded=True):
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("**📊 Customer Base**")
        starting_customers = st.number_input(
            "Starting Customers",
            min_value=1, max_value=1000,
            value=50, step=5,
            key="fc_starting"
        )
        monthly_growth_rate = st.slider(
            "Monthly Growth Rate (%)",
            min_value=1, max_value=50,
            value=20, step=1,
            key="fc_growth"
        ) / 100.0
        churn_rate = st.slider(
            "Monthly Churn Rate (%)",
            min_value=1, max_value=30,
            value=5, step=1,
            key="fc_churn"
        ) / 100.0
    
    with col2:
        st.markdown("**💰 Revenue & Pricing**")
        price_per_customer = st.number_input(
            "Price per Customer ($/mo)",
            min_value=1, max_value=10000,
            value=100, step=10,
            key="fc_price"
        )
        cac_simplified = st.number_input(
            "CAC ($)",
            min_value=0, max_value=10000,
            value=150, step=10,
            key="fc_cac"
        )
        pricing_tier = st.selectbox(
            "Pricing Model",
            ["Single Tier", "Multi-Tier (Basic/Pro/Enterprise)"],
            key="fc_tier"
        )
    
    with col3:
        st.markdown("**📋 Costs**")
        fixed_costs = st.number_input(
            "Fixed Costs ($/mo)",
            min_value=0, max_value=100000,
            value=5000, step=500,
            key="fc_fixed"
        )
        variable_cost = st.number_input(
            "Variable Cost ($/cust)",
            min_value=0, max_value=1000,
            value=10, step=5,
            key="fc_variable"
        )
        simulation_months = st.slider(
            "Simulation Period (months)",
            min_value=12, max_value=60,
            value=24, step=6,
            key="fc_months"
        )
    
    with col4:
        st.markdown("**🎯 Scenario Settings**")
        show_scenarios = st.checkbox(
            "Show 3-Way Comparison",
            value=True,
            key="fc_scenarios"
        )
        scenario_name = st.text_input(
            "Scenario Name",
            value="Custom Scenario",
            key="fc_name"
        )

high_churn_rate = churn_rate * 2.0
low_churn_rate = max(0.01, churn_rate * 0.5)
optimistic_growth = min(0.50, monthly_growth_rate * 1.5)
pessimistic_growth = max(0.05, monthly_growth_rate * 0.5)

st.markdown("---")

df_base = run_cached_simulation(
    starting_customers, monthly_growth_rate, churn_rate, price_per_customer,
    fixed_costs, variable_cost, cac_simplified, simulation_months, "base"
)

if show_scenarios:
    df_optimistic = run_cached_simulation(
        starting_customers, optimistic_growth, low_churn_rate, price_per_customer,
        fixed_costs, variable_cost, cac_simplified, simulation_months, "optimistic"
    )
    df_pessimistic = run_cached_simulation(
        starting_customers, pessimistic_growth, high_churn_rate, price_per_customer,
        fixed_costs, variable_cost, cac_simplified, simulation_months, "pessimistic"
    )

st.markdown('<div class="section-heading">📊 Key Performance Indicators</div>', unsafe_allow_html=True)

col1, col2, col3, col4, col5, col6 = st.columns(6)
final_base = df_base.iloc[-1]

kpis = [
    (col1, "FINAL MRR", f"${final_base['MRR']:,.0f}", "Base Case", "green"),
    (col2, "CUSTOMERS", f"{int(final_base['Total_Customers'])}", "Base Case", ""),
    (col3, "GROSS MARGIN", f"{final_base['Gross_Margin_%']:.1f}%", "Base Case", "green"),
    (col4, "LTV:CAC", f"{final_base['LTV_CAC_Ratio']:.1f}x", "Target: 3x", ""),
    (col5, "CAC PAYBACK", f"{final_base['CAC_Payback_Pro']:.1f}mo", "Pro Plan", ""),
    (col6, "HEADCOUNT", f"{int(final_base['Total_Headcount'])}", "All Depts", ""),
]

for col, title, val, sub, cls in kpis:
    with col:
        st.markdown(f"""
        <div class="metric-card {cls}">
            <div class="metric-title">{title}</div>
            <div class="metric-value">{val}</div>
            <div class="metric-sub">{sub}</div>
        </div>
        """, unsafe_allow_html=True)

if show_scenarios:
    st.markdown("---")
    st.markdown('<div class="section-heading">🎭 3-Way Scenario Comparison</div>', unsafe_allow_html=True)
    
    final_opt = df_optimistic.iloc[-1]
    final_pess = df_pessimistic.iloc[-1]
    
    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        st.markdown(f"""
        <div class="metric-card optimistic">
            <div class="metric-title">🎯 OPTIMISTIC</div>
            <div class="metric-value">${final_opt['MRR']:,.0f}</div>
            <div class="metric-sub">MRR | Growth: {optimistic_growth*100:.0f}% | Churn: {low_churn_rate*100:.0f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with sc2:
        st.markdown(f"""
        <div class="metric-card green">
            <div class="metric-title">📊 BASE CASE</div>
            <div class="metric-value">${final_base['MRR']:,.0f}</div>
            <div class="metric-sub">MRR | Growth: {monthly_growth_rate*100:.0f}% | Churn: {churn_rate*100:.0f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with sc3:
        st.markdown(f"""
        <div class="metric-card pessimistic">
            <div class="metric-title">⚠️ PESSIMISTIC</div>
            <div class="metric-value">${final_pess['MRR']:,.0f}</div>
            <div class="metric-sub">MRR | Growth: {pessimistic_growth*100:.0f}% | Churn: {high_churn_rate*100:.0f}%</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")
st.markdown('<div class="section-heading">📈 Customer Growth</div>', unsafe_allow_html=True)

if show_scenarios:
    fig = go.Figure()
    fig.add_scatter(x=df_optimistic["Month"], y=df_optimistic["Total_Customers"],
                    name=f"Optimistic ({optimistic_growth*100:.0f}% growth, {low_churn_rate*100:.0f}% churn)", 
                    mode="lines+markers", line=dict(color="#10b981", width=2), marker=dict(size=5))
    fig.add_scatter(x=df_base["Month"], y=df_base["Total_Customers"],
                    name=f"Base Case ({monthly_growth_rate*100:.0f}% growth, {churn_rate*100:.0f}% churn)", 
                    mode="lines+markers", line=dict(color="#2980b9", width=2.5), marker=dict(size=5))
    fig.add_scatter(x=df_pessimistic["Month"], y=df_pessimistic["Total_Customers"],
                    name=f"Pessimistic ({pessimistic_growth*100:.0f}% growth, {high_churn_rate*100:.0f}% churn)", 
                    mode="lines+markers", line=dict(color="#e74c3c", width=2, dash="dash"), marker=dict(size=5))
    fig.update_layout(title="Total Customers Over Time - 3 Scenarios", **fin_fig())
else:
    fig = go.Figure()
    fig.add_scatter(x=df_base["Month"], y=df_base["Total_Customers"],
                    name="Total Customers", mode="lines+markers",
                    line=dict(color="#2980b9", width=2.5), marker=dict(size=5),
                    fill="tozeroy", fillcolor="rgba(41,128,185,0.1)")
    fig.add_bar(x=df_base["Month"], y=df_base["New_Customers"],
               name="New Customers", marker_color="#2ecc71", opacity=0.4)
    fig.add_bar(x=df_base["Month"], y=-df_base["Churned_Customers"],
               name="Churned", marker_color="#e74c3c", opacity=0.4)
    fig.update_layout(title="Customer Acquisition & Churn", **fin_fig())
st.plotly_chart(fig, use_container_width=True)

st.markdown('<div class="section-heading">💵 Revenue Analysis</div>', unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1:
    if show_scenarios:
        fig = go.Figure()
        fig.add_scatter(x=df_optimistic["Month"], y=df_optimistic["MRR"],
                       name="Optimistic", mode="lines+markers",
                       line=dict(color="#10b981", width=2))
        fig.add_scatter(x=df_base["Month"], y=df_base["MRR"],
                       name="Base Case", mode="lines+markers",
                       line=dict(color="#2980b9", width=2.5))
        fig.add_scatter(x=df_pessimistic["Month"], y=df_pessimistic["MRR"],
                       name="Pessimistic", mode="lines+markers",
                       line=dict(color="#e74c3c", width=2, dash="dash"))
        fig.update_layout(title="MRR Comparison - 3 Scenarios", **fin_fig())
    else:
        fig = go.Figure()
        fig.add_bar(x=df_base["Month"], y=df_base["New_MRR"],
                   name="New MRR", marker_color="#2ecc71", opacity=0.85)
        fig.add_bar(x=df_base["Month"], y=df_base["Expansion_MRR"],
                   name="Expansion MRR", marker_color="#a9dfbf", opacity=0.85)
        fig.add_bar(x=df_base["Month"], y=df_base["Churn_MRR"],
                   name="Churn MRR", marker_color="#e74c3c", opacity=0.85)
        fig.add_scatter(x=df_base["Month"], y=df_base["Net_New_MRR"],
                       name="Net New MRR", mode="lines+markers",
                       line=dict(color="#00b4d8", width=2))
        fig.update_layout(barmode="relative", title="MRR Movements", **fin_fig())
    st.plotly_chart(fig, use_container_width=True)

with c2:
    fig = go.Figure()
    fig.add_scatter(x=df_base["Month"], y=df_base["MoM_Growth_%"],
                   name="MoM Growth %", mode="lines+markers",
                   line=dict(color="#2980b9", width=2),
                   fill="tozeroy", fillcolor="rgba(41,128,185,0.1)")
    if show_scenarios:
        fig.add_scatter(x=df_optimistic["Month"], y=df_optimistic["MoM_Growth_%"],
                       name="Optimistic", mode="lines", line=dict(color="#10b981", width=1.5, dash="dot"))
        fig.add_scatter(x=df_pessimistic["Month"], y=df_pessimistic["MoM_Growth_%"],
                       name="Pessimistic", mode="lines", line=dict(color="#e74c3c", width=1.5, dash="dot"))
    fig.update_layout(title="Month-over-Month Growth %", yaxis_ticksuffix="%", **fin_fig())
    st.plotly_chart(fig, use_container_width=True)

st.markdown('<div class="section-heading">📉 Profitability & Cash Flow</div>', unsafe_allow_html=True)

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
        fig.add_scatter(x=df_base["Month"], y=df_base[col_name],
                       name=name, stackgroup="costs", fillcolor=color,
                       line=dict(color=color, width=0.5), mode="lines")
    fig.add_scatter(x=df_base["Month"], y=df_base["Total_Revenue"],
                   name="Revenue", mode="lines", line=dict(color="#27ae60", width=2.5))
    fig.add_scatter(x=df_base["Month"], y=df_base["EBIT"],
                   name="EBIT", mode="lines", line=dict(color="#2980b9", width=2, dash="dash"))
    fig.update_layout(title="Revenue, Costs & EBIT", **fin_fig())
    st.plotly_chart(fig, use_container_width=True)

with c2:
    if show_scenarios:
        fig = go.Figure()
        fig.add_scatter(x=df_optimistic["Month"], y=df_optimistic["Cumulative_Cash"],
                       name="Optimistic", mode="lines+markers",
                       line=dict(color="#10b981", width=2))
        fig.add_scatter(x=df_base["Month"], y=df_base["Cumulative_Cash"],
                       name="Base Case", mode="lines+markers",
                       line=dict(color="#2980b9", width=2.5))
        fig.add_scatter(x=df_pessimistic["Month"], y=df_pessimistic["Cumulative_Cash"],
                       name="Pessimistic", mode="lines+markers",
                       line=dict(color="#e74c3c", width=2, dash="dash"))
        fig.add_hline(y=0, line_color="white", line_dash="dot")
        fig.update_layout(title="Cumulative Cash - 3 Scenarios", **fin_fig())
    else:
        fig = go.Figure()
        fig.add_scatter(x=df_base["Month"], y=df_base["Profit_Loss"],
                       name="Monthly P&L", mode="lines+markers",
                       line=dict(color="#e74c3c", width=2))
        fig.add_scatter(x=df_base["Month"], y=df_base["Cumulative_Cash"],
                       name="Cumulative Cash", mode="lines+markers",
                       line=dict(color="#9b59b6", width=2.5))
        fig.add_hline(y=0, line_color="white", line_dash="dot")
        fig.update_layout(title="Profit/Loss & Cumulative Cash", **fin_fig())
    st.plotly_chart(fig, use_container_width=True)

st.markdown('<div class="section-heading">🎯 Unit Economics</div>', unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
with c1:
    fig = go.Figure()
    if show_scenarios:
        fig.add_scatter(x=df_optimistic["Month"], y=df_optimistic["LTV_CAC_Ratio"],
                       name="Optimistic", mode="lines", line=dict(color="#10b981", width=2))
        fig.add_scatter(x=df_base["Month"], y=df_base["LTV_CAC_Ratio"],
                       name="Base Case", mode="lines", line=dict(color="#2980b9", width=2.5))
        fig.add_scatter(x=df_pessimistic["Month"], y=df_pessimistic["LTV_CAC_Ratio"],
                       name="Pessimistic", mode="lines", line=dict(color="#e74c3c", width=2, dash="dash"))
    else:
        fig.add_scatter(x=df_base["Month"], y=df_base["LTV_CAC_Ratio"],
                       name="LTV:CAC", mode="lines+markers",
                       line=dict(color="#e67e22", width=2.5))
    fig.add_hline(y=3.0, line_color="#27ae60", line_dash="dash",
                 annotation_text="3x Benchmark")
    fig.update_layout(title="LTV / CAC Ratio", **fin_fig())
    st.plotly_chart(fig, use_container_width=True)

with c2:
    fig = go.Figure()
    fig.add_scatter(x=df_base["Month"], y=df_base["CAC_Payback_Basic"],
                   name="Basic", mode="lines+markers",
                   line=dict(color="#8e44ad", width=2))
    fig.add_scatter(x=df_base["Month"], y=df_base["CAC_Payback_Pro"],
                   name="Pro", mode="lines+markers",
                   line=dict(color="#2980b9", width=2))
    fig.add_scatter(x=df_base["Month"], y=df_base["CAC_Payback_Enterprise"],
                   name="Enterprise", mode="lines+markers",
                   line=dict(color="#27ae60", width=2))
    fig.update_layout(title="CAC Payback (months)", **fin_fig())
    st.plotly_chart(fig, use_container_width=True)

with c3:
    fig = go.Figure()
    fig.add_scatter(x=df_base["Month"], y=df_base["Gross_Margin_%"],
                   name="Gross Margin", mode="lines+markers",
                   line=dict(color="#2980b9", width=2.5),
                   fill="tozeroy", fillcolor="rgba(41,128,185,0.1)")
    fig.update_layout(title="Gross Margin %", yaxis_ticksuffix="%",
                      yaxis_range=[0, 100], **fin_fig())
    st.plotly_chart(fig, use_container_width=True)

st.markdown('<div class="section-heading">👥 Headcount & Efficiency</div>', unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1:
    fig = go.Figure()
    for col_name, color, name in [
        ("HC_GA", "#5dade2", "G&A"),
        ("HC_Engineering", "#f0b27a", "Engineering"),
        ("HC_Marketing", "#a9dfbf", "Marketing"),
        ("HC_Sales", "#f9e79f", "Sales"),
        ("HC_CS", "#d2b4de", "CS"),
    ]:
        fig.add_scatter(x=df_base["Month"], y=df_base[col_name],
                       name=name, stackgroup="hc", fillcolor=color,
                       line=dict(color=color, width=0.5), mode="lines")
    fig.update_layout(title="Headcount by Department", **fin_fig())
    st.plotly_chart(fig, use_container_width=True)

with c2:
    fig = go.Figure()
    if show_scenarios:
        fig.add_scatter(x=df_optimistic["Month"], y=df_optimistic["SM_Efficiency"],
                       name="Optimistic", mode="lines", line=dict(color="#10b981", width=2))
        fig.add_scatter(x=df_base["Month"], y=df_base["SM_Efficiency"],
                       name="Base Case", mode="lines", line=dict(color="#2980b9", width=2.5))
        fig.add_scatter(x=df_pessimistic["Month"], y=df_pessimistic["SM_Efficiency"],
                       name="Pessimistic", mode="lines", line=dict(color="#e74c3c", width=2, dash="dash"))
    else:
        fig.add_scatter(x=df_base["Month"], y=df_base["SM_Efficiency"],
                       name="S&M Efficiency", mode="lines+markers",
                       line=dict(color="#2980b9", width=2.5),
                       fill="tozeroy", fillcolor="rgba(41,128,185,0.08)")
    fig.add_hline(y=1.0, line_color="#e74c3c", line_dash="dash",
                 annotation_text="1.0x Break-even")
    fig.update_layout(title="Sales & Marketing Efficiency", **fin_fig())
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.markdown('<div class="section-heading">🔬 Sensitivity Analysis</div>', unsafe_allow_html=True)

st.info("**What-If Analysis:** Adjust parameters below to see real-time impact on key metrics. All charts update instantly without clicking any button!")

sa_col1, sa_col2 = st.columns(2)

with sa_col1:
    st.markdown("**🎚️ Sensitivity Controls**")
    
    sens_churn_low = st.slider(
        "Churn Rate - Low Scenario (%)",
        min_value=1, max_value=15,
        value=3, step=1,
        key="sens_churn_low"
    ) / 100.0
    
    sens_churn_high = st.slider(
        "Churn Rate - High Scenario (%)",
        min_value=5, max_value=30,
        value=12, step=1,
        key="sens_churn_high"
    ) / 100.0
    
    sens_growth_low = st.slider(
        "Growth Rate - Low Scenario (%)",
        min_value=5, max_value=30,
        value=10, step=1,
        key="sens_growth_low"
    ) / 100.0
    
    sens_growth_high = st.slider(
        "Growth Rate - High Scenario (%)",
        min_value=15, max_value=50,
        value=35, step=1,
        key="sens_growth_high"
    ) / 100.0
    
    sens_price_low = st.slider(
        "Price - Low Scenario ($)",
        min_value=25, max_value=200,
        value=50, step=5,
        key="sens_price_low"
    )
    
    sens_price_high = st.slider(
        "Price - High Scenario ($)",
        min_value=75, max_value=500,
        value=200, step=5,
        key="sens_price_high"
    )

df_sens_low_churn = run_cached_simulation(
    starting_customers, monthly_growth_rate, sens_churn_low, price_per_customer,
    fixed_costs, variable_cost, cac_simplified, simulation_months, "sens_low_churn"
)
df_sens_high_churn = run_cached_simulation(
    starting_customers, monthly_growth_rate, sens_churn_high, price_per_customer,
    fixed_costs, variable_cost, cac_simplified, simulation_months, "sens_high_churn"
)
df_sens_low_growth = run_cached_simulation(
    starting_customers, sens_growth_low, churn_rate, price_per_customer,
    fixed_costs, variable_cost, cac_simplified, simulation_months, "sens_low_growth"
)
df_sens_high_growth = run_cached_simulation(
    starting_customers, sens_growth_high, churn_rate, price_per_customer,
    fixed_costs, variable_cost, cac_simplified, simulation_months, "sens_high_growth"
)
df_sens_low_price = run_cached_simulation(
    starting_customers, monthly_growth_rate, churn_rate, sens_price_low,
    fixed_costs, variable_cost, cac_simplified, simulation_months, "sens_low_price"
)
df_sens_high_price = run_cached_simulation(
    starting_customers, monthly_growth_rate, churn_rate, sens_price_high,
    fixed_costs, variable_cost, cac_simplified, simulation_months, "sens_high_price"
)

with sa_col2:
    st.markdown("**📊 Sensitivity Impact Summary**")
    
    final_sens = {
        "Low Churn": df_sens_low_churn.iloc[-1],
        "High Churn": df_sens_high_churn.iloc[-1],
        "Low Growth": df_sens_low_growth.iloc[-1],
        "High Growth": df_sens_high_growth.iloc[-1],
        "Low Price": df_sens_low_price.iloc[-1],
        "High Price": df_sens_high_price.iloc[-1],
    }
    
    sensitivity_data = []
    for scenario, data in final_sens.items():
        sensitivity_data.append({
            "Scenario": scenario,
            "MRR": data['MRR'],
            "Customers": int(data['Total_Customers']),
            "LTV:CAC": data['LTV_CAC_Ratio'],
            "Cum. Cash": data['Cumulative_Cash'],
            "Breakeven Mo": data['Cumulative_Cash'] >= 0
        })
    
    sens_df = pd.DataFrame(sensitivity_data)
    
    def highlight_breakeven(val):
        if isinstance(val, bool):
            return 'color: #10b981; font-weight: bold' if val else 'color: #ef4444'
        return ''
    
    st.dataframe(
        sens_df.style.format({
            "MRR": "${:,.0f}",
            "Cum. Cash": "${:,.0f}",
            "LTV:CAC": "{:.2f}x"
        }).applymap(highlight_breakeven, subset=['Breakeven Mo']),
        use_container_width=True, hide_index=True
    )

st.markdown('<div class="section-heading">📈 Sensitivity Charts</div>', unsafe_allow_html=True)

sc1, sc2 = st.columns(2)
with sc1:
    st.markdown("**Churn Rate Impact on MRR**")
    fig = go.Figure()
    fig.add_scatter(x=df_sens_low_churn["Month"], y=df_sens_low_churn["MRR"],
                   name=f"Low ({sens_churn_low*100:.0f}% churn)", mode="lines+markers",
                   line=dict(color="#10b981", width=2))
    fig.add_scatter(x=df_base["Month"], y=df_base["MRR"],
                   name=f"Base ({churn_rate*100:.0f}% churn)", mode="lines+markers",
                   line=dict(color="#2980b9", width=2.5))
    fig.add_scatter(x=df_sens_high_churn["Month"], y=df_sens_high_churn["MRR"],
                   name=f"High ({sens_churn_high*100:.0f}% churn)", mode="lines+markers",
                   line=dict(color="#e74c3c", width=2, dash="dash"))
    fig.update_layout(title="Churn Rate Sensitivity", **fin_fig())
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("**Price Impact on MRR**")
    fig = go.Figure()
    fig.add_scatter(x=df_sens_low_price["Month"], y=df_sens_low_price["MRR"],
                   name=f"Low (${sens_price_low})", mode="lines+markers",
                   line=dict(color="#10b981", width=2))
    fig.add_scatter(x=df_base["Month"], y=df_base["MRR"],
                   name=f"Base (${price_per_customer})", mode="lines+markers",
                   line=dict(color="#2980b9", width=2.5))
    fig.add_scatter(x=df_sens_high_price["Month"], y=df_sens_high_price["MRR"],
                   name=f"High (${sens_price_high})", mode="lines+markers",
                   line=dict(color="#e74c3c", width=2, dash="dash"))
    fig.update_layout(title="Price Sensitivity", **fin_fig())
    st.plotly_chart(fig, use_container_width=True)

with sc2:
    st.markdown("**Growth Rate Impact on Customers**")
    fig = go.Figure()
    fig.add_scatter(x=df_sens_low_growth["Month"], y=df_sens_low_growth["Total_Customers"],
                   name=f"Low ({sens_growth_low*100:.0f}%)", mode="lines+markers",
                   line=dict(color="#10b981", width=2))
    fig.add_scatter(x=df_base["Month"], y=df_base["Total_Customers"],
                   name=f"Base ({monthly_growth_rate*100:.0f}%)", mode="lines+markers",
                   line=dict(color="#2980b9", width=2.5))
    fig.add_scatter(x=df_sens_high_growth["Month"], y=df_sens_high_growth["Total_Customers"],
                   name=f"High ({sens_growth_high*100:.0f}%)", mode="lines+markers",
                   line=dict(color="#e74c3c", width=2, dash="dash"))
    fig.update_layout(title="Growth Rate Sensitivity", **fin_fig())
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("**LTV:CAC Ratio Across Scenarios**")
    fig = go.Figure()
    fig.add_scatter(x=df_sens_low_churn["Month"], y=df_sens_low_churn["LTV_CAC_Ratio"],
                   name="Low Churn", mode="lines", line=dict(color="#10b981", width=2))
    fig.add_scatter(x=df_base["Month"], y=df_base["LTV_CAC_Ratio"],
                   name="Base Case", mode="lines", line=dict(color="#2980b9", width=2.5))
    fig.add_scatter(x=df_sens_high_churn["Month"], y=df_sens_high_churn["LTV_CAC_Ratio"],
                   name="High Churn", mode="lines", line=dict(color="#e74c3c", width=2, dash="dash"))
    fig.add_scatter(x=df_sens_low_price["Month"], y=df_sens_low_price["LTV_CAC_Ratio"],
                   name="Low Price", mode="lines", line=dict(color="#f59e0b", width=1.5, dash="dot"))
    fig.add_scatter(x=df_sens_high_price["Month"], y=df_sens_high_price["LTV_CAC_Ratio"],
                   name="High Price", mode="lines", line=dict(color="#8b5cf6", width=1.5, dash="dot"))
    fig.add_hline(y=3.0, line_color="#27ae60", line_dash="dash",
                 annotation_text="3x Benchmark")
    fig.update_layout(title="LTV:CAC Sensitivity", **fin_fig())
    st.plotly_chart(fig, use_container_width=True)

st.markdown('<div class="section-heading">📋 Detailed Results Table</div>', unsafe_allow_html=True)

display_cols = ["Month", "Total_Customers", "New_Customers", "Churned_Customers",
               "MRR", "ARR", "Gross_Profit", "Total_Costs", "Profit_Loss",
               "Cumulative_Cash", "Churn_Rate_%", "LTV_CAC_Ratio"]

if show_scenarios:
    tab1, tab2, tab3, tab4 = st.tabs(["Base Case", "Optimistic", "Pessimistic", "Sensitivity"])
    with tab1:
        st.dataframe(df_base[display_cols].style.format({
            "MRR": "${:,.0f}",
            "ARR": "${:,.0f}",
            "Gross_Profit": "${:,.0f}",
            "Total_Costs": "${:,.0f}",
            "Profit_Loss": "${:,.0f}",
            "Cumulative_Cash": "${:,.0f}",
            "Churn_Rate_%": "{:.1f}%",
            "LTV_CAC_Ratio": "{:.2f}x"
        }), use_container_width=True, hide_index=True)
    with tab2:
        st.dataframe(df_optimistic[display_cols].style.format({
            "MRR": "${:,.0f}",
            "ARR": "${:,.0f}",
            "Gross_Profit": "${:,.0f}",
            "Total_Costs": "${:,.0f}",
            "Profit_Loss": "${:,.0f}",
            "Cumulative_Cash": "${:,.0f}",
            "Churn_Rate_%": "{:.1f}%",
            "LTV_CAC_Ratio": "{:.2f}x"
        }), use_container_width=True, hide_index=True)
    with tab3:
        st.dataframe(df_pessimistic[display_cols].style.format({
            "MRR": "${:,.0f}",
            "ARR": "${:,.0f}",
            "Gross_Profit": "${:,.0f}",
            "Total_Costs": "${:,.0f}",
            "Profit_Loss": "${:,.0f}",
            "Cumulative_Cash": "${:,.0f}",
            "Churn_Rate_%": "{:.1f}%",
            "LTV_CAC_Ratio": "{:.2f}x"
        }), use_container_width=True, hide_index=True)
    with tab4:
        all_sens = pd.concat([
            df_sens_low_churn.assign(Scenario=f"Low Churn ({sens_churn_low*100:.0f}%)"),
            df_sens_high_churn.assign(Scenario=f"High Churn ({sens_churn_high*100:.0f}%)"),
            df_sens_low_growth.assign(Scenario=f"Low Growth ({sens_growth_low*100:.0f}%)"),
            df_sens_high_growth.assign(Scenario=f"High Growth ({sens_growth_high*100:.0f}%)"),
        ])
        st.dataframe(all_sens[["Month", "Scenario", "MRR", "Total_Customers", "Cumulative_Cash", "LTV_CAC_Ratio"]].style.format({
            "MRR": "${:,.0f}",
            "Cumulative_Cash": "${:,.0f}",
            "LTV_CAC_Ratio": "{:.2f}x"
        }), use_container_width=True, hide_index=True)
else:
    tab1, tab2 = st.tabs(["Base Case", "Sensitivity"])
    with tab1:
        st.dataframe(df_base[display_cols].style.format({
            "MRR": "${:,.0f}",
            "ARR": "${:,.0f}",
            "Gross_Profit": "${:,.0f}",
            "Total_Costs": "${:,.0f}",
            "Profit_Loss": "${:,.0f}",
            "Cumulative_Cash": "${:,.0f}",
            "Churn_Rate_%": "{:.1f}%",
            "LTV_CAC_Ratio": "{:.2f}x"
        }), use_container_width=True, hide_index=True)
    with tab2:
        all_sens = pd.concat([
            df_sens_low_churn.assign(Scenario=f"Low Churn ({sens_churn_low*100:.0f}%)"),
            df_sens_high_churn.assign(Scenario=f"High Churn ({sens_churn_high*100:.0f}%)"),
            df_sens_low_growth.assign(Scenario=f"Low Growth ({sens_growth_low*100:.0f}%)"),
            df_sens_high_growth.assign(Scenario=f"High Growth ({sens_growth_high*100:.0f}%)"),
        ])
        st.dataframe(all_sens[["Month", "Scenario", "MRR", "Total_Customers", "Cumulative_Cash", "LTV_CAC_Ratio"]].style.format({
            "MRR": "${:,.0f}",
            "Cumulative_Cash": "${:,.0f}",
            "LTV_CAC_Ratio": "{:.2f}x"
        }), use_container_width=True, hide_index=True)

st.markdown('<div class="section-heading">📝 Model Summary</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    if show_scenarios:
        breakeven_opt = df_optimistic[df_optimistic['Cumulative_Cash'] >= 0]['Month'].min()
        breakeven_base = df_base[df_base['Cumulative_Cash'] >= 0]['Month'].min()
        breakeven_pess = df_pessimistic[df_pessimistic['Cumulative_Cash'] >= 0]['Month'].min()
        
        def format_breakeven(month):
            if pd.notna(month):
                return f"Month {int(month)}"
            return "Not achieved"
        
        st.markdown(f"""
        **📊 Scenario Summary**
        
        | Scenario | Final MRR | Customers | LTV:CAC | Break-even |
        |----------|-----------|-----------|---------|------------|
        | 🎯 Optimistic | ${final_opt['MRR']:,.0f} | {int(final_opt['Total_Customers'])} | {final_opt['LTV_CAC_Ratio']:.2f}x | {format_breakeven(breakeven_opt)} |
        | 📊 Base Case | ${final_base['MRR']:,.0f} | {int(final_base['Total_Customers'])} | {final_base['LTV_CAC_Ratio']:.2f}x | {format_breakeven(breakeven_base)} |
        | ⚠️ Pessimistic | ${final_pess['MRR']:,.0f} | {int(final_pess['Total_Customers'])} | {final_pess['LTV_CAC_Ratio']:.2f}x | {format_breakeven(breakeven_pess)} |
        """)
    else:
        breakeven_base = df_base[df_base['Cumulative_Cash'] >= 0]['Month'].min()
        if pd.notna(breakeven_base):
            st.success(f"✅ Break-even achieved in Month {int(breakeven_base)}")
        else:
            st.warning(f"⚠️ Break-even not achieved within {simulation_months} months")
        
        st.markdown(f"""
        **Base Case Scenario ({churn_rate*100:.0f}% churn)**  
        - Final MRR: ${final_base['MRR']:,.0f}  
        - Final Customers: {int(final_base['Total_Customers'])}  
        - Final Cumulative Cash: ${final_base['Cumulative_Cash']:,.0f}  
        - Total Churned ({simulation_months}mo): {int(df_base['Churned_Customers'].sum())}  
        - Final LTV:CAC: {final_base['LTV_CAC_Ratio']:.2f}x  
        - Final Headcount: {int(final_base['Total_Headcount'])}
        """)

with col2:
    st.markdown(f"""
    **🔑 Key Assumptions**
    
    - Starting Customers: **{starting_customers}**
    - Monthly Growth: **{monthly_growth_rate*100:.0f}%** (Range: {pessimistic_growth*100:.0f}% - {optimistic_growth*100:.0f}%)
    - Monthly Churn: **{churn_rate*100:.0f}%** (Range: {low_churn_rate*100:.0f}% - {high_churn_rate*100:.0f}%)
    - Price per Customer: **${price_per_customer}** (Range: ${sens_price_low} - ${sens_price_high})
    - CAC: **${cac_simplified}**
    - Fixed Costs: **${fixed_costs:,}/mo**
    - Variable Cost: **${variable_cost}/customer**
    - Simulation Period: **{simulation_months} months**
    """)

st.markdown("---")
st.markdown('<div class="section-heading">📤 Export Center</div>', unsafe_allow_html=True)

st.markdown("""
<style>
    .export-card {
        background: linear-gradient(135deg, #0d1b3e 0%, #1a2744 100%);
        border: 1px solid #2d4f8a;
        border-radius: 16px;
        padding: 24px;
        margin: 10px 0;
        transition: all 0.3s ease;
    }
    .export-card:hover {
        border-color: #00b4d8;
        transform: translateY(-2px);
        box-shadow: 0 8px 32px rgba(0, 180, 216, 0.15);
    }
    .export-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #e2e8f0;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .export-desc {
        font-size: 0.8rem;
        color: #7a9cc4;
        margin-bottom: 16px;
    }
    .export-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 12px;
    }
    .export-btn {
        background: rgba(0, 180, 216, 0.1);
        border: 1px solid rgba(0, 180, 216, 0.3);
        border-radius: 10px;
        padding: 14px 18px;
        color: #00b4d8;
        font-weight: 600;
        font-size: 0.85rem;
        text-align: left;
        transition: all 0.2s ease;
        cursor: pointer;
    }
    .export-btn:hover {
        background: rgba(0, 180, 216, 0.2);
        border-color: #00b4d8;
        transform: translateX(4px);
    }
    .export-btn-icon {
        font-size: 1.2rem;
        margin-right: 8px;
    }
</style>
""", unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="export-card">', unsafe_allow_html=True)
    st.markdown('<div class="export-title">📊 Chart Exports (PNG)</div>', unsafe_allow_html=True)
    st.markdown('<div class="export-desc">High-quality chart images for presentations & reports</div>', unsafe_allow_html=True)
    
    chart_cols = st.columns(4)
    
    chart_data = [
        ("📊 Customer Growth", df_base["Month"], {"Optimistic": df_optimistic["Total_Customers"].values, "Base": df_base["Total_Customers"].values, "Pessimistic": df_pessimistic["Total_Customers"].values}, ["#10b981", "#2980b9", "#e74c3c"]),
        ("📈 MRR Growth", df_base["Month"], {"Optimistic": df_optimistic["MRR"].values, "Base": df_base["MRR"].values, "Pessimistic": df_pessimistic["MRR"].values}, ["#10b981", "#2980b9", "#e74c3c"]),
        ("💰 Cash Flow", df_base["Month"], {"Optimistic": df_optimistic["Cumulative_Cash"].values, "Base": df_base["Cumulative_Cash"].values, "Pessimistic": df_pessimistic["Cumulative_Cash"].values}, ["#10b981", "#2980b9", "#e74c3c"]),
        ("🎯 LTV:CAC Ratio", df_base["Month"], df_base["LTV_CAC_Ratio"].values, None),
    ]
    
    for idx, (label, x, y_data, colors_list) in enumerate(chart_data):
        with chart_cols[idx]:
            img_bytes = create_matplotlib_chart(x, y_data, label.split(' ', 1)[1], colors_list=colors_list)
            st.download_button(
                f"⬇️ {label}",
                img_bytes,
                file_name=f"chart_{label.split(' ', 1)[1].lower().replace(' ', '_')}_{scenario_name.replace(' ', '_').lower()}.png",
                mime="image/png",
                use_container_width=True,
                key=f"chart_btn_{idx}"
            )
    st.markdown('</div>', unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="export-card">', unsafe_allow_html=True)
    st.markdown('<div class="export-title">📋 Data Exports</div>', unsafe_allow_html=True)
    st.markdown('<div class="export-desc">Simulation data in CSV format</div>', unsafe_allow_html=True)
    
    csv_cols = st.columns(3)
    
    csv_base = df_base[display_cols].to_csv(index=False)
    with csv_cols[0]:
        st.download_button("📄 Base Case CSV", csv_base, f"base_case_{scenario_name.replace(' ', '_').lower()}.csv", "text/csv", use_container_width=True)
    
    csv_full = df_base.to_csv(index=False)
    with csv_cols[1]:
        st.download_button("📄 Full Data CSV", csv_full, f"full_data_{scenario_name.replace(' ', '_').lower()}.csv", "text/csv", use_container_width=True)
    
    all_sens = pd.concat([
        df_sens_low_churn.assign(Scenario=f"Low Churn ({sens_churn_low*100:.0f}%)"),
        df_sens_high_churn.assign(Scenario=f"High Churn ({sens_churn_high*100:.0f}%)"),
        df_sens_low_growth.assign(Scenario=f"Low Growth ({sens_growth_low*100:.0f}%)"),
        df_sens_high_growth.assign(Scenario=f"High Growth ({sens_growth_high*100:.0f}%)"),
    ])
    csv_sens = all_sens[["Month", "Scenario", "MRR", "Total_Customers", "Cumulative_Cash", "LTV_CAC_Ratio"]].to_csv(index=False)
    with csv_cols[2]:
        st.download_button("📄 Sensitivity CSV", csv_sens, f"sensitivity_{scenario_name.replace(' ', '_').lower()}.csv", "text/csv", use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="export-card">', unsafe_allow_html=True)
    st.markdown('<div class="export-title">📑 PDF Reports</div>', unsafe_allow_html=True)
    st.markdown('<div class="export-desc">Complete professional reports with charts & tables</div>', unsafe_allow_html=True)
    
    pdf_cols = st.columns(3)
    
    chart_data_pdf = [
        ("Customer Growth", df_base["Month"], {"Optimistic": df_optimistic["Total_Customers"].values, "Base": df_base["Total_Customers"].values, "Pessimistic": df_pessimistic["Total_Customers"].values}, ["#10b981", "#2980b9", "#e74c3c"]),
        ("MRR Growth", df_base["Month"], {"Optimistic": df_optimistic["MRR"].values, "Base": df_base["MRR"].values, "Pessimistic": df_pessimistic["MRR"].values}, ["#10b981", "#2980b9", "#e74c3c"]),
        ("Cumulative Cash", df_base["Month"], {"Optimistic": df_optimistic["Cumulative_Cash"].values, "Base": df_base["Cumulative_Cash"].values, "Pessimistic": df_pessimistic["Cumulative_Cash"].values}, ["#10b981", "#2980b9", "#e74c3c"]),
        ("LTV/CAC Ratio", df_base["Month"], df_base["LTV_CAC_Ratio"].values, None),
    ]
    bytes_list = [create_matplotlib_chart(x, y, title, colors_list=c) for title, x, y, c in chart_data_pdf]
    
    with pdf_cols[0]:
        with st.spinner("Generating Complete Report..."):
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Image as RLImage, Spacer, PageBreak, Table, TableStyle, HRFlowable
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
            from datetime import datetime
            
            buf = BytesIO()
            doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=0.5*inch, leftMargin=0.5*inch, topMargin=0.5*inch, bottomMargin=0.5*inch)
            styles = getSampleStyleSheet()
            
            title_s = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, spaceAfter=8, alignment=TA_CENTER, textColor=colors.HexColor('#1a237e'), fontName='Helvetica-Bold')
            subtitle_s = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=12, spaceAfter=6, alignment=TA_CENTER, textColor=colors.HexColor('#546e7a'))
            head_s = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, spaceAfter=12, spaceBefore=18, textColor=colors.HexColor('#0277bd'), fontName='Helvetica-Bold')
            subhead_s = ParagraphStyle('SubHead', parent=styles['Heading3'], fontSize=12, spaceAfter=8, spaceBefore=12, textColor=colors.HexColor('#37474f'), fontName='Helvetica-Bold')
            normal_s = ParagraphStyle('Normal', parent=styles['Normal'], fontSize=10, spaceAfter=8, alignment=TA_JUSTIFY, leading=15)
            bullet_s = ParagraphStyle('Bullet', parent=styles['Normal'], fontSize=10, spaceAfter=6, leftIndent=25, bulletIndent=12, leading=15)
            footer_s = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER, textColor=colors.grey)
            
            DARK_BLUE = colors.HexColor('#1a237e')
            MEDIUM_BLUE = colors.HexColor('#0277bd')
            LIGHT_BLUE = colors.HexColor('#e3f2fd')
            ROW_ALT = colors.HexColor('#f5f5f5')
            ROW_WHITE = colors.white
            BORDER = colors.HexColor('#90a4ae')
            TEXT_DARK = colors.HexColor('#263238')
            TEXT_BOLD = colors.HexColor('#1a237e')
            GREEN_ACCENT = colors.HexColor('#2e7d32')
            RED_ACCENT = colors.HexColor('#c62828')
            ORANGE_ACCENT = colors.HexColor('#ef6c00')
            
            final_base = df_base.iloc[-1]
            breakeven_month = df_base[df_base['Cumulative_Cash'] >= 0]['Month'].min()
            breakeven_text = f"Month {int(breakeven_month)}" if pd.notna(breakeven_month) else "Not achieved"
            
            cash = final_base.get('Cumulative_Cash', 0)
            profit = final_base.get('Profit_Loss', 0)
            if cash > 0 and profit < 0:
                runway_months = int(cash / abs(profit)) if profit != 0 else None
                runway_text = f"{runway_months} months" if runway_months else "N/A"
            elif profit >= 0:
                runway_text = "Cash positive"
            else:
                runway_text = "N/A (burning cash)"
            
            ltv_cac = final_base.get('LTV_CAC_Ratio', 0)
            if ltv_cac >= 3:
                ltv_status = "Healthy (>=3x)"
            elif ltv_cac >= 1:
                ltv_status = "Moderate (1-3x)"
            else:
                ltv_status = "Critical (<1x)"
            
            total_rev = df_base['Total_Revenue'].sum()
            total_costs = df_base['Total_Costs'].sum()
            net_cash = total_rev - total_costs
            
            elems = []
            
            elems.append(HRFlowable(width="100%", thickness=3, color=colors.HexColor('#0d1b3e'), spaceAfter=15))
            elems.append(Paragraph("SaaS Financial Simulation Report", title_s))
            elems.append(Paragraph(f"<b>{scenario_name}</b>", subtitle_s))
            elems.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')} | Forecast Period: {simulation_months} Months", subtitle_s))
            elems.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#bdc3c7'), spaceBefore=10, spaceAfter=20))
            
            elems.append(Paragraph("Executive Summary", head_s))
            elems.append(Paragraph("This report provides a comprehensive financial simulation of the SaaS business model based on the Christoph Janz SaaS Financial Plan methodology. The analysis covers customer acquisition, churn, revenue development, cost structure, and cash flow projections.", normal_s))
            elems.append(Spacer(1, 12))
            
            summary_kpis = [
                ["📊 Metric", "💰 Value", "📝 Interpretation"],
                ["Final MRR", f"${final_base['MRR']:,.0f}", f"{int(final_base['Total_Customers']):,} customers × ${price_per_customer}/mo"],
                ["Final ARR", f"${final_base['ARR']:,.0f}", "Annual Recurring Revenue (MRR × 12)"],
                ["Total Revenue", f"${total_rev:,.0f}", f"Cumulative over {simulation_months} months"],
                ["Net Cash Position", f"${net_cash:,.0f}", "Total Revenue − Total Costs"],
                ["Gross Margin", f"{final_base['Gross_Margin_%']:.1f}%", "Revenue − COGS as % of Revenue"],
                ["LTV:CAC Ratio", f"{ltv_cac:.2f}x", ltv_status],
                ["CAC Payback", f"{final_base.get('CAC_Payback_Pro', 0):.1f} mo", "Time to recover acquisition cost"],
                ["Break-even Point", breakeven_text, "When cumulative cash turns positive"],
                ["Cash Runway", runway_text, "Months of operation remaining"],
            ]
            kpi_t = Table(summary_kpis, colWidths=[1.5*inch, 1.4*inch, 2.6*inch])
            kpi_t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), DARK_BLUE),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('LEFTPADDING', (0, 0), (-1, -1), 12),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('LINEBELOW', (0, 0), (-1, 0), 2, MEDIUM_BLUE),
                ('LINEBELOW', (0, -1), (-1, -1), 1.5, MEDIUM_BLUE),
                ('LINEBEFORE', (1, 0), (1, -1), 1, colors.HexColor('#cfd8dc')),
                ('LINEBEFORE', (2, 0), (2, -1), 1, colors.HexColor('#cfd8dc')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [ROW_WHITE, ROW_ALT]),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('TEXTCOLOR', (1, 1), (1, -1), TEXT_BOLD),
                ('FONTNAME', (1, 1), (1, -1), 'Helvetica-Bold'),
                ('TEXTCOLOR', (2, 1), (2, -1), TEXT_DARK),
            ]))
            elems.append(kpi_t)
            elems.append(Spacer(1, 18))
            
            elems.append(Paragraph("Key Business Insights", subhead_s))
            
            avg_mrr_growth = df_base['MoM_Growth_%'].mean()
            churn_rate_val = churn_rate * 100
            churn_impact = "High" if churn_rate_val > 5 else ("Moderate" if churn_rate_val > 2 else "Low")
            
            insights = [
                f"<b>Growth Trajectory:</b> The business is growing at an average of {avg_mrr_growth:.1f}% month-over-month in MRR. "
                f"Starting from ${df_base.iloc[0]['MRR']:,.0f} in Month 1, MRR reaches ${final_base['MRR']:,.0f} by Month {simulation_months}.",
                
                f"<b>Churn Impact:</b> With a {churn_rate_val:.1f}% monthly churn rate (rated as {churn_impact}), "
                f"the business must acquire approximately {int(final_base['Churned_Customers'].sum())} new customers over {simulation_months} months just to maintain the customer base. "
                f"Net customer growth is {(final_base['Total_Customers'] - starting_customers):.0f} customers.",
                
                f"<b>Unit Economics:</b> The LTV:CAC ratio of {ltv_cac:.2f}x indicates {ltv_status.lower()}. "
                f"{'This is a healthy ratio where customer lifetime value significantly exceeds acquisition costs.' if ltv_cac >= 3 else 'Improving this ratio requires either increasing customer lifetime (reducing churn) or optimizing CAC.'}",
                
                f"<b>Profitability Path:</b> {'Break-even has been achieved' if pd.notna(breakeven_month) else 'Break-even has not been achieved'} within the {simulation_months}-month simulation period. "
                f"The cumulative cash position stands at ${cash:,.0f} {'(profitable)' if cash >= 0 else '(still accumulating losses)'}.",
                
                f"<b>Cost Structure:</b> Fixed costs of ${fixed_costs:,}/month represent {fixed_costs/final_base['Total_Costs']*100:.0f}% of final month costs. "
                f"Variable costs scale at ${variable_cost}/customer, ensuring margins improve as the business scales.",
            ]
            
            for insight in insights:
                elems.append(Paragraph(f"• {insight}", bullet_s))
            
            elems.append(Spacer(1, 15))
            
            elems.append(Paragraph("Charts & Visual Analysis", head_s))
            for chart_title, img_bytes in [("Customer Growth Over Time", bytes_list[0]), ("Monthly Recurring Revenue (MRR)", bytes_list[1]), ("Cumulative Cash Flow", bytes_list[2]), ("LTV:CAC Ratio Trend", bytes_list[3])]:
                elems.append(Paragraph(chart_title, subhead_s))
                elems.append(RLImage(BytesIO(img_bytes), width=6.5*inch, height=3.5*inch))
                elems.append(Spacer(1, 10))
            
            elems.append(PageBreak())
            
            elems.append(Paragraph("Model Assumptions & Parameters", head_s))
            elems.append(Paragraph("The following table documents all input parameters used in this simulation. These assumptions form the basis of the financial model and can be adjusted to test different scenarios.", normal_s))
            elems.append(Spacer(1, 12))
            
            assump_data = [
                ["📋 Parameter", "💵 Value", "📖 Description", "📈 Impact"],
                ["Starting Customers", f"{starting_customers:,}", "Initial customer base at Month 0", f"Starting revenue: ${starting_customers * price_per_customer:,}/mo"],
                ["Monthly Growth Rate", f"{monthly_growth_rate*100:.1f}%", "New customers as % of current base", f"+{int(starting_customers * monthly_growth_rate * 12):,} customers/year"],
                ["Monthly Churn Rate", f"{churn_rate*100:.1f}%", "Customers lost each month", f"-{int(starting_customers * churn_rate * 12):,} customers/year"],
                ["Price per Customer", f"${price_per_customer:,}", "Monthly revenue per customer", f"${int(final_base['Total_Customers']) * price_per_customer:,} MRR at scale"],
                ["Customer Acquisition Cost", f"${cac_simplified:,}", "Cost to acquire one customer", f"${int(final_base['Total_Customers']) * cac_simplified:,} total"],
                ["Fixed Monthly Costs", f"${fixed_costs:,}", "Recurring operating expenses", f"${fixed_costs * simulation_months:,} total over period"],
                ["Variable Cost", f"${variable_cost}/cust", "Cost to serve each customer", f"${int(final_base['Total_Customers']) * variable_cost:,}/mo at scale"],
                ["Simulation Period", f"{simulation_months} months", "Forecast horizon", "Standard SaaS planning window"],
            ]
            assump_t = Table(assump_data, colWidths=[1.5*inch, 0.85*inch, 1.8*inch, 2.1*inch])
            assump_t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), MEDIUM_BLUE),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('LINEBELOW', (0, 0), (-1, 0), 2, DARK_BLUE),
                ('LINEBELOW', (0, -1), (-1, -1), 1.5, DARK_BLUE),
                ('LINEBEFORE', (1, 0), (1, -1), 1, colors.HexColor('#cfd8dc')),
                ('LINEBEFORE', (2, 0), (2, -1), 1, colors.HexColor('#cfd8dc')),
                ('LINEBEFORE', (3, 0), (3, -1), 1, colors.HexColor('#cfd8dc')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [ROW_WHITE, ROW_ALT]),
                ('TEXTCOLOR', (1, 1), (1, -1), TEXT_BOLD),
                ('FONTNAME', (1, 1), (1, -1), 'Helvetica-Bold'),
            ]))
            elems.append(assump_t)
            elems.append(Spacer(1, 22))
            
            if show_scenarios:
                elems.append(Paragraph("Scenario Comparison Analysis", head_s))
                elems.append(Paragraph("Three scenarios were modeled to understand the range of possible outcomes based on varying growth and churn assumptions.", normal_s))
                elems.append(Spacer(1, 12))
                
                final_opt = df_optimistic.iloc[-1]
                final_pess = df_pessimistic.iloc[-1]
                
                opt_growth = optimistic_growth * 100
                pess_growth = pessimistic_growth * 100
                opt_churn = low_churn_rate * 100
                pess_churn = high_churn_rate * 100
                
                GREEN_CELL = colors.HexColor('#c8e6c9')
                BLUE_CELL = colors.HexColor('#bbdefb')
                RED_CELL = colors.HexColor('#ffcdd2')
                YELLOW_CELL = colors.HexColor('#fff9c4')
                
                scenario_data = [
                    ["📊 Metric", "🌟 Optimistic", "📊 Base Case", "⚠️ Pessimistic", "📐 Range"],
                    ["Growth Rate", f"{opt_growth:.0f}%", f"{monthly_growth_rate*100:.0f}%", f"{pess_growth:.0f}%", f"{(opt_growth-pess_growth):.0f} pp"],
                    ["Churn Rate", f"{opt_churn:.1f}%", f"{churn_rate*100:.1f}%", f"{pess_churn:.1f}%", f"{(pess_churn-opt_churn):.1f} pp"],
                    ["Final MRR", f"${final_opt['MRR']:,.0f}", f"${final_base['MRR']:,.0f}", f"${final_pess['MRR']:,.0f}", f"${(final_opt['MRR']-final_pess['MRR']):,.0f}"],
                    ["Final Customers", f"{int(final_opt['Total_Customers']):,}", f"{int(final_base['Total_Customers']):,}", f"{int(final_pess['Total_Customers']):,}", f"{int(final_opt['Total_Customers']-final_pess['Total_Customers']):,}"],
                    ["Gross Margin", f"{final_opt['Gross_Margin_%']:.1f}%", f"{final_base['Gross_Margin_%']:.1f}%", f"{final_pess['Gross_Margin_%']:.1f}%", f"{(final_opt['Gross_Margin_%']-final_pess['Gross_Margin_%']):.1f} pp"],
                    ["LTV:CAC Ratio", f"{final_opt['LTV_CAC_Ratio']:.2f}x", f"{final_base['LTV_CAC_Ratio']:.2f}x", f"{final_pess['LTV_CAC_Ratio']:.2f}x", f"{(final_opt['LTV_CAC_Ratio']-final_pess['LTV_CAC_Ratio']):.2f}x"],
                    ["Break-even Month", format_breakeven(breakeven_opt), format_breakeven(breakeven_base), format_breakeven(breakeven_pess), "—"],
                    ["Final Cash Position", f"${final_opt['Cumulative_Cash']:,.0f}", f"${final_base['Cumulative_Cash']:,.0f}", f"${final_pess['Cumulative_Cash']:,.0f}", f"${(final_opt['Cumulative_Cash']-final_pess['Cumulative_Cash']):,.0f}"],
                ]
                scenario_t = Table(scenario_data, colWidths=[1.3*inch, 1.05*inch, 1.05*inch, 1.05*inch, 0.9*inch])
                scenario_t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), DARK_BLUE),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                    ('TOPPADDING', (0, 0), (-1, -1), 10),
                    ('LINEBELOW', (0, 0), (-1, 0), 2, MEDIUM_BLUE),
                    ('LINEBELOW', (0, -1), (-1, -1), 1.5, MEDIUM_BLUE),
                    ('LINEBEFORE', (1, 0), (1, -1), 1, colors.HexColor('#cfd8dc')),
                    ('LINEBEFORE', (2, 0), (2, -1), 1, colors.HexColor('#cfd8dc')),
                    ('LINEBEFORE', (3, 0), (3, -1), 1, colors.HexColor('#cfd8dc')),
                    ('LINEBEFORE', (4, 0), (4, -1), 1, colors.HexColor('#cfd8dc')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [ROW_WHITE, ROW_ALT]),
                    ('BACKGROUND', (1, 1), (1, -1), GREEN_CELL),
                    ('BACKGROUND', (2, 1), (2, -1), BLUE_CELL),
                    ('BACKGROUND', (3, 1), (3, -1), RED_CELL),
                    ('BACKGROUND', (4, 1), (4, -1), YELLOW_CELL),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('TEXTCOLOR', (0, 0), (0, -1), DARK_BLUE),
                ]))
                elems.append(scenario_t)
                elems.append(Spacer(1, 18))
                
                elems.append(Paragraph("Scenario Assumptions:", subhead_s))
                scenario_notes = [
                    f"<b>🌟 Optimistic:</b> {opt_growth:.0f}% monthly growth, {opt_churn:.1f}% monthly churn — Best-case with high growth and low churn. Represents ideal market conditions.",
                    f"<b>📊 Base Case:</b> {monthly_growth_rate*100:.0f}% monthly growth, {churn_rate*100:.1f}% monthly churn — Most likely scenario based on current trajectory and market conditions.",
                    f"<b>⚠️ Pessimistic:</b> {pess_growth:.0f}% monthly growth, {pess_churn:.1f}% monthly churn — Worst-case with reduced growth and higher churn. For risk assessment.",
                ]
                for note in scenario_notes:
                    elems.append(Paragraph(f"• {note}", bullet_s))
                elems.append(Spacer(1, 18))
            
            elems.append(Paragraph("Monthly Financial Data", head_s))
            elems.append(Paragraph("Detailed monthly breakdown of key metrics. Data is sampled every month for the full simulation period.", normal_s))
            elems.append(Spacer(1, 12))
            
            monthly_data = [["📅 Month", "👥 Customers", "➕ New", "➖ Churned", "💵 MRR", "💰 Revenue", "📊 Costs", "📈 P&L", "💳 Cash"]]
            for _, row in df_base.iterrows():
                monthly_data.append([
                    f"M{int(row['Month']):02d}",
                    f"{int(row['Total_Customers']):,}",
                    f"+{int(row['New_Customers'])}",
                    f"-{int(row['Churned_Customers'])}",
                    f"${row['MRR']:,.0f}",
                    f"${row['Total_Revenue']:,.0f}",
                    f"${row['Total_Costs']:,.0f}",
                    f"${row['Profit_Loss']:,.0f}",
                    f"${row['Cumulative_Cash']:,.0f}",
                ])
            monthly_t = Table(monthly_data, colWidths=[0.55*inch, 0.75*inch, 0.55*inch, 0.6*inch, 0.75*inch, 0.75*inch, 0.75*inch, 0.7*inch, 0.8*inch])
            monthly_t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), DARK_BLUE),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('LINEBELOW', (0, 0), (-1, 0), 2, MEDIUM_BLUE),
                ('LINEBELOW', (0, -1), (-1, -1), 1.5, MEDIUM_BLUE),
                ('LINEBEFORE', (1, 0), (1, -1), 0.5, colors.HexColor('#cfd8dc')),
                ('LINEBEFORE', (2, 0), (2, -1), 0.5, colors.HexColor('#cfd8dc')),
                ('LINEBEFORE', (3, 0), (3, -1), 0.5, colors.HexColor('#cfd8dc')),
                ('LINEBEFORE', (4, 0), (4, -1), 0.5, colors.HexColor('#cfd8dc')),
                ('LINEBEFORE', (5, 0), (5, -1), 0.5, colors.HexColor('#cfd8dc')),
                ('LINEBEFORE', (6, 0), (6, -1), 0.5, colors.HexColor('#cfd8dc')),
                ('LINEBEFORE', (7, 0), (7, -1), 0.5, colors.HexColor('#cfd8dc')),
                ('LINEBEFORE', (8, 0), (8, -1), 0.5, colors.HexColor('#cfd8dc')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [ROW_WHITE, ROW_ALT]),
            ]))
            elems.append(monthly_t)
            
            elems.append(PageBreak())
            
            elems.append(Paragraph("Data Dictionary & Glossary", head_s))
            elems.append(Paragraph("Reference guide for all metrics and terms used in this report.", normal_s))
            elems.append(Spacer(1, 10))
            
            glossary = [
                ["Term", "Definition", "Formula / Notes"],
                ["MRR (Monthly Recurring Revenue)", "Total predictable revenue generated each month from active subscriptions", "Active Customers × Price per Customer"],
                ["ARR (Annual Recurring Revenue)", "Annualized version of MRR for yearly planning", "MRR × 12"],
                ["Churn Rate", "Percentage of customers who cancel or don't renew in a given period", "Churned Customers / Total Customers × 100"],
                ["Customer Lifetime Value (LTV)", "Total revenue expected from a customer over their entire relationship", "ARPU × Customer Lifetime or Gross Margin per Customer / Churn Rate"],
                ["Customer Acquisition Cost (CAC)", "Total cost to acquire a new customer", "Total Sales & Marketing Costs / New Customers Acquired"],
                ["LTV:CAC Ratio", "Efficiency of customer acquisition investment", "LTV / CAC (Target: ≥3x for healthy SaaS)"],
                ["CAC Payback Period", "Time required to recover the cost of acquiring a customer", "CAC / (ARPU × Gross Margin)"],
                ["Gross Margin", "Revenue remaining after deducting cost of goods sold (COGS)", "(Revenue - COGS) / Revenue × 100"],
                ["Contribution Margin", "Revenue remaining after variable costs", "Revenue - Variable Costs"],
                ["Break-even Point", "When total revenue equals total costs (neither profit nor loss)", "Fixed Costs / Contribution Margin per Customer"],
                ["Cash Runway", "How long the company can operate before running out of cash", "Cash Balance / Monthly Burn Rate"],
                ["Burn Rate", "Net amount of cash spent each month", "Costs - Revenue (for losing money)"],
                ["Net Revenue Retention (NRR)", "Revenue retained from existing customers including expansions and contractions", "Typically calculated over a 12-month period"],
                ["Compound Monthly Growth Rate (CMGR)", "Average monthly growth rate compounded over time", "(Final/Initial)^(1/Months) - 1"],
            ]
            glossary_t = Table(glossary, colWidths=[1.5*inch, 2.5*inch, 2.3*inch])
            glossary_t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), MEDIUM_BLUE),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('LINEBELOW', (0, 0), (-1, 0), 2, DARK_BLUE),
                ('LINEBELOW', (0, -1), (-1, -1), 1.5, DARK_BLUE),
                ('LINEBEFORE', (1, 0), (1, -1), 1, BORDER),
                ('LINEBEFORE', (2, 0), (2, -1), 1, BORDER),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [ROW_WHITE, ROW_ALT]),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('TEXTCOLOR', (0, 1), (0, -1), TEXT_BOLD),
            ]))
            elems.append(glossary_t)
            elems.append(Spacer(1, 20))
            
            elems.append(Paragraph("Methodology Notes", head_s))
            methodology = [
                "This financial model is based on the SaaS Financial Plan 2.0 methodology developed by Christoph Janz (The SaaS Co-Founder Fund).",
                "All projections are based on the assumptions listed in this report and should be validated against actual business data.",
                "The model does not account for external factors such as market conditions, competitive pressures, or macroeconomic trends.",
                "Sensitivity analysis should be conducted to understand the impact of varying key assumptions.",
                "This report is intended for strategic planning purposes and should not be used as the sole basis for investment decisions.",
            ]
            for note in methodology:
                elems.append(Paragraph(f"• {note}", bullet_s))
            
            elems.append(Spacer(1, 20))
            elems.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#bdc3c7'), spaceAfter=10))
            elems.append(Paragraph("Generated by BahnSetu SaaS Financial Dashboard | Based on SaaS Financial Plan 2.0 by Christoph Janz", footer_s))
            
            doc.build(elems)
            buf.seek(0)
            pdf_bytes = buf.getvalue()
        
        st.download_button("📑 Complete PDF Report", pdf_bytes, f"saas_report_{scenario_name.replace(' ', '_').lower()}.pdf", "application/pdf", use_container_width=True)
    
    with pdf_cols[1]:
        with st.spinner("Generating Charts Report..."):
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Image as RLImage, Spacer, PageBreak, Table, TableStyle, HRFlowable
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.enums import TA_CENTER
            from datetime import datetime
            
            buf = BytesIO()
            doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=0.5*inch, leftMargin=0.5*inch, topMargin=0.5*inch, bottomMargin=0.5*inch)
            styles = getSampleStyleSheet()
            
            title_s = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, spaceAfter=8, alignment=TA_CENTER, textColor=DARK_BLUE, fontName='Helvetica-Bold')
            subtitle_s = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=12, spaceAfter=6, alignment=TA_CENTER, textColor=colors.HexColor('#546e7a'))
            head_s = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, spaceAfter=12, spaceBefore=15, textColor=MEDIUM_BLUE, fontName='Helvetica-Bold')
            caption_s = ParagraphStyle('Caption', parent=styles['Normal'], fontSize=9, spaceAfter=15, textColor=TEXT_DARK, alignment=TA_CENTER)
            footer_s = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER, textColor=colors.grey)
            
            DARK_BLUE = colors.HexColor('#1a237e')
            MEDIUM_BLUE = colors.HexColor('#0277bd')
            LIGHT_BLUE = colors.HexColor('#e3f2fd')
            ROW_ALT = colors.HexColor('#f5f5f5')
            ROW_WHITE = colors.white
            BORDER = colors.HexColor('#90a4ae')
            TEXT_DARK = colors.HexColor('#263238')
            TEXT_BOLD = colors.HexColor('#1a237e')
            GREEN_CELL = colors.HexColor('#c8e6c9')
            BLUE_CELL = colors.HexColor('#bbdefb')
            YELLOW_CELL = colors.HexColor('#fff9c4')
            
            final_base = df_base.iloc[-1]
            breakeven_text = format_breakeven(breakeven_base)
            
            elems = []
            elems.append(HRFlowable(width="100%", thickness=3, color=colors.HexColor('#0d1b3e'), spaceAfter=15))
            elems.append(Paragraph("Charts & Visual Analysis", title_s))
            elems.append(Paragraph(f"<b>{scenario_name}</b>", subtitle_s))
            elems.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')} | {simulation_months}-Month Forecast", subtitle_s))
            elems.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#bdc3c7'), spaceBefore=10, spaceAfter=20))
            
            elems.append(Paragraph("Key Highlights at a Glance", head_s))
            highlights_data = [
                ["📊 Metric", "💰 Value"],
                ["Final MRR", f"${final_base['MRR']:,.0f}"],
                ["Final Customers", f"{int(final_base['Total_Customers']):,}"],
                ["LTV:CAC Ratio", f"{final_base['LTV_CAC_Ratio']:.2f}x"],
                ["Break-even Point", breakeven_text],
            ]
            highlights_t = Table(highlights_data, colWidths=[1.8*inch, 1.5*inch])
            highlights_t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), DARK_BLUE),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('LINEBELOW', (0, 0), (-1, 0), 2, MEDIUM_BLUE),
                ('LINEBELOW', (0, -1), (-1, -1), 1.5, MEDIUM_BLUE),
                ('LINEBEFORE', (1, 0), (1, -1), 1, BORDER),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [ROW_WHITE, ROW_ALT]),
                ('FONTNAME', (1, 1), (1, -1), 'Helvetica-Bold'),
                ('TEXTCOLOR', (1, 1), (1, -1), TEXT_BOLD),
            ]))
            elems.append(highlights_t)
            elems.append(Spacer(1, 20))
            
            chart_info = [
                ("Customer Growth", bytes_list[0], f"Shows the trajectory of customer acquisition over {simulation_months} months. Net customer growth is {int(final_base['Total_Customers'] - starting_customers):,} customers."),
                ("Monthly Recurring Revenue (MRR)", bytes_list[1], f"Revenue progression from ${df_base.iloc[0]['MRR']:,.0f} to ${final_base['MRR']:,.0f} - a {((final_base['MRR']/df_base.iloc[0]['MRR'])-1)*100:.0f}% increase."),
                ("Cumulative Cash Position", bytes_list[2], f"Tracks cash flow. Break-even achieved at {breakeven_text}. Final cash position: ${final_base['Cumulative_Cash']:,.0f}."),
                ("LTV:CAC Ratio Trend", bytes_list[3], f"Unit economics metric. Target is 3x. Final ratio: {final_base['LTV_CAC_Ratio']:.2f}x."),
            ]
            
            for title, img_bytes, caption in chart_info:
                elems.append(Paragraph(title, head_s))
                elems.append(RLImage(BytesIO(img_bytes), width=6.5*inch, height=3.5*inch))
                elems.append(Paragraph(caption, caption_s))
                elems.append(Spacer(1, 10))
            
            elems.append(Spacer(1, 15))
            elems.append(HRFlowable(width="100%", thickness=3, color=DARK_BLUE, spaceAfter=10))
            elems.append(Paragraph("Generated by BahnSetu SaaS Financial Dashboard | Based on SaaS Financial Plan 2.0", footer_s))
            
            doc.build(elems)
            buf.seek(0)
            charts_pdf = buf.getvalue()
        
        st.download_button("📊 Charts Only PDF", charts_pdf, f"charts_{scenario_name.replace(' ', '_').lower()}.pdf", "application/pdf", use_container_width=True)
    
    with pdf_cols[2]:
        with st.spinner("Generating Tables Report..."):
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.enums import TA_CENTER
            from datetime import datetime
            
            buf = BytesIO()
            doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=0.4*inch, leftMargin=0.4*inch, topMargin=0.4*inch, bottomMargin=0.4*inch)
            styles = getSampleStyleSheet()
            
            title_s = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, spaceAfter=8, alignment=TA_CENTER, textColor=DARK_BLUE, fontName='Helvetica-Bold')
            subtitle_s = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=12, spaceAfter=6, alignment=TA_CENTER, textColor=colors.HexColor('#546e7a'))
            head_s = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, spaceAfter=12, spaceBefore=15, textColor=MEDIUM_BLUE, fontName='Helvetica-Bold')
            footer_s = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER, textColor=colors.grey)
            
            DARK_BLUE = colors.HexColor('#1a237e')
            MEDIUM_BLUE = colors.HexColor('#0277bd')
            LIGHT_BLUE = colors.HexColor('#e3f2fd')
            ROW_ALT = colors.HexColor('#f5f5f5')
            ROW_WHITE = colors.white
            BORDER = colors.HexColor('#90a4ae')
            TEXT_DARK = colors.HexColor('#263238')
            TEXT_BOLD = colors.HexColor('#1a237e')
            
            final_base = df_base.iloc[-1]
            
            elems = []
            elems.append(HRFlowable(width="100%", thickness=3, color=DARK_BLUE, spaceAfter=15))
            elems.append(Paragraph("Data Tables Report", title_s))
            elems.append(Paragraph(f"<b>{scenario_name}</b>", subtitle_s))
            elems.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')} | {simulation_months}-Month Simulation", subtitle_s))
            elems.append(HRFlowable(width="100%", thickness=1, color=BORDER, spaceBefore=10, spaceAfter=15))
            
            elems.append(Paragraph("Monthly Financial Summary", head_s))
            monthly_data = [["📅 Month", "👥 Customers", "➕ New", "➖ Churned", "💵 MRR", "💰 Revenue", "📊 Costs", "📈 P&L", "💳 Cash"]]
            for _, row in df_base.iterrows():
                monthly_data.append([
                    f"M{int(row['Month']):02d}",
                    f"{int(row['Total_Customers']):,}",
                    f"+{int(row['New_Customers'])}",
                    f"-{int(row['Churned_Customers'])}",
                    f"${row['MRR']:,.0f}",
                    f"${row['Total_Revenue']:,.0f}",
                    f"${row['Total_Costs']:,.0f}",
                    f"${row['Profit_Loss']:,.0f}",
                    f"${row['Cumulative_Cash']:,.0f}",
                ])
            monthly_t = Table(monthly_data, colWidths=[0.55*inch, 0.7*inch, 0.5*inch, 0.55*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.65*inch, 0.75*inch])
            monthly_t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), DARK_BLUE),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
                ('TOPPADDING', (0, 0), (-1, -1), 7),
                ('LINEBELOW', (0, 0), (-1, 0), 2, MEDIUM_BLUE),
                ('LINEBELOW', (0, -1), (-1, -1), 1.5, MEDIUM_BLUE),
                ('LINEBEFORE', (1, 0), (1, -1), 0.5, BORDER),
                ('LINEBEFORE', (2, 0), (2, -1), 0.5, BORDER),
                ('LINEBEFORE', (3, 0), (3, -1), 0.5, BORDER),
                ('LINEBEFORE', (4, 0), (4, -1), 0.5, BORDER),
                ('LINEBEFORE', (5, 0), (5, -1), 0.5, BORDER),
                ('LINEBEFORE', (6, 0), (6, -1), 0.5, BORDER),
                ('LINEBEFORE', (7, 0), (7, -1), 0.5, BORDER),
                ('LINEBEFORE', (8, 0), (8, -1), 0.5, BORDER),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [ROW_WHITE, ROW_ALT]),
            ]))
            elems.append(monthly_t)
            elems.append(Spacer(1, 15))
            
            elems.append(Paragraph("Key Metrics by Month", head_s))
            metrics_data = [["📅 Month", "📊 Gross Margin", "💎 LTV:CAC", "⏱️ CAC Payback", "📈 MoM Growth"]]
            for _, row in df_base.iterrows():
                metrics_data.append([
                    f"M{int(row['Month']):02d}",
                    f"{row['Gross_Margin_%']:.1f}%",
                    f"{row['LTV_CAC_Ratio']:.2f}x",
                    f"{row.get('CAC_Payback_Pro', 0):.1f} mo",
                    f"{row['MoM_Growth_%']:.1f}%",
                ])
            metrics_t = Table(metrics_data, colWidths=[0.65*inch, 1.05*inch, 0.95*inch, 1.05*inch, 0.95*inch])
            metrics_t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), MEDIUM_BLUE),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('LINEBELOW', (0, 0), (-1, 0), 2, DARK_BLUE),
                ('LINEBELOW', (0, -1), (-1, -1), 1.5, DARK_BLUE),
                ('LINEBEFORE', (1, 0), (1, -1), 0.5, BORDER),
                ('LINEBEFORE', (2, 0), (2, -1), 0.5, BORDER),
                ('LINEBEFORE', (3, 0), (3, -1), 0.5, BORDER),
                ('LINEBEFORE', (4, 0), (4, -1), 0.5, BORDER),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [ROW_WHITE, ROW_ALT]),
            ]))
            elems.append(metrics_t)
            
            elems.append(Spacer(1, 15))
            
            elems.append(Paragraph("Departmental Costs", head_s))
            dept_data = [["📅 Month", "🏭 COGS", "🔬 R&D", "📣 Sales & Mktg", "📋 G&A", "🤝 Customer Success"]]
            for _, row in df_base.iterrows():
                dept_data.append([
                    f"M{int(row['Month']):02d}",
                    f"${row['COGS']:,.0f}",
                    f"${row['RD_Cost']:,.0f}",
                    f"${row['SM_Cost']:,.0f}",
                    f"${row['GA_Cost']:,.0f}",
                    f"${row['CS_Cost']:,.0f}",
                ])
            dept_t = Table(dept_data, colWidths=[0.55*inch, 0.85*inch, 0.85*inch, 0.95*inch, 0.85*inch, 1.0*inch])
            dept_t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), TEXT_BOLD),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
                ('TOPPADDING', (0, 0), (-1, -1), 7),
                ('LINEBELOW', (0, 0), (-1, 0), 2, MEDIUM_BLUE),
                ('LINEBELOW', (0, -1), (-1, -1), 1.5, MEDIUM_BLUE),
                ('LINEBEFORE', (1, 0), (1, -1), 0.5, BORDER),
                ('LINEBEFORE', (2, 0), (2, -1), 0.5, BORDER),
                ('LINEBEFORE', (3, 0), (3, -1), 0.5, BORDER),
                ('LINEBEFORE', (4, 0), (4, -1), 0.5, BORDER),
                ('LINEBEFORE', (5, 0), (5, -1), 0.5, BORDER),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [ROW_WHITE, ROW_ALT]),
            ]))
            elems.append(dept_t)
            
            elems.append(Spacer(1, 15))
            elems.append(HRFlowable(width="100%", thickness=3, color=DARK_BLUE, spaceAfter=10))
            elems.append(Paragraph("Generated by BahnSetu SaaS Financial Dashboard | Based on SaaS Financial Plan 2.0", footer_s))
            
            doc.build(elems)
            buf.seek(0)
            tables_pdf = buf.getvalue()
        
        st.download_button("📋 Tables Only PDF", tables_pdf, f"tables_{scenario_name.replace(' ', '_').lower()}.pdf", "application/pdf", use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")
st.markdown(f"""
<div style="text-align: center; color: #4a6fa5; font-family: 'IBM Plex Mono'; font-size: 0.8rem;">
    📊 Scenario: {scenario_name} | Real-Time Analysis // Updates on every slider change<br>
    🎭 3-Way Scenarios: Optimistic/Base/Pessimistic | 🔬 Sensitivity Analysis: Churn/Growth/Price
</div>
""", unsafe_allow_html=True)
