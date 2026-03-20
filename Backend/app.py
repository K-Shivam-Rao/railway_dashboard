import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

# ---------------------------------------------------------
# 1. Model the Financial Inputs
# ---------------------------------------------------------


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
            "Sales":        6000,
            "Marketing":    5500,
            "CS":           4500,
            "G&A":          5000,
        }

    def __repr__(self):
        return (f"SaaSConfig(Start={self.customers}, Growth={self.growth_rate*100}%, "
                f"Churn={self.churn_rate*100}%, Price=${self.price})")


# ---------------------------------------------------------
# 2. Simulate Monthly Growth + Financials + Extra Metrics
# ---------------------------------------------------------


def run_simulation(config, months=24):
    """
    Simulates the SaaS metrics over a specified number of months.
    Returns a Pandas DataFrame with all calculated metrics.
    """
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

        # ── Customer movements ──────────────────────────────────────────────
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

        # ── Core SaaS metrics ───────────────────────────────────────────────
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
        # Simple rule: 1 new hire per dept per N customers added
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


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def fmt_currency(ax, axis="y"):
    formatter = mticker.FuncFormatter(lambda x, _: f"${x:,.0f}")
    if axis == "y":
        ax.yaxis.set_major_formatter(formatter)
    else:
        ax.xaxis.set_major_formatter(formatter)

MONTHS_LABEL = lambda df: df["Month"].astype(str)


# ---------------------------------------------------------
# 5a. Original 3-chart figure (preserved)
# ---------------------------------------------------------

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
    fmt_currency(ax)

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
    print(f"[CHART] Saved: {filename}")
    plt.close()


# ---------------------------------------------------------
# 5b. NEW — Dashboard 1: MRR Movements, MRR Growth,
#           Enterprise Wins/Losses, Cost Breakdowns
# ---------------------------------------------------------

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
    fmt_currency(ax)

    # [0,1] MRR Growth + MoM %
    ax = axes[0, 1]
    ax2 = ax.twinx()
    ax.bar(months, df["Net_New_MRR"], label="Net New MRR", color="#27ae60", alpha=0.8)
    ax2.plot(months, df["MoM_Growth_%"], color="#2980b9", linewidth=2, marker='s', markersize=4, label="MoM growth %")
    ax.set_title("MRR Growth")
    ax.set_xlabel("Month"); ax.set_ylabel("Net New MRR ($)"); ax2.set_ylabel("MoM Growth %")
    fmt_currency(ax)
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
    fmt_currency(ax)

    # [1,1] Monthly Costs by Category (same data, different palette for visual variety)
    ax = axes[1, 1]
    ax.stackplot(months, df["COGS"], df["RD_Cost"], df["SM_Cost"], df["GA_Cost"], df["CS_Cost"],
                 labels=["CoGS", "R&D", "Sales & Marketing", "G&A", "Customer Success"],
                 colors=["#117a65", "#1a5276", "#7d6608", "#784212", "#4a235a"], alpha=0.75)
    ax.set_title("Monthly Costs by Category")
    ax.set_xlabel("Month"); ax.set_ylabel("Cost ($)")
    ax.legend(fontsize=7, loc='upper left'); ax.grid(True, linestyle='--', alpha=0.5)
    fmt_currency(ax)

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
    fmt_currency(ax)

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    filename = f"saas_dashboard1_{title_suffix.replace(' ', '_').replace('(','').replace(')','').lower()}.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"[CHART] Saved: {filename}")
    plt.close()


# ---------------------------------------------------------
# 5c. NEW — Dashboard 2: Revenue vs Costs, Gross Margin,
#           Headcount, S&M Efficiency, CAC Payback
# ---------------------------------------------------------

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
    fmt_currency(ax1)

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

    # ── ROW 2: 2 charts (span slightly wider) ────────────────────────────────

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
    print(f"[CHART] Saved: {filename}")
    plt.close()


# ---------------------------------------------------------
# 5d. NEW — Dashboard 3: Scenario Comparison (Base vs High Churn)
# ---------------------------------------------------------

def visualize_comparison(df_base, df_churn):
    fig, axes = plt.subplots(2, 3, figsize=(22, 12))
    fig.suptitle("Scenario Comparison: Base Case vs High Churn", fontsize=15, fontweight='bold')

    months = df_base["Month"]

    comparisons = [
        (axes[0, 0], "MRR",              "MRR ($)",          "MRR Growth"),
        (axes[0, 1], "Total_Customers",  "Customers",        "Total Customers"),
        (axes[0, 2], "Cumulative_Cash",  "Cumulative Cash ($)", "Cumulative Cash"),
        (axes[1, 0], "Gross_Margin_%",   "Gross Margin %",   "Gross Margin"),
        (axes[1, 1], "SM_Efficiency",    "S&M Efficiency",   "S&M Efficiency"),
        (axes[1, 2], "EBIT",             "EBIT ($)",         "EBIT"),
    ]

    for ax, col, ylabel, title in comparisons:
        ax.plot(months, df_base[col],  linewidth=2, marker='o', markersize=3,
                color="#2980b9", label="Base Case (5% churn)")
        ax.plot(months, df_churn[col], linewidth=2, marker='s', markersize=3,
                color="#e74c3c", label="High Churn (10% churn)", linestyle='--')
        ax.set_title(title); ax.set_xlabel("Month"); ax.set_ylabel(ylabel)
        ax.legend(fontsize=8); ax.grid(True, linestyle='--', alpha=0.5)
        if "$" in ylabel:
            fmt_currency(ax)
        if "%" in ylabel:
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.1f}%"))

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    filename = "saas_scenario_comparison.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"[CHART] Saved: {filename}")
    plt.close()


# ---------------------------------------------------------
# Summary Print
# ---------------------------------------------------------

def print_summary(df, config):
    print("\n" + "="*50)
    print("FINANCIAL SIMULATION SUMMARY")
    print("="*50)
    print(f"Assumptions: Start={config.customers}, Growth={config.growth_rate*100}%, Churn={config.churn_rate*100}%")
    print(f"Price: ${config.price}, Fixed Costs: ${config.fixed_costs:,}")
    print("-" * 50)

    breakeven_month = df[df['Cumulative_Cash'] >= 0]['Month'].min()
    if pd.notna(breakeven_month):
        print(f"[OK]    Break-even Month   : Month {int(breakeven_month)}")
    else:
        print(f"[ERROR] Break-even         : Not reached within {len(df)} months")

    final = df.iloc[-1]
    print(f"[MRR]   Final MRR          : ${final['MRR']:,.0f}")
    print(f"[ARR]   Final ARR          : ${final['ARR']:,.0f}")
    print(f"[USERS] Final Customers    : {int(final['Total_Customers'])}")
    print(f"[CASH]  Final Cum. Cash    : ${final['Cumulative_Cash']:,.0f}")
    print(f"[MARGIN]Final Gross Margin : {final['Gross_Margin_%']:.1f}%")
    print(f"[HC]    Final Headcount    : {int(final['Total_Headcount'])}")
    print(f"[LTV]   LTV/CAC Ratio      : {final['LTV_CAC_Ratio']:.2f}x")

    total_lost   = df['Churned_Customers'].sum()
    total_gained = df['New_Customers'].sum()
    print(f"[WARN]  Total Churned      : {int(total_lost)} ({(total_lost/total_gained)*100:.1f}% of gains)")
    print("="*50 + "\n")


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

if __name__ == "__main__":

    # ── Scenario A: Base Case ──────────────────────────────────────────────
    print("Running Scenario A: Base Case...")
    config_base = SaaSModelConfig(
        starting_customers=50,
        monthly_growth_rate=0.20,
        churn_rate=0.05,
        price_per_customer=100,
        fixed_costs=5000,
        variable_cost_per_customer=10,
        cac_simplified=150,
        initial_eng=5, initial_sales=3, initial_marketing=2, initial_cs=2, initial_ga=2
    )

    df_base = run_simulation(config_base, months=24)
    print_summary(df_base, config_base)
    visualize_results(df_base,     title_suffix="(Base Case)")
    visualize_dashboard_1(df_base, title_suffix="(Base Case)")
    visualize_dashboard_2(df_base, title_suffix="(Base Case)")

    df_base.to_csv("simulation_results_base.csv", index=False)
    print("[CSV] Saved: simulation_results_base.csv")

    # ── Scenario B: High Churn ─────────────────────────────────────────────
    print("\nRunning Scenario B: High Churn Analysis...")
    config_high_churn = SaaSModelConfig(
        starting_customers=50,
        monthly_growth_rate=0.20,
        churn_rate=0.10,
        price_per_customer=100,
        fixed_costs=5000,
        variable_cost_per_customer=10,
        cac_simplified=150,
        initial_eng=5, initial_sales=3, initial_marketing=2, initial_cs=2, initial_ga=2
    )

    df_churn = run_simulation(config_high_churn, months=24)
    print_summary(df_churn, config_high_churn)
    visualize_results(df_churn,     title_suffix="(High Churn Scenario)")
    visualize_dashboard_1(df_churn, title_suffix="(High Churn Scenario)")
    visualize_dashboard_2(df_churn, title_suffix="(High Churn Scenario)")

    df_churn.to_csv("simulation_results_high_churn.csv", index=False)
    print("[CSV] Saved: simulation_results_high_churn.csv")

    # ── Scenario Comparison ────────────────────────────────────────────────
    print("\nGenerating scenario comparison chart...")
    visualize_comparison(df_base, df_churn)

    print("\n[DONE] All files generated successfully.")