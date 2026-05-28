import dataclasses
import logging
import random
from datetime import datetime, timedelta
from typing import Optional

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import streamlit as st

from utils.exceptions import ConfigurationError, SimulationError

logger = logging.getLogger(__name__)

# Import sample data functions
SAMPLE_DATA_AVAILABLE = False
try:
    from data.sample_data import (
        get_at_risk_df,
        get_business_map_data,
        get_contract_amendments,
        get_contract_health_df,
        get_customer_df,
        get_customer_insights,
        get_engagement_timeline,
        get_financial_projections,
        get_high_value_customers_df,
        get_leadership_data,
        get_operator_comparison_benchmarks,
        get_operator_history,
        get_operator_monthly_stats,
        get_operator_profile,
        get_renewal_forecast_df,
        get_renewal_health_summary,
        get_rfm_df,
        get_station_df,
        get_support_ticket_trend,
        get_support_tickets,
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

    # Build agg dict conditionally to avoid passing None in .agg()
    station_agg = {
        "Gates": ("gate_id", "count"),
        "Active_Gates": ("door_state", lambda x: (x != "offline").sum()),
        "Passengers": ("people", "sum"),
        "Avg_Sync": ("sync_score", "mean"),
        "Avg_Risk": ("risk_score", "mean"),
        "Criticals": ("maintenance_status", lambda x: (x == "CRITICAL").sum()),
        "Warnings": ("maintenance_status", lambda x: (x == "WARNING").sum()),
        "Avg_People": ("people", "mean"),
    }
    if "congestion_score" in df.columns:
        station_agg["Avg_Congestion"] = ("congestion_score", "mean")

    station_summary = df.groupby("station").agg(**station_agg).reset_index()

    # Round numeric columns
    numeric_cols = ["Avg_Sync", "Avg_Risk", "Avg_People"]
    for col in numeric_cols:
        if col in station_summary.columns:
            station_summary[col] = station_summary[col].round(1)

    if "Avg_Congestion" in station_summary.columns:
        station_summary["Avg_Congestion"] = station_summary["Avg_Congestion"].round(1)

    renamed = ["Station", "Gates", "Active", "Passengers", "Avg Sync %",
               "Avg Risk", "Criticals", "Warnings", "Avg Pax"]
    if "Avg_Congestion" in station_summary.columns:
        renamed.append("Avg Cong %")
    station_summary.columns = renamed

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

def get_financial_model_data(months=24, starting_customers=5000, monthly_growth_rate=0.15,
                             churn_rate=0.02, price_per_customer=249, fixed_costs=120000,
                             variable_cost_per_customer=25, cac_simplified=300,
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
    if not SAMPLE_DATA_AVAILABLE:
        logger.error("sample_data module not available")
        return pd.DataFrame()
    try:
        return get_contract_health_df()
    except Exception as e:
        logger.error(f"Failed to load contract health data: {e}")
        return pd.DataFrame()


def get_renewal_forecast(customer_df=None):
    """Return renewal forecast from sample data."""
    if not SAMPLE_DATA_AVAILABLE:
        logger.error("sample_data module not available")
        return pd.DataFrame(columns=["days_to_renewal", "total_contract_value_eur"])
    try:
        return get_renewal_forecast_df()
    except Exception as e:
        logger.error(f"Failed to load renewal forecast: {e}")
        return pd.DataFrame(columns=["days_to_renewal", "total_contract_value_eur"])


def get_at_risk_accounts(customer_df=None):
    """Return at-risk accounts from sample data."""
    if not SAMPLE_DATA_AVAILABLE:
        logger.error("sample_data module not available")
        return pd.DataFrame(columns=["risk_level"])
    try:
        return get_at_risk_df()
    except Exception as e:
        logger.error(f"Failed to load at-risk accounts: {e}")
        return pd.DataFrame(columns=["risk_level"])


def get_renewal_health_summary(customer_df=None):
    """Return renewal health summary from sample data."""
    try:
        from data.sample_data import get_contract_health_df, get_customer_df
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
    if not customer_id:
        return pd.DataFrame()
    if not SAMPLE_DATA_AVAILABLE:
        logger.error("sample_data module not available")
        return pd.DataFrame()
    try:
        from data.sample_data import get_operator_history as _get_data
        return _get_data(customer_id)
    except Exception as e:
        logger.error(f"Failed to load operator history: {e}")
        return pd.DataFrame()


def get_contract_amendments(customer_id=None, customer_df=None):
    """Return contract amendments from sample data."""
    if not customer_id:
        return pd.DataFrame()
    if not SAMPLE_DATA_AVAILABLE:
        logger.error("sample_data module not available")
        return pd.DataFrame()
    try:
        from data.sample_data import get_contract_amendments as _get_data
        result = _get_data(customer_id)
        return pd.DataFrame(result) if isinstance(result, list) else result
    except Exception as e:
        logger.error(f"Failed to load contract amendments: {e}")
        return pd.DataFrame()


def get_support_tickets(customer_id=None, limit=100):
    """Return support tickets from sample data."""
    if not customer_id:
        return pd.DataFrame()
    if not SAMPLE_DATA_AVAILABLE:
        logger.error("sample_data module not available")
        return pd.DataFrame()
    try:
        from data.sample_data import get_support_tickets as _get_data
        return _get_data(customer_id, limit)
    except Exception as e:
        logger.error(f"Failed to load support tickets: {e}")
        return pd.DataFrame()


def get_engagement_timeline(customer_id=None, months_back=12):
    """Return engagement timeline from sample data."""
    if not customer_id:
        customer_id = "all"
    if not SAMPLE_DATA_AVAILABLE:
        logger.error("sample_data module not available")
        return pd.DataFrame()
    # Ensure months_back is valid
    try:
        months_back = int(months_back) if months_back else 12
        if months_back < 1:
            months_back = 12
    except (ValueError, TypeError):
        months_back = 12
    try:
        from data.sample_data import get_engagement_timeline as _get_data
        return _get_data(customer_id, months_back)
    except ValueError as e:
        if "All arrays must be of the same length" in str(e):
            logger.warning(f"Data shape mismatch in engagement timeline, returning empty: {e}")
            return pd.DataFrame(columns=["date", "type", "direction", "our_participants", "their_participants", "outcome", "follow_up_date"])
        logger.error(f"Failed to load engagement timeline: {e}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Failed to load engagement timeline: {e}")
        return pd.DataFrame()


def get_operator_health_trend(customer_id=None, months_back=12):
    """Return operator health trend from sample data."""
    if not customer_id:
        customer_id = "all"
    if not SAMPLE_DATA_AVAILABLE:
        logger.error("sample_data module not available")
        return pd.DataFrame()
    # Ensure months_back is valid
    try:
        months_back = int(months_back) if months_back else 12
        if months_back < 1:
            months_back = 12
    except (ValueError, TypeError):
        months_back = 12
    try:
        from data.sample_data import get_operator_health_trend as _get_data
        result = _get_data(customer_id, months_back)
        return result if isinstance(result, pd.DataFrame) else pd.DataFrame()
    except ValueError as e:
        if "All arrays must be of the same length" in str(e):
            logger.warning(f"Data shape mismatch in health trend, returning empty: {e}")
            return pd.DataFrame(columns=["Month", "Health Score"])
        logger.error(f"Failed to load operator health trend: {e}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Failed to load operator health trend: {e}")
        return pd.DataFrame()


def get_support_ticket_trend(customer_id=None, months_back=6):
    """Return support ticket trend from sample data."""
    if not customer_id:
        customer_id = "all"
    if not SAMPLE_DATA_AVAILABLE:
        logger.error("sample_data module not available")
        return pd.DataFrame()
    # Ensure months_back is valid
    try:
        months_back = int(months_back) if months_back else 6
        if months_back < 1:
            months_back = 6
    except (ValueError, TypeError):
        months_back = 6
    try:
        from data.sample_data import get_support_ticket_trend as _get_data
        return _get_data(customer_id, months_back)
    except ValueError as e:
        if "All arrays must be of the same length" in str(e):
            logger.warning(f"Data shape mismatch in ticket trend, returning empty: {e}")
            return pd.DataFrame(columns=["Month", "Tickets"])
        logger.error(f"Failed to load support ticket trend: {e}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Failed to load support ticket trend: {e}")
        return pd.DataFrame()


def get_financial_projections(months_ahead=24):
    """Return financial projections from sample data."""
    if not SAMPLE_DATA_AVAILABLE:
        logger.error("sample_data module not available")
        return {}
    try:
        from data.sample_data import get_financial_projections as _get_data
        return _get_data(months_ahead)
    except Exception as e:
        logger.error(f"Failed to load financial projections: {e}")
        return {}


def get_operator_comparison_benchmarks(customer_id=None):
    """Return operator comparison benchmarks from sample data."""
    if not SAMPLE_DATA_AVAILABLE:
        logger.error("sample_data module not available")
        return {}
    try:
        from data.sample_data import get_operator_comparison_benchmarks as _get_data
        return _get_data(customer_id)
    except Exception as e:
        logger.error(f"Failed to load operator benchmarks: {e}")
        return {}


def get_operator_monthly_stats(customer_id=None, months_back=6):
    """Return operator monthly stats from sample data."""
    if not customer_id:
        customer_id = "all"
    if not SAMPLE_DATA_AVAILABLE:
        logger.error("sample_data module not available")
        return pd.DataFrame()
    # Ensure months_back is valid
    try:
        months_back = int(months_back) if months_back else 6
        if months_back < 1:
            months_back = 6
    except (ValueError, TypeError):
        months_back = 6
    try:
        from data.sample_data import get_operator_monthly_stats as _get_data
        return _get_data(customer_id, months_back)
    except ValueError as e:
        if "All arrays must be of the same length" in str(e):
            logger.warning(f"Data shape mismatch in monthly stats, returning empty: {e}")
            return pd.DataFrame(columns=["Month", "PSD Activations", "Incidents", "Uptime %", "Projects Completed", "Tickets Opened", "Engagements"])
        logger.error(f"Failed to load operator monthly stats: {e}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Failed to load operator monthly stats: {e}")
        return pd.DataFrame()


def get_business_map_data():
    """Return business map data from sample data."""
    if not SAMPLE_DATA_AVAILABLE:
        logger.error("sample_data module not available")
        return pd.DataFrame(columns=["status"])
    try:
        from data.sample_data import get_station_df as _get_data
        return _get_data()
    except Exception as e:
        logger.error(f"Failed to load business map data: {e}")
        return pd.DataFrame(columns=["status"])


# ─────────────────────────────────────
# TRAINING SIMULATOR - INCIDENT SIMULATION
# ─────────────────────────────────────

# Root cause categories
ROOT_CAUSES = {
    "equipment_failure": {"weight": 0.35, "label": "Equipment Failure", "preventable": "Yes - predictive maintenance"},
    "weather": {"weight": 0.20, "label": "Weather Conditions", "preventable": "Partial -应急预案"},
    "human_error": {"weight": 0.25, "label": "Human Error", "preventable": "Yes - training required"},
    "system_overload": {"weight": 0.15, "label": "System Overload", "preventable": "Yes - capacity planning"},
    "external": {"weight": 0.05, "label": "External Factors", "preventable": "No"},
}

# Improvement areas mapping
IMPROVEMENT_AREAS = {
    "equipment_failure": "Equipment & Maintenance",
    "weather": "Emergency Protocols",
    "human_error": "Staff Training",
    "system_overload": "System Capacity",
    "external": "Contingency Planning",
}

@dataclasses.dataclass
class Incident:
    """Represents a single incident in the training simulator."""
    id: str
    timestamp: datetime
    station: str
    incident_type: str
    severity: str  # CRITICAL, WARNING, INFO
    description: str
    assigned_persona: str | None = None
    assigned_role: str | None = None
    status: str = "pending"  # pending, assigned, resolved, failed, escalated
    response_time_min: float = 0.0
    resolution_time_min: float = 0.0
    outcome: str | None = None
    cascade_parent_id: str | None = None
    is_compound: bool = False
    sub_incidents: list[str] = dataclasses.field(default_factory=list)
    weather_modified: bool = False
    # New fields for lifecycle & accountability
    root_cause: str | None = None
    improvement_area: str | None = None
    preventable: str | None = None
    time_to_assign: float = 0.0  # seconds from creation to assignment
    time_to_resolve: float = 0.0  # seconds from creation to resolution
    escalation_count: int = 0
    was_escalated: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "station": self.station,
            "incident_type": self.incident_type,
            "severity": self.severity,
            "description": self.description,
            "assigned_persona": self.assigned_persona,
            "assigned_role": self.assigned_role,
            "status": self.status,
            "response_time_min": self.response_time_min,
            "resolution_time_min": self.resolution_time_min,
            "outcome": self.outcome,
            "cascade_parent_id": self.cascade_parent_id,
            "is_compound": self.is_compound,
            "sub_incidents": self.sub_incidents,
            "weather_modified": self.weather_modified,
            "root_cause": self.root_cause,
            "improvement_area": self.improvement_area,
            "preventable": self.preventable,
            "time_to_assign": self.time_to_assign,
            "time_to_resolve": self.time_to_resolve,
            "escalation_count": self.escalation_count,
            "was_escalated": self.was_escalated,
        }


@dataclasses.dataclass
class SimulationPersona:
    """Represents a persona in the training simulator."""
    name: str
    role: str
    specialties: list[str]
    avg_response_min: float
    success_rate: float
    assigned_count: int = 0
    resolved_count: int = 0
    active_count: int = 0
    total_response_time: float = 0.0
    current_assigned: int = 0
    current_resolved: int = 0
    current_success_rate: float = 0.0
    fatigue: float = 0.0
    stress_events: int = 0
    fatigue_incidents: int = 0

    @property
    def needs_break(self) -> bool:
        return self.fatigue > 70.0

    @property
    def is_overloaded(self) -> bool:
        return self.fatigue > 50.0 or self.active_count > 3

    @property
    def fatigue_level(self) -> str:
        if self.fatigue < 30:
            return "fresh"
        elif self.fatigue < 50:
            return "normal"
        elif self.fatigue < 70:
            return "tired"
        elif self.fatigue < 85:
            return "exhausted"
        else:
            return "critical"

    @property
    def success_rate_computed(self) -> float:
        """Compute success rate from session stats."""
        if self.current_assigned == 0:
            return self.success_rate
        return (self.current_resolved / self.current_assigned) * 100

    def apply_fatigue_to_success(self, base_success: float) -> float:
        if self.fatigue < 30:
            return base_success
        penalty = (self.fatigue - 30) / 100 * 0.5
        return max(0.1, base_success - penalty)

    def apply_fatigue_to_response(self, base_response: float) -> float:
        if self.fatigue < 30:
            return base_response
        penalty = (self.fatigue - 30) / 100 * 1.5
        return base_response * (1 + penalty)

    def trigger_stress_event(self, amount: float = 30.0):
        self.fatigue = min(100.0, self.fatigue + amount)
        self.stress_events += 1
        if self.fatigue > 70:
            self.fatigue_incidents += 1

    def add_incident_load(self):
        self.fatigue = min(100.0, self.fatigue + 5.0)
        self.fatigue_incidents += 1
        if self.fatigue > 70:
            self.fatigue_incidents += 1

    def recover(self, amount: float = 10.0):
        self.fatigue = max(0.0, self.fatigue - amount)

    def rest_interval_recovery(self):
        self.fatigue = max(0.0, self.fatigue - 15.0)

    def record_assignment(self):
        self.assigned_count += 1
        self.active_count += 1
        self.current_assigned += 1
        self.add_incident_load()

    def record_resolution(self, success: bool, response_time: float):
        self.active_count = max(0, self.active_count - 1)
        if success:
            self.resolved_count += 1
            self.current_resolved += 1
        self.total_response_time += response_time

    def to_competency_score(self, benchmark: dict) -> "CompetencyScore":
        all_incidents = self.assigned_count
        resolved = self.resolved_count

        accuracy = (resolved / max(all_incidents, 1)) * 100

        speed_score = 0.0
        if self.total_response_time > 0 and resolved > 0:
            avg_rt = self.total_response_time / resolved
            speed_ratio = benchmark.get("speed", 2.0) / max(avg_rt, 0.1)
            speed_score = min(100.0, speed_ratio * 50)

        critical_score = accuracy
        specialty_score = 80.0
        escalation_score = max(0.0, 100.0 - self.stress_events * 10)
        balance_score = max(0.0, 100.0 - self.fatigue * 0.5)

        overall = (speed_score + accuracy + critical_score + specialty_score +
                   escalation_score + balance_score) / 6.0

        return CompetencyScore(
            persona_name=self.name,
            speed_score=speed_score,
            accuracy_score=accuracy,
            critical_score=critical_score,
            specialty_score=specialty_score,
            escalation_score=escalation_score,
            balance_score=balance_score,
            overall_score=overall,
        )


SCENARIO_STEP_TYPES = [
    "trigger", "cascade", "weather_change", "escalation_point",
    "time_pressure", "multi_station_wave", "stress_event", "rest_interval"
]

SCENARIO_PRESETS = {
    "quick_drill": {
        "description": "Fast-paced drill for new trainees",
        "tags": ["beginner", "short"],
        "steps": [
            {"type": "trigger", "severity_override": "MIXED", "delay_sec": 0},
            {"type": "time_pressure", "delay_sec": 30},
        ]
    },
    "critical_hours": {
        "description": "Rush hour simulation with high pressure",
        "tags": ["intermediate", "stress"],
        "steps": [
            {"type": "trigger", "severity_override": "HIGH_CRITICAL", "delay_sec": 0},
            {"type": "multi_station_wave", "delay_sec": 20},
            {"type": "stress_event", "delay_sec": 45},
        ]
    },
    "night_shift": {
        "description": "Low-staff night shift with fatigue elements",
        "tags": ["advanced", "fatigue"],
        "steps": [
            {"type": "trigger", "severity_override": "LOW_INFO", "delay_sec": 0},
            {"type": "fatigue_spike", "delay_sec": 60},
            {"type": "rest_interval", "delay_sec": 120},
        ]
    },
    "multi_station_cascade": {
        "description": "Cascading failures across multiple stations",
        "tags": ["advanced", "cascade"],
        "steps": [
            {"type": "trigger", "severity_override": "CRITICAL", "delay_sec": 0},
            {"type": "cascade", "delay_sec": 15, "station_filter": "secondary"},
            {"type": "escalation_point", "delay_sec": 40},
            {"type": "cascade", "delay_sec": 60, "station_filter": "tertiary"},
        ]
    },
    "weather_event": {
        "description": "Severe weather causing cascading issues",
        "tags": ["intermediate", "weather"],
        "steps": [
            {"type": "weather_change", "weather": "storm", "delay_sec": 0},
            {"type": "trigger", "delay_sec": 5},
            {"type": "cascade", "delay_sec": 30},
            {"type": "rest_interval", "delay_sec": 90},
        ]
    },
    "shift_simulation": {
        "description": "Full shift simulation with realistic pacing",
        "tags": ["intermediate", "full-shift"],
        "steps": [
            {"type": "trigger", "severity_override": "MIXED", "delay_sec": 0},
            {"type": "time_pressure", "delay_sec": 60},
            {"type": "stress_event", "delay_sec": 120},
            {"type": "rest_interval", "delay_sec": 180},
            {"type": "multi_station_wave", "delay_sec": 240},
            {"type": "stress_event", "delay_sec": 300},
            {"type": "rest_interval", "delay_sec": 360},
        ]
    },
}

COMPETENCY_BENCHMARKS = {
    "speed": 2.0,
    "accuracy": 90.0,
    "critical": 85.0,
    "specialty": 80.0,
    "escalation": 10.0,
    "balance": 20.0,
}


@dataclasses.dataclass
class ScenarioStep:
    step_id: str
    step_type: str
    delay_sec: float = 0.0
    severity_override: str | None = None
    station_filter: str | None = None
    incident_type_override: str | None = None
    weather_override: str | None = None
    stress_amount: float = 0.0
    next_steps: list[str] = dataclasses.field(default_factory=list)
    config: dict = dataclasses.field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "step_type": self.step_type,
            "delay_sec": self.delay_sec,
            "severity_override": self.severity_override,
            "station_filter": self.station_filter,
            "incident_type_override": self.incident_type_override,
            "weather_override": self.weather_override,
            "stress_amount": self.stress_amount,
            "next_steps": self.next_steps,
            "config": self.config,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ScenarioStep":
        return cls(
            step_id=data.get("step_id", ""),
            step_type=data.get("step_type", "trigger"),
            delay_sec=data.get("delay_sec", 0.0),
            severity_override=data.get("severity_override"),
            station_filter=data.get("station_filter"),
            incident_type_override=data.get("incident_type_override"),
            weather_override=data.get("weather_override"),
            stress_amount=data.get("stress_amount", 0.0),
            next_steps=data.get("next_steps", []),
            config=data.get("config", {}),
        )


@dataclasses.dataclass
class Scenario:
    name: str
    description: str = ""
    steps: list[ScenarioStep] = dataclasses.field(default_factory=list)
    base_incidents: int = 20
    rate_per_sec: int = 1
    tags: list[str] = dataclasses.field(default_factory=list)
    is_custom: bool = False

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "steps": [s.to_dict() for s in self.steps],
            "base_incidents": self.base_incidents,
            "rate_per_sec": self.rate_per_sec,
            "tags": self.tags,
            "is_custom": self.is_custom,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Scenario":
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            steps=[ScenarioStep.from_dict(s) for s in data.get("steps", [])],
            base_incidents=data.get("base_incidents", 20),
            rate_per_sec=data.get("rate_per_sec", 1),
            tags=data.get("tags", []),
            is_custom=data.get("is_custom", False),
        )

    @classmethod
    def from_preset(cls, preset_name: str) -> Optional["Scenario"]:
        if preset_name not in SCENARIO_PRESETS:
            return None
        p = SCENARIO_PRESETS[preset_name]
        steps = []
        for i, step_data in enumerate(p["steps"]):
            step = ScenarioStep(
                step_id=f"step_{i:02d}",
                step_type=step_data.get("type", "trigger"),
                delay_sec=step_data.get("delay_sec", 0),
                severity_override=step_data.get("severity_override"),
                station_filter=step_data.get("station_filter"),
                weather_override=step_data.get("weather"),
                stress_amount=30.0 if step_data.get("type") == "stress_event" else 0.0,
            )
            steps.append(step)
        return cls(
            name=preset_name,
            description=p["description"],
            steps=steps,
            base_incidents=SCENARIO_MODES.get(preset_name, {}).get("incidents", 20),
            rate_per_sec=SCENARIO_MODES.get(preset_name, {}).get("rate", 1),
            tags=p["tags"],
        )

    def get_active_step(self, elapsed_sec: float) -> ScenarioStep | None:
        active = None
        for step in sorted(self.steps, key=lambda s: s.delay_sec, reverse=True):
            if elapsed_sec >= step.delay_sec:
                active = step
                break
        return active


@dataclasses.dataclass
class CompetencyScore:
    persona_name: str
    speed_score: float = 0.0
    accuracy_score: float = 0.0
    critical_score: float = 0.0
    specialty_score: float = 0.0
    escalation_score: float = 0.0
    balance_score: float = 0.0
    overall_score: float = 0.0

    def to_radar_dict(self) -> dict:
        labels = ["Speed", "Accuracy", "Critical\nHandling", "Specialty\nMatch", "Escalation\nControl", "Workload\nBalance"]
        values = [
            self.speed_score,
            self.accuracy_score,
            self.critical_score,
            self.specialty_score,
            self.escalation_score,
            self.balance_score,
        ]
        return {"labels": labels, "values": values}

    def get_weakest_area(self) -> tuple[str, float]:
        areas = [
            ("Speed", self.speed_score),
            ("Accuracy", self.accuracy_score),
            ("Critical Handling", self.critical_score),
            ("Specialty Match", self.specialty_score),
            ("Escalation Control", self.escalation_score),
            ("Workload Balance", self.balance_score),
        ]
        return min(areas, key=lambda x: x[1])

    def get_strengths(self) -> list[str]:
        return [name for name, score in [
            ("Speed", self.speed_score),
            ("Accuracy", self.accuracy_score),
            ("Critical Handling", self.critical_score),
            ("Specialty Match", self.specialty_score),
            ("Escalation Control", self.escalation_score),
            ("Workload Balance", self.balance_score),
        ] if score >= 80]


# Station and incident type configurations
STATIONS = [
    "Berlin Hauptbahnhof", "Munich Hauptbahnhof", "Frankfurt Hauptbahnhof",
    "Hamburg Hauptbahnhof", "Cologne Hauptbahnhof", "Stuttgart Hauptbahnhof",
    "Düsseldorf Hauptbahnhof", "Dresden Hauptbahnhof", "Hanover Hauptbahnhof",
    "Leipzig Hauptbahnhof"
]

INCIDENT_TYPES = {
    "CRITICAL": [
        ("gate_jam", "Gate jammed open/closed", ["Maintenance Engineer", "Gate Technician"]),
        ("sync_failure", "5G sync lost", ["Network Controller", "CTO"]),
        ("power_surge", "UPS overload detected", ["Maintenance Engineer", "Shift Supervisor"]),
        ("safety_breach", "Platform safety violation", ["Safety Officer", "Shift Supervisor"]),
        ("fire_alarm", "Fire detection triggered", ["Security Lead", "Shift Supervisor"]),
    ],
    "WARNING": [
        ("temp_high", "Temperature threshold exceeded", ["Safety Officer", "Maintenance Engineer"]),
        ("vibration", "Vibration levels elevated", ["Maintenance Engineer"]),
        ("sync_degrade", "Sync score degraded", ["Network Controller"]),
        ("sensor_fault", "Sensor calibration drift", ["Gate Technician"]),
        ("pressure_drop", "PSD pressure anomaly", ["Maintenance Engineer"]),
    ],
    "INFO": [
        ("passenger_congestion", "Platform overcrowding", ["Customer Relations", "Shift Supervisor"]),
        ("minor_fault", "Minor equipment fault", ["Gate Technician"]),
        ("schedule_delay", "Train running behind", ["Network Controller"]),
        ("cleaning_alert", "Platform cleaning required", ["Shift Supervisor"]),
        ("access_issue", "Restricted platform access", ["Security Lead"]),
    ],
}

WEATHER_MODIFIERS = {
    "normal": {"temp_high": 1.0, "vibration": 1.0, "gate_jam": 1.0, "sync_failure": 1.0},
    "storm": {"temp_high": 1.0, "vibration": 2.0, "gate_jam": 2.0, "sync_failure": 1.5, "power_surge": 2.0},
    "fog": {"sync_failure": 1.5},
    "heatwave": {"temp_high": 2.0, "vibration": 1.5, "gate_jam": 1.3},
    "rain": {"vibration": 1.2, "passenger_congestion": 1.5},
}

SCENARIO_MODES = {
    "quick_drill": {"incidents": 20, "rate": 3, "duration": 10},
    "shift_simulation": {"incidents": 50, "rate": 2, "duration": 60},
    "critical_hours": {"incidents": 30, "rate": 2, "duration": 30},
    "night_shift": {"incidents": 15, "rate": 1, "duration": 15},
    "weather_event": {"incidents": 25, "rate": 2, "duration": 25},
    "multi_station_cascade": {"incidents": 40, "rate": 2, "duration": 40},
}


def get_simulation_personas() -> list[SimulationPersona]:
    """Return the 12 personas for the training simulator."""
    return [
        SimulationPersona("Khushboo Patil", "CEO", ["Strategic", "Crisis"], 5.0, 95.0),
        SimulationPersona("Namrata Joshi", "COO", ["Operations", "Escalation"], 3.0, 92.0),
        SimulationPersona("Kona Shivam Rao", "CTO", ["Technical", "System"], 2.0, 90.0),
        SimulationPersona("Sanika Kale", "CPO", ["Process", "UX"], 4.0, 88.0),
        SimulationPersona("Nikhil Chavan", "CFO", ["Business", "Cost"], 6.0, 85.0),
        SimulationPersona("Shift Supervisor", "Operations", ["All", "Coordination"], 1.5, 87.0),
        SimulationPersona("Maintenance Engineer", "Operations", ["Mechanical", "Gate"], 2.0, 92.0),
        SimulationPersona("Safety Officer", "Operations", ["Safety", "Compliance"], 2.5, 90.0),
        SimulationPersona("Network Controller", "Operations", ["Network", "Sync"], 1.5, 89.0),
        SimulationPersona("Customer Relations", "Operations", ["Passenger", "Comm"], 3.0, 86.0),
        SimulationPersona("Gate Technician", "Operations", ["Gate", "Sensor"], 1.0, 88.0),
        SimulationPersona("Security Lead", "Operations", ["Security", "Access"], 2.0, 91.0),
    ]


class SimulationSession:
    """Manages a training simulation session."""

    def __init__(self, target_incidents: int = 20, rate_per_sec: int = 1,
                 seed: int | None = None, duration_minutes: int = 0,
                 scenario: Scenario | None = None):
        self.target_incidents = target_incidents
        self.rate_per_sec = 1
        self.duration_minutes = duration_minutes
        self.seed = seed
        self.rng = random.Random(seed)
        self.is_running = False
        self.is_paused = False
        self.incidents: list[Incident] = []
        self.personas = get_simulation_personas()
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None
        self.last_incident_time: datetime | None = None
        self.mode = "quick_drill"
        self.weather = "normal"
        self.metrics: dict = {}
        self._incident_counter = 0
        self.scenario: Scenario | None = scenario
        self.annotations: dict[str, str] = {}
        self.bookmarks: list[dict] = []
        self.rest_interval_counter: int = 0

    @property
    def is_duration_mode(self) -> bool:
        return self.duration_minutes > 0

    @property
    def competency_scores(self) -> list[CompetencyScore]:
        scores = []
        for p in self.personas:
            score = p.to_competency_score(COMPETENCY_BENCHMARKS)
            scores.append(score)
        return scores

    @property
    def team_fatigue_summary(self) -> dict:
        return {
            p.name: {
                "fatigue": p.fatigue,
                "level": p.fatigue_level,
                "needs_break": p.needs_break,
                "stress_events": p.stress_events,
            }
            for p in self.personas
        }

    @property
    def replay_timeline(self) -> list[dict]:
        timeline = []
        for inc in self.incidents:
            timeline.append({
                "id": inc.id,
                "timestamp": inc.timestamp,
                "seconds": (inc.timestamp - self.start_time).total_seconds() if self.start_time and inc.timestamp else 0,
                "severity": inc.severity,
                "station": inc.station,
                "description": inc.description,
                "assigned": inc.assigned_persona,
                "status": inc.status,
                "outcome": inc.outcome,
                "annotation": self.annotations.get(inc.id, ""),
            })
        return timeline

    def start(self):
        self.is_running = True
        self.is_paused = False
        self.start_time = datetime.now()
        self.last_incident_time = self.start_time
        if self.scenario:
            self.mode = self.scenario.name
            for step in self.scenario.steps:
                if step.weather_override:
                    self.weather = step.weather_override
        for p in self.personas:
            p.fatigue = 0.0
            p.stress_events = 0
            p.fatigue_incidents = 0

    def pause(self):
        self.is_paused = True

    def resume(self):
        self.is_paused = False
        self.last_incident_time = datetime.now()

    def stop(self):
        self.is_running = False
        self.end_time = datetime.now()
        self._calculate_metrics()

    def reset(self):
        self.is_running = False
        self.is_paused = False
        self.incidents = []
        self.personas = get_simulation_personas()
        self.start_time = None
        self.end_time = None
        self.last_incident_time = None
        self._incident_counter = 0
        self.metrics = {}
        self.annotations = {}
        self.bookmarks = []
        self.rest_interval_counter = 0

    def set_scenario(self, scenario: Scenario):
        self.scenario = scenario
        self.target_incidents = scenario.base_incidents
        self.rate_per_sec = scenario.rate_per_sec

    def add_annotation(self, incident_id: str, text: str):
        self.annotations[incident_id] = text

    def add_bookmark(self, incident_id: str, label: str):
        self.bookmarks.append({"incident_id": incident_id, "label": label, "at": datetime.now()})

    def _generate_incident_id(self) -> str:
        self._incident_counter += 1
        return f"INC-{datetime.now().strftime('%Y%m%d')}-{self._incident_counter:04d}"

    def _get_severity_weights(self) -> dict[str, float]:
        weights = {"CRITICAL": 0.2, "WARNING": 0.35, "INFO": 0.45}
        if self.mode == "critical_hours":
            weights = {"CRITICAL": 0.35, "WARNING": 0.4, "INFO": 0.25}
        elif self.mode == "night_shift":
            weights = {"CRITICAL": 0.1, "WARNING": 0.3, "INFO": 0.6}
        if self.scenario and self.scenario.steps:
            elapsed = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
            active_step = self.scenario.get_active_step(elapsed)
            if active_step and active_step.severity_override:
                override = active_step.severity_override
                if override == "HIGH_CRITICAL":
                    weights = {"CRITICAL": 0.6, "WARNING": 0.3, "INFO": 0.1}
                elif override == "LOW_INFO":
                    weights = {"CRITICAL": 0.05, "WARNING": 0.25, "INFO": 0.7}
                elif override == "CRITICAL":
                    weights = {"CRITICAL": 0.7, "WARNING": 0.2, "INFO": 0.1}
        return weights

    def _apply_scenario_step_effects(self, elapsed_sec: float):
        if not self.scenario or not self.scenario.steps:
            return
        triggered_steps = set()
        for step in self.scenario.steps:
            if elapsed_sec >= step.delay_sec:
                if step.step_type == "stress_event":
                    for p in self.personas:
                        if p.current_assigned > 0:
                            p.trigger_stress_event(step.stress_amount or 30.0)
                    triggered_steps.add(step.step_id)
                elif step.step_type == "rest_interval":
                    for p in self.personas:
                        p.rest_interval_recovery()
                    triggered_steps.add(step.step_id)
                elif step.step_type == "weather_change" and step.weather_override:
                    self.weather = step.weather_override
                    triggered_steps.add(step.step_id)
        self.rest_interval_counter = len([s for s in self.scenario.steps if s.step_type == "rest_interval" and s.step_id in triggered_steps])

    def _get_root_cause(self) -> tuple:
        causes = list(ROOT_CAUSES.keys())
        weights = [ROOT_CAUSES[c]["weight"] for c in causes]
        root_cause = self.rng.choices(causes, weights=weights)[0]
        cause_info = ROOT_CAUSES[root_cause]
        return root_cause, cause_info["label"], cause_info["preventable"]

    def generate_single(self) -> Incident | None:
        if not self.is_running or self.is_paused:
            return None

        if self.is_duration_mode and self.start_time:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            self._apply_scenario_step_effects(elapsed)
            if elapsed >= self.duration_minutes * 60:
                return None

        if not self.is_duration_mode and len(self.incidents) >= self.target_incidents:
            return None

        incident = self._create_incident()
        self.incidents.append(incident)
        self.last_incident_time = datetime.now()
        return incident

    def _create_incident(self) -> Incident:
        incident_id = self._generate_incident_id()
        timestamp = datetime.now()
        station = self.rng.choice(STATIONS[:5])

        severity_weights = self._get_severity_weights()
        severity = self.rng.choices(
            list(severity_weights.keys()),
            weights=list(severity_weights.values())
        )[0]

        incident_def = self.rng.choice(INCIDENT_TYPES[severity])
        incident_type, desc_template, eligible_roles = incident_def

        weather_mods = WEATHER_MODIFIERS.get(self.weather, {"temp_high": 1.0, "vibration": 1.0, "gate_jam": 1.0, "sync_failure": 1.0})
        weather_modified = weather_mods.get(incident_type, 1.0) > 1.0

        root_cause, cause_label, preventable = self._get_root_cause()
        improvement_area = IMPROVEMENT_AREAS.get(root_cause, "General")

        return Incident(
            id=incident_id,
            timestamp=timestamp,
            station=station,
            incident_type=incident_type,
            severity=severity,
            description=f"{desc_template} at {station}",
            weather_modified=weather_modified,
            root_cause=cause_label,
            preventable=preventable,
            improvement_area=improvement_area,
        )

    def assign_incident(self, incident: Incident) -> bool:
        if not self.personas:
            return False

        incident_type = incident.incident_type.lower()
        severity = incident.severity

        specialty_map = {
            "gate_jam": ["Maintenance Engineer", "Gate Technician", "Shift Supervisor"],
            "sync_failure": ["Network Controller", "CTO", "Shift Supervisor"],
            "sync_degrade": ["Network Controller", "CTO"],
            "power_surge": ["Maintenance Engineer", "Shift Supervisor", "COO"],
            "fire_alarm": ["Security Lead", "Shift Supervisor", "Safety Officer"],
            "safety_breach": ["Safety Officer", "Shift Supervisor", "COO"],
            "temp_high": ["Safety Officer", "Maintenance Engineer", "Gate Technician"],
            "vibration": ["Maintenance Engineer", "Safety Officer"],
            "sensor_fault": ["Gate Technician", "Maintenance Engineer"],
            "pressure_drop": ["Maintenance Engineer", "Safety Officer"],
            "passenger_congestion": ["Customer Relations", "Shift Supervisor", "Security Lead"],
            "minor_fault": ["Gate Technician", "Maintenance Engineer", "Shift Supervisor"],
            "schedule_delay": ["Network Controller", "Shift Supervisor"],
            "cleaning_alert": ["Shift Supervisor", "Security Lead"],
            "access_issue": ["Security Lead", "Shift Supervisor"],
        }

        matching_personas = specialty_map.get(incident_type, ["Shift Supervisor"])
        eligible = [p for p in self.personas if p.role in matching_personas]

        if not eligible:
            eligible = list(self.personas)

        eligible.sort(key=lambda p: (p.fatigue * 0.3 + p.current_assigned * 10))
        persona = eligible[0]

        incident.assigned_persona = persona.name
        incident.assigned_role = persona.role
        incident.status = "assigned"
        persona.record_assignment()

        if incident.timestamp:
            incident.time_to_assign = (datetime.now() - incident.timestamp).total_seconds()

        if severity == "CRITICAL":
            incident.escalation_level = 0

        return True

    def resolve_incident(self, incident: Incident, success: bool = True):
        if incident.status not in ["assigned", "escalated"]:
            return
        incident.status = "resolved" if success else "failed"

        for p in self.personas:
            if p.name == incident.assigned_persona:
                base_rt = p.avg_response_min
                variance = self.rng.gauss(0, 0.2)
                severity_mult = 0.8 if incident.severity == "CRITICAL" else 1.2 if incident.severity == "INFO" else 1.0
                response_time = max(0.1, p.apply_fatigue_to_response(base_rt * severity_mult + variance))

                eff_success = success
                if success and p.fatigue > 50:
                    recovery_chance = p.apply_fatigue_to_success(1.0)
                    eff_success = self.rng.random() < recovery_chance
                    if not eff_success:
                        incident.status = "failed"

                p.record_resolution(eff_success, response_time)
                incident.resolution_time_min = response_time

                if incident.timestamp:
                    incident.time_to_resolve = (datetime.now() - incident.timestamp).total_seconds()

                incident.was_escalated = incident.escalation_count > 0
                break

    def _calculate_metrics(self):
        total = len(self.incidents)
        resolved = len([i for i in self.incidents if i.status == "resolved"])
        failed = len([i for i in self.incidents if i.status == "failed"])
        escalated = len([i for i in self.incidents if i.was_escalated])
        critical = len([i for i in self.incidents if i.severity == "CRITICAL"])
        warning = len([i for i in self.incidents if i.severity == "WARNING"])
        info = len([i for i in self.incidents if i.severity == "INFO"])

        avg_response = 0
        resolution_times = [i.resolution_time_min for i in self.incidents if i.resolution_time_min > 0]
        if resolution_times:
            avg_response = sum(resolution_times) / len(resolution_times)

        root_causes = {}
        for inc in self.incidents:
            cause = inc.root_cause or "Unknown"
            root_causes[cause] = root_causes.get(cause, 0) + 1

        improvement_areas = {}
        for inc in self.incidents:
            area = inc.improvement_area or "General"
            improvement_areas[area] = improvement_areas.get(area, 0) + 1

        persona_stats = {}
        for inc in self.incidents:
            if inc.assigned_persona:
                if inc.assigned_persona not in persona_stats:
                    persona_stats[inc.assigned_persona] = {"assigned": 0, "resolved": 0, "failed": 0, "escalated": 0, "fatigue_end": 0, "stress_events": 0}
                persona_stats[inc.assigned_persona]["assigned"] += 1
                if inc.status == "resolved":
                    persona_stats[inc.assigned_persona]["resolved"] += 1
                elif inc.status == "failed":
                    persona_stats[inc.assigned_persona]["failed"] += 1
                if inc.was_escalated:
                    persona_stats[inc.assigned_persona]["escalated"] += 1

        for p in self.personas:
            if p.name in persona_stats:
                persona_stats[p.name]["fatigue_end"] = p.fatigue
                persona_stats[p.name]["stress_events"] = p.stress_events

        worst_performer = max(persona_stats.items(), key=lambda x: x[1]["failed"])[0] if persona_stats else None

        competency_scores = {
            p.name: p.to_competency_score(COMPETENCY_BENCHMARKS).to_radar_dict()
            for p in self.personas
        }

        self.metrics = {
            "total_incidents": total,
            "resolved": resolved,
            "failed": failed,
            "escalated": escalated,
            "critical": critical,
            "warning": warning,
            "info": info,
            "success_rate": (resolved / total * 100) if total > 0 else 0,
            "avg_response_time": avg_response,
            "duration_sec": (self.end_time - self.start_time).total_seconds() if self.end_time and self.start_time else 0,
            "root_causes": root_causes,
            "improvement_areas": improvement_areas,
            "persona_stats": persona_stats,
            "worst_performer": worst_performer,
            "competency_scores": competency_scores,
            "team_fatigue": self.team_fatigue_summary,
        }

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame([i.to_dict() for i in self.incidents])


# ═══════════════════════════════════════════════════
# ANOMALY DETECTION & TIME-SERIES ANALYTICS LAB
# ═══════════════════════════════════════════════════

_SKLEARN_AVAILABLE = False
try:
    from sklearn.ensemble import IsolationForest as _IsolationForest
    _SKLEARN_AVAILABLE = True
except ImportError:
    pass


def detect_anomalies_zscore(
    series: pd.Series,
    threshold: float = 3.0,
) -> pd.DataFrame:
    """
    Detect anomalies using Z-score method.
    Flags points where |Z| > threshold.
    """
    result = pd.DataFrame({"value": series.values})
    mean, std = series.mean(), series.std()
    if std == 0:
        result["z_score"] = 0.0
        result["is_anomaly"] = False
    else:
        result["z_score"] = (series.values - mean) / std
        result["is_anomaly"] = result["z_score"].abs() > threshold
    result["threshold_upper"] = mean + threshold * std
    result["threshold_lower"] = mean - threshold * std
    return result


def detect_anomalies_iqr(
    series: pd.Series,
    multiplier: float = 1.5,
) -> pd.DataFrame:
    """
    Detect anomalies using IQR (Tukey's fences) method.
    """
    result = pd.DataFrame({"value": series.values})
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    iqr = q3 - q1
    lower_fence = q1 - multiplier * iqr
    upper_fence = q3 + multiplier * iqr
    result["lower_fence"] = lower_fence
    result["upper_fence"] = upper_fence
    result["is_anomaly"] = (series.values < lower_fence) | (series.values > upper_fence)
    return result


def detect_anomalies_moving_average(
    series: pd.Series,
    window: int = 12,
    std_mult: float = 2.0,
) -> pd.DataFrame:
    """
    Detect anomalies using rolling moving average band.
    """
    result = pd.DataFrame({"value": series.values})
    rolling_mean = series.rolling(window=window, center=True, min_periods=1).mean()
    rolling_std = series.rolling(window=window, center=True, min_periods=1).std().fillna(0)
    result["rolling_mean"] = rolling_mean
    result["rolling_upper"] = rolling_mean + std_mult * rolling_std
    result["rolling_lower"] = rolling_mean - std_mult * rolling_std
    result["is_anomaly"] = (series.values > result["rolling_upper"]) | (series.values < result["rolling_lower"])
    return result


def detect_anomalies_isolation_forest(
    df: pd.DataFrame,
    features: list,
    contamination: float = 0.05,
    random_state: int = 42,
) -> pd.DataFrame:
    """
    Detect anomalies using Isolation Forest.
    Returns input DataFrame with anomaly_score and is_anomaly columns added.
    If scikit-learn is unavailable, returns a DataFrame with a note column.
    """
    result = df.copy()
    if not _SKLEARN_AVAILABLE:
        result["is_anomaly"] = False
        result["anomaly_score"] = 0.0
        result["_note"] = "Install scikit-learn to use Isolation Forest"
        return result

    X = df[features].select_dtypes(include=[np.number]).dropna()
    if X.empty:
        result["is_anomaly"] = False
        result["anomaly_score"] = 0.0
        return result

    model = _IsolationForest(contamination=contamination, random_state=random_state, n_estimators=100)
    preds = model.fit_predict(X)
    scores = model.decision_function(X)

    aligned = pd.Series(index=X.index, data=preds == -1, dtype=bool)
    score_aligned = pd.Series(index=X.index, data=scores)
    result["is_anomaly"] = aligned.reindex(result.index, fill_value=False)
    result["anomaly_score"] = score_aligned.reindex(result.index, fill_value=0.0)
    return result


def evaluate_detection_method(
    true_labels: pd.Series,
    pred_labels: pd.Series,
) -> dict:
    """
    Evaluate anomaly detection results.
    Returns dict with precision, recall, f1, accuracy, and confusion matrix values.
    """
    tp = (pred_labels & true_labels).sum()
    fp = (pred_labels & ~true_labels).sum()
    fn = (~pred_labels & true_labels).sum()
    tn = (~pred_labels & ~true_labels).sum()

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / (tp + fp + fn + tn) if (tp + fp + fn + tn) > 0 else 0.0

    return {
        "true_positives": int(tp),
        "false_positives": int(fp),
        "false_negatives": int(fn),
        "true_negatives": int(tn),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "accuracy": round(accuracy, 4),
        "total_detected": int(pred_labels.sum()),
        "total_true": int(true_labels.sum()),
    }


def decompose_timeseries(
    series: pd.Series,
    period: int = 24,
) -> dict:
    """
    Simple time-series decomposition into trend, seasonal, and residual components.
    """
    result = {}
    values = series.values
    n = len(values)

    # Trend: centered moving average over one period
    trend = pd.Series(values).rolling(window=period, center=True, min_periods=1).mean().values

    # Detrended
    detrended = values - trend

    # Seasonal: average detrended value at each position in the period
    seasonal = np.zeros(n)
    for i in range(period):
        indices = range(i, n, period)
        if indices:
            seasonal[list(indices)] = np.nanmean(detrended[list(indices)])

    # Residual
    residual = values - trend - seasonal

    result["trend"] = trend
    result["seasonal"] = seasonal
    result["residual"] = residual
    result["original"] = values
    result["period"] = period

    return result


def compute_sensor_correlations(
    df: pd.DataFrame,
    sensor_cols: list = None,
) -> pd.DataFrame:
    """
    Compute Pearson correlation matrix for sensor columns.
    """
    if sensor_cols is None:
        sensor_cols = ["sensor_temp", "sensor_vib", "people", "risk_score"]
    available = [c for c in sensor_cols if c in df.columns]
    if len(available) < 2:
        return pd.DataFrame()
    return df[available].select_dtypes(include=[np.number]).corr()


def analyze_sensor_health_profile(
    df: pd.DataFrame,
    station: str = None,
) -> pd.DataFrame:
    """
    Build per-gate health profile with anomaly flags using IQR.
    """
    gate_col = "gate_id" if "gate_id" in df.columns else "gate"
    subset = df[df["station"] == station].copy() if station and "station" in df.columns else df.copy()

    if subset.empty:
        return pd.DataFrame()

    profile = subset.groupby(gate_col).agg(
        avg_temp=("sensor_temp", "mean"),
        avg_vib=("sensor_vib", "mean"),
        avg_people=("people", "mean"),
        avg_risk=("risk_score", "mean"),
        max_temp=("sensor_temp", "max"),
        max_vib=("sensor_vib", "max"),
        readings=("sensor_temp", "count"),
    ).reset_index()

    # Flag anomalies using IQR per column
    for col in ["avg_temp", "avg_vib", "avg_people", "avg_risk"]:
        q1, q3 = profile[col].quantile(0.25), profile[col].quantile(0.75)
        iqr = q3 - q1
        low = q1 - 1.5 * iqr
        high = q3 + 1.5 * iqr
        profile[f"{col}_anomaly"] = (profile[col] < low) | (profile[col] > high)

    profile["total_flags"] = (
        profile["avg_temp_anomaly"].astype(int)
        + profile["avg_vib_anomaly"].astype(int)
        + profile["avg_people_anomaly"].astype(int)
        + profile["avg_risk_anomaly"].astype(int)
    )

    return profile.sort_values("total_flags", ascending=False)
