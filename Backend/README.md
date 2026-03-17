# SaaS Financial Simulation

A Python-based SaaS financial modeling tool that simulates monthly metrics including MRR, customer growth, churn, LTV, CAC, and profitability over time.

## Features

- Monthly simulation of customer acquisition, churn, and growth
- Key SaaS metrics: MRR, LTV, CAC, Churn Rate, Contribution Margin
- Profit & Loss tracking with cumulative cash flow
- Breakeven analysis
- Automated visualization with matplotlib
- Scenario comparison (Base Case vs High Churn)

## Requirements

- Python 3.10+
- pandas
- matplotlib
- numpy

## Installation

```bash
pip install -r requirements.txt
```

## Usage

Run the simulation:

```bash
python app.py
```

This will:
- Run two scenarios (Base Case and High Churn)
- Generate summary statistics
- Create visualization charts (PNG files)
- Export results to CSV files

## Configuration

Edit the `SaaSModelConfig` parameters in `app.py`:

- `starting_customers`: Initial number of customers
- `monthly_growth_rate`: Monthly growth rate (e.g., 0.20 for 20%)
- `churn_rate`: Monthly churn rate (e.g., 0.05 for 5%)
- `price_per_customer`: MRR per customer
- `fixed_costs`: Monthly fixed costs
- `variable_cost_per_customer`: Variable cost per customer
- `cac_simplified`: Customer Acquisition Cost

## Output

- Console summary with breakeven month and final metrics
- Charts saved as `saas_simulation_<scenario>.png`
- CSV exports: `simulation_results_<scenario>.csv`

## License

MIT
