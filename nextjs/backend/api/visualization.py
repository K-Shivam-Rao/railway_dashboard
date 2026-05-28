"""GET /api/v1/viz/* — architecture, vulnerability, live-metrics, loopholes, recommendations."""
from fastapi import APIRouter, HTTPException
from backend.core.data_manager import data_manager as dm

router = APIRouter(prefix="/viz", tags=["Visualization"])


@router.get("/architecture")
async def get_architecture():
    try:
        return {"html": dm.build_architecture_flow_html()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vulnerability-scores")
async def get_vulnerability_scores():
    try:
        df = dm.get_station_vulnerability_scores()
        return {"scores": df.to_dict(orient="records") if not df.empty else []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/live-metrics")
async def get_live_metrics():
    try:
        return {"metrics": dm.generate_live_metrics()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/loopholes")
async def get_loopholes():
    try:
        return {"loopholes": dm.analyze_loopholes()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations")
async def get_viz_recommendations():
    try:
        return {"recommendations": dm.generate_recommendations()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
