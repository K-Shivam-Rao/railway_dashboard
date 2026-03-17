import pandas as pd
import matplotlib.pyplot as plt
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
                 cac_simplified=100):
        self.customers = starting_customers
        self.growth_rate = monthly_growth_rate
        self.churn_rate = churn_rate
        self.price = price_per_customer
        self.fixed_costs = fixed_costs
        self.variable_cost = variable_cost_per_customer
        self.cac = cac_simplified  # Simplified Customer Acquisition Cost

    def __repr__(self):
        return (f"SaaSConfig(Start={self.customers}, Growth={self.growth_rate*100}%, "
                f"Churn={self.churn_rate*100}%, Price=${self.price})")

# ---------------------------------------------------------
# 2. Simulate Monthly Growth & 4. Profit & Cash Flow
# ---------------------------------------------------------


def run_simulation(config, months=24):
    """
    Simulates the SaaS metrics over a specified number of months.
    Returns a Pandas DataFrame with all calculated metrics.
    """
    data = []

    # Initial State
    current_customers = config.customers
    # Initial investment to acquire starting customers
    cumulative_cash = - (current_customers * config.cac)

    for month in range(1, months + 1):
        # --- Logic from Task 2 ---
        new_customers = int(current_customers * config.growth_rate)
        churned_customers = int(current_customers * config.churn_rate)

        # Update Total Customers
        total_customers = current_customers + new_customers - churned_customers

        # --- Logic from Task 3: Core Metrics ---
        mrr = total_customers * config.price

        # Churn Rate % (Absolute churned / Start of month customers)
        churn_percentage = (churned_customers / current_customers) * \
            100 if current_customers > 0 else 0

        # Contribution Margin: (Price - Variable Cost)
        contribution_margin = config.price - config.variable_cost
        contribution_margin_pct = (
            contribution_margin / config.price) * 100 if config.price > 0 else 0

        # LTV (Simplified: Contribution Margin / Churn Rate)
        # Note: Using monthly churn rate for simplified monthly LTV
        ltv = (contribution_margin /
               config.churn_rate) if config.churn_rate > 0 else 0

        # CAC is already in config, but we calculate total CAC spent this month
        total_cac_spent = new_customers * config.cac

        # --- Logic from Task 4: Financials ---
        total_revenue = mrr
        variable_costs_total = total_customers * config.variable_cost

        # Total Costs = Fixed + Variable + CAC (Marketing/Sales)
        total_costs = config.fixed_costs + variable_costs_total + total_cac_spent

        profit_loss = total_revenue - total_costs
        cumulative_cash += profit_loss

        # Store Data
        row = {
            "Month": month,
            "Start_Customers": current_customers,
            "New_Customers": new_customers,
            "Churned_Customers": churned_customers,
            "Total_Customers": total_customers,
            "MRR": mrr,
            "Revenue_Growth_Rate": 0,  # Will calculate next
            "Churn_Rate_%": round(churn_percentage, 2),
            "LTV": round(ltv, 2),
            "CAC": config.cac,
            "Contribution_Margin_$": round(contribution_margin, 2),
            "Total_Revenue": total_revenue,
            "Total_Costs": total_costs,
            "Profit_Loss": profit_loss,
            "Cumulative_Cash": cumulative_cash
        }
        data.append(row)

        # Update current_customers for next iteration
        current_customers = total_customers

    df = pd.DataFrame(data)

    # Calculate Revenue Growth Rate (Month over Month)
    df["Revenue_Growth_Rate"] = df["MRR"].pct_change() * 100
    df["Revenue_Growth_Rate"] = df["Revenue_Growth_Rate"].fillna(
        0)  # First month is 0 or NA

    return df

# ---------------------------------------------------------
# 5. Output & Visualization
# ---------------------------------------------------------


def visualize_results(df, title_suffix=""):
    """Generates and saves the required charts."""
    plt.figure(figsize=(18, 5))

    # Chart 1: Customers Growth
    plt.subplot(1, 3, 1)
    plt.plot(df['Month'], df['Total_Customers'], marker='o',
             color='tab:blue', label='Total Customers')
    plt.bar(df['Month'], df['New_Customers'],
            color='tab:green', alpha=0.3, label='New Customers')
    plt.title('Customer Growth')
    plt.xlabel('Month')
    plt.ylabel('Customers')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)

    # Chart 2: MRR Growth
    plt.subplot(1, 3, 2)
    plt.plot(df['Month'], df['MRR'], marker='s', color='tab:orange')
    plt.title('MRR Growth')
    plt.xlabel('Month')
    plt.ylabel('MRR ($)')
    plt.grid(True, linestyle='--', alpha=0.6)

    # Format Y-axis to currency
    ax = plt.gca()
    ax.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, p: format(int(x), ',')))

    # Chart 3: Profit Curve & Cumulative Cash
    plt.subplot(1, 3, 3)
    plt.plot(df['Month'], df['Profit_Loss'], marker='x',
             color='tab:red', label='Monthly P&L')
    plt.plot(df['Month'], df['Cumulative_Cash'], marker='.',
             linewidth=2, color='tab:purple', label='Cumulative Cash')
    plt.axhline(0, color='black', linewidth=1)  # Breakeven line
    plt.title('Profit & Cash Flow')
    plt.xlabel('Month')
    plt.ylabel('Amount ($)')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)

    plt.suptitle(
        f'SaaS Financial Simulation Results {title_suffix}', fontsize=16)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    filename = f"saas_simulation_{title_suffix.replace(' ', '_').lower()}.png"
    plt.savefig(filename)
    print(f"[CHART] Chart saved as: {filename}")


def print_summary(df, config):
    """Prints key interpretation points."""
    print("\n" + "="*40)
    print("FINANCIAL SIMULATION SUMMARY")
    print("="*40)
    print(
        f"Assumptions: Start={config.customers} users, Growth={config.growth_rate*100}%, Churn={config.churn_rate*100}%")
    print(f"Price: ${config.price}, Fixed Costs: ${config.fixed_costs:,}")
    print("-" * 40)

    # 1. Breakeven Analysis
    breakeven_month = df[df['Cumulative_Cash'] >= 0]['Month'].min()
    if pd.notna(breakeven_month):
        print(f"[OK] Break-even Month: Month {int(breakeven_month)}")
    else:
        print(f"[ERROR] Break-even: Not reached within {len(df)} months")

    # 2. Final Metrics
    final_row = df.iloc[-1]
    print(f"[CHART] Final MRR (Month {len(df)}): ${final_row['MRR']:,.2f}")
    print(f"[USERS] Final Customers: {int(final_row['Total_Customers'])}")
    print(f"[MONEY] Final Cumulative Cash: ${final_row['Cumulative_Cash']:,.2f}")

    # 3. Impact of Churn
    total_lost = df['Churned_Customers'].sum()
    total_gained = df['New_Customers'].sum()
    print(
        f"[WARN] Total Churned Customers: {int(total_lost)} ({(total_lost/total_gained)*100:.1f}% of gains)")
    print("="*40 + "\n")

# ---------------------------------------------------------
# Main Execution Block
# ---------------------------------------------------------


if __name__ == "__main__":
    # --- Scenario A: Base Case (Healthy Growth) ---
    print("Running Scenario A: Base Case...")
    config_base = SaaSModelConfig(
        starting_customers=50,
        monthly_growth_rate=0.20,  # 20% growth
        churn_rate=0.05,           # 5% churn
        price_per_customer=100,    # $100 MRR
        fixed_costs=5000,          # $5k fixed (Servers, Salaries)
        variable_cost_per_customer=10,  # $10 variable (Hosting per user)
        cac_simplified=150         # $150 to acquire a customer
    )

    df_base = run_simulation(config_base, months=24)
    print_summary(df_base, config_base)
    visualize_results(df_base, title_suffix="(Base Case)")

    # Export table for submission
    df_base.to_csv("simulation_results_base.csv", index=False)
    print("[CSV] Table saved as: simulation_results_base.csv")

    # --- Scenario B: High Churn (Analysis Task Requirement) ---
    print("Running Scenario B: High Churn Analysis...")
    config_high_churn = SaaSModelConfig(
        starting_customers=50,
        monthly_growth_rate=0.20,
        churn_rate=0.10,           # 10% churn (Doubled!)
        price_per_customer=100,
        fixed_costs=5000,
        variable_cost_per_customer=10,
        cac_simplified=150
    )

    df_churn = run_simulation(config_high_churn, months=24)
    print_summary(df_churn, config_high_churn)
    visualize_results(df_churn, title_suffix="(High Churn Scenario)")

    # Export high churn results
    df_churn.to_csv("simulation_results_high_churn.csv", index=False)
    print("[CSV] Table saved as: simulation_results_high_churn.csv")
