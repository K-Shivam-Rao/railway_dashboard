"""GET /api/v1/customers/* — customer analytics."""
from fastapi import APIRouter, HTTPException, Query
from backend.core.data_manager import data_manager as dm

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("")
async def list_customers():
    try:
        data = dm.get_customer_data()
        if data is None:
            return {"customers":[],"total":0}
        records = data.to_dict(orient="records") if hasattr(data,"to_dict") else data
        return {"customers":records,"total":len(records)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rfm")
async def get_rfm():
    try:
        data = dm.get_rfm_analysis()
        if data is None or data.empty:
            return {"segments":{}}
        segs = data.groupby("segment")["id"].count().to_dict()
        return {"segments":{str(k):int(v) for k,v in segs.items()},
                "customers":data.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/high-value")
async def get_high_value():
    try:
        data = dm.get_customer_data()
        if data is None or data.empty:
            return []
        return data[data.get("health_score",0) >= 80].to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contract-health")
async def get_contract_health():
    try:
        data = dm.get_contract_health_score()
        if data is None or data.empty:
            return []
        return data.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/renewal-forecast")
async def get_renewal_forecast():
    try:
        data = dm.get_renewal_forecast()
        if data is None or data.empty:
            return []
        return data.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/at-risk")
async def get_at_risk():
    try:
        data = dm.get_contract_health_score()
        if data is None or data.empty:
            return []
        return data[data.get("risk_level","").astype(str).isin(["Critical","High"])].to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/renewal-health-summary")
async def get_renewal_summary():
    try:
        data = dm.get_renewal_forecast()
        if data is None or data.empty:
            return {"pending":0,"early":0,"on_track":0}
        return {"pending": int((data["renewal_status"]=="pending").sum()),
                "early":   int((data["renewal_status"]=="early").sum()),
                "on_track":int((data["renewal_status"]=="on-track").sum())}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/operators/{operator_id}")
async def get_operator_profile(operator_id: str):
    try:
        data = dm.get_customer_data()
        if data is None or data.empty:
            return {}
        row = data[data["name"].str.lower() == operator_id.lower()]
        if row.empty:
            row = data[data["id"].str.lower() == operator_id.lower()]
        if row.empty:
            return {}
        return row.iloc[0].to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
