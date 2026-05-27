"""GET /api/v1/metrics/{station} — station KPIs."""
from fastapi import APIRouter, HTTPException
from backend.core.data_manager import data_manager as dm
from backend.models.metrics import KPIStrip, KPIItem, PSDAnalytics, SensorTimeSeries

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get("/{station}")
async def get_station_metrics(station: str):
    try:
        result = dm.get_metrics(station)
        gates_total, gates_active, people_total, alerts, avg_sync, warnings_ct, metrics = result
        pax_per_gate = round(people_total / max(gates_active, 1), 1) if isinstance(people_total, (int, float)) else 0
        health_score = round(
            (avg_sync * 0.4) + (100 - metrics.get("avg_risk", 0)) * 0.3
            + (gates_active / max(gates_total, 1) * 100) * 0.3, 1) \
            if isinstance(avg_sync, (int, float)) else 0
        return {
            "station": station, "gates_total": int(gates_total),
            "gates_active": int(gates_active), "passengers_total": int(people_total),
            "alerts": int(alerts), "warnings": int(warnings_ct),
            "avg_sync": int(avg_sync),
            "status": "critical" if int(alerts) > 0 else ("warning" if int(warnings_ct) > 0 else "normal"),
            "pax_per_gate": pax_per_gate, "health_score": health_score,
            **{k: v for k, v in metrics.items() if not isinstance(v, list)},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{station}/kpi-strip")
async def get_kpi_strip(station: str):
    try:
        result = dm.get_metrics(station)
        gates_total, gates_active, people_total, alerts, avg_sync, warnings_ct, _ = result
        items = [
            KPIItem(label="Active Gates", value=f"{gates_active}/{gates_total}",
                    trend="up" if gates_active > 0 else "down", icon="door", color="emerald"),
            KPIItem(label="Sync Health", value=f"{avg_sync}%",
                    trend="up" if avg_sync >= 85 else "down", trend_value=f"{avg_sync}%",
                    icon="activity", color="cyan"),
            KPIItem(label="Passengers", value=f"{int(people_total):,}",
                    trend="up", icon="users", color="fuchsia"),
            KPIItem(label="Alerts", value=str(int(alerts)),
                    trend="down" if alerts == 0 else "up", trend_value=f"{alerts} active",
                    icon="alert", color="amber"),
            KPIItem(label="Warnings", value=str(int(warnings_ct)),
                    trend="down" if warnings_ct == 0 else "neutral",
                    icon="warning", color="emerald" if warnings_ct == 0 else "amber"),
        ]
        return {"items": [i.model_dump() for i in items]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{station}/psd-analytics")
async def get_psd_analytics(station: str):
    try:
        door_cycles_df, temp_df = dm.get_psd_analytics(station)
        return {
            "door_cycles": {
                "timestamps": door_cycles_df["Hour"].tolist(),
                "values":     door_cycles_df["Door Cycles"].tolist(),
            },
            "temperature": {
                "timestamps": temp_df["Hour"].tolist(),
                "values":     temp_df["Avg Temp (°C)"].tolist(),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
