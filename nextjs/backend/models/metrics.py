"""Station / gate metrics models."""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class GateInfo(BaseModel):
    gate_id:     str
    platform:    str
    door_state:  str
    sensor_temp: float
    sensor_vib:  float
    people:      int
    sync_score:  int
    door_health: int
    risk_score:  int


class StationMetrics(BaseModel):
    gates_total:   int
    gates_active:  int
    passengers:    int
    alerts:        int
    warnings:      int
    avg_sync:      int
    health_score:  float
    avg_temp:      float
    avg_vib:       float


class StationInfo(BaseModel):
    station:        str
    total_stations: int
    gates_total:    int
    gates_active:   int
    alerts:         int
    warnings:       int
    avg_sync:       int
    passengers:     int
    status:         str
    dot_color:      str


class StationDetail(BaseModel):
    station:  str
    metrics:  StationMetrics
    gates:    List[GateInfo]


class KPIItem(BaseModel):
    label:      str
    value:      str
    trend:      str
    trend_value: Optional[str] = None
    icon:       str
    color:      str


class KPIStrip(BaseModel):
    items: List[KPIItem]


class PSDAnalytics(BaseModel):
    door_cycles: Dict[str, List[float | str]]
    temperature: Dict[str, List[float | str]]


class SensorTimeSeries(BaseModel):
    timestamps: List[str]
    values:     List[float]


class NetworkSummary(BaseModel):
    total_gates:    int
    total_people:   int
    critical_count: int
    warning_count:  int
    optimal_count:  int
    network_sync:   int
