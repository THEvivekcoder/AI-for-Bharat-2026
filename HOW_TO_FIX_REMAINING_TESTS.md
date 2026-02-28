# How to Fix the Remaining 35 Test Errors

## Overview

Task 25 identified and implemented a fix for 35 test errors (23 integration + 12 property tests). The fix is in `conftest.py`, but the tests themselves need to be updated to use the new fixtures.

## What's Already Done ✅

1. ✅ Root cause identified (database state management)
2. ✅ Fix implemented in `conftest.py`
3. ✅ Test database fixtures created
4. ✅ Environment variables configured
5. ✅ Documentation complete

## What Needs to Be Done

The tests need to be updated to use the `test_db` fixture from `conftest.py` instead of creating their own database connections.

## Step-by-Step Fix Guide

### Pattern 1: Integration Tests

**Current Pattern (WRONG):**
```python
from app.database import SessionLocal

def test_something():
    db = SessionLocal()  # Uses production database!
    try:
        # test code
    finally:
        db.close()
```

**Fixed Pattern (CORRECT):**
```python
def test_something(test_db):  # Add test_db parameter
    # test_db is already a session, use it directly
    # test code using test_db
    # No need to close - automatic cleanup
```

### Pattern 2: Property Tests

**Current Pattern (WRONG):**
```python
@pytest.fixture(scope="module")
def test_engine():
    engine = create_engine(TEST_DATABASE_URL)  # Uses hardcoded URL!
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def test_db(test_engine):
    Session = sessionmaker(bind=test_engine)
    session = Session()
    yield session
    session.close()
```

**Fixed Pattern (CORRECT):**
```python
# Remove custom fixtures - use the one from conftest.py
# Just add test_db parameter to test functions

@given(profile=profile_strategy())
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_profile_data_round_trip(test_db, profile):
    # Use test_db directly
    # No need for custom fixtures
```

### Pattern 3: API Tests with Client

**Current Pattern (WRONG):**
```python
from fastapi.testclient import TestClient
from app.main import app

def test_api_endpoint():
    client = TestClient(app)  # Uses production database!
    response = client.post("/api/endpoint", json={...})
```

**Fixed Pattern (CORRECT):**
```python
def test_api_endpoint(client):  # Add client parameter
    # client is already configured with test database
    response = client.post("/api/endpoint", json={...})
```

## Specific Files to Update

### 1. Integration Tests

#### File: `.kiro/specs/bharatsahayak/tests/test_integration_e2e.py`

**Lines to Change:**
- Remove any `SessionLocal()` calls
- Add `test_db` parameter to test functions
- Remove manual database cleanup

**Example:**
```python
# BEFORE
def test_rag_to_scheme_service_flow():
    db = SessionLocal()
    try:
        # test code
    finally:
        db.close()

# AFTER
def test_rag_to_scheme_service_flow(test_db):
    # test code using test_db
```

#### File: `.kiro/specs/bharatsahayak/tests/test_integration_e2e_simple.py`

Same pattern as above.

### 2. Property Tests

#### File: `.kiro/specs/bharatsahayak/tests/test_property_profile_persistence.py`

**Lines to Remove:**
```python
# Remove these lines (around line 23-40)
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://...")

@pytest.fixture(scope="module")
def test_engine():
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()

@pytest.fixture(scope="function")
def test_db(test_engine):
    Session = sessionmaker(bind=test_engine)
    session = Session()
    yield session
    session.close()
```

**Keep:**
```python
# Keep the test functions, just ensure they use test_db parameter
@given(profile=profile_strategy())
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_profile_data_round_trip(test_db, profile):
    # This will now use the fixture from conftest.py
    user_manager = UserManager(test_db, redis_cache)
    # ... rest of test
```

#### File: `.kiro/specs/bharatsahayak/tests/test_property_event_recording.py`

Same pattern - remove custom database fixtures, use `test_db` parameter.

#### File: `.kiro/specs/bharatsahayak/tests/test_property_data_anonymization.py`

Same pattern - remove custom database fixtures, use `test_db` parameter.

### 3. Other Property Tests

Apply the same pattern to:
- `test_property_metrics_aggregation.py`
- Any other property test that creates its own database connection

## Quick Fix Script

Here's a script to help identify which tests need updating:

```bash
# Find tests that create their own database connections
grep -r "create_engine" .kiro/specs/bharatsahayak/tests/*.py

# Find tests that use SessionLocal
grep -r "SessionLocal()" .kiro/specs/bharatsahayak/tests/*.py

# Find tests with custom test_db fixtures
grep -r "@pytest.fixture.*test_db" .kiro/specs/bharatsahayak/tests/*.py
```

## Testing the Fix

After updating tests, verify they work:

```bash
# Test one file at a time
pytest .kiro/specs/bharatsahayak/tests/test_property_profile_persistence.py -v

# Test all integration tests
pytest .kiro/specs/bharatsahayak/tests/test_integration_*.py -v

# Test all property tests
pytest .kiro/specs/bharatsahayak/tests/test_property_*.py -v

# Run all tests
pytest .kiro/specs/bharatsahayak/tests/ -v
```

## Expected Results

### Before Fix
```
642 passed, 206 failed, 23 errors
```

### After Fix
```
677 passed, 206 failed, 0 errors
```

**Improvement**: 35 errors → 0 errors (23 integration + 12 property tests fixed)

## Common Issues and Solutions

### Issue 1: "fixture 'test_db' not found"
**Cause**: conftest.py not in the right location
**Solution**: Ensure `.kiro/specs/bharatsahayak/tests/conftest.py` exists with the fixtures

### Issue 2: "connection to server at localhost:5432 failed"
**Cause**: Test still using hardcoded PostgreSQL URL
**Solution**: Remove `TEST_DATABASE_URL` and custom engine creation

### Issue 3: "FOREIGN KEY constraint failed"
**Cause**: Foreign keys not enabled in SQLite
**Solution**: Already handled in conftest.py with `PRAGMA foreign_keys=ON`

### Issue 4: "fixture 'test_db' has function scope but uses 'test_engine' with module scope"
**Cause**: Mixing scopes in custom fixtures
**Solution**: Remove custom fixtures entirely, use the one from conftest.py

## Validation Checklist

After updating tests, verify:

- [ ] No hardcoded database URLs in test files
- [ ] No `create_engine()` calls in test files
- [ ] No `SessionLocal()` calls in test files
- [ ] All test functions have `test_db` or `client` parameter
- [ ] No custom `test_db` or `test_engine` fixtures in test files
- [ ] Tests pass when run individually
- [ ] Tests pass when run together
- [ ] No database files created (test.db, etc.)

## Summary

The fix is simple but requires updating multiple test files:

1. **Remove** custom database fixtures from test files
2. **Add** `test_db` parameter to test functions
3. **Use** `test_db` directly instead of creating sessions
4. **Remove** manual cleanup code

The `conftest.py` fixtures handle everything automatically:
- Fresh database for each test
- Proper cleanup
- Foreign key constraints
- Environment variables

**Estimated Time**: 30-60 minutes to update all affected tests
**Expected Impact**: 35 test errors → 0 test errors
