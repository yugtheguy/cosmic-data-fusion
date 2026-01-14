"""
Pytest configuration and fixtures for all tests.

Ensures tests use PostgreSQL+PostGIS instead of SQLite,
and applies Alembic migrations before each test session.
"""

import os
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.main import app
from app.database import Base, get_db
from fastapi.testclient import TestClient


# Use PostgreSQL for tests (read from DATABASE_URL env var)
TEST_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:Lokesh%406789@localhost:5432/cosmic"
)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Set up test database and apply migrations at session start.
    This runs once per test session and applies Alembic migrations.
    """
    from alembic.config import Config
    from alembic.command import upgrade

    # Apply migrations to test DB
    alembic_cfg = Config("alembic.ini")
    # Escape % signs for ConfigParser (% -> %%)
    escaped_url = TEST_DATABASE_URL.replace("%", "%%")
    alembic_cfg.set_main_option("sqlalchemy.url", escaped_url)
    
    try:
        upgrade(alembic_cfg, "head")
        print("\n✅ Alembic migrations applied to test database")
    except Exception as e:
        print(f"\n⚠️  Migration warning: {e}")
        # Continue anyway; tables might already exist


@pytest.fixture
def db_engine():
    """Create a test database engine."""
    engine = create_engine(TEST_DATABASE_URL, echo=False)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine) -> Session:
    """Create a new database session for a test."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()

    # Bind session to app for this test
    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session: Session) -> TestClient:
    """Create a test client with overridden DB dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
