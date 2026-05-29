from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from institute.database import get_db
from institute.modules.auth.schemas import (
    LoginRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
)
from institute.modules.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    service = AuthService(db)
    return await service.register(data)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate a user and return a JWT",
)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    service = AuthService(db)
    return await service.login(data.email, data.password)
