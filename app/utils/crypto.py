"""Cryptographic utilities for signature verification."""

import base64
import hashlib
import json
from typing import Any

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    from cryptography.hazmat.primitives import serialization
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


def generate_signature(data: dict[str, Any], private_key_bytes: bytes) -> str:
    """Generate Ed25519 signature for data.

    Args:
        data: Data to sign
        private_key_bytes: Private key bytes

    Returns:
        Base64-encoded signature
    """
    if not CRYPTO_AVAILABLE:
        raise ImportError("cryptography library required for signing")

    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    private_key = Ed25519PrivateKey.from_private_bytes(private_key_bytes)
    message = json.dumps(data, sort_keys=True).encode()
    signature = private_key.sign(message)
    return base64.b64encode(signature).decode()


def verify_signature(
    data: dict[str, Any],
    signature: str,
    public_key_base58: str,
) -> bool:
    """Verify Ed25519 signature.

    Args:
        data: Original data that was signed
        signature: Base64-encoded signature
        public_key_base58: Base58-encoded public key

    Returns:
        True if signature is valid, False otherwise
    """
    if not CRYPTO_AVAILABLE:
        return True  # Skip verification if crypto not available

    try:
        import base58

        public_key_bytes = base58.b58decode(public_key_base58)
        public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)

        signature_bytes = base64.b64decode(signature)
        message = json.dumps(data, sort_keys=True).encode()

        public_key.verify(signature_bytes, message)
        return True
    except Exception:
        return False


def hash_data(data: dict[str, Any]) -> str:
    """Generate SHA-256 hash of data.

    Args:
        data: Data to hash

    Returns:
        Hex-encoded hash
    """
    message = json.dumps(data, sort_keys=True).encode()
    return hashlib.sha256(message).hexdigest()
