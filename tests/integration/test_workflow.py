"""Integration tests for complete workflow scenarios."""

import pytest


class TestCompleteWorkflow:
    """Test complete user workflow scenarios."""

    def test_full_farm_setup_workflow(self, client, mock_bigchaindb):
        """Test complete workflow: register -> create farm -> add field -> add sensor."""
        # 1. Register user
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "farmer@example.com",
                "password": "farmpassword123",
                "full_name": "John Farmer",
            },
        )
        assert register_response.status_code == 200

        # 2. Login
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "farmer@example.com",
                "password": "farmpassword123",
            },
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Create farm
        farm_response = client.post(
            "/api/v1/farms",
            headers=headers,
            json={
                "name": "Green Valley Farm",
                "location": {"latitude": 45.815, "longitude": 15.982},
                "area_hectares": 250.0,
                "crop_types": ["wheat", "barley", "sunflower"],
                "description": "Family farm in Croatian countryside",
            },
        )
        assert farm_response.status_code == 201
        farm_id = farm_response.json()["id"]

        # 4. Create field
        field_response = client.post(
            "/api/v1/fields",
            headers=headers,
            json={
                "name": "North Field",
                "farm_id": farm_id,
                "boundaries": [
                    {"latitude": 45.815, "longitude": 15.982},
                    {"latitude": 45.816, "longitude": 15.982},
                    {"latitude": 45.816, "longitude": 15.983},
                    {"latitude": 45.815, "longitude": 15.983},
                ],
                "area_hectares": 50.0,
                "crop_type": "wheat",
                "soil_type": "loam",
            },
        )
        assert field_response.status_code == 201
        field_id = field_response.json()["id"]

        # 5. Register sensor
        sensor_response = client.post(
            "/api/v1/sensors",
            headers=headers,
            json={
                "sensor_id": "SENSOR-001",
                "sensor_type": "soil_moisture",
                "field_id": field_id,
                "farm_id": farm_id,
                "location": {"latitude": 45.8155, "longitude": 15.9825},
                "manufacturer": "SoilTech",
                "model": "SM-2000",
            },
        )
        assert sensor_response.status_code == 201

        # 6. List sensors
        sensors_response = client.get(
            f"/api/v1/sensors?farm_id={farm_id}",
            headers=headers,
        )
        assert sensors_response.status_code == 200
        assert sensors_response.json()["total"] == 1

    def test_measurement_recording_workflow(self, client, mock_bigchaindb):
        """Test workflow for recording sensor measurements."""
        # Setup: Register and login
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "sensor_user@example.com",
                "password": "sensorpass123",
                "full_name": "Sensor User",
            },
        )
        login_resp = client.post(
            "/api/v1/auth/login",
            data={"username": "sensor_user@example.com", "password": "sensorpass123"},
        )
        headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

        # Create farm and sensor
        farm_resp = client.post(
            "/api/v1/farms",
            headers=headers,
            json={
                "name": "Sensor Test Farm",
                "location": {"latitude": 45.0, "longitude": 18.0},
                "area_hectares": 100.0,
            },
        )
        farm_id = farm_resp.json()["id"]

        sensor_resp = client.post(
            "/api/v1/sensors",
            headers=headers,
            json={
                "sensor_id": "TEMP-001",
                "sensor_type": "temperature",
                "field_id": "",
                "farm_id": farm_id,
            },
        )
        assert sensor_resp.status_code == 201

        # Record measurement
        measurement_resp = client.post(
            "/api/v1/measurements",
            headers=headers,
            json={
                "sensor_id": "TEMP-001",
                "value": 25.5,
                "unit": "celsius",
                "quality": "good",
            },
        )
        assert measurement_resp.status_code == 201
        assert measurement_resp.json()["value"] == 25.5

        # List measurements
        list_resp = client.get("/api/v1/measurements", headers=headers)
        assert list_resp.status_code == 200
        assert list_resp.json()["total"] >= 1
