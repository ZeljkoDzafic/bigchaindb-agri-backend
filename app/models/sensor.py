"""Sensor models for the BigchainDB Agri Backend."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SensorType(str, Enum):
    """Types of sensors supported."""

    SOIL_MOISTURE = "soil_moisture"
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    LIGHT = "light"
    PH = "ph"
    NITROGEN = "nitrogen"
    PHOSPHORUS = "phosphorus"
    POTASSIUM = "potassium"


class SensorStatus(str, Enum):
    """Sensor operational status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    ERROR = "error"


class SensorCreate(BaseModel):
    """Schema for registering a new sensor."""

    sensor_id: str = Field(..., min_length=1, max_length=100)
    sensor_type: SensorType
    field_id: str
    farm_id: str
    location: Optional[dict] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    calibration_date: Optional[datetime] = None


class Sensor(SensorCreate):
    """Sensor model with additional fields."""

    id: str
    status: SensorStatus = SensorStatus.ACTIVE
    created_at: datetime
    last_reading_at: Optional[datetime] = None


class SensorResponse(BaseModel):
    """Response schema for sensor operations."""

    id: str
    transaction_id: str
    sensor_id: str
    sensor_type: SensorType
    field_id: str
    farm_id: str
    status: SensorStatus
    created_at: datetime


class SensorData(BaseModel):
    """Schema for submitting sensor data."""

    value: float
    unit: str = Field(..., min_length=1, max_length=20)
    quality: str = Field(default="good")
    timestamp: Optional[datetime] = None
    signature: Optional[str] = None
