"""Unit tests for farm routes."""

import pytest


class TestFarmRoutes:
    """Tests for farm management endpoints."""

    def test_list_farms_empty(self, client, auth_headers):
        """Test listing farms when empty."""
        response = client.get("/api/v1/farms", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["farms"] == []
        assert data["total"] == 0

    def test_create_farm(self, client, auth_headers, mock_bigchaindb):
        """Test creating a new farm."""
        response = client.post(
            "/api/v1/farms",
            headers=auth_headers,
            json={
                "name": "Test Farm",
                "location": {"latitude": 45.5, "longitude": 18.5},
                "area_hectares": 100.0,
                "crop_types": ["wheat", "corn"],
                "description": "A test farm",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Farm"
        assert "transaction_id" in data
        assert "id" in data

    def test_create_farm_no_auth(self, client):
        """Test creating farm without authentication."""
        response = client.post(
            "/api/v1/farms",
            json={
                "name": "Test Farm",
                "location": {"latitude": 45.5, "longitude": 18.5},
                "area_hectares": 100.0,
            },
        )
        assert response.status_code == 401

    def test_create_farm_invalid_location(self, client, auth_headers):
        """Test creating farm with invalid location."""
        response = client.post(
            "/api/v1/farms",
            headers=auth_headers,
            json={
                "name": "Test Farm",
                "location": {"latitude": 200, "longitude": 18.5},
                "area_hectares": 100.0,
            },
        )
        assert response.status_code == 422

    def test_get_farm(self, client, auth_headers, mock_bigchaindb):
        """Test getting a farm by ID."""
        # Create a farm first
        create_response = client.post(
            "/api/v1/farms",
            headers=auth_headers,
            json={
                "name": "Test Farm",
                "location": {"latitude": 45.5, "longitude": 18.5},
                "area_hectares": 100.0,
            },
        )
        farm_id = create_response.json()["id"]

        # Get the farm
        response = client.get(f"/api/v1/farms/{farm_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Farm"

    def test_get_farm_not_found(self, client, auth_headers):
        """Test getting non-existent farm."""
        response = client.get("/api/v1/farms/nonexistent", headers=auth_headers)
        assert response.status_code == 404

    def test_list_farms_with_data(self, client, auth_headers, mock_bigchaindb):
        """Test listing farms with data."""
        # Create farms
        for i in range(3):
            client.post(
                "/api/v1/farms",
                headers=auth_headers,
                json={
                    "name": f"Farm {i}",
                    "location": {"latitude": 45.5 + i, "longitude": 18.5},
                    "area_hectares": 100.0 + i * 10,
                },
            )

        response = client.get("/api/v1/farms", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["farms"]) == 3
