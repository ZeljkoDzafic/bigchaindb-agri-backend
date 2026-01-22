"""Field models for the BigchainDB Agri Backend."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Coordinate(BaseModel):
    """Geographic coordinate."""

    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class FieldCreate(BaseModel):
    """Schema for creating a new field."""

    name: str = Field(..., min_length=1, max_length=255)
    farm_id: str
    boundaries: list[Coordinate] = Field(default_factory=list)
    area_hectares: float = Field(..., gt=0)
    crop_type: Optional[str] = None
    soil_type: Optional[str] = None


class FieldModel(FieldCreate):
    """Field model with additional fields."""

    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class FieldResponse(BaseModel):
    """Response schema for field operations."""

    id: str
    transaction_id: str
    name: str
    farm_id: str
    created_at: datetime
