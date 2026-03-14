"""
Database connection and session management using SQLAlchemy async with SQLite.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import event
from sqlalchemy.orm import declarative_base
import os
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

# Will be set by init_db()
engine = None
AsyncSessionLocal = None


def get_database_url(storage_path: str) -> str:
    """Get the database URL based on storage path."""
    db_path = os.path.join(storage_path, "data.db")
    return f"sqlite+aiosqlite:///{db_path}"


def _set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable foreign key support for SQLite connections."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


async def init_db(storage_path: str):
    """
    Initialize the database connection and create tables.

    This should be called once at application startup.
    """
    global engine, AsyncSessionLocal

    # Ensure storage directory exists
    os.makedirs(storage_path, exist_ok=True)

    db_url = get_database_url(storage_path)
    logger.info(f"Initializing database at: {db_url}")

    # Create async engine with SQLite optimizations
    engine = create_async_engine(
        db_url,
        echo=False,  # Set to True for SQL debugging
        future=True,
        connect_args={"check_same_thread": False},
    )

    # Register event listener to enable foreign keys on each connection
    # Note: For aiosqlite, we need to use the sync engine's pool
    from sqlalchemy import event as sync_event

    @sync_event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Create session factory
    AsyncSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    # Create tables
    from .models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database initialized successfully")


async def get_db() -> AsyncSession:
    """
    Dependency that provides a database session.

    Usage in FastAPI:
        @router.get("/")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    if AsyncSessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_db():
    """Close the database connection pool."""
    global engine
    if engine:
        await engine.dispose()
        logger.info("Database connection closed")