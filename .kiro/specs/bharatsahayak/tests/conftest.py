"""
Pytest configuration for BharatSahayak tests

Sets up test environment variables.
Database fixtures are in root conftest.py.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Set environment for testing
os.environ.setdefault("TESTING", "1")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("ENCRYPTION_KEY", "test-encryption-key-32-bytes-long!")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-key-for-testing-only")
