"""GET /api/v1/analytics/* — anomaly detection, decomposition, correlations."""
from fastapi import APIRouter, HTTPException, Query
from backend.core.data_manager import data_manager as dm
from pydantic import BaseModel

router = APIRouter(prefix="/analytics", tags=["Analytics"])


class AnomalyRequest(BaseModel):
    station:      str   = ""
    method:       str   = "zscore"
    sensor:       str   = "sensor_temp"
    threshold:    float = 2.0
    contamination:float = 0.1
    window:       int   = 5


@router.post("/anomaly-detection")
async def detect_anomalies(req: AnomalyRequest):
    try:
        kwargs = req.model_dump()
        method = kwargs.pop("method")
        fn = {**{"zscore":dm.detect_anomalies_zscore,"iqr":dm.detect_anomalies_iqr,
                 "moving_average":dm.detect_anomalies_moving_average,
                 "isolation_forest":dm.detect_anomalies_isolation_forest}}.get(method)
        if fn is None:
            raise HTTPException(status_code=400, detail=f"Unknown method: {method}")
        df = fn(kwargs.pop("station"), kwargs.pop("sensor"), **kwargs)
        return {"items": df.to_dict(orient="records") if not df.empty else [],
                "count": int(len(df))}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/decomposition")
async def get_decomposition(station: str = Query(...), sensor: str = "sensor_temp", period: int = 24):
    try:
        result = dm.decompose_timeseries(station, sensor, period)
        return {"trend": result["trend"].tolist() if not result["trend"].empty else [],
                "seasonal": result["seasonal"].tolist() if not result["seasonal"].empty else [],
                "residual": result["residual"].tolist() if not result["residual"].empty else []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/correlations")
async def get_correlations(station: str = Query(...)):
    try:
        df = dm.compute_sensor_correlations(station)
        return {"pairs": df.to_dict(orient="records") if not df.empty else []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health-profile")
async def get_health_profile(station: str = Query(...)):
    try:
        return dm.analyze_sensor_health_profile(station)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
