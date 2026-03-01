"""
Pytest configuration for property-based tests.

This conftest is specific to property tests and doesn't require
the full application setup.
"""

import pytest

# Configure pytest markers for property tests
def pytest_configure(config):
    """Configure pytest with custom settings for property tests."""
    config.addinivalue_line(
        "markers", "property: mark test as a property-based test"
    )
