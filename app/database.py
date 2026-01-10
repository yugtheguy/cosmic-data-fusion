"""
Database configuration for COSMIC Data Fusion.

SQLAlchemy setup with SQLite backend, designed with PostgreSQL-compatible patterns.
Uses modern SQLAlchemy 2.0 style with type hints.
"""

import logging
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# Configure module logger
logger = logging.getLogger(__name__)

# SQLite database path
# check_same_thread=False required for FastAPI's multi-threaded async handling
# Safe because SQLAlchemy Session handles thread-safety internally
DATABASE_URL = "sqlite:///./cosmic_data_fusion.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,  # Set True for SQL debugging
)

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
