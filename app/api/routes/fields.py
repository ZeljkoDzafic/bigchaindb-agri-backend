"""Field management routes."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.routes.auth import User, get_current_user
from app.api.routes.farms import farms_db, user_keypairs
from app.models.field import FieldCreate, FieldResponse
from app.services.bigchaindb_service import BigchainDBService

router = APIRouter()

fields_db: dict = {}


def get_bdb_service() -> BigchainDBService:
    """Get BigchainDB service instance."""
    return BigchainDBService()


@router.get("")
async def list_fields(
    farm_id: str = None,
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
):
    """List all fields, optionally filtered by farm."""
    user_fields = []
    for field in fields_db.values():
        farm = farms_db.get(field.get("farm_id"))
        if farm and farm.get("owner_email") == current_user.email:
            if farm_id is None or field.get("farm_id") == farm_id:
                user_fields.append(field)

    return {
        "fields": user_fields[skip:skip + limit],
        "total": len(user_fields),
    }


@router.post("", response_model=FieldResponse, status_code=status.HTTP_201_CREATED)
async def create_field(
    field_data: FieldCreate,
    current_user: User = Depends(get_current_user),
    bdb_service: BigchainDBService = Depends(get_bdb_service),
):
    """Create a new field asset in BigchainDB."""
    farm = farms_db.get(field_data.farm_id)
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

    keypair = user_keypairs.get(current_user.email)
    if not keypair:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User keypair not found",
        )

    asset_data = {
        "type": "field",
        "name": field_data.name,
        "farm_id": field_data.farm_id,
        "boundaries": [b.model_dump() for b in field_data.boundaries],
        "area_hectares": field_data.area_hectares,
        "crop_type": field_data.crop_type,
        "soil_type": field_data.soil_type,
    }

    metadata = {
        "created_at": datetime.utcnow().isoformat(),
        "created_by": current_user.email,
    }

    try:
        tx = bdb_service.create_asset(
            asset_data, metadata,
            keypair["public_key"], keypair["private_key"]
        )
        field_id = f"field_{tx['id'][:8]}"

        fields_db[field_id] = {
            "id": field_id,
            "transaction_id": tx["id"],
            "name": field_data.name,
            "farm_id": field_data.farm_id,
            "created_at": datetime.utcnow().isoformat(),
            **field_data.model_dump(),
        }

        return FieldResponse(
            id=field_id,
            transaction_id=tx["id"],
            name=field_data.name,
            farm_id=field_data.farm_id,
            created_at=datetime.utcnow(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create field: {str(e)}",
        )


@router.get("/{field_id}")
async def get_field(
    field_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get field details by ID."""
    field = fields_db.get(field_id)
    if not field:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field not found",
        )

    farm = farms_db.get(field.get("farm_id"))
    if not farm or farm.get("owner_email") != current_user.email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return field
