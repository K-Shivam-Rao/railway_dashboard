"""GET /api/v1/incidents — incident log with pagination."""
from fastapi import APIRouter, HTTPException, Query
from backend.core.data_manager import data_manager as dm
import pandas as pd
import numpy as np

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.get("")
async def list_incidents(
    station: str | None = Query(None),
    severity: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    try:
        incidents = dm.get_incidents()
        if not isinstance(incidents, pd.DataFrame) or incidents.empty:
            return {"items":[],"total":0,"page":page,"page_size":page_size}
        if station:
            incidents = incidents[incidents.get("Station","").str.contains(station, case=False, na=False)]
        if severity:
            incidents = incidents[incidents.get("Severity","").str.lower() == severity.lower()]
        total = len(incidents)
        start, end = (page-1)*page_size, page*page_size
        items = [dict(id=str(r.get("ID",r.get("id",""))),
                      station=str(r.get("Station",r.get("station",""))),
                      severity=str(r.get("Severity",r.get("severity","info"))).lower(),
                      category=str(r.get("Category",r.get("category",""))),
                      description=str(r.get("Description",r.get("description",""))),
                      timestamp=str(r.get("Timestamp",r.get("timestamp",""))),
                      resolved=bool(r.get("Resolved",r.get("resolved",False))))
                 for _, r in incidents.iloc[start:end].iterrows()]
        return {"items":items,"total":total,"page":page,"page_size":page_size}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_incident_summary():
    try:
        incidents = dm.get_incidents()
        if not isinstance(incidents, pd.DataFrame) or incidents.empty:
            return {"total":0,"critical":0,"warning":0,"info":0,"resolved":0,"open":0,"by_category":{}}
        total     = len(incidents)
        sev       = incidents.get("Severity", incidents.get("severity", pd.Series()))
        critical  = int((sev.str.lower() == "critical").sum())
        warning   = int((sev.str.lower() == "warning").sum())
        info_ct   = total - critical - warning
        res_col   = incidents.get("Resolved", incidents.get("resolved", pd.Series([False]*total)))
        resolved  = int(res_col.sum()) if res_col.dtype == bool else 0
        open_ct   = total - resolved
        cat_col   = incidents.get("Category", incidents.get("category", pd.Series()))
        by_cat    = {str(k):int(v) for k,v in (cat_col.value_counts().to_dict() if not cat_col.empty else {}).items()}
        return dict(total=total, critical=critical, warning=warning, info=info_ct,
                    resolved=resolved, open=open_ct, by_category=by_cat)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
