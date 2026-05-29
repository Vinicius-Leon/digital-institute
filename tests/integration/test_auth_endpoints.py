import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestRegisterEndpoint:
    async def test_register_returns_201_with_user_data(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "novo@example.com", "password": "senha1234"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "novo@example.com"
        assert "id" in data
        assert "hashed_password" not in data  # never expose the password

    async def test_register_duplicate_email_returns_409(self, client: AsyncClient):
        payload = {"email": "duplicado@example.com", "password": "senha1234"}
        await client.post("/api/v1/auth/register", json=payload)
        response = await client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 409
        assert "detail" in response.json()

    async def test_register_invalid_email_returns_422(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "nao-e-um-email", "password": "senha1234"},
        )
        assert response.status_code == 422


@pytest.mark.integration
class TestLoginEndpoint:
    async def test_login_valid_credentials_returns_token(self, client: AsyncClient):
        # First register
        await client.post(
            "/api/v1/auth/register",
            json={"email": "login@example.com", "password": "senha1234"},
        )
        # Then login
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "login@example.com", "password": "senha1234"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password_returns_401(self, client: AsyncClient):
        await client.post(
            "/api/v1/auth/register",
            json={"email": "senha@example.com", "password": "senha1234"},
        )
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "senha@example.com", "password": "senhaerrada"},
        )
        assert response.status_code == 401


@pytest.mark.integration
class TestHealthEndpoint:
    async def test_health_returns_ok_when_db_connected(self, client: AsyncClient):
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["dependencies"]["database"]["status"] == "ok"
