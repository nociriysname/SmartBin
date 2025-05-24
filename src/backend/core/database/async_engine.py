from contextvars import ContextVar
from typing import Annotated

from fastapi.params import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)

from src.backend.core.config import settings
from src.backend.core.exc import HTTPError

__all__ = ("SessionDep", "get_session", "check_db_active", "get_engine")

engine: AsyncEngine = create_async_engine(
    settings.database_url,
    max_overflow=10,
    pool_recycle=3600,
    pool_size=20,
    isolation_level="SERIALIZABLE",
)


def get_engine() -> AsyncEngine:
    return engine


async def get_session(eng: AsyncEngine = Depends(get_engine)):
    session = AsyncSession(eng, autoflush=False, expire_on_commit=False)
    async with session:
        try:
            yield session
            await session.commit()
        except HTTPError as Error:
            if Error.commit_db:
                await session.commit()

            raise Error
        finally:
            await session.close()


async def check_db_active(session: AsyncSession):
    await session.execute(select(True))


SessionDep = Annotated[AsyncSession, Depends(get_session)]

CTX_KEEP_SESSION: ContextVar[bool] = ContextVar(
    "CTX_KEEP_SESSION",
    default=False,
)
