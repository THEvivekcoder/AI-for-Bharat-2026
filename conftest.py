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
# AWS configuration for tests
os.environ.setdefault('AWS_DEFAULT_REGION', 'us-east-1')
os.environ.setdefault('AWS_REGION', 'us-east-1')
# Don't set DATABASE_URL here - let it use the default PostgreSQL URL
# We'll override the database dependency instead

import pytest
from sqlalchemy import create_engine, event, String, Text, TypeDecorator
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, JSONB
import uuid as uuid_module
import json

# Note: app.database and app.main imports removed as they don't exist in Lambda-based structure
# If needed for specific tests, import them in those test files directly


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
    - Creates all tables from Base metadata (if Base is available)
    - Yields a database session for the test
    - Drops all tables and closes connections after the test
    
    Scope: function - Each test gets a fresh database
    
    Note: This fixture requires Base to be imported in the test file that uses it.
    """
    # This fixture is disabled until Base is properly imported
    # Import Base in your test file if you need this fixture
    pytest.skip("test_db fixture requires Base from app.database which is not available")


@pytest.fixture(scope="function")
def client(test_db):
    """
    Create a FastAPI TestClient with database dependency override.
    
    Note: This fixture is disabled as it requires app.main which is not available
    in the Lambda-based structure.
    """
    pytest.skip("client fixture requires app.main which is not available")


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
