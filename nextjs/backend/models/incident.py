"""Incident / alert models."""
from pydantic import BaseModel
from typing import List, Optional


class Incident(BaseModel):
    id:          str
    station:     str
    severity:    str
    category:    str
    description: str
    timestamp:   str
    resolved:    bool


class IncidentSummary(BaseModel):
    total:      int
    critical:   int
    warning:    int
    info:       int
    resolved:   int
    open:       int
    by_category: dict


class PhaseCard(BaseModel):
    id:          str
    title:       str
    severity:    str
    description: str
