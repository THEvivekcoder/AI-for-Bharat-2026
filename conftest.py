"""
Pytest configuration and fixtures for BharatSahayak tests.

This file provides test database fixtures that ensure proper isolation
between tests by using in-memory SQLite databases with proper cleanup.
"""

import os
import base64

# Set test environment variables BEFORE any imports
# This must happen before app.main is imported
test_key = b'test_encryption_key_32bytes_long'
os.environ.setdefault('ENCRYPTION_KEY', base64.b64encode(test_key).decode('utf-8'))
os.environ.setdefault('JWT_SECRET', 'test-jwt-secret-key-for-testing-only')
os.environ.setdefault('TESTING', '1')
os.environ.setdefault('REDIS_URL', 'redis://localhost:6379/1')
# Don't set DATABASE_URL here - let it use the default PostgreSQL URL
# We'll override the database dependency instead

import pytest
from sqlalchemy import create_engine, event, String, Text, TypeDecorator
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, JSONB
from fastapi.testclient import TestClient
import uuid as uuid_module
import json

from app.database import Base, get_db
from app.main import app


# Custom UUID type for SQLite compatibility
class SQLiteUUID(TypeDecorator):
    """Platform-independent UUID type for SQLite"""
    impl = String
    cache_ok = True
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid_module.UUID):
            return str(value)
        return str(value)
    
    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, uuid_module.UUID):
            return uuid_module.UUID(value)
        return value


# Custom JSONB type for SQLite compatibility
class SQLiteJSONB(TypeDecorator):
    """Platform-independent JSONB type for SQLite"""
    impl = Text
    cache_ok = True
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        return json.dumps(value)
    
    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return json.loads(value)


@pytest.fixture(scope="function")
def test_db():
    """
    Create a fresh in-memory SQLite database for each test function.
    
    This fixture:
    - Creates a new in-memory SQLite database
    - Creates all tables from Base metadata
    - Yields a database session for the test
    - Drops all tables and closes connections after the test
    
    Scope: function - Each test gets a fresh database
    """
    # Create in-memory SQLite engine with StaticPool to prevent connection issues
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False  # Set to True for SQL debugging
    )
    
    # Enable foreign key constraints for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    # Replace PostgreSQL-specific types with SQLite-compatible types
    @event.listens_for(Base.metadata, "before_create")
    def receive_before_create(target, connection, **kw):
        """Replace PostgreSQL-specific types with SQLite-compatible types"""
        if connection.dialect.name == 'sqlite':
            for table in target.tables.values():
                for column in table.columns:
                    if isinstance(column.type, PostgresUUID):
                        column.type = SQLiteUUID()
                    elif isinstance(column.type, JSONB):
                        column.type = SQLiteJSONB()
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session factory
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
    
    # Create session
    db = TestingSessionLocal()
    
    try:
        yield db
    finally:
        # Cleanup
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture(scope="function")
def client(test_db):
    """
    Create a FastAPI TestClient with database dependency override.
    
    This fixture:
    - Overrides the get_db dependency to use test_db
    - Creates a TestClient for making API requests
    - Cleans up dependency overrides after the test
    
    Args:
        test_db: The test database session fixture
    
    Returns:
        TestClient: FastAPI test client with test database
    """
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    # Override the database dependency
    app.dependency_overrides[get_db] = override_get_db
    
    # Create test client
    test_client = TestClient(app)
    
    yield test_client
    
    # Cleanup: Remove dependency override
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def db_session(test_db):
    """
    Alias for test_db for backward compatibility.
    
    Some tests may use db_session instead of test_db.
    """
    return test_db


@pytest.fixture(scope="session")
def test_settings():
    """
    Provide test-specific settings.
    
    Returns:
        dict: Test configuration settings
    """
    return {
        "database_url": "sqlite:///:memory:",
        "testing": True,
        "debug": False,
        "encryption_key": "test-encryption-key-32-bytes-long!",
        "jwt_secret": "test-jwt-secret-key",
        "jwt_algorithm": "HS256",
        "jwt_expiration_minutes": 30
    }


# Configure pytest to show more detailed output for failed assertions
def pytest_configure(config):
    """Configure pytest with custom settings."""
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "property: mark test as a property-based test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


# Add custom assertion rewriting for better error messages
pytest.register_assert_rewrite("app.tests")
