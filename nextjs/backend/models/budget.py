"""Budget / ROI model objects."""
from pydantic import BaseModel
from typing import List, Optional


class BudgetOverview(BaseModel):
    total_budget: float
    spent:        float
    remaining:    float
    utilization:  float
    top_expenses: Optional[list] = None


class ROIData(BaseModel):
    project:       str
    invested:      float
    returned:      float
    roi:           float


class MonthlySpend(BaseModel):
    month:   str
    budget:  float
    spent:   float


class ScenarioProjection(BaseModel):
    month:       int
    revenue:     float
    baseline:    float
    conservative:float
    optimistic:  float
