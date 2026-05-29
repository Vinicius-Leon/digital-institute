import logging
import time

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from institute.config import get_settings
from institute.modules.health.schemas import DependencyStatus, HealthResponse

logger = logging.getLogger(__name__)
settings = get_settings()


class HealthService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def check(self) -> HealthResponse:
        dependencies = {}

        dependencies["database"] = await self._check_database()

        overall_status = "ok"
        if any(d.status == "unavailable" for d in dependencies.values()):
            overall_status = "unavailable"
        elif any(d.status == "degraded" for d in dependencies.values()):
            overall_status = "degraded"

        return HealthResponse(
            status=overall_status,
            version="0.1.0",
            environment=settings.environment,
            dependencies=dependencies,
        )

    async def _check_database(self) -> DependencyStatus:
        try:
            start = time.perf_counter()
            await self._db.execute(text("SELECT 1"))
            latency_ms = (time.perf_counter() - start) * 1000
            return DependencyStatus(status="ok", latency_ms=round(latency_ms, 2))
        except Exception as e:
            logger.error("Database health check failed", extra={"error": str(e)})
            return DependencyStatus(status="unavailable", detail=str(e))
