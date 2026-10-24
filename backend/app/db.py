from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

_settings = get_settings()
engine = (
    create_async_engine(
        _settings.database_url,
        pool_pre_ping=True,
        connect_args={"statement_cache_size": 0},
    )
    if _settings.database_url
    else None
)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False) if engine else None


async def get_session() -> AsyncIterator[AsyncSession]:
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL is not configured")
    async with SessionLocal() as session:
        yield session
