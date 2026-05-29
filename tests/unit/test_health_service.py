from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from institute.modules.health.service import HealthService


@pytest.fixture
def mock_db():
    return AsyncMock(spec=AsyncSession)


@pytest.mark.unit
class TestHealthService:
    async def test_health_returns_ok_when_db_responds(self, mock_db):
        """Health deve retornar ok quando o banco responde."""
        mock_db.execute = AsyncMock(return_value=MagicMock())

        service = HealthService(mock_db)
        result = await service.check()

        assert result.status == "ok"
        assert result.dependencies["database"].status == "ok"

    async def test_health_returns_unavailable_when_db_fails(self, mock_db):
        """Health deve retornar unavailable quando o banco falha."""
        mock_db.execute = AsyncMock(side_effect=Exception("connection refused"))

        service = HealthService(mock_db)
        result = await service.check()

        assert result.status == "unavailable"
        assert result.dependencies["database"].status == "unavailable"
        assert "connection refused" in result.dependencies["database"].detail

    async def test_health_includes_latency_when_db_ok(self, mock_db):
        """Health deve incluir latência quando o banco responde."""
        mock_db.execute = AsyncMock(return_value=MagicMock())

        service = HealthService(mock_db)
        result = await service.check()

        assert result.dependencies["database"].latency_ms is not None
        assert result.dependencies["database"].latency_ms >= 0
