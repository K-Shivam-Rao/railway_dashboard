"""GET /api/v1/financial/* — SaaS financial model + simulation."""
from fastapi import APIRouter, HTTPException
from backend.core.data_manager import data_manager as dm
from pydantic import BaseModel

router = APIRouter(prefix="/financial", tags=["Financial"])


class SimulationParams(BaseModel):
    starting_customers:   int    = 50
    monthly_growth_rate:  float  = 0.08
    churn_rate:           float  = 0.03
    price_per_customer:   float  = 149.0
    fixed_costs:          float  = 35000.0
    variable_cost_per_customer: float = 20.0
    cac_simplified:       float  = 100.0
    months:               int    = 24


@router.get("/model")
async def get_financial_model():
    try:
        data = dm.get_financial_model_data()
        if data is None or data.empty:
            return {"projections":[], "overview":{}}
        records = data.to_dict(orient="records")
        overview = {
            "total_revenue": round(sum(r.get("mrr",0) for r in records), 2),
            "net_income":    round(sum(r.get("net_income",0) for r in records), 2),
        }
        return {"projections": records, "overview": overview}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simulate")
async def simulate_financials(params: SimulationParams):
    try:
        data = dm.get_financial_model_data()
        if data is None or data.empty:
            return {"scenarios": {}}
        df = data.copy()
        for mult, name in [(params.monthly_growth_rate*1.2, "optimistic"),
                           (params.monthly_growth_rate*0.8, "conservative"),
                           (params.monthly_growth_rate,      "baseline")]:
            rows = []
            cust = params.starting_customers
            for m in range(params.months):
                cust  = max(0, int(cust * (1 + mult - params.churn_rate)))
                mr    = cust * params.price_per_customer
                cogs  = cust * params.variable_cost_per_customer
                net   = mr - cogs - params.fixed_costs
                rows.append(dict(month=m+1, mrr=round(mr,2), cogs=round(cogs,2),
                                 fixed_costs=params.fixed_costs, net_income=round(net,2)))
            df[f"{name}_net_income"] = [r["net_income"] for r in rows]
        scenarios = {k: df[["month",k+"_net_income"]].rename(columns={k+"_net_income":"net_income"}).to_dict("records")
                     for k in ["optimistic","conservative","baseline"] if k+"_net_income" in df.columns}
        return {"scenarios": scenarios}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
