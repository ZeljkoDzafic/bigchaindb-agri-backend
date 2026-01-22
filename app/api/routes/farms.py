"""Farm management routes."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.routes.auth import User, get_current_user
from app.models.farm import FarmCreate, FarmResponse
from app.services.bigchaindb_service import BigchainDBService

router = APIRouter()


# In-memory store for demo (replace with database in production)
farms_db: dict = {}
user_keypairs: dict = {}  # Store user keypairs (in production, use secure storage)


def get_bdb_service() -> BigchainDBService:
    """Get BigchainDB service instance."""
    return BigchainDBService()


@router.get("")
async def list_farms(
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
):
    """List all farms for the current user."""
    user_farms = [
        farm for farm in farms_db.values()
        if farm.get("owner_email") == current_user.email
    ]
    return {
        "farms": user_farms[skip:skip + limit],
        "total": len(user_farms),
    }


@router.post("", response_model=FarmResponse, status_code=status.HTTP_201_CREATED)
async def create_farm(
    farm_data: FarmCreate,
    current_user: User = Depends(get_current_user),
    bdb_service: BigchainDBService = Depends(get_bdb_service),
):
    """Create a new farm asset in BigchainDB."""
    # Generate or retrieve user keypair
    if current_user.email not in user_keypairs:
        public_key, private_key = bdb_service.generate_keypair()
        user_keypairs[current_user.email] = {
            "public_key": public_key,
            "private_key": private_key,
        }
    else:
        keypair = user_keypairs[current_user.email]
        public_key = keypair["public_key"]
        private_key = keypair["private_key"]

    # Prepare asset data
    asset_data = {
        "type": "farm",
        "name": farm_data.name,
        "location": farm_data.location.model_dump(),
        "area_hectares": farm_data.area_hectares,
        "crop_types": farm_data.crop_types,
        "description": farm_data.description,
    }

    metadata = {
        "created_at": datetime.utcnow().isoformat(),
        "created_by": current_user.email,
    }

    try:
        tx = bdb_service.create_asset(asset_data, metadata, public_key, private_key)
        farm_id = f"farm_{tx['id'][:8]}"

        # Store in local cache
        farms_db[farm_id] = {
            "id": farm_id,
            "transaction_id": tx["id"],
            "name": farm_data.name,
            "owner_public_key": public_key,
            "owner_email": current_user.email,
            "created_at": datetime.utcnow().isoformat(),
            **farm_data.model_dump(),
        }

        return FarmResponse(
            id=farm_id,
            transaction_id=tx["id"],
            name=farm_data.name,
            owner_public_key=public_key,
            created_at=datetime.utcnow(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create farm: {str(e)}",
        )


@router.get("/{farm_id}")
async def get_farm(
    farm_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get farm details by ID."""
    farm = farms_db.get(farm_id)
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

    return farm


@router.put("/{farm_id}")
async def update_farm(
    farm_id: str,
    farm_data: FarmCreate,
    current_user: User = Depends(get_current_user),
    bdb_service: BigchainDBService = Depends(get_bdb_service),
):
    """Update farm metadata via TRANSFER transaction."""
    farm = farms_db.get(farm_id)
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

    metadata = {
        "updated_at": datetime.utcnow().isoformat(),
        "updated_by": current_user.email,
        "changes": farm_data.model_dump(),
    }

    try:
        # Get the asset ID from the transaction ID
        asset_id = farm["transaction_id"]
        tx = bdb_service.transfer_asset(
            asset_id=asset_id,
            metadata=metadata,
            current_owner_public_key=keypair["public_key"],
            current_owner_private_key=keypair["private_key"],
        )

        # Update local cache
        farms_db[farm_id].update({
            **farm_data.model_dump(),
            "updated_at": datetime.utcnow().isoformat(),
        })

        return {
            "id": farm_id,
            "transaction_id": tx["id"],
            "message": "Farm updated successfully",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update farm: {str(e)}",
        )
