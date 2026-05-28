"""Customer / operator / contract renewal models."""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class Customer(BaseModel):
    id:           str
    name:         str
    station:      str
    contract_type:str
    monthly_value:float
    health_score: int
    contract_end: str
    status:       str
    renewal_probability: Optional[float] = None


class RFMData(BaseModel):
    id:           str
    segment:      str
    recency:      int
    frequency:    int
    monetary:     float
    rfm_score:    float


class ContractHealth(BaseModel):
    id:            str
    health_score:  int
    risk_level:    str
    station:       str


class RenewalForecast(BaseModel):
    id:           str
    renewal_date: str
    days_until_renewal: int
    renewal_probability: float
    expected_value: float
    renewal_status: str


class OperatorProfile(BaseModel):
    id:         str
    name:       str
    station:    str
    month:      int
    year:       int
    pax:        int
    door_health:float
