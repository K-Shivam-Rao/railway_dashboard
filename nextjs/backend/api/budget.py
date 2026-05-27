"""GET /api/v1/budget/* — budget, ROI, projections."""
from fastapi import APIRouter, HTTPException
from backend.core.data_manager import data_manager as dm

router = APIRouter(prefix="/budget", tags=["Budget"])


@router.get("/overview")
async def get_budget_overview():
    try:
        overview = dm.get_budget_overview()
        data     = dm.generate_budget_data()
        return {"overview":overview if isinstance(overview,dict) else {},
                "data": data.to_dict(orient="records") if hasattr(data,"to_dict") else data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/roi")
async def get_roi():
    try:
        data = dm.generate_roi_data()
        return {"projects":(data.to_dict(orient="records") if hasattr(data,"to_dict") else data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monthly-spend")
async def get_monthly_spend():
    try:
        data = dm.generate_monthly_spend()
        return {"data":(data.to_dict(orient="records") if hasattr(data,"to_dict") else data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scenarios")
async def get_projections():
    try:
        data = dm.generate_scenario_projections()
        return {k:v.to_dict(orient="records") if hasattr(v,"to_dict") else v
                for k,v in data.items()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations")
async def get_recommendations():
    try:
        return {"recommendations": dm.generate_optimization_recommendations()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
