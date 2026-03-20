import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
    
    .stButton > button {
        background: linear-gradient(135deg, #0d47a1 0%, #1565c0 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #1565c0 0%, #0288d1 100%);
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
    <div class="header-sub">BahnSetu Financial Simulator // Backend Analysis Tool</div>
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
        high_churn_mult = st.slider(
            "High Churn Multiplier",
            min_value=1.0, max_value=5.0,
            value=2.0, step=0.5,
            key="fc_hcmult"
        )
    
    with col4:
        st.markdown("**⏱️ Simulation**")
        simulation_months = st.slider(
            "Simulation Period (months)",
            min_value=12, max_value=60,
            value=24, step=6,
            key="fc_months"
        )
        show_comparison = st.checkbox(
            "Show Scenario Comparison",
            value=True,
            key="fc_compare"
        )
        scenario_name = st.text_input(
            "Scenario Name",
            value="Custom Scenario",
            key="fc_name"
        )

high_churn_rate = churn_rate * high_churn_mult

st.markdown("---")

if st.button("🚀 Run Simulation", type="primary", use_container_width=True):
    config_base = SaaSModelConfig(
        starting_customers=starting_customers,
        monthly_growth_rate=monthly_growth_rate,
        churn_rate=churn_rate,
        price_per_customer=price_per_customer,
        fixed_costs=fixed_costs,
        variable_cost_per_customer=variable_cost,
        cac_simplified=cac_simplified
    )
    
    config_high = SaaSModelConfig(
        starting_customers=starting_customers,
        monthly_growth_rate=monthly_growth_rate,
        churn_rate=high_churn_rate,
        price_per_customer=price_per_customer,
        fixed_costs=fixed_costs,
        variable_cost_per_customer=variable_cost,
        cac_simplified=cac_simplified
    )
    
    with st.spinner("Running simulation..."):
        df_base = run_simulation(config_base, months=simulation_months)
        df_high = run_simulation(config_high, months=simulation_months)
        
        os.makedirs("output", exist_ok=True)
        df_base.to_csv(f"output/simulation_{scenario_name.replace(' ', '_').lower()}_base.csv", index=False)
        df_high.to_csv(f"output/simulation_{scenario_name.replace(' ', '_').lower()}_high_churn.csv", index=False)
    
    st.success(f"✅ Simulation complete! Results saved to output/ directory.")
    
    st.markdown('<div class="section-heading">📊 Key Performance Indicators</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    final_base = df_base.iloc[-1]
    final_high = df_high.iloc[-1]
    
    kpis = [
        (col1, "FINAL MRR", f"${final_base['MRR']:,.0f}", "Base Case", "green"),
        (col2, "HIGH CHURN MRR", f"${final_high['MRR']:,.0f}", "High Churn", "alert"),
        (col3, "CUSTOMERS", f"{int(final_base['Total_Customers'])}", "Base Case", ""),
        (col4, "CHURNED", f"{int(final_high['Churn_Rate_%'])}%", "High Churn", "alert"),
        (col5, "GROSS MARGIN", f"{final_base['Gross_Margin_%']:.1f}%", "Base Case", "green"),
        (col6, "LTV:CAC", f"{final_base['LTV_CAC_Ratio']:.1f}x", "Base Case", ""),
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
    
    st.markdown('<div class="section-heading">📈 Customer Growth</div>', unsafe_allow_html=True)
    
    if show_comparison:
        fig = go.Figure()
        fig.add_scatter(x=df_base["Month"], y=df_base["Total_Customers"],
                        name="Base Case", mode="lines+markers",
                        line=dict(color="#2980b9", width=2), marker=dict(size=5))
        fig.add_scatter(x=df_high["Month"], y=df_high["Total_Customers"],
                        name=f"High Churn ({high_churn_rate*100:.0f}%)", 
                        mode="lines+markers", line=dict(color="#e74c3c", width=2, dash="dash"))
        fig.update_layout(title="Total Customers Over Time", **fin_fig())
        st.plotly_chart(fig, use_container_width=True)
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
        if show_comparison:
            fig = go.Figure()
            fig.add_scatter(x=df_base["Month"], y=df_base["MRR"],
                           name="Base Case", mode="lines+markers",
                           line=dict(color="#27ae60", width=2))
            fig.add_scatter(x=df_high["Month"], y=df_high["MRR"],
                           name=f"High Churn", mode="lines+markers",
                           line=dict(color="#e74c3c", width=2, dash="dash"))
            fig.update_layout(title="MRR Comparison", **fin_fig())
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
                       name="Base Case", mode="lines+markers",
                       line=dict(color="#2980b9", width=2))
        if show_comparison:
            fig.add_scatter(x=df_high["Month"], y=df_high["MoM_Growth_%"],
                           name="High Churn", mode="lines+markers",
                           line=dict(color="#e74c3c", width=2, dash="dash"))
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
        fig.add_scatter(x=df_base["Month"], y=df_base["SM_Efficiency"],
                       name="S&M Efficiency", mode="lines+markers",
                       line=dict(color="#2980b9", width=2.5),
                       fill="tozeroy", fillcolor="rgba(41,128,185,0.08)")
        fig.add_hline(y=1.0, line_color="#e74c3c", line_dash="dash",
                     annotation_text="1.0x Break-even")
        fig.update_layout(title="Sales & Marketing Efficiency", **fin_fig())
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown('<div class="section-heading">📋 Detailed Results Table</div>', unsafe_allow_html=True)
    
    display_cols = ["Month", "Total_Customers", "New_Customers", "Churned_Customers",
                   "MRR", "ARR", "Gross_Profit", "Total_Costs", "Profit_Loss",
                   "Cumulative_Cash", "Churn_Rate_%", "LTV_CAC_Ratio"]
    
    tab1, tab2 = st.tabs(["Base Case", "High Churn"])
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
        st.dataframe(df_high[display_cols].style.format({
            "MRR": "${:,.0f}",
            "ARR": "${:,.0f}",
            "Gross_Profit": "${:,.0f}",
            "Total_Costs": "${:,.0f}",
            "Profit_Loss": "${:,.0f}",
            "Cumulative_Cash": "${:,.0f}",
            "Churn_Rate_%": "{:.1f}%",
            "LTV_CAC_Ratio": "{:.2f}x"
        }), use_container_width=True, hide_index=True)
    
    st.markdown('<div class="section-heading">📝 Model Summary</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        **Base Case Scenario ({churn_rate*100:.0f}% churn)**  
        - Final MRR: ${final_base['MRR']:,.0f}  
        - Final Customers: {int(final_base['Total_Customers'])}  
        - Final Cumulative Cash: ${final_base['Cumulative_Cash']:,.0f}  
        - Total Churned (24mo): {int(df_base['Churned_Customers'].sum())}  
        - Final LTV:CAC: {final_base['LTV_CAC_Ratio']:.2f}x  
        - Final Headcount: {int(final_base['Total_Headcount'])}
        """)
    with col2:
        st.markdown(f"""
        **High Churn Scenario ({high_churn_rate*100:.0f}% churn)**  
        - Final MRR: ${final_high['MRR']:,.0f}  
        - Final Customers: {int(final_high['Total_Customers'])}  
        - Final Cumulative Cash: ${final_high['Cumulative_Cash']:,.0f}  
        - Total Churned (24mo): {int(df_high['Churned_Customers'].sum())}  
        - Final LTV:CAC: {final_high['LTV_CAC_Ratio']:.2f}x  
        - Final Headcount: {int(final_high['Total_Headcount'])}
        """)
    
    breakeven_base = df_base[df_base['Cumulative_Cash'] >= 0]['Month'].min()
    breakeven_high = df_high[df_high['Cumulative_Cash'] >= 0]['Month'].min()
    
    col1, col2 = st.columns(2)
    with col1:
        if pd.notna(breakeven_base):
            st.success(f"✅ Base Case Break-even: Month {int(breakeven_base)}")
        else:
            st.warning(f"⚠️ Base Case Break-even: Not achieved within {simulation_months} months")
    with col2:
        if pd.notna(breakeven_high):
            st.success(f"✅ High Churn Break-even: Month {int(breakeven_high)}")
        else:
            st.warning(f"⚠️ High Churn Break-even: Not achieved within {simulation_months} months")
    
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: #4a6fa5; font-family: 'IBM Plex Mono'; font-size: 0.8rem;">
        💾 Results saved to: <code>output/simulation_{scenario_name.replace(' ', '_').lower()}_*.csv</code><br>
        📊 Scenario: {scenario_name} | Growth: {monthly_growth_rate*100:.0f}% | Churn: {churn_rate*100:.0f}% / {high_churn_rate*100:.0f}%
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("👈 Configure your model parameters above and click **Run Simulation** to generate results.")
    
    st.markdown('<div class="section-heading">📖 Quick Start Guide</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **1. Customer Parameters**  
        - Start with a realistic customer base (10-100 for early stage)  
        - Growth rate of 15-25% is typical for healthy SaaS  
        - Churn rate of 3-7% is industry standard
        
        **2. Revenue Settings**  
        - Price per customer should match your target market  
        - Consider tiered pricing for enterprise vs SMB  
        - CAC should reflect your actual marketing spend
        """)
    with col2:
        st.markdown("""
        **3. Cost Structure**  
        - Fixed costs include G&A, office, admin  
        - Variable costs are COGS per customer  
        - Headcount grows with customer base
        
        **4. Key Benchmarks**  
        - LTV:CAC > 3:1 is healthy  
        - CAC Payback < 12 months is ideal  
        - Gross Margin > 70% is SaaS standard
        """)
