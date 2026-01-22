"""Farm models for the BigchainDB Agri Backend."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Location(BaseModel):
    """Geographic location."""

    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class FarmCreate(BaseModel):
    """Schema for creating a new farm."""

    name: str = Field(..., min_length=1, max_length=255)
    location: Location
    area_hectares: float = Field(..., gt=0)
    crop_types: list[str] = Field(default_factory=list)
    description: Optional[str] = None


class Farm(FarmCreate):
    """Farm model with additional fields."""

    id: str
    owner_public_key: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class FarmResponse(BaseModel):
    """Response schema for farm operations."""

    id: str
    transaction_id: str
    name: str
    owner_public_key: str
    created_at: datetime
