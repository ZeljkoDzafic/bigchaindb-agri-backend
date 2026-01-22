"""Pytest fixtures for the BigchainDB Agri Backend tests."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.routes.auth import fake_users_db, get_password_hash
from app.api.routes.farms import farms_db, user_keypairs
from app.api.routes.fields import fields_db
from app.api.routes.sensors import sensors_db
from app.api.routes.measurements import measurements_db


@pytest.fixture(autouse=True)
def clear_databases():
    """Clear all in-memory databases before each test."""
    fake_users_db.clear()
    farms_db.clear()
    fields_db.clear()
    sensors_db.clear()
    measurements_db.clear()
    user_keypairs.clear()
    yield
    fake_users_db.clear()
    farms_db.clear()
    fields_db.clear()
    sensors_db.clear()
    measurements_db.clear()
    user_keypairs.clear()


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def test_user():
    """Create a test user and return credentials."""
    user_data = {
        "email": "test@example.com",
        "full_name": "Test User",
        "public_key": "test_public_key",
        "hashed_password": get_password_hash("testpassword"),
        "disabled": False,
    }
    fake_users_db["test@example.com"] = user_data
    return {
        "email": "test@example.com",
        "password": "testpassword",
    }


@pytest.fixture
def auth_headers(client, test_user):
    """Get authorization headers for authenticated requests."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user["email"],
            "password": test_user["password"],
        },
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_bigchaindb(mocker):
    """Mock BigchainDB service."""
    mock_service = mocker.patch("app.services.bigchaindb_service.BigchainDBService")
    instance = mock_service.return_value

    instance.generate_keypair.return_value = ("mock_public_key", "mock_private_key")
    instance.create_asset.return_value = {"id": "mock_transaction_id_12345678"}
    instance.transfer_asset.return_value = {"id": "mock_transfer_id_12345678"}

    return instance
