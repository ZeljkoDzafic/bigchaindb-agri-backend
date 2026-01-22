"""Measurement models for the BigchainDB Agri Backend."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MeasurementCreate(BaseModel):
    """Schema for creating a new measurement."""

    sensor_id: str
    value: float
    unit: str = Field(..., min_length=1, max_length=20)
    quality: str = Field(default="good")
    timestamp: Optional[datetime] = None


class Measurement(MeasurementCreate):
    """Measurement model with additional fields."""

    id: str
    transaction_id: str
    field_id: str
    farm_id: str
    created_at: datetime


class MeasurementResponse(BaseModel):
    """Response schema for measurement operations."""

    id: str
    transaction_id: str
    sensor_id: str
    value: float
    unit: str
    quality: str
    timestamp: datetime
    created_at: datetime


class MeasurementQuery(BaseModel):
    """Query parameters for measurements."""

    sensor_id: Optional[str] = None
    field_id: Optional[str] = None
    farm_id: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)
