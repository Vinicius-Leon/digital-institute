import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from institute.config import get_settings
from institute.exceptions import ConflictError, UnauthorizedError
from institute.modules.auth.models import User
from institute.modules.auth.repository import UserRepository
from institute.modules.auth.schemas import TokenResponse, UserCreate, UserResponse

logger = logging.getLogger(__name__)
settings = get_settings()


class AuthService:
    def __init__(
        self,
        db: AsyncSession,
        password_hasher: PasswordHasher | None = None,
    ) -> None:
        self._db = db
        self._repo = UserRepository(db)
        self._ph = password_hasher or PasswordHasher()

    async def register(self, data: UserCreate) -> UserResponse:
        existing = await self._repo.get_by_email(data.email)
        if existing:
            raise ConflictError(f"Email '{data.email}' is already registered.")

        hashed_password = self._ph.hash(data.password)
        user = await self._repo.create(
            email=data.email,
            hashed_password=hashed_password,
        )

        logger.info("User registered", extra={"user_id": str(user.id)})
        return UserResponse.model_validate(user)

    async def login(self, email: str, password: str) -> TokenResponse:
        user = await self._repo.get_by_email(email)

        if user is None:
            try:
                self._ph.verify(
                    "$argon2id$v=19$m=65536,t=3,p=4$dummysaltdummy$dummyhashplaceholder",
                    password,
                )
            except (VerifyMismatchError, VerificationError):
                pass
            raise UnauthorizedError("Invalid email or password.")

        try:
            self._ph.verify(user.hashed_password, password)
        except VerifyMismatchError:
            raise UnauthorizedError("Invalid email or password.") from None

        if not user.is_active:
            raise UnauthorizedError("Invalid email or password.")

        token = self._create_token(user)
        logger.info("User logged in", extra={"user_id": str(user.id)})
        return token

    def _create_token(self, user: User) -> TokenResponse:
        expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "exp": expire,
            "iat": datetime.now(UTC),
        }
        token = jwt.encode(
            payload,
            settings.secret_key,
            algorithm=settings.jwt_algorithm,
        )
        return TokenResponse(
            access_token=token,
            expires_in=settings.jwt_expire_minutes * 60,
        )

    @staticmethod
    def verify_token(token: str) -> dict[str, Any]:
        try:
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[settings.jwt_algorithm],
            )
            return payload
        except JWTError:
            raise UnauthorizedError("Invalid or expired token.") from None
