"""Station / gate detail models."""
from pydantic import BaseModel
from typing import List, Optional
from backend.models.metrics import GateInfo, StationMetrics


class StationStatus(BaseModel):
    station:    str
    status:     str   # operational | warning | critical
    passengers: int
    sync_score: int


class StationDetail(BaseModel):
    station:      str
    metrics:      StationMetrics
    gates:        List[GateInfo]
