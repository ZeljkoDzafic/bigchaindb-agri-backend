"""Measurement routes for sensor data."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.routes.auth import User, get_current_user
from app.api.routes.farms import farms_db, user_keypairs
from app.api.routes.sensors import sensors_db
from app.models.measurement import MeasurementCreate, MeasurementResponse
from app.services.bigchaindb_service import BigchainDBService
from app.services.rabbitmq_service import RabbitMQService

router = APIRouter()

measurements_db: list = []


def get_bdb_service() -> BigchainDBService:
    """Get BigchainDB service instance."""
    return BigchainDBService()


def get_rabbitmq_service() -> RabbitMQService:
    """Get RabbitMQ service instance."""
    return RabbitMQService()


@router.get("")
async def list_measurements(
    sensor_id: Optional[str] = None,
    field_id: Optional[str] = None,
    farm_id: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
):
    """List measurements with optional filters."""
    filtered = []
    for m in measurements_db:
        sensor = sensors_db.get(m.get("internal_sensor_id"))
        if not sensor:
            continue

        farm = farms_db.get(sensor.get("farm_id"))
        if not farm or farm.get("owner_email") != current_user.email:
            continue

        if sensor_id and m.get("sensor_id") != sensor_id:
            continue
        if field_id and sensor.get("field_id") != field_id:
            continue
        if farm_id and sensor.get("farm_id") != farm_id:
            continue

        m_time = datetime.fromisoformat(m.get("timestamp", m.get("created_at")))
        if from_date and m_time < from_date:
            continue
        if to_date and m_time > to_date:
            continue

        filtered.append(m)

    return {
        "measurements": filtered[skip:skip + limit],
        "total": len(filtered),
    }


@router.post("", response_model=MeasurementResponse, status_code=status.HTTP_201_CREATED)
async def create_measurement(
    measurement_data: MeasurementCreate,
    current_user: User = Depends(get_current_user),
    bdb_service: BigchainDBService = Depends(get_bdb_service),
):
    """Record a new sensor measurement in BigchainDB."""
    # Find sensor by sensor_id
    sensor = None
    internal_sensor_id = None
    for sid, s in sensors_db.items():
        if s.get("sensor_id") == measurement_data.sensor_id:
            sensor = s
            internal_sensor_id = sid
            break

    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor not found",
        )

    farm = farms_db.get(sensor.get("farm_id"))
    if not farm or farm.get("owner_email") != current_user.email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    keypair = user_keypairs.get(current_user.email)
    if not keypair:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User keypair not found",
        )

    timestamp = measurement_data.timestamp or datetime.utcnow()

    metadata = {
        "reading": {
            "sensor_id": measurement_data.sensor_id,
            "value": measurement_data.value,
            "unit": measurement_data.unit,
            "quality": measurement_data.quality,
            "timestamp": timestamp.isoformat(),
        },
        "recorded_at": datetime.utcnow().isoformat(),
        "recorded_by": current_user.email,
    }

    try:
        tx = bdb_service.transfer_asset(
            asset_id=sensor["transaction_id"],
            metadata=metadata,
            current_owner_public_key=keypair["public_key"],
            current_owner_private_key=keypair["private_key"],
        )

        measurement = {
            "id": f"measurement_{tx['id'][:8]}",
            "transaction_id": tx["id"],
            "sensor_id": measurement_data.sensor_id,
            "internal_sensor_id": internal_sensor_id,
            "value": measurement_data.value,
            "unit": measurement_data.unit,
            "quality": measurement_data.quality,
            "timestamp": timestamp.isoformat(),
            "created_at": datetime.utcnow().isoformat(),
        }
        measurements_db.append(measurement)

        return MeasurementResponse(
            id=measurement["id"],
            transaction_id=tx["id"],
            sensor_id=measurement_data.sensor_id,
            value=measurement_data.value,
            unit=measurement_data.unit,
            quality=measurement_data.quality,
            timestamp=timestamp,
            created_at=datetime.utcnow(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record measurement: {str(e)}",
        )


@router.post("/batch", status_code=status.HTTP_201_CREATED)
async def create_batch_measurements(
    measurements: list[MeasurementCreate],
    current_user: User = Depends(get_current_user),
    bdb_service: BigchainDBService = Depends(get_bdb_service),
    rabbitmq_service: RabbitMQService = Depends(get_rabbitmq_service),
):
    """Record multiple measurements. Queues for async processing if many."""
    if len(measurements) > 10:
        # Queue for async processing
        for m in measurements:
            rabbitmq_service.publish(
                message={
                    "sensor_id": m.sensor_id,
                    "value": m.value,
                    "unit": m.unit,
                    "quality": m.quality,
                    "timestamp": (m.timestamp or datetime.utcnow()).isoformat(),
                    "user_email": current_user.email,
                },
                routing_key="sensor.data.batch",
            )
        return {
            "message": f"Queued {len(measurements)} measurements for processing",
            "queued": len(measurements),
        }

    # Process synchronously for small batches
    results = []
    for m in measurements:
        try:
            result = await create_measurement(m, current_user, bdb_service)
            results.append({"success": True, "id": result.id})
        except HTTPException as e:
            results.append({"success": False, "error": e.detail})

    return {
        "message": f"Processed {len(measurements)} measurements",
        "results": results,
    }


@router.get("/{measurement_id}")
async def get_measurement(
    measurement_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get measurement details by ID."""
    measurement = None
    for m in measurements_db:
        if m.get("id") == measurement_id:
            measurement = m
            break

    if not measurement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Measurement not found",
        )

    sensor = sensors_db.get(measurement.get("internal_sensor_id"))
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated sensor not found",
        )

    farm = farms_db.get(sensor.get("farm_id"))
    if not farm or farm.get("owner_email") != current_user.email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return measurement
