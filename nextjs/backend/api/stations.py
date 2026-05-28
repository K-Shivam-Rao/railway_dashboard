"""GET /api/v1/stations — all stations with gate details."""
from fastapi import APIRouter, HTTPException
from backend.core.data_manager import data_manager as dm

router = APIRouter(prefix="/stations", tags=["Stations"])


@router.get("")
async def list_stations():
    try:
        stations  = dm.get_stations()
        df        = dm.load_data()
        result    = []
        for i, s in enumerate(stations):
            sdf           = df[df["station"] == s]
            gates_total   = len(sdf)
            gates_active  = int((sdf["door_state"] != "offline").sum()) if "door_state" in sdf.columns else gates_total
            alerts        = int((sdf["maintenance_status"] == "CRITICAL").sum()) if "maintenance_status" in sdf.columns else 0
            warnings      = int((sdf["maintenance_status"] == "WARNING").sum())  if "maintenance_status" in sdf.columns else 0
            avg_sync      = int(sdf["sync_score"].mean()) if "sync_score" in sdf.columns else 0
            pax           = int(sdf["people"].sum())     if "people"    in sdf.columns else 0
            status = "critical" if alerts > 0 else ("warning" if warnings > 0 else "operational")
            dot    = "offline"  if status == "critical" else ("warning" if status == "warning" else "online")
            result.append(dict(name=s, index=i+1, total_stations=len(stations),
                                gates_total=gates_total, gates_active=gates_active,
                                passengers_total=pax, avg_sync=avg_sync,
                                alerts=alerts, warnings=warnings, status=status, dot_color=dot))
        return {"stations": result, "total": len(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{station}")
async def get_station_detail(station: str):
    try:
        stations = dm.get_stations()
        if station not in stations:
            raise HTTPException(status_code=404, detail=f"Station '{station}' not found")
        df       = dm.get_station_df(station)
        result   = dm.get_metrics(station)
        gates_total, gates_active, people_total, alerts, avg_sync, warnings_ct, _ = result
        gates = [dict(gate_id=str(r.get("gate_id","")), platform=str(r.get("platform","")),
                       door_state=str(r.get("door_state","")), sensor_temp=float(r.get("sensor_temp",0)),
                       sensor_vib=float(r.get("sensor_vib",0)),
                       people=int(r.get("people",0)), sync_score=int(r.get("sync_score",0)),
                       door_health=int(r.get("door_health",0)), risk_score=int(r.get("risk_score",0)))
                 for _, r in df.iterrows()]
        return {
            "station": station,
            "metrics": dict(gates_total=int(gates_total), gates_active=int(gates_active),
                            passengers_total=int(people_total), alerts=int(alerts),
                            warnings=int(warnings_ct), avg_sync=int(avg_sync),
                            status="critical" if int(alerts) > 0
                                   else ("warning" if int(warnings_ct) > 0 else "normal")),
            "gates": gates,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
