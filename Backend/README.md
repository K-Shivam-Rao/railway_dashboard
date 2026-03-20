# SaaS Financial Simulation

A Python-based SaaS financial modeling tool that simulates monthly metrics including MRR, customer growth, churn, LTV, CAC, and profitability over time.

## Features

- Monthly simulation of customer acquisition, churn, and growth
- Key SaaS metrics: MRR, LTV, CAC, Churn Rate, Contribution Margin
- Profit & Loss tracking with cumulative cash flow
- Breakeven analysis
- Automated visualization with matplotlib
- Scenario comparison (Base Case vs High Churn)
- **Interactive Streamlit dashboard with parameter controls**

## Quick Start

### Option 1: Command-Line Script

```bash
# Install dependencies
pip install -r requirements.txt

# Run standalone simulation
python app.py
```

This will:
- Run two scenarios (Base Case and High Churn)
- Generate summary statistics
- Create visualization charts (PNG files)
- Export results to CSV files

### Option 2: Streamlit Dashboard (Recommended)

```bash
# From the Backend directory
cd Backend
streamlit run dashboard.py
```

The dashboard provides:
- **Interactive parameter controls** (sliders, number inputs)
- Real-time simulation updates
- Side-by-side scenario comparison
- Comprehensive charts and KPIs
- Data table export

## Project Structure

```
Backend/
├── app.py              # Standalone Python simulation script
├── dashboard.py        # Interactive Streamlit dashboard
├── requirements.txt    # Python dependencies
├── README.md           # This file
├── output/             # Generated CSV results (created on run)
├── *.png               # Generated visualization charts
└── simulation_results_*.csv  # CSV exports
```

## Configuration

### Via Dashboard (Recommended)

Use the interactive controls in the Streamlit dashboard:
- Starting Customers (1-1000)
- Monthly Growth Rate (1-50%)
- Monthly Churn Rate (1-30%)
- Price per Customer ($)
- Fixed Costs ($/month)
- Variable Cost per Customer ($)
- CAC (Customer Acquisition Cost)
- High Churn Multiplier (1x-5x)
- Simulation Period (12-60 months)

### Via Code (app.py)

Edit the `SaaSModelConfig` parameters in `app.py`:

```python
config_base = SaaSModelConfig(
    starting_customers=50,           # Initial number of customers
    monthly_growth_rate=0.20,       # 20% monthly growth
    churn_rate=0.05,                # 5% monthly churn
    price_per_customer=100,        # $100 MRR per customer
    fixed_costs=5000,               # $5,000 monthly fixed costs
    variable_cost_per_customer=10,   # $10 variable cost per customer
    cac_simplified=150,             # $150 customer acquisition cost
)
```

## Key Parameters Explained

| Parameter | Default | Description |
|-----------|---------|-------------|
| `starting_customers` | 50 | Initial customer base |
| `monthly_growth_rate` | 0.20 | Growth rate (20% = 0.20) |
| `churn_rate` | 0.05 | Monthly churn (5% = 0.05) |
| `price_per_customer` | 100 | Average MRR per customer |
| `fixed_costs` | 5000 | Monthly fixed operating costs |
| `variable_cost_per_customer` | 10 | Variable COGS per customer |
| `cac_simplified` | 150 | Customer acquisition cost |

## Output Files

### CSV Exports
- `simulation_results_base.csv` - Base case scenario data
- `simulation_results_high_churn.csv` - High churn scenario data

### Charts
- `saas_simulation_base_case.png` - Basic 3-chart overview
- `saas_dashboard1_base_case.png` - Revenue & cost detail
- `saas_dashboard2_base_case.png` - Efficiency metrics
- `saas_scenario_comparison.png` - Base vs High Churn comparison

## Key Metrics Calculated

| Metric | Description |
|--------|-------------|
| MRR | Monthly Recurring Revenue |
| ARR | Annual Recurring Revenue (MRR × 12) |
| LTV | Lifetime Value = (Price - Variable Cost) / Churn Rate |
| CAC | Customer Acquisition Cost |
| LTV:CAC | Ratio - should exceed 3:1 |
| Gross Margin | (Revenue - COGS) / Revenue |
| S&M Efficiency | Net New MRR / Sales & Marketing Cost |
| CAC Payback | Months to recover CAC |

## License

MIT
