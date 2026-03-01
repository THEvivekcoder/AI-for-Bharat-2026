# Core Data Access Layer

This directory contains the DynamoDB repository classes for the BharatSahayak application.

## Overview

The core data access layer provides a clean abstraction over DynamoDB operations with:
- CRUD operations for all data models
- Error handling for DynamoDB exceptions
- Serialization/deserialization of Pydantic models
- Search and filter capabilities
- Support for both query (with GSI) and scan operations

## Repository Classes

### BaseRepository

Base class providing common DynamoDB operations:
- Connection management to DynamoDB
- Error handling and logging
- Serialization/deserialization of datetime fields
- Common exception types: `DynamoDBRepositoryError`, `ItemNotFoundError`

### UserRepository

Manages user profile CRUD operations in the `Users` table.

**Key Methods:**
- `create(user_profile)` - Create a new user profile
- `get(user_id)` - Retrieve user by ID
- `update(user_profile)` - Update existing user
- `delete(user_id)` - Delete user profile
- `get_by_phone_number(phone_number)` - Find user by phone (requires GSI or falls back to scan)

**Example Usage:**
```python
from src.core import UserRepository
from src.models.user import UserProfile
from src.models.location import Location

# Initialize repository
user_repo = UserRepository(table_name="Users", region_name="us-east-1")

# Create a user
user = UserProfile(
    user_id="user_123",
    phone_number="+919876543210",
    language="hi",
    location=Location(state="Maharashtra", district="Pune", pincode="411014")
)
user_repo.create(user)

# Retrieve user
retrieved_user = user_repo.get("user_123")

# Update user
retrieved_user.age = 35
user_repo.update(retrieved_user)

# Find by phone number
user = user_repo.get_by_phone_number("+919876543210")
```

### SchemeRepository

Manages government scheme data with search and filter capabilities.

**Key Methods:**
- `create(scheme)` - Create a new scheme
- `get(scheme_id)` - Retrieve scheme by ID
- `update(scheme)` - Update existing scheme
- `delete(scheme_id)` - Delete scheme
- `search_schemes(query, filters, limit)` - Search schemes with filters
- `get_all_schemes(category, limit)` - Get all schemes, optionally by category
- `get_schemes_by_state(state, limit)` - Get schemes for a specific state

**SchemeFilters:**
- `category` - Filter by scheme category (agriculture, health, education, etc.)
- `state` - Filter by state (None or empty string for central schemes)
- `department` - Filter by government department
- `keywords` - List of keywords to search in name/description

**Example Usage:**
```python
from src.core import SchemeRepository, SchemeFilters
from src.models.scheme import Scheme
from src.models.eligibility import EligibilityCriteria

# Initialize repository
scheme_repo = SchemeRepository(table_name="Schemes", region_name="us-east-1")

# Search schemes by category
filters = SchemeFilters(category="agriculture")
schemes = scheme_repo.search_schemes(filters=filters)

# Search with keywords
schemes = scheme_repo.search_schemes(query="farmer", filters=filters)

# Get schemes for a state
maharashtra_schemes = scheme_repo.get_schemes_by_state("Maharashtra")

# Get central schemes (state=None)
central_schemes = scheme_repo.get_schemes_by_state(None)
```

### ProfileRepository

Specialized repository for user profile management with additional business logic.

**Key Methods:**
- `get_profile(user_id)` - Retrieve user profile
- `create_profile(user_profile)` - Create new profile
- `update_profile(user_id, updates, create_if_not_exists)` - Update specific fields
- `delete_profile(user_id)` - Delete profile
- `update_location(user_id, location)` - Update user location
- `update_preferences(user_id, preferences)` - Update user preferences
- `profile_exists(user_id)` - Check if profile exists

**Example Usage:**
```python
from src.core import ProfileRepository

# Initialize repository
profile_repo = ProfileRepository(table_name="UserProfiles", region_name="us-east-1")

# Get profile
profile = profile_repo.get_profile("user_123")

# Update specific fields
profile_repo.update_profile("user_123", {"age": 36, "occupation": "teacher"})

# Update location
new_location = {
    "state": "Karnataka",
    "district": "Bangalore",
    "pincode": "560001"
}
profile_repo.update_location("user_123", new_location)

# Update preferences
new_prefs = {
    "notification_enabled": False,
    "preferred_categories": ["agriculture", "health"]
}
profile_repo.update_preferences("user_123", new_prefs)

# Check if profile exists
if profile_repo.profile_exists("user_123"):
    print("Profile exists")
```

## Error Handling

All repositories use consistent error handling:

**ItemNotFoundError:**
- Raised when a requested item doesn't exist
- Raised when conditional checks fail (e.g., updating non-existent item)

**DynamoDBRepositoryError:**
- Base exception for all DynamoDB-related errors
- Includes detailed error messages from AWS
- Logs errors for debugging

**Example Error Handling:**
```python
from src.core import UserRepository, ItemNotFoundError, DynamoDBRepositoryError

user_repo = UserRepository()

try:
    user = user_repo.get("nonexistent_user")
except ItemNotFoundError as e:
    print(f"User not found: {e}")
except DynamoDBRepositoryError as e:
    print(f"Database error: {e}")
```

## DynamoDB Table Requirements

### Users Table
- **Partition Key:** `user_id` (String)
- **GSI (Optional):** `phone_number-index` on `phone_number` for efficient lookups

### Schemes Table
- **Partition Key:** `scheme_id` (String)
- **GSI (Recommended):** `category-index` on `category` for efficient category queries

### UserProfiles Table
- **Partition Key:** `user_id` (String)

## Testing

Unit tests are available in `tests/unit/`:
- `test_user_repository.py` - Tests for UserRepository
- `test_scheme_repository.py` - Tests for SchemeRepository
- `test_profile_repository.py` - Tests for ProfileRepository

Run tests:
```bash
pytest tests/unit/test_user_repository.py -v
pytest tests/unit/test_scheme_repository.py -v
pytest tests/unit/test_profile_repository.py -v
```

## Configuration

Repositories can be configured with:
- `table_name` - DynamoDB table name
- `region_name` - AWS region (default: us-east-1)

AWS credentials should be configured via:
- Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
- AWS credentials file (~/.aws/credentials)
- IAM role (when running on AWS services)

## Performance Considerations

1. **Use GSI for Queries:** When available, repositories use Global Secondary Indexes for efficient queries. If GSI is not available, they fall back to table scans (less efficient).

2. **Limit Results:** All search methods accept a `limit` parameter to control the number of results returned.

3. **Batch Operations:** For bulk operations, consider using DynamoDB batch write operations (not currently implemented in base repositories).

4. **Caching:** Consider implementing caching layer (Redis/ElastiCache) for frequently accessed data.

## Future Enhancements

- Batch read/write operations
- Pagination support for large result sets
- Query result caching
- Conditional updates with optimistic locking
- DynamoDB Streams integration for change tracking
