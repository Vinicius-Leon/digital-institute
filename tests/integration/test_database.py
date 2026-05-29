import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from institute.database import get_db


@pytest.mark.integration
class TestGetDb:
    async def test_get_db_yields_session(self):
        """get_db should yield a valid database session."""
        async for session in get_db():
            assert isinstance(session, AsyncSession)

    async def test_get_db_rolls_back_on_exception(self):
        """get_db should perform a rollback when an exception is raised."""
        gen = get_db()
        session = await gen.__anext__()
        assert isinstance(session, AsyncSession)

        with pytest.raises(RuntimeError):
            await gen.athrow(RuntimeError("erro simulado"))
