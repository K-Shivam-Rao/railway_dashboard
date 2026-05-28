"""Anomaly-detection / TSC / correlation models."""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class AnomalyResult(BaseModel):
    anomaly_score: float
    is_anomaly:    bool
    timestamp:     Optional[str] = None
    value:         Optional[float] = None


class DecompositionResult(BaseModel):
    trend:     List[float]
    seasonal:  List[float]
    residual:  List[float]


class SensorCorrelation(BaseModel):
    sensor_a:    str
    sensor_b:    str
    correlation: float


class CorrelationMatrix(BaseModel):
    sensors:  List[str]
    matrix:   List[List[float]]


class HealthProfile(BaseModel):
    health_score: int
    sensors:      Dict[str, Dict[str, float]]
