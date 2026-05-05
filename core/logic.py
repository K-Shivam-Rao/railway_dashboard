import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from typing import Dict, List, Tuple, Optional

from utils.exceptions import DataValidationError, SimulationError, ConfigurationError

# Import sample data functions
SAMPLE_DATA_AVAILABLE = False
try:
    from data.sample_data import (
        get_customer_df, get_rfm_df, get_customer_insights,
        get_station_df, get_operator_profile,
        get_contract_health_df, get_renewal_forecast_df,
        get_at_risk_df, get_renewal_health_summary,
        get_high_value_customers_df, get_operator_history,
        get_support_tickets, get_engagement_timeline,
        get_operator_monthly_stats, get_contract_amendments,
        get_financial_projections, get_operator_comparison_benchmarks,
        get_support_ticket_trend, get_business_map_data,
        get_leadership_data,
    )
    SAMPLE_DATA_AVAILABLE = True
    logger.info("Successfully loaded sample data functions")
except ImportError as e:
    logger.error(f"Failed to import sample_data module: {e}")
    logger.warning("Customer/operator data will not be available")


# ─────────────────────────────────────
# SAAS FINANCIAL MODEL
# ─────────────────────────────────────

class SaaSModelConfig:
    """
    Configuration class for SaaS Financial Model parameters.
    """

    def __init__(self, starting_customers, monthly_growth_rate, churn_rate,
                 price_per_customer, fixed_costs, variable_cost_per_customer,
                 cac_simplified=100,
                 # Department headcount starting points
                 initial_eng=5, initial_sales=3, initial_marketing=2,
                 initial_cs=2, initial_ga=2,
                 # Revenue split across tiers
                 basic_pct=0.5, pro_pct=0.35, enterprise_pct=0.15,
                 basic_price=49, pro_price=99, enterprise_price=299):

        # Validate inputs
        if starting_customers < 0:
            raise ConfigurationError(f"starting_customers must be non-negative, got {starting_customers}")
        if not (0 <= monthly_growth_rate <= 1):
            raise ConfigurationError(f"monthly_growth_rate must be between 0 and 1, got {monthly_growth_rate}")
        if not (0 <= churn_rate <= 1):
            raise ConfigurationError(f"churn_rate must be between 0 and 1, got {churn_rate}")
        if price_per_customer < 0:
            raise ConfigurationError(f"price_per_customer must be non-negative, got {price_per_customer}")
        if fixed_costs < 0:
            raise ConfigurationError(f"fixed_costs must be non-negative, got {fixed_costs}")
        if variable_cost_per_customer < 0:
            raise ConfigurationError(f"variable_cost_per_customer must be non-negative, got {variable_cost_per_customer}")

        self.customers = starting_customers
        self.growth_rate = monthly_growth_rate
        self.churn_rate = churn_rate
        self.price = price_per_customer
        self.fixed_costs = fixed_costs
        self.variable_cost = variable_cost_per_customer
        self.cac = cac_simplified

        # Headcount seeds
        self.initial_eng = initial_eng
        self.initial_sales = initial_sales
        self.initial_marketing = initial_marketing
        self.initial_cs = initial_cs
        self.initial_ga = initial_ga

        # Pricing tier mix
        self.basic_pct = basic_pct
        self.pro_pct = pro_pct
        self.enterprise_pct = enterprise_pct
        self.basic_price = basic_price
        self.pro_price = pro_price
        self.enterprise_price = enterprise_price

        # Avg salary per department per head (monthly)
        self.salary = {
            "Engineering": 8500,
            "Sales": 6000,
            "Marketing": 5500,
            "CS": 4500,
            "G&A": 5000,
        }

    def __repr__(self):
        return (f"SaaSConfig(Start={self.customers}, Growth={self.growth_rate*100}%, "
                f"Churn={self.churn_rate*100}%, Price=${self.price})")


def run_simulation(config, months=24):
    """
    Simulates the SaaS metrics over a specified number of months.
    Returns a Pandas DataFrame with all calculated metrics.
    """
    try:
        data = []

        current_customers = config.customers
        cumulative_cash = -(current_customers * config.cac)

        # Headcount state
        hc = {
            "Engineering": config.initial_eng,
            "Sales":        config.initial_sales,
            "Marketing":    config.initial_marketing,
            "CS":           config.initial_cs,
            "G&A":          config.initial_ga,
        }

        prev_mrr = None

        for month in range(1, months + 1):

            # ── Customer movements ──────────────────────────────────────────
            new_customers = int(current_customers * config.growth_rate)
            churned_customers = int(current_customers * config.churn_rate)

            # Expansion MRR: existing customers upgrading (simplified: 2% of base)
            expansion_customers = int(current_customers * 0.02)
            expansion_mrr = expansion_customers * (config.price * 0.20)   # 20% ARPU uplift

            total_customers = current_customers + new_customers - churned_customers

            # ── Pricing tier breakdown ──────────────────────────────────────────
            basic_cust      = int(total_customers * config.basic_pct)
            pro_cust        = int(total_customers * config.pro_pct)
            enterprise_cust = total_customers - basic_cust - pro_cust

            tier_mrr = (basic_cust * config.basic_price
                        + pro_cust * config.pro_price
                        + enterprise_cust * config.enterprise_price)

            # Use tier_mrr as the canonical MRR
            new_mrr      = new_customers * config.price
            churn_mrr    = churned_customers * config.price
            net_new_mrr  = new_mrr - churn_mrr + expansion_mrr
            mrr          = tier_mrr

            mom_growth   = ((mrr - prev_mrr) / prev_mrr * 100) if prev_mrr else 0

            # ── Core SaaS metrics ─────────────────────────────────────────────
            churn_pct          = (churned_customers / current_customers * 100
                                   if current_customers > 0 else 0)
            contribution_margin = config.price - config.variable_cost
            ltv                = (contribution_margin / config.churn_rate
                                   if config.churn_rate > 0 else 0)
            ltv_cac_ratio      = ltv / config.cac if config.cac > 0 else 0

            # CAC Payback (months to recover CAC from gross profit per customer)
            gross_profit_per_cust = config.price - config.variable_cost
            cac_payback_basic      = config.cac / (config.basic_price      - config.variable_cost) if (config.basic_price      - config.variable_cost) > 0 else 0
            cac_payback_pro        = config.cac / (config.pro_price        - config.variable_cost) if (config.pro_price        - config.variable_cost) > 0 else 0
            cac_payback_enterprise = config.cac / (config.enterprise_price - config.variable_cost) if (config.enterprise_price - config.variable_cost) > 0 else 0

            total_cac_spent    = new_customers * config.cac

            # ── Headcount (hire 1 per dept every ~4-6 months scaled by customers) ─
            for dept, threshold in [("Engineering", 30), ("Sales", 20),
                                 ("Marketing", 25), ("CS", 35), ("G&A", 50)]:
                if total_customers // threshold > (current_customers // threshold):
                    hc[dept] += 1

            total_headcount = sum(hc.values())

            # ── Salary costs ─────────────────────────────────────────────────────
            salary_eng       = hc["Engineering"] * config.salary["Engineering"]
            salary_sales     = hc["Sales"]       * config.salary["Sales"]
            salary_marketing = hc["Marketing"]   * config.salary["Marketing"]
            salary_cs        = hc["CS"]          * config.salary["CS"]
            salary_ga        = hc["G&A"]         * config.salary["G&A"]
            total_salaries   = salary_eng + salary_sales + salary_marketing + salary_cs + salary_ga

            # ── Cost breakdown by P&L category ──────────────────────────────────
            cogs              = total_customers * config.variable_cost          # Cost of Goods Sold
            rd_cost           = salary_eng                                       # R&D ≈ Engineering salaries
            sm_cost           = salary_sales + salary_marketing + total_cac_spent  # Sales & Marketing
            ga_cost           = salary_ga + config.fixed_costs                  # G&A
            total_costs       = cogs + rd_cost + sm_cost + ga_cost + salary_cs

            # ── Gross Profit ─────────────────────────────────────────────────────
            gross_profit      = mrr - cogs
            gross_margin_pct  = (gross_profit / mrr * 100) if mrr > 0 else 0

            # ── EBIT ─────────────────────────────────────────────────────────────
            ebit = mrr - total_costs

            # ── Sales & Marketing Efficiency (New MRR / S&M spend) ───────────────
            sm_efficiency = net_new_mrr / sm_cost if sm_cost > 0 else 0

            # ── ARR ──────────────────────────────────────────────────────────────
            arr = mrr * 12

            # ── Cash Flow ────────────────────────────────────────────────────────
            profit_loss    = mrr - total_costs
            cumulative_cash += profit_loss

            # ── Enterprise customer wins/losses ──────────────────────────────────
            new_enterprise      = max(1, int(new_customers      * config.enterprise_pct))
            lost_enterprise     = max(0, int(churned_customers  * config.enterprise_pct))
            upgrade_to_enterprise = max(0, int(expansion_customers * 0.3))

            row = {
                # Time
                "Month":                  month,

                # Customer movements
                "Start_Customers":        current_customers,
                "New_Customers":          new_customers,
                "Churned_Customers":      churned_customers,
                "Total_Customers":        total_customers,

                # Tier breakdown
                "Basic_Customers":        basic_cust,
                "Pro_Customers":          pro_cust,
                "Enterprise_Customers":   enterprise_cust,

                # MRR movements
                "New_MRR":                round(new_mrr, 2),
                "Churn_MRR":              round(-churn_mrr, 2),
                "Expansion_MRR":          round(expansion_mrr, 2),
                "Net_New_MRR":            round(net_new_mrr, 2),
                "MRR":                    round(mrr, 2),
                "ARR":                    round(arr, 2),
                "MoM_Growth_%":           round(mom_growth, 2),

                # SaaS metrics
                "Churn_Rate_%":           round(churn_pct, 2),
                "LTV":                    round(ltv, 2),
                "CAC":                    config.cac,
                "LTV_CAC_Ratio":          round(ltv_cac_ratio, 2),
                "CAC_Payback_Basic":      round(cac_payback_basic, 2),
                "CAC_Payback_Pro":        round(cac_payback_pro, 2),
                "CAC_Payback_Enterprise": round(cac_payback_enterprise, 2),
                "Contribution_Margin_$":  round(contribution_margin, 2),

                # Financials
                "Total_Revenue":          round(mrr, 2),
                "Gross_Profit":           round(gross_profit, 2),
                "Gross_Margin_%":         round(gross_margin_pct, 2),
                "COGS":                   round(cogs, 2),
                "RD_Cost":                round(rd_cost, 2),
                "SM_Cost":                round(sm_cost, 2),
                "GA_Cost":                round(ga_cost, 2),
                "CS_Cost":                round(salary_cs, 2),
                "Total_Costs":            round(total_costs, 2),
                "EBIT":                   round(ebit, 2),
                "Profit_Loss":            round(profit_loss, 2),
                "Cumulative_Cash":        round(cumulative_cash, 2),

                # Efficiency
                "SM_Efficiency":          round(sm_efficiency, 4),

                # Headcount
                "HC_Engineering":         hc["Engineering"],
                "HC_Sales":               hc["Sales"],
                "HC_Marketing":           hc["Marketing"],
                "HC_CS":                  hc["CS"],
                "HC_GA":                  hc["G&A"],
                "Total_Headcount":        total_headcount,

                # Salaries
                "Salary_Engineering":     salary_eng,
                "Salary_Sales":           salary_sales,
                "Salary_Marketing":       salary_marketing,
                "Salary_CS":              salary_cs,
                "Salary_GA":              salary_ga,
                "Total_Salaries":         total_salaries,

                # Enterprise wins/losses
                "New_Enterprise_Wins":    new_enterprise,
                "Enterprise_Upgrades":    upgrade_to_enterprise,
                "Lost_Enterprise":        lost_enterprise,
            }
            data.append(row)

            prev_mrr           = mrr
            current_customers  = total_customers

        df = pd.DataFrame(data)
        return df

    except Exception as e:
        raise SimulationError(f"Simulation failed: {e}")


def print_summary(df, config):
    logger.info("="*50 + " FINANCIAL SIMULATION SUMMARY " + "="*50)
    logger.info(f"Assumptions: Start={config.customers}, Growth={config.growth_rate*100}%, Churn={config.churn_rate*100}%")
    logger.info(f"Price: ${config.price}, Fixed Costs: ${config.fixed_costs:,}")
    logger.info("-" * 50)

    breakeven_month = df[df['Cumulative_Cash'] >= 0]['Month'].min()
    if pd.notna(breakeven_month):
        logger.info(f"[OK]    Break-even Month   : Month {int(breakeven_month)}")
    else:
        logger.warning(f"[ERROR] Break-even         : Not reached within {len(df)} months")

    final = df.iloc[-1]
    logger.info(f"[MRR]   Final MRR          : ${final['MRR']:,.0f}")
    logger.info(f"[ARR]   Final ARR          : ${final['ARR']:,.0f}")
    logger.info(f"[USERS] Final Customers    : {int(final['Total_Customers'])}")
    logger.info(f"[CASH]  Final Cum. Cash    : ${final['Cumulative_Cash']:,.0f}")
    logger.info(f"[MARGIN]Final Gross Margin : {final['Gross_Margin_%']:.1f}%")
    logger.info(f"[HC]    Final Headcount    : {int(final['Total_Headcount'])}")
    logger.info(f"[LTV]   LTV/CAC Ratio      : {final['LTV_CAC_Ratio']:.2f}x")

    total_lost   = df['Churned_Customers'].sum()
    total_gained = df['New_Customers'].sum()
    logger.warning(f"[WARN]  Total Churned      : {int(total_lost)} ({(total_lost/total_gained)*100:.1f}% of gains)")
    logger.info("="*50)


# ─────────────────────────────────────
# SAAS VISUALIZATION FUNCTIONS
# ─────────────────────────────────────

def visualize_results(df, title_suffix=""):
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # Chart 1: Customers Growth
    ax = axes[0]
    ax.plot(df['Month'], df['Total_Customers'], marker='o', color='tab:blue', label='Total Customers')
    ax.bar(df['Month'], df['New_Customers'], color='tab:green', alpha=0.3, label='New Customers')
    ax.set_title('Customer Growth')
    ax.set_xlabel('Month')
    ax.set_ylabel('Customers')
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.6)

    # Chart 2: MRR Growth
    ax = axes[1]
    ax.plot(df['Month'], df['MRR'], marker='s', color='tab:orange')
    ax.set_title('MRR Growth')
    ax.set_xlabel('Month')
    ax.set_ylabel('MRR ($)')
    ax.grid(True, linestyle='--', alpha=0.6)
    mticker_formatter = mticker.FuncFormatter(lambda x, _: f"${x:,.0f}")
    ax.yaxis.set_major_formatter(mticker_formatter)

    # Chart 3: Profit Curve & Cumulative Cash
    ax = axes[2]
    ax.plot(df['Month'], df['Profit_Loss'], marker='x', color='tab:red', label='Monthly P&L')
    ax.plot(df['Month'], df['Cumulative_Cash'], marker='.', linewidth=2, color='tab:purple', label='Cumulative Cash')
    ax.axhline(0, color='black', linewidth=1)
    ax.set_title('Profit & Cash Flow')
    ax.set_xlabel('Month')
    ax.set_ylabel('Amount ($)')
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.6)

    fig.suptitle(f'SaaS Financial Simulation Results {title_suffix}', fontsize=16)
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])

    filename = f"saas_simulation_{title_suffix.replace(' ', '_').replace('(','').replace(')','').lower()}.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    logger.info(f"[CHART] Saved: {filename}")
    plt.close()


def visualize_dashboard_1(df, title_suffix=""):
    fig, axes = plt.subplots(2, 3, figsize=(22, 12))
    fig.suptitle(f'SaaS Dashboard 1 — Revenue & Cost Detail {title_suffix}', fontsize=15, fontweight='bold')
    months = df["Month"]

    # ── TOP ROW ──────────────────────────────────────────────────────────────

    # [0,0] MRR Movements (stacked bar + net line)
    ax = axes[0, 0]
    ax.bar(months, df["New_MRR"],       label="New MRR (new customers)",  color="#2ecc71", alpha=0.85)
    ax.bar(months, df["Expansion_MRR"], label="Net Expansion MRR",        color="#a9dfbf", alpha=0.85,
           bottom=df["New_MRR"])
    ax.bar(months, df["Churn_MRR"],     label="Churn MRR",                color="#e74c3c", alpha=0.85)
    ax.plot(months, df["Net_New_MRR"],  label="Net New MRR",              color="#2980b9", linewidth=2, marker='o', markersize=4)
    ax.set_title("MRR Movements")
    ax.set_xlabel("Month"); ax.set_ylabel("MRR ($)")
    ax.legend(fontsize=7); ax.grid(True, linestyle='--', alpha=0.5)
    mticker_formatter = mticker.FuncFormatter(lambda x, _: f"${x:,.0f}")
    ax.yaxis.set_major_formatter(mticker_formatter)

    # [0,1] MRR Growth + MoM %
    ax = axes[0, 1]
    ax2 = ax.twinx()
    ax.bar(months, df["Net_New_MRR"], label="Net New MRR", color="#27ae60", alpha=0.8)
    ax2.plot(months, df["MoM_Growth_%"], color="#2980b9", linewidth=2, marker='s', markersize=4, label="MoM growth %")
    ax.set_title("MRR Growth")
    ax.set_xlabel("Month"); ax.set_ylabel("Net New MRR ($)"); ax2.set_ylabel("MoM Growth %")
    ax.yaxis.set_major_formatter(mticker_formatter)
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.1f}%"))
    lines1, lab1 = ax.get_legend_handles_labels()
    lines2, lab2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, lab1 + lab2, fontsize=7)
    ax.grid(True, linestyle='--', alpha=0.5)

    # [0,2] Enterprise Customer Wins/Losses
    ax = axes[0, 2]
    ax.bar(months, df["New_Enterprise_Wins"],  label="New Enterprise customers", color="#2ecc71", alpha=0.85)
    ax.bar(months, df["Enterprise_Upgrades"],  label="Upgrades from Pro",        color="#a9cce3", alpha=0.85,
           bottom=df["New_Enterprise_Wins"])
    ax.bar(months, -df["Lost_Enterprise"],     label="Lost customers",           color="#e74c3c", alpha=0.85)
    ax.axhline(0, color='black', linewidth=0.8)
    ax.set_title("Enterprise Customer Wins/Losses")
    ax.set_xlabel("Month"); ax.set_ylabel("Customers")
    ax.legend(fontsize=7); ax.grid(True, linestyle='--', alpha=0.5)

    # ── BOTTOM ROW ───────────────────────────────────────────────────────────

    # [1,0] Monthly Costs by P&L Category (stacked area)
    ax = axes[1, 0]
    ax.stackplot(months, df["COGS"], df["RD_Cost"], df["SM_Cost"], df["GA_Cost"], df["CS_Cost"],
                 labels=["CoGS", "R&D", "S&M", "G&A", "CS"],
                 colors=["#5dade2", "#a9cce3", "#f9e79f", "#f0b27a", "#d2b4de"], alpha=0.85)
    ax.set_title("Monthly Costs by P&L Category")
    ax.set_xlabel("Month"); ax.set_ylabel("Cost ($)")
    ax.legend(fontsize=7, loc='upper left'); ax.grid(True, linestyle='--', alpha=0.5)
    ax.yaxis.set_major_formatter(mticker_formatter)

    # [1,1] Monthly Costs by Category (same data, different palette for visual variety)
    ax = axes[1, 1]
    ax.stackplot(months, df["COGS"], df["RD_Cost"], df["SM_Cost"], df["GA_Cost"], df["CS_Cost"],
                 labels=["CoGS", "R&D", "Sales & Marketing", "G&A", "Customer Success"],
                 colors=["#117a65", "#1a5276", "#7d6608", "#784212", "#4a235a"], alpha=0.75)
    ax.set_title("Monthly Costs by Category")
    ax.set_xlabel("Month"); ax.set_ylabel("Cost ($)")
    ax.legend(fontsize=7, loc='upper left'); ax.grid(True, linestyle='--', alpha=0.5)
    ax.yaxis.set_major_formatter(mticker_formatter)

    # [1,2] Monthly Salaries by Department
    ax = axes[1, 2]
    ax.stackplot(months,
                 df["Salary_GA"], df["Salary_Engineering"], df["Salary_Marketing"],
                 df["Salary_Sales"], df["Salary_CS"],
                 labels=["G&A", "Engineering", "Marketing", "Sales", "CS"],
                 colors=["#5dade2", "#f0b27a", "#a9dfbf", "#f9e79f", "#d2b4de"], alpha=0.85)
    ax.set_title("Monthly Salaries by Department")
    ax.set_xlabel("Month"); ax.set_ylabel("Salary Cost ($)")
    ax.legend(fontsize=7, loc='upper left'); ax.grid(True, linestyle='--', alpha=0.5)
    ax.yaxis.set_major_formatter(mticker_formatter)

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    filename = f"saas_dashboard1_{title_suffix.replace(' ', '_').replace('(','').replace(')','').lower()}.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    logger.info(f"[CHART] Saved: {filename}")
    plt.close()


def visualize_dashboard_2(df, title_suffix=""):
    fig = plt.figure(figsize=(22, 12))
    fig.suptitle(f'SaaS Dashboard 2 — Efficiency & Growth Metrics {title_suffix}', fontsize=15, fontweight='bold')

    months = df["Month"]

    # ── ROW 1: 3 charts ──────────────────────────────────────────────────────

    # [1] Revenue, Costs & EBIT
    ax1 = fig.add_subplot(2, 3, 1)
    ax1.stackplot(months, df["COGS"], df["RD_Cost"], df["SM_Cost"], df["GA_Cost"], df["CS_Cost"],
                  labels=["CoGS", "R&D", "S&M", "G&A", "CS"],
                  colors=["#f0b27a", "#a9dfbf", "#aed6f1", "#d2b4de", "#f9e79f"], alpha=0.8)
    ax1.plot(months, df["Total_Revenue"], color="#27ae60", linewidth=2.5, label="Revenues")
    ax1.plot(months, df["EBIT"],          color="#2980b9", linewidth=2,   label="EBIT", linestyle='--')
    ax1.axhline(0, color='black', linewidth=0.8)
    ax1.set_title("Revenues, Costs & EBIT"); ax1.set_xlabel("Month"); ax1.set_ylabel("Amount ($)")
    ax1.legend(fontsize=7, loc='upper left'); ax1.grid(True, linestyle='--', alpha=0.5)
    mticker_formatter = mticker.FuncFormatter(lambda x, _: f"${x:,.0f}")
    ax1.yaxis.set_major_formatter(mticker_formatter)

    # [2] Gross Profit Margin %
    ax2 = fig.add_subplot(2, 3, 2)
    ax2.plot(months, df["Gross_Margin_%"], color="#2980b9", linewidth=2, marker='o', markersize=4)
    ax2.fill_between(months, df["Gross_Margin_%"], alpha=0.15, color="#2980b9")
    ax2.set_title("Gross Profit Margin"); ax2.set_xlabel("Month"); ax2.set_ylabel("Gross Margin %")
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}%"))
    ax2.set_ylim(0, 100); ax2.grid(True, linestyle='--', alpha=0.5)

    # [3] Headcount by Department
    ax3 = fig.add_subplot(2, 3, 3)
    ax3.stackplot(months,
                  df["HC_GA"], df["HC_Engineering"], df["HC_Marketing"], df["HC_Sales"], df["HC_CS"],
                  labels=["G&A", "Engineering", "Marketing", "Sales", "CS"],
                  colors=["#5dade2", "#f0b27a", "#a9dfbf", "#f9e79f", "#d2b4de"], alpha=0.85)
    ax3.set_title("Headcount by Department"); ax3.set_xlabel("Month"); ax3.set_ylabel("Headcount")
    ax3.legend(fontsize=7, loc='upper left'); ax3.grid(True, linestyle='--', alpha=0.5)

    # ── ROW 2: 2 charts (span slightly wider) ────────────────────────

    # [4] Sales & Marketing Efficiency
    ax4 = fig.add_subplot(2, 3, 4)
    ax4.plot(months, df["SM_Efficiency"], color="#2980b9", linewidth=2.5, marker='o', markersize=4)
    ax4.fill_between(months, df["SM_Efficiency"], alpha=0.12, color="#2980b9")
    ax4.axhline(1.0, color='red', linestyle='--', linewidth=1, label="1.0x (break-even)")
    ax4.set_title("Sales & Marketing Efficiency"); ax4.set_xlabel("Month"); ax4.set_ylabel("Efficiency Ratio")
    ax4.legend(fontsize=7); ax4.grid(True, linestyle='--', alpha=0.5)

    # [5] CAC Payback Time by Pricing Plan
    ax5 = fig.add_subplot(2, 3, 5)
    ax5.plot(months, df["CAC_Payback_Basic"],      color="#8e44ad", linewidth=2, marker='o', markersize=4, label="Basic")
    ax5.plot(months, df["CAC_Payback_Pro"],        color="#2980b9", linewidth=2, marker='s', markersize=4, label="Pro")
    ax5.plot(months, df["CAC_Payback_Enterprise"], color="#27ae60", linewidth=2, marker='^', markersize=4, label="Enterprise")
    ax5.set_title("CAC Payback Time — by Pricing Plan"); ax5.set_xlabel("Month"); ax5.set_ylabel("Months to Payback")
    ax5.legend(fontsize=7); ax5.grid(True, linestyle='--', alpha=0.5)

    # [6] LTV / CAC Ratio
    ax6 = fig.add_subplot(2, 3, 6)
    ax6.plot(months, df["LTV_CAC_Ratio"], color="#e67e22", linewidth=2.5, marker='D', markersize=4)
    ax6.axhline(3.0, color='green', linestyle='--', linewidth=1.2, label="3x (benchmark)")
    ax6.fill_between(months, df["LTV_CAC_Ratio"], 3.0,
                     where=(df["LTV_CAC_Ratio"] >= 3.0), alpha=0.15, color='green', label="Above 3x")
    ax6.fill_between(months, df["LTV_CAC_Ratio"], 3.0,
                     where=(df["LTV_CAC_Ratio"] < 3.0),  alpha=0.15, color='red',   label="Below 3x")
    ax6.set_title("LTV / CAC Ratio"); ax6.set_xlabel("Month"); ax6.set_ylabel("LTV:CAC")
    ax6.legend(fontsize=7); ax6.grid(True, linestyle='--', alpha=0.5)

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    filename = f"saas_dashboard2_{title_suffix.replace(' ', '_').replace('(','').replace(')','').lower()}.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    logger.info(f"[CHART] Saved: {filename}")
    plt.close()


def visualize_comparison(df_base, df_churn):
    fig, axes = plt.subplots(2, 3, figsize=(22, 12))
    fig.suptitle("Scenario Comparison: Base Case vs High Churn", fontsize=15, fontweight='bold')

    months = df_base["Month"]

    comparisons = [
        (axes[0,0], "MRR",              "MRR ($)",          "MRR Growth"),
        (axes[0,1], "Total_Customers",  "Customers",        "Total Customers"),
        (axes[0,2], "Cumulative_Cash",  "Cumulative Cash ($)", "Cumulative Cash"),
        (axes[1,0], "Gross_Margin_%",   "Gross Margin %",   "Gross Margin"),
        (axes[1,1], "SM_Efficiency",    "S&M Efficiency",   "S&M Efficiency"),
        (axes[1,2], "EBIT",             "EBIT ($)",         "EBIT"),
    ]

    for ax, col, ylabel, title in comparisons:
        ax.plot(months, df_base[col],  linewidth=2, marker='o', markersize=3,
                color="#2980b9", label="Base Case (5% churn)")
        ax.plot(months, df_churn[col], linewidth=2, marker='s', markersize=3,
                color="#e74c3c", label="High Churn (10% churn)", linestyle='--')
        ax.set_title(title); ax.set_xlabel("Month"); ax.set_ylabel(ylabel)
        ax.legend(fontsize=8); ax.grid(True, linestyle='--', alpha=0.5)
        if "$" in ylabel:
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
        if "%" in ylabel:
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.1f}%"))

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    filename = "saas_scenario_comparison.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    logger.info(f"[CHART] Saved: {filename}")
    plt.close()


# ─────────────────────────────────────
# STATION METRICS
# ─────────────────────────────────────

@st.cache_data(ttl=60, show_spinner=False)
def get_metrics(df, station_name):
    """Get comprehensive station-level metrics."""
    station_df = df[df["station"] == station_name]
    if station_df.empty:
        return 0, 0, 0, 0, 0, 0, None

    gates_total = len(station_df)
    gates_active = len(station_df[station_df["door_state"] != "offline"])
    people_total = int(station_df["people"].sum())
    critical_count = len(station_df[station_df["maintenance_status"] == "CRITICAL"])
    warning_count = len(station_df[station_df["maintenance_status"] == "WARNING"])
    monitor_count = len(station_df[station_df["maintenance_status"] == "MONITOR"])
    optimal_count = len(station_df[station_df["maintenance_status"] == "OPTIMAL"])

    avg_sync = int(station_df["sync_score"].mean()) if not station_df.empty else 0
    avg_risk = int(station_df["risk_score"].mean()) if not station_df.empty else 0
    avg_congestion = (
        int(station_df.get("congestion_score", pd.Series(0)).mean())
        if not station_df.empty
        else 0
    )

    # High-risk gates
    high_risk_gates = station_df[station_df["risk_score"] >= 70]
    high_risk_count = len(high_risk_gates)

    # Energy stats
    avg_power = float(station_df.get("power_consumption", pd.Series(15)).mean())

    metrics = {
        "gates_total": gates_total,
        "gates_active": gates_active,
        "people_total": people_total,
        "critical_count": critical_count,
        "warning_count": warning_count,
        "monitor_count": monitor_count,
        "optimal_count": optimal_count,
        "avg_sync": avg_sync,
        "avg_risk": avg_risk,
        "avg_congestion": avg_congestion,
        "high_risk_count": high_risk_count,
        "avg_power": avg_power,
        "critical_gates": high_risk_gates[
            ["gate_id", "door_state", "sensor_temp", "sensor_vib", "risk_score"]
        ].to_dict("records")
        if not high_risk_gates.empty
        else [],
    }

    return (
        gates_total,
        gates_active,
        people_total,
        critical_count,
        avg_sync,
        warning_count,
        metrics,
    )


# ─────────────────────────────────────
# ANALYTICS: PER-STATION CHARTS
# ─────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def get_psd_analytics(station_name):
    """Deterministic hourly chart data for door cycles and temperature."""
    rng = np.random.RandomState(seed=sum(ord(c) for c in station_name))

    hours = [
        "06:00",
        "07:00",
        "08:00",
        "09:00",
        "10:00",
        "12:00",
        "14:00",
        "16:00",
        "17:00",
        "18:00",
        "20:00",
        "22:00",
    ]
    flow = rng.randint(150, 900, size=len(hours))
    # Rush-hour spike
    flow[2] = rng.randint(700, 900)
    flow[4] = rng.randint(650, 850)
    flow[10] = rng.randint(600, 850)

    temp = np.linspace(22, 34, len(hours)) + rng.normal(0, 1, len(hours))

    return (
        pd.DataFrame({"Hour": hours, "Door Cycles": flow}),
        pd.DataFrame({"Hour": hours, "Avg Temp (°C)": temp.round(1)}),
    )


# ─────────────────────────────────────
# ANALYTICS: NETWORK-WIDE
# ─────────────────────────────────────

@st.cache_data(ttl=60, show_spinner=False)
def get_network_summary(df):
    """Comprehensive network-wide analytics."""
    total_gates = len(df)
    total_people = int(df["people"].sum())
    total_critical = len(df[df["maintenance_status"] == "CRITICAL"])
    total_warning = len(df[df["maintenance_status"] == "WARNING"])
    total_monitor = len(df[df["maintenance_status"] == "MONITOR"])
    total_optimal = len(df[df["maintenance_status"] == "OPTIMAL"])

    # Overall performance metrics
    network_sync = int(df["sync_score"].mean()) if not df.empty else 0
    network_risk = int(df["risk_score"].mean()) if not df.empty else 0

    # Status distribution
    status_dist = df.groupby("maintenance_status").size().reset_index(name="Count")
    door_dist = df.groupby("door_state").size().reset_index(name="Count")

    # Operator performance
    if "operator" in df.columns:
        operator_stats = (
            df.groupby("operator")
            .agg(
                Gates=("gate_id", "count"),
                Avg_Sync=("sync_score", "mean"),
                Avg_Risk=("risk_score", "mean"),
                Criticals=("maintenance_status", lambda x: (x == "CRITICAL").sum()),
            )
            .round(2)
            .reset_index()
        )
        operator_stats.columns = [
            "Operator",
            "Gates",
            "Avg Sync %",
            "Avg Risk",
            "Criticals",
        ]
    else:
        operator_stats = pd.DataFrame()

    # Train type distribution
    if "train_type" in df.columns:
        train_type_dist = (
            df.groupby("train_type")
            .agg(Count=("gate_id", "count"), Avg_Sync=("sync_score", "mean"))
            .round(1)
            .reset_index()
        )
    else:
        train_type_dist = pd.DataFrame()

    # Station detailed summary
    station_summary = (
        df.groupby("station")
        .agg(
            Gates=("gate_id", "count"),
            Active_Gates=("door_state", lambda x: (x != "offline").sum()),
            Passengers=("people", "sum"),
            Avg_Sync=("sync_score", "mean"),
            Avg_Risk=("risk_score", "mean"),
            Criticals=("maintenance_status", lambda x: (x == "CRITICAL").sum()),
            Warnings=("maintenance_status", lambda x: (x == "WARNING").sum()),
            Avg_People=("people", "mean"),
            Avg_Congestion=("congestion_score", "mean")
            if "congestion_score" in df.columns
            else None,
        )
        .reset_index()
    )

    # Round numeric columns
    numeric_cols = ["Avg_Sync", "Avg_Risk", "Avg_People"]
    for col in numeric_cols:
        if col in station_summary.columns:
            station_summary[col] = station_summary[col].round(1)

    if "Avg_Congestion" in station_summary.columns:
        station_summary["Avg_Congestion"] = station_summary["Avg_Congestion"].round(1)

    station_summary.columns = [
        "Station",
        "Gates",
        "Active",
        "Passengers",
        "Avg Sync %",
        "Avg Risk",
        "Criticals",
        "Warnings",
        "Avg Pax",
        "Avg Cong %",
    ]

    # Network health score (0-100)
    health_components = [
        network_sync * 0.3,
        (100 - network_risk) * 0.3,
        (total_optimal / max(total_gates, 1)) * 100 * 0.2,
        (1 - total_critical / max(total_gates, 1)) * 100 * 0.2,
    ]
    network_health = sum(health_components)

    # Power consumption stats
    if "power_consumption" in df.columns:
        total_power = df["power_consumption"].sum()
        avg_power = df["power_consumption"].mean()
    else:
        total_power = 0
        avg_power = 0

    # Peak hour analysis
    if "is_peak_hour" in df.columns:
        peak_gates = len(df[df["is_peak_hour"]])
        peak_congestion = (
            df[df["is_peak_hour"]]["congestion_score"].mean()
            if "congestion_score" in df.columns
            else 0
        )
    else:
        peak_gates = 0
        peak_congestion = 0

    return {
        "total_gates": total_gates,
        "total_people": total_people,
        "critical_count": total_critical,
        "warning_count": total_warning,
        "monitor_count": total_monitor,
        "optimal_count": total_optimal,
        "network_sync": network_sync,
        "network_risk": network_risk,
        "network_health": round(network_health, 1),
        "status_dist": status_dist,
        "door_dist": door_dist,
        "station_summary": station_summary,
        "operator_stats": operator_stats,
        "train_type_dist": train_type_dist,
        "total_power_kw": round(total_power, 1),
        "avg_power_w": round(avg_power, 1),
        "peak_gates": peak_gates,
        "peak_congestion": round(peak_congestion, 1) if peak_congestion else 0,
    }


# ─────────────────────────────────────
# ANALYTICS: PREDICTIVE MAINTENANCE TIMELINE
# ─────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def get_maintenance_forecast(station_name):
    """Simulate a 7-day risk forecast for the selected station."""
    rng = np.random.RandomState(seed=sum(ord(c) for c in station_name) + 42)

    today = datetime.today()
    days = [(today + timedelta(days=i)).strftime("%b %d") for i in range(7)]

    # Randomized but station-consistent risk forecast
    base_risk = rng.randint(10, 40)
    risks = np.clip(base_risk + rng.normal(0, 8, 7).cumsum(), 5, 95).round(1)

    return pd.DataFrame({"Date": days, "Predicted Risk %": risks})


# ─────────────────────────────────────
# ANALYTICS: PASSENGER FLOW HEATMAP DATA
# ─────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def get_passenger_heatmap(station_name):
    """7-day x 12-hour passenger flow matrix."""
    rng = np.random.RandomState(seed=sum(ord(c) for c in station_name) + 99)

    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    hours = ["06", "07", "08", "09", "10", "12", "14", "16", "17", "18", "20", "22"]

    matrix = rng.randint(50, 800, size=(len(days), len(hours)))
    # Add rush hour peaks Mon-Fri
    for d in range(5):
        matrix[d][2] = rng.randint(650, 900)  # 08:00
        matrix[d][9] = rng.randint(600, 850)  # 18:00
    # Lower weekends
    for d in [5, 6]:
        matrix[d] = (matrix[d] * 0.5).astype(int)

    return pd.DataFrame(matrix, index=days, columns=hours)


# ─────────────────────────────────────
# INCIDENT LOG
# ─────────────────────────────────────

@st.cache_data(ttl=60, show_spinner=False)
def get_incident_log(df):
    """Generate incident records from critical/warning gates."""
    incidents = []
    now = datetime.now()

    critical_gates = df[df["maintenance_status"].isin(["CRITICAL", "WARNING"])].copy()
    for i, (_, row) in enumerate(critical_gates.iterrows()):
        delta = timedelta(minutes=np.random.randint(2, 240))
        ts = (now - delta).strftime("%H:%M")
        severity = (
            "🔴 CRITICAL" if row["maintenance_status"] == "CRITICAL" else "🟡 WARNING"
        )
        if row["door_state"] == "jammed":
            desc = f"Gate {row['gate_id']} jammed — manual override required"
        elif row["sensor_temp"] > 45:
            desc = f"Thermal anomaly {row['sensor_temp']}°C on Gate {row['gate_id']}"
        else:
            desc = (
                f"Sync score degraded ({row['sync_score']}%) on Gate {row['gate_id']}"
            )
        incidents.append(
            {
                "Time": ts,
                "Station": row["station"],
                "Platform": row["platform"],
                "Gate": row["gate_id"],
                "Severity": severity,
                "Description": desc,
                "Temp (°C)": row["sensor_temp"],
                "Vibration": row["sensor_vib"],
            }
        )

    return (
        pd.DataFrame(incidents).sort_values("Time", ascending=False)
        if incidents
        else pd.DataFrame()
    )


# ─────────────────────────────────────
# LEADERSHIP DATA
# ─────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def get_leadership_data():
    return [
        {
            "name": "Khushboo Patil",
            "role": "CEO",
            "desc": "Business Strategy, Market Expansion, and Organizational Leadership",
            "img": "https://ui-avatars.com/api/?name=Khushboo+Patil&background=0e4d92&color=fff",
            "linkedin": "#",
            "experience": "15+ years in Railway Technology and Business Development",
            "education": "MBA, Technical University of Munich",
            "specialization": "Strategic Partnerships, Market Entry Strategy",
            "achievements": [
                "Led expansion to 15+ German railway stations",
                "Secured €2.5M in Series A funding",
                "Established partnerships with DB and regional operators",
            ],
            "quote": "Safety is not just a feature, it's our foundation.",
        },
        {
            "name": "Namrata Joshi",
            "role": "COO",
            "desc": "Operations Management, Strategic Planning, and Project Coordination",
            "img": "https://ui-avatars.com/api/?name=Namrata+Joshi&background=0e4d92&color=fff",
            "linkedin": "#",
            "experience": "12+ years in Operations and Project Management",
            "education": "MSc Operations Management, ETH Zurich",
            "specialization": "Large-scale infrastructure rollouts",
            "achievements": [
                "Managed rollout of 200+ PSD units across Germany",
                "Reduced average deployment time by 40%",
                "Achieved 99.5% on-time delivery rate",
            ],
            "quote": "Efficiency and safety go hand in hand.",
        },
        {
            "name": "Kona Shivam Rao",
            "role": "CTO",
            "desc": "Systems Engineering, Automation, and Rail Technology Development",
            "img": "https://ui-avatars.com/api/?name=Kona+Shivam+Rao&background=0e4d92&color=fff",
            "linkedin": "#",
            "experience": "18+ years in Systems Engineering and IoT",
            "education": "PhD Computer Science, TU Berlin",
            "specialization": "IoT sensors, Edge computing, Safety systems",
            "achievements": [
                "Patented 3 safety-critical sensor technologies",
                "Led development of real-time monitoring platform",
                "Achieved SIL-2 safety certification for core systems",
            ],
            "quote": "Innovation in safety never sleeps.",
        },
        {
            "name": "Sanika Kale",
            "role": "CPO",
            "desc": "Product Innovation, UX Design, and Platform System Integration",
            "img": "https://ui-avatars.com/api/?name=Sanika+Kale&background=0e4d92&color=fff",
            "linkedin": "#",
            "experience": "10+ years in Product Management and UX",
            "education": "MDes Product Design, IIT Bombay",
            "specialization": "User-centric safety interfaces",
            "achievements": [
                "Designed award-winning operator dashboard",
                "Reduced user onboarding time by 60%",
                "Led integration of 5+ third-party platforms",
            ],
            "quote": "Great products make safety invisible.",
        },
        {
            "name": "Nikhil Chavan",
            "role": "CFO",
            "desc": "Financial Strategy, Infrastructure Investment, and Strategic Partnerships",
            "img": "https://ui-avatars.com/api/?name=Nikhil+Chavan&background=0e4d92&color=fff",
            "linkedin": "#",
            "experience": "14+ years in Finance and Investment Banking",
            "education": "CFA Charterholder, Wharton MBA",
            "specialization": "Infrastructure financing, SaaS metrics",
            "achievements": [
                "Raised €5M in total funding across 3 rounds",
                "Achieved 40% YoY revenue growth for 2 consecutive years",
                "Optimized cash flow to support 300% expansion",
            ],
            "quote": "Sustainable growth enables safer railways.",
        },
    ]


# ─────────────────────────────────────
# TECH STACK DATA
# ─────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def get_tech_stack():
    return [
        {"layer": "Sensing", "tech": "IoT Sensors",
            "detail": "Temperature, vibration, proximity (0.1ms latency)"},
        {"layer": "Edge", "tech": "PSD Controllers",
            "detail": "Real-time gate logic with fail-safe override"},
        {"layer": "Network", "tech": "5G / Fiber",
            "detail": "Sub-10ms station-to-cloud sync"},
        {"layer": "Platform", "tech": "BahnSetu Core",
            "detail": "Microservices architecture, 99.97% uptime SLA"},
        {"layer": "Analytics", "tech": "ML Pipeline",
            "detail": "Predictive maintenance, anomaly detection"},
        {"layer": "Interface", "tech": "SicherGleis Pro",
            "detail": "Unified dashboard (this application)"},
    ]


# ─────────────────────────────────────
# OOP CLASSES
# ─────────────────────────────────────

class StationAnalytics:
    """Station analytics OOP wrapper."""
    
    @staticmethod
    def get_metrics(df, station_name):
        return get_metrics(df, station_name)
    
    @staticmethod
    def get_psd_analytics(station_name):
        return get_psd_analytics(station_name)
    
    @staticmethod
    def get_network_summary(df):
        return get_network_summary(df)
    
    @staticmethod
    def get_maintenance_forecast(station_name):
        return get_maintenance_forecast(station_name)
    
    @staticmethod
    def get_passenger_heatmap(station_name):
        return get_passenger_heatmap(station_name)
    
    @staticmethod
    def get_incident_log(df):
        return get_incident_log(df)


class FinancialModel:
    """Financial model OOP wrapper."""
    
    @staticmethod
    def run_simulation(config, months=24):
        return run_simulation(config, months)
    
    @staticmethod
    def print_summary(df, config):
        return print_summary(df, config)
    
    @staticmethod
    def visualize_results(df, title_suffix=""):
        return visualize_results(df, title_suffix)
    
    @staticmethod
    def visualize_dashboard_1(df, title_suffix=""):
        return visualize_dashboard_1(df, title_suffix)
    
    @staticmethod
    def visualize_dashboard_2(df, title_suffix=""):
        return visualize_dashboard_2(df, title_suffix)
    
    @staticmethod
    def visualize_comparison(df_base, df_churn):
        return visualize_comparison(df_base, df_churn)


class CustomerSegmenter:
    """Customer segmentation OOP wrapper (placeholder)."""
    
    @staticmethod
    def get_customer_data():
        return []  # Placeholder
    
    @staticmethod
    def get_rfm_analysis():
        return {}  # Placeholder
    
    @staticmethod
    def get_high_value_customers():
        return []  # Placeholder
    
    @staticmethod
    def get_customer_business_insights():
        return {}  # Placeholder
    
    @staticmethod
    def get_contract_health_score():
        return {}  # Placeholder
    
    @staticmethod
    def get_renewal_forecast():
        return {}  # Placeholder
    
    @staticmethod
    def get_at_risk_accounts():
        return []  # Placeholder


# ─────────────────────────────────────
# PLACEHOLDER FUNCTIONS FOR MISSING IMPORTS
# ─────────────────────────────────────

def get_financial_model_data(months=24, starting_customers=50, monthly_growth_rate=0.20,
                             churn_rate=0.05, price_per_customer=100, fixed_costs=5000,
                             variable_cost_per_customer=10, cac_simplified=150,
                             churn_rate_high=None):
    """Return (df_base, df_high_churn) for Financial Model tab."""
    if churn_rate_high is None:
        churn_rate_high = churn_rate * 2
    
    config_base = SaaSModelConfig(starting_customers, monthly_growth_rate, churn_rate,
                                   price_per_customer, fixed_costs, variable_cost_per_customer, cac_simplified)
    df_base = run_simulation(config_base, months)
    
    config_high = SaaSModelConfig(starting_customers, monthly_growth_rate, churn_rate_high,
                                   price_per_customer, fixed_costs, variable_cost_per_customer, cac_simplified)
    df_churn = run_simulation(config_high, months)
    
    return df_base, df_churn


def get_customer_data():
    """Return customer/operator data from sample data."""
    if not SAMPLE_DATA_AVAILABLE:
        logger.error("sample_data module not available - cannot load customer data")
        return pd.DataFrame(columns=[
            "customer_id", "customer_name", "tier", "satisfaction_score",
            "rfm_segment", "segment", "risk_level", "total_contract_value_eur",
            "days_to_renewal", "avg_response_hours"
        ])
    try:
        return get_customer_df()
    except Exception as e:
        logger.error(f"Failed to load customer data: {e}")
        return pd.DataFrame(columns=[
            "customer_id", "customer_name", "tier", "satisfaction_score",
            "rfm_segment", "segment", "risk_level", "total_contract_value_eur",
            "days_to_renewal", "avg_response_hours"
        ])


def get_rfm_analysis(customer_df=None):
    """Return RFM analysis DataFrame from sample data."""
    if not SAMPLE_DATA_AVAILABLE:
        logger.error("sample_data module not available - cannot load RFM data")
        return pd.DataFrame(columns=[
            "rfm_segment", "segment",
            "recency_score", "frequency_score", "monetary_score",
            "platforms_installed", "total_contract_value_eur"
        ])
    try:
        return get_rfm_df()
    except Exception as e:
        logger.error(f"Failed to load RFM analysis: {e}")
        return pd.DataFrame(columns=[
            "rfm_segment", "segment",
            "recency_score", "frequency_score", "monetary_score",
            "platforms_installed", "total_contract_value_eur"
        ])


def get_high_value_customers(customer_df=None):
    """Return high-value customers from sample data."""
    if not SAMPLE_DATA_AVAILABLE:
        logger.error("sample_data module not available")
        return pd.DataFrame()
    try:
        return get_high_value_customers_df()
    except Exception as e:
        logger.error(f"Failed to load high value customers: {e}")
        return pd.DataFrame()


def get_customer_business_insights(customer_df=None):
    """Return business insights from sample data."""
    try:
        return get_customer_insights()
    except Exception as e:
        logger.error(f"Error in get_customer_insights: {e}")
        return {
            "total_customers": 0,
            "total_trains_covered": 0,
            "total_contract_value_eur": 0,
            "avg_contract_value_eur": 0,
            "total_psd_units": 0,
            "high_value_count": 0,
            "avg_satisfaction": 0,
            "risk_rate": 0,
            "at_risk_count": 0,
            "at_risk_pct": 0,
            "strategic_count": 0,
            "strategic_pct": 0,
            "top_operator_type": "National",
            "recommendations": [],
        }


def get_contract_health_score(customer_df=None):
    """Return contract health scores from sample data."""
    try:
        return get_contract_health_df()
    except:
        return pd.DataFrame()


def get_renewal_forecast(customer_df=None):
    """Return renewal forecast from sample data."""
    try:
        return get_renewal_forecast_df()
    except:
        return pd.DataFrame(columns=["days_to_renewal", "total_contract_value_eur"])


def get_at_risk_accounts(customer_df=None):
    """Return at-risk accounts from sample data."""
    try:
        return get_at_risk_df()
    except:
        return pd.DataFrame(columns=["risk_level"])


def get_renewal_health_summary(customer_df=None):
    """Return renewal health summary from sample data."""
    try:
        from data.sample_data import get_customer_df, get_contract_health_df
        health_df = get_contract_health_df()
        customer_df = get_customer_df()
        
        avg_health = health_df["health_score"].mean()
        healthy_count = len(health_df[health_df["health_score"] >= 70])
        critical_count = len(health_df[health_df["health_score"] < 50])
        
        # At-risk high (High Risk)
        at_risk_high = len(customer_df[customer_df["risk_level"] == "High Risk"])
        # At-risk counts
        at_risk_customers = customer_df[customer_df["risk_level"].isin(["High Risk", "Medium Risk"])]
        contract_value_at_risk = at_risk_customers["total_contract_value_eur"].sum()
        
        # Renewal counts
        renewal_critical = len(customer_df[customer_df["days_to_renewal"] <= 30])
        renewal_urgent = len(customer_df[(customer_df["days_to_renewal"] > 30) & (customer_df["days_to_renewal"] <= 60)])
        renewal_upcoming = len(customer_df[(customer_df["days_to_renewal"] > 60) & (customer_df["days_to_renewal"] <= 90)])
        
        # Upcoming renewals value
        upcoming_30d = customer_df[customer_df["days_to_renewal"] <= 30]["total_contract_value_eur"].sum()
        upcoming_60d = customer_df[customer_df["days_to_renewal"] <= 60]["total_contract_value_eur"].sum()
        upcoming_90d = customer_df[customer_df["days_to_renewal"] <= 90]["total_contract_value_eur"].sum()
        
        return {
            "avg_health_score": avg_health,
            "healthy_pct": (healthy_count / len(health_df)) * 100 if len(health_df) > 0 else 0,
            "healthy_count": healthy_count,
            "total_operators": len(health_df),
            "critical_count": critical_count,
            "at_risk_high": at_risk_high,
            "contract_value_at_risk": contract_value_at_risk,
            "renewal_critical": renewal_critical,
            "renewal_urgent": renewal_urgent,
            "renewal_upcoming": renewal_upcoming,
            "upcoming_renewals_30d": upcoming_30d,
            "upcoming_renewals_60d": upcoming_60d,
            "upcoming_renewals_90d": upcoming_90d,
        }
    except Exception as e:
        logger.error(f"Error in get_renewal_health_summary: {e}")
        return {
            "avg_health_score": 0,
            "healthy_pct": 0,
            "healthy_count": 0,
            "total_operators": 0,
            "critical_count": 0,
            "at_risk_high": 0,
            "contract_value_at_risk": 0,
            "renewal_critical": 0,
            "renewal_urgent": 0,
            "renewal_upcoming": 0,
            "upcoming_renewals_30d": 0,
            "upcoming_renewals_60d": 0,
            "upcoming_renewals_90d": 0,
        }


def get_operator_history(customer_id=None):
    """Return operator history from sample data."""
    try:
        from data.sample_data import get_operator_history as _get_data
        return _get_data(customer_id) if customer_id else pd.DataFrame()
    except:
        return pd.DataFrame()


def get_contract_amendments(customer_id=None, customer_df=None):
    """Return contract amendments from sample data."""
    try:
        from data.sample_data import get_contract_amendments as _get_data
        result = _get_data(customer_id) if customer_id else []
        return pd.DataFrame(result) if isinstance(result, list) else result
    except:
        return pd.DataFrame()


def get_support_tickets(customer_id=None, limit=100):
    """Return support tickets from sample data."""
    try:
        from data.sample_data import get_support_tickets as _get_data
        return _get_data(customer_id, limit) if customer_id else pd.DataFrame()
    except:
        return pd.DataFrame()


def get_engagement_timeline(customer_id=None, months_back=12):
    """Return engagement timeline from sample data."""
    if not customer_id:
        customer_id = "all"
    try:
        from data.sample_data import get_engagement_timeline as _get_data
        return _get_data(customer_id, months_back)
    except:
        return pd.DataFrame()


def get_operator_health_trend(customer_id=None, months_back=12):
    """Return operator health trend from sample data."""
    if not customer_id:
        customer_id = "all"
    try:
        from data.sample_data import get_operator_health_trend as _get_trend
        result = _get_trend(customer_id, months_back)
        return result if isinstance(result, pd.DataFrame) else pd.DataFrame()
    except:
        return pd.DataFrame()


def get_support_ticket_trend(customer_id=None, months_back=6):
    """Return support ticket trend from sample data."""
    if not customer_id:
        customer_id = "all"
    try:
        from data.sample_data import get_support_ticket_trend as _get_data
        return _get_data(customer_id, months_back)
    except:
        return pd.DataFrame()


def get_financial_projections(months_ahead=24):
    """Return financial projections from sample data."""
    try:
        from data.sample_data import get_financial_projections as _get_proj
        return _get_proj(months_ahead)
    except:
        return {}


def get_operator_comparison_benchmarks(customer_id=None):
    """Return operator comparison benchmarks from sample data."""
    try:
        from data.sample_data import get_operator_comparison_benchmarks as _get_bench
        return _get_bench(customer_id)
    except:
        return {}


def get_operator_monthly_stats(customer_id=None, months_back=6):
    """Return operator monthly stats from sample data."""
    if not customer_id:
        customer_id = "all"
    try:
        from data.sample_data import get_operator_monthly_stats as _get_data
        return _get_data(customer_id, months_back)
    except:
        return pd.DataFrame()


def get_business_map_data():
    """Return business map data from sample data."""
    try:
        return get_station_df()
    except:
        return pd.DataFrame(columns=["status"])
