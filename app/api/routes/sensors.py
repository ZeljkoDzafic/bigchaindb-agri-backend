"""Sensor management routes."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.routes.auth import User, get_current_user
from app.api.routes.farms import farms_db, user_keypairs
from app.api.routes.fields import fields_db
from app.models.sensor import SensorCreate, SensorResponse, SensorStatus
from app.services.bigchaindb_service import BigchainDBService

router = APIRouter()

sensors_db: dict = {}


def get_bdb_service() -> BigchainDBService:
    """Get BigchainDB service instance."""
    return BigchainDBService()


@router.get("")
async def list_sensors(
    farm_id: str = None,
    field_id: str = None,
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
):
    """List all sensors, optionally filtered by farm or field."""
    user_sensors = []
    for sensor in sensors_db.values():
        farm = farms_db.get(sensor.get("farm_id"))
        if farm and farm.get("owner_email") == current_user.email:
            if farm_id and sensor.get("farm_id") != farm_id:
                continue
            if field_id and sensor.get("field_id") != field_id:
                continue
            user_sensors.append(sensor)

    return {
        "sensors": user_sensors[skip:skip + limit],
        "total": len(user_sensors),
    }


@router.post("", response_model=SensorResponse, status_code=status.HTTP_201_CREATED)
async def register_sensor(
    sensor_data: SensorCreate,
    current_user: User = Depends(get_current_user),
    bdb_service: BigchainDBService = Depends(get_bdb_service),
):
    """Register a new sensor in BigchainDB."""
    farm = farms_db.get(sensor_data.farm_id)
    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm not found",
        )

    if farm.get("owner_email") != current_user.email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    if sensor_data.field_id and sensor_data.field_id not in fields_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field not found",
        )

    keypair = user_keypairs.get(current_user.email)
    if not keypair:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User keypair not found",
        )

    asset_data = {
        "type": "sensor",
        "sensor_id": sensor_data.sensor_id,
        "sensor_type": sensor_data.sensor_type.value,
        "field_id": sensor_data.field_id,
        "farm_id": sensor_data.farm_id,
        "location": sensor_data.location,
        "manufacturer": sensor_data.manufacturer,
        "model": sensor_data.model,
    }

    metadata = {
        "created_at": datetime.utcnow().isoformat(),
        "registered_by": current_user.email,
        "status": SensorStatus.ACTIVE.value,
    }

    try:
        tx = bdb_service.create_asset(
            asset_data, metadata,
            keypair["public_key"], keypair["private_key"]
        )
        internal_id = f"sensor_{tx['id'][:8]}"

        sensors_db[internal_id] = {
            "id": internal_id,
            "transaction_id": tx["id"],
            "sensor_id": sensor_data.sensor_id,
            "sensor_type": sensor_data.sensor_type,
            "field_id": sensor_data.field_id,
            "farm_id": sensor_data.farm_id,
            "status": SensorStatus.ACTIVE,
            "created_at": datetime.utcnow().isoformat(),
            **sensor_data.model_dump(),
        }

        return SensorResponse(
            id=internal_id,
            transaction_id=tx["id"],
            sensor_id=sensor_data.sensor_id,
            sensor_type=sensor_data.sensor_type,
            field_id=sensor_data.field_id,
            farm_id=sensor_data.farm_id,
            status=SensorStatus.ACTIVE,
            created_at=datetime.utcnow(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register sensor: {str(e)}",
        )


@router.get("/{sensor_id}")
async def get_sensor(
    sensor_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get sensor details by ID."""
    sensor = sensors_db.get(sensor_id)
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

    return sensor


@router.patch("/{sensor_id}/status")
async def update_sensor_status(
    sensor_id: str,
    new_status: SensorStatus,
    current_user: User = Depends(get_current_user),
    bdb_service: BigchainDBService = Depends(get_bdb_service),
):
    """Update sensor status."""
    sensor = sensors_db.get(sensor_id)
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

    metadata = {
        "updated_at": datetime.utcnow().isoformat(),
        "updated_by": current_user.email,
        "status": new_status.value,
    }

    try:
        tx = bdb_service.transfer_asset(
            asset_id=sensor["transaction_id"],
            metadata=metadata,
            current_owner_public_key=keypair["public_key"],
            current_owner_private_key=keypair["private_key"],
        )

        sensors_db[sensor_id]["status"] = new_status
        sensors_db[sensor_id]["updated_at"] = datetime.utcnow().isoformat()

        return {
            "id": sensor_id,
            "transaction_id": tx["id"],
            "status": new_status,
            "message": "Sensor status updated successfully",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update sensor status: {str(e)}",
        )
