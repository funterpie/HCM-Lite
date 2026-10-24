import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

# asyncpg + Supabase pooler gotcha: statement_cache_size=0 for port 6543
engine = create_async_engine(
    settings.DATABASE_URL,
    connect_args={"statement_cache_size": 0},
    echo=False
)

SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with SessionLocal() as session:
        yield session
