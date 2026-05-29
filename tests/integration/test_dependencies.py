import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestGetCurrentUser:
    async def test_protected_endpoint_without_token_returns_401(
        self, client: AsyncClient
    ):
        """Accessing a protected endpoint without token should return 401."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    async def test_protected_endpoint_with_valid_token_returns_user(
        self, client: AsyncClient
    ):
        """Accessing a protected endpoint with valid token should return user data."""
        await client.post(
            "/api/v1/auth/register",
            json={"email": "me@example.com", "password": "senha1234"},
        )
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "me@example.com", "password": "senha1234"},
        )
        token = login_response.json()["access_token"]

        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["email"] == "me@example.com"

    async def test_protected_endpoint_with_invalid_token_returns_401(
        self, client: AsyncClient
    ):
        """Accessing a protected endpoint with invalid token should return 401."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer token.invalido.aqui"},
        )
        assert response.status_code == 401
