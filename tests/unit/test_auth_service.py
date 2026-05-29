from unittest.mock import AsyncMock, MagicMock

import pytest
from argon2.exceptions import VerifyMismatchError
from pydantic import ValidationError

from institute.exceptions import ConflictError, UnauthorizedError
from institute.modules.auth.schemas import UserCreate
from institute.modules.auth.service import AuthService


@pytest.fixture
def mock_db():
    """Fake bank session — the service will not use the real bank."""
    return AsyncMock()


@pytest.fixture
def mock_hasher():
    """Fake password hasher — avoids dealing with C extension constraints."""
    hasher = MagicMock()
    hasher.hash.return_value = "hashed_password"
    hasher.verify.return_value = True
    return hasher


@pytest.fixture
def auth_service(mock_db, mock_hasher):
    return AuthService(db=mock_db, password_hasher=mock_hasher)


@pytest.mark.unit
class TestAuthServiceRegister:
    async def test_register_new_user_succeeds(self, auth_service, mock_hasher):
        """Registering a new email should return the user's data."""
        from unittest.mock import patch

        with (
            patch.object(auth_service._repo, "get_by_email", return_value=None),
            patch.object(
                auth_service._repo,
                "create",
                return_value=MagicMock(
                    id="123e4567-e89b-12d3-a456-426614174000",
                    email="test@example.com",
                    is_active=True,
                    created_at=MagicMock(),
                ),
            ),
        ):
            data = UserCreate(email="test@example.com", password="senha123")
            result = await auth_service.register(data)
            assert result.email == "test@example.com"
            mock_hasher.hash.assert_called_once_with("senha123")

    async def test_register_duplicate_email_raises_conflict(self, auth_service):
        """Registering an existing email should raise ConflictError."""
        from unittest.mock import patch

        existing_user = MagicMock()
        with patch.object(
            auth_service._repo, "get_by_email", return_value=existing_user
        ):
            data = UserCreate(email="existing@example.com", password="senha123")
            with pytest.raises(ConflictError):
                await auth_service.register(data)

    async def test_register_short_password_raises_validation_error(self, auth_service):
        """Password with less than 8 characters should fail Pydantic validation."""
        with pytest.raises(ValidationError):
            UserCreate(email="test@example.com", password="123")


@pytest.mark.unit
class TestAuthServiceLogin:
    async def test_login_nonexistent_user_raises_unauthorized(self, auth_service):
        """Login with non-existent email should return generic error."""
        from unittest.mock import patch

        with patch.object(auth_service._repo, "get_by_email", return_value=None):
            with pytest.raises(UnauthorizedError):
                await auth_service.login("ghost@example.com", "qualquersenha")

    async def test_login_inactive_user_raises_unauthorized(
        self, auth_service, mock_hasher
    ):
        """Login with inactive user should raise UnauthorizedError."""
        from unittest.mock import patch

        inactive_user = MagicMock()
        inactive_user.is_active = False
        inactive_user.hashed_password = "hashed_password"
        mock_hasher.verify.return_value = True

        with patch.object(
            auth_service._repo, "get_by_email", return_value=inactive_user
        ):
            with pytest.raises(UnauthorizedError):
                await auth_service.login("inactive@example.com", "senha123")

    async def test_login_wrong_password_raises_unauthorized(
        self, auth_service, mock_hasher
    ):
        """Login with wrong password should raise UnauthorizedError."""
        from unittest.mock import patch

        user = MagicMock()
        user.is_active = True
        user.hashed_password = "hashed_password"
        mock_hasher.verify.side_effect = VerifyMismatchError()

        with patch.object(auth_service._repo, "get_by_email", return_value=user):
            with pytest.raises(UnauthorizedError):
                await auth_service.login("user@example.com", "senhaerrada")


@pytest.mark.unit
class TestVerifyToken:
    def test_verify_valid_token_returns_payload(self):
        """Valid token should decode and return the payload."""
        user = MagicMock()
        user.id = "123e4567-e89b-12d3-a456-426614174000"
        user.email = "test@example.com"

        service = AuthService.__new__(AuthService)
        token_response = service._create_token(user)

        payload = AuthService.verify_token(token_response.access_token)
        assert payload["email"] == "test@example.com"
        assert payload["sub"] == str(user.id)

    def test_verify_invalid_token_raises_unauthorized(self):
        """Invalid token should raise UnauthorizedError."""
        with pytest.raises(UnauthorizedError):
            AuthService.verify_token("token.invalido.aqui")
