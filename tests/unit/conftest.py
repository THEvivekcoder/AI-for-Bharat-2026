"""Pytest configuration for unit tests."""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set test environment variables
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
os.environ['ENVIRONMENT'] = 'test'
os.environ['LOG_LEVEL'] = 'ERROR'
os.environ['SCHEMES_TABLE'] = 'test-schemes-table'
os.environ['PROFILES_TABLE'] = 'test-profiles-table'
os.environ['USERS_TABLE'] = 'test-users-table'
