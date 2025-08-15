"""
Database configuration for Mockly backend
Handles SQLAlchemy setup and database connections
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from typing import AsyncGenerator
import os

# Database URL - using SQLite for simplicity
# Use in-memory SQLite for production deployments where filesystem is read-only
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///:memory:")

# Handle both sync and async URLs properly
if DATABASE_URL.startswith("sqlite+aiosqlite:"):
    # If async SQLite URL is provided, derive sync URL from it
    SYNC_DATABASE_URL = DATABASE_URL.replace("sqlite+aiosqlite:", "sqlite:")
    ASYNC_DATABASE_URL = DATABASE_URL
elif DATABASE_URL.startswith("postgresql+asyncpg:"):
    # If async PostgreSQL URL is provided, derive sync URL from it
    SYNC_DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg:", "postgresql:")
    ASYNC_DATABASE_URL = DATABASE_URL
elif DATABASE_URL.startswith("postgresql:"):
    # If sync PostgreSQL URL is provided, derive async URL from it
    SYNC_DATABASE_URL = DATABASE_URL
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql:", "postgresql+asyncpg:")
else:
    # If sync SQLite URL is provided, derive async URL from it
    SYNC_DATABASE_URL = DATABASE_URL
    ASYNC_DATABASE_URL = DATABASE_URL.replace("sqlite:", "sqlite+aiosqlite:")

# Create engines with conditional connect_args for SQLite only
if "sqlite" in SYNC_DATABASE_URL:
    engine = create_engine(SYNC_DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(SYNC_DATABASE_URL)

if "sqlite" in ASYNC_DATABASE_URL:
    async_engine = create_async_engine(ASYNC_DATABASE_URL, connect_args={"check_same_thread": False})
else:
    async_engine = create_async_engine(ASYNC_DATABASE_URL)

# Create session makers
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

# Base class for models
Base = declarative_base()

# Dependency to get database session
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close() 