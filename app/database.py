"""
Database configuration for COSMIC Data Fusion.

Supports both SQLite (development/testing) and PostgreSQL+PostGIS (production).
Uses modern SQLAlchemy 2.0 style with type hints.
"""

import logging
import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# Configure module logger
logger = logging.getLogger(__name__)

# Database URL - read from environment or default to SQLite
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./cosmic_data_fusion.db"
)

# Determine database type
is_sqlite = SQLALCHEMY_DATABASE_URL.startswith("sqlite")
is_postgres = SQLALCHEMY_DATABASE_URL.startswith("postgresql")

# Configure engine based on database type
if is_sqlite:
    # SQLite: check_same_thread=False for FastAPI compatibility
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,  # Set True for SQL debugging
    )
    logger.info("Using SQLite database")
elif is_postgres:
    # PostgreSQL: Use connection pooling for production
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,  # Verify connections before use
        pool_size=10,        # Connection pool size
        max_overflow=20,     # Max overflow connections
        echo=False,          # Set True for SQL debugging
    )
    logger.info("Using PostgreSQL database with connection pooling")
else:
    raise ValueError(f"Unsupported database URL: {SQLALCHEMY_DATABASE_URL}")

# Session factory
# autocommit=False: Explicit transaction control
# autoflush=False: Manual flush control for batch operations
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session.
    
    Yields:
        SQLAlchemy Session instance
        
    Note:
        Session is automatically closed after request completion,
        even if an exception occurs.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database tables.
    
    Creates all tables defined in ORM models if they don't exist.
    Called at application startup.
    """
    # Import models to register them with Base.metadata
    from app import models  # noqa: F401
    
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully")
