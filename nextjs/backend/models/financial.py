"""Financial / SaaS projection models."""
from pydantic import BaseModel
from typing import List, Optional


class FinancialProjection(BaseModel):
    month:         int
    customers:     int
    mrr:           float
    cogs:          float
    fixed_costs:   float
    net_income:    float
    cash_bank:     float


class ScenarioComparison(BaseModel):
    scenario:     str
    months:       List[int]
    net_incomes:  List[float]


class FinancialModelConfig(BaseModel):
    starting_customers:   int    = 50
    monthly_growth_rate:  float  = 0.08
    churn_rate:           float  = 0.03
    price_per_customer:   float  = 149.0
    fixed_costs:          float  = 35000.0
    variable_cost_per_customer: float = 20.0


class FinancialOverview(BaseModel):
    total_revenue: float
    net_income:    float
    cagr:          Optional[float] = None
