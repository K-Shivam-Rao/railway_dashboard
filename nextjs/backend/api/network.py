"""GET /api/v1/network/summary + business-map."""
from fastapi import APIRouter, HTTPException
from backend.core.data_manager import data_manager as dm
import pandas as pd

router = APIRouter(prefix="/network", tags=["Network"])


def _records(df):
    if df is None or (isinstance(df, pd.DataFrame) and df.empty):
        return []
    return df.to_dict(orient="records")


@router.get("/summary")
async def get_network_summary():
    try:
        result = dm.get_network_summary()
        if not result:
            return {}
        return dict(
            total_gates     = int(result.get("total_gates", 0)),
            total_people    = int(result.get("total_people", 0)),
            critical_count  = int(result.get("critical_count", 0)),
            warning_count   = int(result.get("warning_count", 0)),
            optimal_count   = int(result.get("optimal_count", 0)),
            network_sync    = int(result.get("network_sync", 0)),
            station_summary = _records(result.get("station_summary")),
            status_dist     = _records(result.get("status_dist")),
            door_dist       = _records(result.get("door_dist")),
            operator_stats  = _records(result.get("operator_stats")),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/business-map")
async def get_business_map():
    try:
        df = dm.load_data()
        if df.empty or "station" not in df.columns:
            return {"nodes": [], "edges": []}
        stations = df["station"].dropna().unique().tolist()
        nodes = [{"id": s, "label": s, "type": "station"}
                 for s in stations]
        edges = [{"source": stations[i], "target": stations[j], "weight": 1}
                 for i in range(len(stations)) for j in range(i+1, len(stations))]
        return {"nodes": nodes, "edges": edges}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
