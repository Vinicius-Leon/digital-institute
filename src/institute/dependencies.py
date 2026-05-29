from fastapi import Depends, security
from sqlalchemy.ext.asyncio import AsyncSession

from institute.database import get_db
from institute.exceptions import UnauthorizedError
from institute.modules.auth.models import User
from institute.modules.auth.repository import UserRepository
from institute.modules.auth.service import AuthService

oauth2_scheme = security.OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency that extracts and validates the JWT token, returning the current user.

    Use with Depends(get_current_user) on any endpoint that requires authentication.
    """
    import uuid

    payload = AuthService.verify_token(token)
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedError()

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise UnauthorizedError() from None

    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)

    if not user or not user.is_active:
        raise UnauthorizedError()

    return user
