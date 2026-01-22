"""BigchainDB service for transaction management."""

from datetime import datetime
from typing import Any, Optional

from bigchaindb_driver import BigchainDB
from bigchaindb_driver.crypto import generate_keypair

from app.config import get_settings

settings = get_settings()


class BigchainDBService:
    """Service for interacting with BigchainDB."""

    def __init__(self):
        """Initialize BigchainDB connection."""
        self.bdb = BigchainDB(settings.bigchaindb_root_url)

    def generate_keypair(self) -> tuple[str, str]:
        """Generate a new Ed25519 keypair.

        Returns:
            Tuple of (public_key, private_key)
        """
        keypair = generate_keypair()
        return keypair.public_key, keypair.private_key

    def create_asset(
        self,
        asset_data: dict[str, Any],
        metadata: Optional[dict[str, Any]],
        public_key: str,
        private_key: str,
    ) -> dict[str, Any]:
        """Create a new asset in BigchainDB.

        Args:
            asset_data: Asset data to store
            metadata: Optional metadata
            public_key: Owner's public key
            private_key: Owner's private key

        Returns:
            Committed transaction
        """
        prepared_tx = self.bdb.transactions.prepare(
            operation="CREATE",
            signers=public_key,
            asset={"data": asset_data},
            metadata=metadata or {"created_at": datetime.utcnow().isoformat()},
        )

        signed_tx = self.bdb.transactions.fulfill(
            prepared_tx, private_keys=private_key
        )

        return self.bdb.transactions.send_commit(signed_tx)

    def transfer_asset(
        self,
        asset_id: str,
        metadata: dict[str, Any],
        current_owner_public_key: str,
        current_owner_private_key: str,
        new_owner_public_key: Optional[str] = None,
    ) -> dict[str, Any]:
        """Transfer an asset (used for appending data via TRANSFER).

        Args:
            asset_id: ID of the asset to transfer
            metadata: Metadata to append
            current_owner_public_key: Current owner's public key
            current_owner_private_key: Current owner's private key
            new_owner_public_key: New owner's public key (defaults to current)

        Returns:
            Committed transfer transaction
        """
        if new_owner_public_key is None:
            new_owner_public_key = current_owner_public_key

        # Get the latest transaction for this asset
        transactions = self.bdb.transactions.get(asset_id=asset_id)
        latest_tx = transactions[-1]

        output_index = 0
        output = latest_tx["outputs"][output_index]

        transfer_input = {
            "fulfillment": output["condition"]["details"],
            "fulfills": {
                "output_index": output_index,
                "transaction_id": latest_tx["id"],
            },
            "owners_before": output["public_keys"],
        }

        prepared_tx = self.bdb.transactions.prepare(
            operation="TRANSFER",
            asset={"id": asset_id},
            inputs=transfer_input,
            recipients=new_owner_public_key,
            metadata=metadata,
        )

        signed_tx = self.bdb.transactions.fulfill(
            prepared_tx, private_keys=current_owner_private_key
        )

        return self.bdb.transactions.send_commit(signed_tx)

    def get_transaction(self, transaction_id: str) -> Optional[dict[str, Any]]:
        """Get a transaction by ID.

        Args:
            transaction_id: Transaction ID

        Returns:
            Transaction data or None if not found
        """
        try:
            return self.bdb.transactions.retrieve(transaction_id)
        except Exception:
            return None

    def get_asset_transactions(self, asset_id: str) -> list[dict[str, Any]]:
        """Get all transactions for an asset.

        Args:
            asset_id: Asset ID

        Returns:
            List of transactions
        """
        return self.bdb.transactions.get(asset_id=asset_id)

    def search_assets(self, search_term: str) -> list[dict[str, Any]]:
        """Search for assets by term.

        Args:
            search_term: Search term

        Returns:
            List of matching assets
        """
        return self.bdb.assets.get(search=search_term)
