from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from institute.database import get_db
from institute.modules.health.schemas import HealthResponse
from institute.modules.health.service import HealthService

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Checks the application status and dependencies",
)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    """
    Health check endpoint.

    Returns the status of the application and each dependency (database, redis, etc.).
    Used by load balancers and monitoring systems to know
    if the application is healthy.
    """
    service = HealthService(db)
    return await service.check()
