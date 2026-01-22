"""Unit tests for authentication routes."""

import pytest


class TestAuthRoutes:
    """Tests for authentication endpoints."""

    def test_register_user(self, client, mock_bigchaindb):
        """Test user registration."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepassword123",
                "full_name": "New User",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert "public_key" in data

    def test_register_duplicate_email(self, client, test_user, mock_bigchaindb):
        """Test registration with duplicate email."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user["email"],
                "password": "anotherpassword",
                "full_name": "Another User",
            },
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_login_success(self, client, test_user):
        """Test successful login."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user["email"],
                "password": test_user["password"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user["email"],
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "somepassword",
            },
        )
        assert response.status_code == 401

    def test_get_current_user(self, client, auth_headers):
        """Test get current user endpoint."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"

    def test_get_current_user_no_auth(self, client):
        """Test get current user without authentication."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_refresh_token(self, client, auth_headers):
        """Test token refresh."""
        response = client.post("/api/v1/auth/refresh", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
