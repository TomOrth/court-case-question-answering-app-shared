"""
Database session management.

Provides async database engine and session factory.
"""

import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from dotenv import load_dotenv

load_dotenv()

# GET DATABASE_URL from .env
DATABASE_URL = os.getenv('DATABASE_URL')

# Convert to async URL if needed
if DATABASE_URL and DATABASE_URL.startswith('postgresql://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://', 1)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True to see SQL queries in console
    pool_size=5,
    max_overflow=10,
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,  # Don't expire objects after commit
)

async def get_db():
    """Dependency for FastAPI routes to get database session.
    
    Usage:
        @app.get("/api/cases")
        async def get_cases(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Case))
            return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

    