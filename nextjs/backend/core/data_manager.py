"""
DataManager — FastAPI Backend Service Layer.

Reads from stations.parquet / stations.csv at the dashboard root level
and exposes all methods consumed by the API handlers.
"""
import sys
import os
import json
import warnings
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

import pandas as pd
import numpy as np
import polars as pl

# ── Project-root resolution ──────────────────────────────────────
_PROJECT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
_PARQUET_FILE = os.path.join(_PROJECT_ROOT, "stations.parquet")
_CSV_FILE     = os.path.join(_PROJECT_ROOT, "stations.csv")
_DB_FILE      = os.path.join(_PROJECT_ROOT, "simulation_history.db")

_STATION_LIST: Optional[List[str]] = None
_DATAFRAME: Optional[pd.DataFrame] = None


# ── helpers ──────────────────────────────────────────────────────

def _load_parquet() -> pd.DataFrame:
    global _DATAFRAME
    if _DATAFRAME is not None:
        return _DATAFRAME
    if os.path.exists(_PARQUET_FILE):
        _DATAFRAME = pl.read_parquet(_PARQUET_FILE).to_pandas()
    elif os.path.exists(_CSV_FILE):
        _DATAFRAME = pl.read_csv(_CSV_FILE).to_pandas()
    else:
        raise FileNotFoundError(
            f"Neither {_PARQUET_FILE!r} nor {_CSV_FILE!r} found."
        )
    return _DATAFRAME


def _get_station_names(df: pd.DataFrame) -> List[str]:
    if "station" not in df.columns:
        return list(df.index.unique())
    return sorted(df["station"].dropna().unique().tolist())


# ── Service class ────────────────────────────────────────────────

class DataManager:
    """Singleton-like data-access class used by all API handlers."""

    # ── core data loading ────────────────────────────────────────

    def load_data(self) -> pd.DataFrame:
        df = _load_parquet()
        for col in ("sensor_temp", "sensor_vib", "people", "sync_score",
                    "door_health", "risk_score"):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        _ensure_columns(df)
        return df

    def get_stations(self) -> List[str]:
        global _STATION_LIST
        if _STATION_LIST is not None:
            return _STATION_LIST
        try:
            df = _load_parquet()
            _STATION_LIST = _get_station_names(df)
        except Exception:
            _STATION_LIST = []
        return _STATION_LIST or []

    def get_station_df(self, station: str) -> pd.DataFrame:
        df = _load_parquet()
        if "station" in df.columns:
            return df[df["station"] == station].copy()
        return pd.DataFrame()

    # ── metrics ──────────────────────────────────────────────────

    def get_metrics(self, station: str):
        """Return (gates_total, gates_active, people_total, alerts, avg_sync, warnings, metrics_dict)."""
        df = self.get_station_df(station)
        if df.empty:
            return (0, 0, 0, 0, 0, 0, {})
        gates_total   = len(df)
        gates_active  = int((df["door_state"] != "offline").sum()) if "door_state" in df.columns else gates_total
        people_total  = int(df["people"].sum())
        alerts        = int((df["maintenance_status"] == "CRITICAL").sum()) if "maintenance_status" in df.columns else 0
        warnings_ct   = int((df["maintenance_status"] == "WARNING").sum())  if "maintenance_status" in df.columns else 0
        avg_sync      = int(df["sync_score"].mean()) if "sync_score" in df.columns else 0
        metrics = {
            "avg_risk":     float(df["risk_score"].mean())    if "risk_score"     in df.columns else 0.0,
            "avg_health":   float(df["door_health"].mean())   if "door_health"    in df.columns else 0.0,
            "avg_sync":     float(avg_sync),
            "avg_temp":     round(float(df["sensor_temp"].mean()) if "sensor_temp" in df.columns else 0.0, 1),
            "avg_vib":      round(float(df["sensor_vib"].mean())  if "sensor_vib"  in df.columns else 0.0, 2),
            "total_pax":    int(df["people"].sum()),
        }
        return gates_total, gates_active, people_total, alerts, avg_sync, warnings_ct, metrics

    def get_psd_analytics(self, station: str):
        """Return (door_cycles_df, temp_df) with 24-hour series."""
        import random
        df = self.get_station_df(station)
        hours = list(range(24))
        if not df.empty and "people" in df.columns:
            pax = []
            grp = df.groupby("door_state")["people"].sum() if "door_state" in df.columns else pd.Series()
            base = grp.mean() if not grp.empty else 0
            for h in hours:
                pax.append(max(0, int(base * (0.4 + 1.2 * abs(h - 12) / 12))))
        else:
            pax = [0] * 24

        random.seed(hash(station) % (2**31))
        door_values = [max(0, int(pax[h] * (0.5 + random.random()))) for h in hours]

        if not df.empty and "sensor_temp" in df.columns:
            temps = pd.to_numeric(df["sensor_temp"], errors="coerce").clip(-50, 100).tolist()
            temps = (temps + [25.0] * 24)[:24]
        else:
            temps = [25.0] * 24

        door_df = pd.DataFrame({"Hour": [f"{h:02d}:00" for h in hours], "Door Cycles": door_values})
        temp_df = pd.DataFrame({"Hour": [f"{h:02d}:00" for h in hours], "Avg Temp (°C)": temps})
        return door_df, temp_df

    # ── incidents ────────────────────────────────────────────────

    def get_incidents(self) -> pd.DataFrame:
        df = _load_parquet()
        if df.empty:
            return pd.DataFrame(columns=["ID","Station","Severity","Category",
                                         "Description","Timestamp","Resolved"])
        records = []
        wnd = 48  # hours look-back window
        for _, row in df.head(200).iterrows():
            door = str(row.get("door_state", ""))
            health = float(row.get("door_health", 100) or 100)
            temp  = float(row.get("sensor_temp", 25) or 25)
            ts = datetime.now() - pd.Timedelta(hours=int(np.random.uniform(1, wnd*24)))
            if door == "offline" or health < 30:
                records.append(_incident(row, ts, "Critical", "Gate Malfunction",
                                         f"Gate {row.get('gate_id','?')} is {door}. Health={health:.0f}."))
            elif temp > 35:
                records.append(_incident(row, ts, "Warning", "Environmental",
                                         f"High temp {temp:.0f}°C on gate {row.get('gate_id','?')}."))
        return pd.DataFrame(records or
              [dict(ID="",Station="",Severity="",Category="",Description="",Timestamp="",Resolved=False)],
              columns=["ID","Station","Severity","Category","Description","Timestamp","Resolved"])

    # ── network ──────────────────────────────────────────────────

    def get_network_summary(self) -> Dict[str, Any]:
        df = _load_parquet()
        if df.empty:
            return {}
        total_gates  = len(df)
        total_people = int(df["people"].sum()) if "people" in df.columns else 0
        critical = int((df["maintenance_status"] == "CRITICAL").sum()) if "maintenance_status" in df.columns else 0
        warning  = int((df["maintenance_status"] == "WARNING").sum())  if "maintenance_status" in df.columns else 0
        if critical == 0 and "door_state" in df.columns:
            critical = int((df["door_state"] == "offline").sum())
        optimal   = max(total_gates - critical - warning, 0)
        net_sync  = int(df["sync_score"].mean()) if "sync_score" in df.columns else 0

        status_df  = pd.DataFrame([("Optimal",optimal),("Warning",warning),("Critical",critical)],
                                  columns=["status","count"])
        door_df    = _door_dist(df)
        return {
            "total_gates":      total_gates,
            "total_people":     total_people,
            "critical_count":   critical,
            "warning_count":    warning,
            "optimal_count":    optimal,
            "network_sync":     net_sync,
            "station_summary":  pd.DataFrame(),
            "status_dist":      status_df,
            "door_dist":        door_df,
            "operator_stats":   pd.DataFrame(columns=["operator","count"]),
        }

    # ── customers / finance ──────────────────────────────────────

    def get_customer_data(self) -> Optional[pd.DataFrame]:
        df = _load_parquet()
        if df.empty or "station" not in df.columns:
            return None
        rows = []
        for i, st in enumerate(df["station"].dropna().unique()):
            sdf  = df[df["station"] == st]
            pax  = int(sdf["people"].sum()) if "people" in sdf.columns else 0
            hlt  = int(sdf["sync_score"].mean()) if "sync_score" in sdf.columns else 75
            rows.append({
                "id": f"CUST-{1000+i}", "name": f"Operator {st}", "station": st,
                "contract_type": "Annual",
                "monthly_value": round(15000 + pax * 0.05, 2),
                "health_score":  hlt,
                "contract_end":  (datetime.now() + pd.Timedelta(days=180+i*30)).strftime("%Y-%m-%d"),
                "renewal_probability": round(0.7 + np.random.rand()*0.25, 3),
                "status": ("green" if hlt>=80 else "amber" if hlt>=60 else "red"),
            })
        return pd.DataFrame(rows)

    def get_rfm_analysis(self) -> Optional[pd.DataFrame]:
        data = self.get_customer_data()
        if data is None or data.empty:
            return None
        rfm   = data.copy()
        rfm["recency"]  = np.random.randint(1, 365, size=len(rfm))
        rfm["frequency"] = np.random.randint(1, 20, size=len(rfm))
        rfm["monetary"] = rfm.get("monthly_value", pd.Series(15000.0, index=rfm.index)).clip(lower=1000)
        rfm["rfm_score"] = (pd.qcut(rfm["recency"], 5,[5,4,3,2,1]).astype(float) +
                            pd.qcut(rfm["frequency"],5,[1,2,3,4,5],duplicates="drop").astype(float) +
                            pd.qcut(rfm["monetary"],5,[1,2,3,4,5],duplicates="drop").astype(float)) / 3
        rfm["segment"] = pd.cut(rfm["rfm_score"],
                                bins=[0,2,3,4,5],
                                labels=["At Risk","Need Attention","Loyal","Champions"]).astype(str)
        return rfm

    def get_contract_health_score(self) -> Optional[pd.DataFrame]:
        data = self.get_customer_data()
        if data is None or data.empty:
            return None
        df = data.copy()
        df["health_score"] = df.get("health_score", pd.Series(75, index=df.index)).clip(0,100)
        df["risk_level"]   = pd.cut(df["health_score"], bins=[0,40,70,90,100],
                                    labels=["Critical","High","Medium","Low"])
        return df

    def get_renewal_forecast(self) -> Optional[pd.DataFrame]:
        data = self.get_customer_data()
        if data is None or data.empty:
            return None
        df               = data.copy()
        df["renewal_date"] = pd.to_datetime(df.get("contract_end", pd.Timestamp.today()))
        df["days_until_renewal"] = (df["renewal_date"] - pd.Timestamp.today()).dt.days
        df["renewal_probability"] = df.get("renewal_probability", pd.Series(0.75,index=df.index)).round(3)
        df["expected_value"] = (df.get("monthly_value",1) * 12 * df["renewal_probability"]).round(0)
        df["renewal_status"] = df.apply(
            lambda r: "pending" if r["days_until_renewal"]<30
                      else ("early" if r["days_until_renewal"]<90 else "on-track"), axis=1)
        return df

    def get_financial_model_data(self) -> Optional[pd.DataFrame]:
        rows = []
        customers = 5000
        for m in range(24):
            customers = max(0, int(customers * 1.12))
            mr         = customers * 249.0
            cogs       = customers * 25.0
            net        = mr - cogs - 120000.0
            rows.append(dict(month=m+1, customers=customers, mrr=round(mr,2),
                             cash_received=round(mr,2), cogs=round(cogs,2),
                             fixed_costs=120000.0, net_income=round(net,2),
                             cash_bank=round(net*(m+1),2), net_income_cum=round(net*(m+1),2)))
        return pd.DataFrame(rows)

    # ── budget ───────────────────────────────────────────────────

    def get_budget_overview(self) -> Dict[str, Any]:
        return {"total_budget":500000.0,"spent":320000.0,"remaining":180000.0,
                "utilization":0.64,"top_expenses":[]}

    def generate_budget_data(self) -> pd.DataFrame:
        df     = _load_parquet()
        sts    = _get_station_names(df) if not df.empty else ["Berlin Hauptbahnhof"]
        rows   = [{"station":s,"budget":50000.0,"spent":round(30000+i*2000,2),
                   "remaining":round(20000-i*2000,2),"roi":round(0.12+i*0.01,3)}
                  for i,s in enumerate(sts)]
        return pd.DataFrame(rows)

    def generate_roi_data(self) -> pd.DataFrame:
        projects = ["Signal Upgrade","Platform Modernization","Gate Installation",
                     "Track Renewal","Communication System"]
        return pd.DataFrame([dict(project=p, invested=round(50000+__import__("numpy").random.rand()*200000,0),
                                  returned=round(50000+__import__("numpy").random.rand()*200000,0),
                                  roi=round(__import__("numpy").random.rand()*0.4,3))
                             for p in projects])

    def generate_monthly_spend(self) -> pd.DataFrame:
        months = pd.date_range("2025-01-01", periods=12, freq="MS")
        rng    = __import__("numpy").random
        return pd.DataFrame({"month":months.strftime("%Y-%m"),
                             "budget":[42000]*12,
                             "spent":[38000+rng.randint(-5000,5000) for _ in range(12)]})

    def generate_scenario_projections(self):
        scenarios = {}
        for name, mult in [("baseline",1.0),("optimistic",1.2),("conservative",0.8)]:
            rows = [{"month":m+1,"revenue":round(100000*mult*(1.03**m),2)} for m in range(24)]
            scenarios[name] = pd.DataFrame(rows)
        return scenarios

    def generate_optimization_recommendations(self) -> List[Dict]:
        return [
            {"id":1,"category":"Budget","title":"Review high-spend stations",
             "description":"Identify stations spending >80% of budget.","impact":"Medium"},
            {"id":2,"category":"ROI","title":"Increase ROI tracking",
             "description":"Add monthly ROI reporting to quarterly reviews.","impact":"High"},
            {"id":3,"category":"Spend","title":"Reduce variable costs",
             "description":"Negotiate better rates for maintenance contracts.","impact":"Low"},
        ]

    # ── anomaly / analytics stubs ──────────────────────────────

    def detect_anomalies_zscore(self, station: str, sensor: str="sensor_temp", threshold: float=2.0):
        return _anomaly_zscore(self.get_station_df(station), sensor, threshold)

    def detect_anomalies_iqr(self, station: str, sensor: str="sensor_temp", threshold: float=1.5):
        return _anomaly_iqr(self.get_station_df(station), sensor, threshold)

    def detect_anomalies_moving_average(self, station: str, sensor: str="sensor_temp", window: int=5):
        return _anomaly_ma(self.get_station_df(station), sensor, window)

    def detect_anomalies_isolation_forest(self, station: str, sensor: str="sensor_temp",
                                          contamination: float=0.1):
        return _anomaly_if(self.get_station_df(station), sensor, contamination)

    def decompose_timeseries(self, station: str, sensor: str="sensor_temp", period: int=24):
        df = self.get_station_df(station)
        if df.empty or sensor not in df.columns:
            return {"trend":pd.Series(),"seasonal":pd.Series(),"residual":pd.Series()}
        series = pd.to_numeric(df[sensor], errors="coerce").dropna().reset_index(drop=True)
        try:
            from statsmodels.tsa.seasonal import seasonal_decompose
            res = seasonal_decompose(series, model="additive",
                                     period=min(period, len(series)//2))
            return {"trend":res.trend,"seasonal":res.seasonal,"residual":res.resid}
        except Exception:
            ma    = series.rolling(period, center=True).mean()
            resid = series - ma
            return {"trend":ma,"seasonal":pd.Series(0.0, index=series.index),"residual":resid}

    def compute_sensor_correlations(self, station: str) -> pd.DataFrame:
        df = self.get_station_df(station)
        if df.empty:
            return pd.DataFrame()
        num = df.select_dtypes(include="number")
        if num.shape[1] < 2:
            return pd.DataFrame()
        corr   = num.corr()
        pairs  = [dict(sensor_a=corr.columns[i], sensor_b=corr.columns[j],
                       correlation=round(float(corr.iloc[i,j]),4))
                  for i in range(len(corr.columns)) for j in range(i+1, len(corr.columns))]
        return pd.DataFrame(pairs)

    def analyze_sensor_health_profile(self, station: str) -> Dict[str, Any]:
        df   = self.get_station_df(station)
        if df.empty:
            return {"health_score": 0, "sensors": {}}
        numeric = [c for c in df.select_dtypes(include="number").columns if c not in ("gate_id",)]
        stats = {}
        for col in numeric:
            s = pd.to_numeric(df[col], errors="coerce").dropna()
            if not s.empty:
                mean_v, std_v = s.mean(), s.std()
                cvar          = abs(std_v / mean_v) if mean_v != 0 else 0
                score         = max(0, 100 - int(cvar * 100))
                stats[col]    = {"mean":round(float(mean_v),3),"std":round(float(std_v),3),
                                 "range":round(float(s.max()-s.min()),3),"cv":round(float(cvar),3),
                                 "health_score":score}
        avg_hs = int(np.mean([v["health_score"] for v in stats.values()])) if stats else 0
        return {"health_score": avg_hs, "sensors": stats}

    # ── visualization ──────────────────────────────────────────

    def get_station_vulnerability_scores(self) -> pd.DataFrame:
        df = _load_parquet()
        if df.empty or "station" not in df.columns:
            return pd.DataFrame(columns=["station","vulnerability"])
        scores = []
        for st, grp in df.groupby("station"):
            health  = grp["door_health"].mean()  if "door_health"  in grp.columns else 80
            sync    = grp["sync_score"].mean()   if "sync_score"   in grp.columns else 80
            offline = int((grp["door_state"] == "offline").sum()) if "door_state" in grp.columns else 0
            vuln    = max(0, min(100, int(100 - 0.5*(health+sync) + 5*offline/max(len(grp),1))))
            scores.append({"station":st,"vulnerability":vuln})
        result = pd.DataFrame(scores).sort_values("vulnerability",ascending=False)
        return result

    def build_architecture_flow_html(self) -> str:
        return "<html><body><h2>SicherGleis Architecture</h2><p>Not yet implemented.</p></body></html>"

    def generate_recommendations(self) -> List[str]:
        return [
            "Review gates with sync_score below 70.",
            "Run anomaly detection on all high-traffic stations.",
            "Schedule maintenance for all door_health below 60.",
        ]

    def generate_live_metrics(self) -> List[Dict]:
        df = _load_parquet()
        if df.empty:
            return []
        snap = df.sample(min(50, len(df)), random_state=42)
        return [dict(station=str(r.get("station","?")),
                     gate=str(r.get("gate_id","?")),
                     temp=float(r.get("sensor_temp",0)),
                     vib=float(r.get("sensor_vib",0)),
                     people=int(r.get("people",0)),
                     sync_score=int(r.get("sync_score",0)))
                for _, r in snap.iterrows()]

    def analyze_loopholes(self) -> List[Dict]:
        df = _load_parquet()
        if df.empty or "risk_score" not in df.columns:
            return []
        hi = df[df["risk_score"] > 70].head(30)
        return hi[["station","gate_id","door_state","risk_score"]].assign(
            type="gate_misalignment"
        ).to_dict(orient="records") if not hi.empty else []

    def get_training_simulation_data(self) -> Tuple[pd.DataFrame, str]:
        if not os.path.exists(_DB_FILE):
            return (pd.DataFrame(columns=["timestamp","simulation_type","score","accuracy",
                                           "total_runtime","message"]),
                    "No simulation history DB found.")
        try:
            import sqlite3
            con  = sqlite3.connect(_DB_FILE)
            rows = pd.read_sql("SELECT * FROM sessions LIMIT 500", con)
            con.close()
            return rows, f"Loaded {len(rows)} training sessions from SQLite DB."
        except Exception as e:
            return pd.DataFrame(), f"DB error: {e}"


# ──提供给各层的助手 ──────────────────────────────────────────────

def _ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    defaults = dict(door_state="open", sync_score=80, door_health=80,
                    risk_score=20, maintenance_status="OK",
                    sensor_temp=25.0, sensor_vib=0.0, people=0,
                    gate_id="UNKNOWN", platform="1")
    for col, default in defaults.items():
        if col not in df.columns:
            df[col] = default
    return df


def _door_dist(df: pd.DataFrame) -> pd.DataFrame:
    if "door_state" not in df.columns:
        return pd.DataFrame(columns=["state","count"])
    return df["door_state"].value_counts().reset_index().rename(columns={"index":"state","count":"count"})


def _incident(row, ts, sev, cat, desc):
    return dict(ID=f"INC-{abs(hash((row.get('station',''),row.get('gate_id',''),str(ts))))%100000:05d}",
                Station=row.get("station","?"),
                Severity=sev, Category=cat,
                Description=desc,
                Timestamp=ts.isoformat(), Resolved=False)


# ── anomaly short-cuts (free functions used by analytics API) ───

def _anomaly_zscore(df, sensor, threshold):
    if df.empty or sensor not in df.columns:
        return pd.DataFrame()
    s = pd.to_numeric(df[sensor], errors="coerce").dropna()
    if s.std() == 0:
        return pd.DataFrame(columns=[sensor,"anomaly_score","is_anomaly"])
    z = (s - s.mean()) / s.std()
    r = pd.DataFrame({sensor:s,"anomaly_score":z,"is_anomaly":z.abs()>threshold})
    return r[r["is_anomaly"]]

def _anomaly_iqr(df, sensor, threshold):
    if df.empty or sensor not in df.columns:
        return pd.DataFrame()
    s = pd.to_numeric(df[sensor], errors="coerce").dropna()
    q1,q3 = s.quantile(.25), s.quantile(.75)
    lo,hi = q1-threshold*(q3-q1), q3+threshold*(q3-q1)
    return pd.DataFrame({sensor:s[(s<lo)|(s>hi)],"is_anomaly":True})

def _anomaly_ma(df, sensor, window):
    if df.empty or sensor not in df.columns:
        return pd.DataFrame()
    s     = pd.to_numeric(df[sensor], errors="coerce").dropna()
    ma    = s.rolling(window, center=True).mean()
    std   = s.rolling(window, center=True).std()
    idx   = s[(s > ma+2*std)|(s < ma-2*std)].index
    return pd.DataFrame({sensor:s[idx],"ma":ma[idx],"is_anomaly":True})

def _anomaly_if(df, sensor, contamination):
    if df.empty or sensor not in df.columns:
        return pd.DataFrame()
    s = pd.to_numeric(df[sensor], errors="coerce").dropna().values.reshape(-1,1)
    try:
        from sklearn.ensemble import IsolationForest
        preds = IsolationForest(contamination=contamination, random_state=42).fit_predict(s)
        return pd.DataFrame({sensor:s[preds==-1].flatten(),"is_anomaly":True})
    except ImportError:
        return pd.DataFrame(columns=[sensor,"is_anomaly"])


# ── module-level singleton (used as 'from backend.core.data_manager import data_manager') ─

data_manager = DataManager()
