from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from models import DeclarativeBase


async def init_db():
    engine = create_async_engine(
        f"postgresql+asyncpg://" f"postgres:postgres@postgres_bot:5432/bot_db",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(DeclarativeBase.metadata.create_all)
    return sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
