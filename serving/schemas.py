"""
schemas.py
----------
Pydantic models define the shape of data
going in and out of our API endpoints.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AlertResponse(BaseModel):
    id: int
    symbol: str
    anomaly_type: str
    price: float
    z_score: Optional[float]
    if_score: Optional[float]
    timestamp: Optional[datetime]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class StatusResponse(BaseModel):
    status: str
    total_alerts: int
    message: str