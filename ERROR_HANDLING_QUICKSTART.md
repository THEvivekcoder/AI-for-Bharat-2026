# Error Handling Quick Start Guide

## Quick Reference for Developers

### 1. Raising Custom Exceptions

```python
from app.exceptions import (
    DataNotFoundException,
    InsufficientProfileDataException,
    AuthenticationException,
    RateLimitException,
    ExternalServiceException,
    DatabaseException
)

# Data not found
raise DataNotFoundException(
    message="Scheme not found",
    suggestions=["Search by category", "Try different keywords"]
)

# Missing profile data
raise InsufficientProfileDataException(
    message="Cannot check eligibility",
    missing_fields=["age", "income", "location"],
    can_proceed_without=False
)

# Authentication failed
raise AuthenticationException(
    message="Invalid OTP",
    remaining_attempts=2
)

# External service failed
raise ExternalServiceException(
    message="Mandi price API unavailable",
    service_name="mandi_api",
    retry_after_seconds=60
)

# Database error
raise DatabaseException(
    message="Failed to save scheme",
    operation="create"
)
```

### 2. Adding Retry Logic

```python
from app.utils.retry import exponential_backoff

# For async functions
@exponential_backoff(max_retries=3, base_delay=1.0)
async def fetch_external_data():
    # Your API call here
    response = await external_api.get_data()
    return response

# For sync functions
@exponential_backoff(max_retries=3, base_delay=1.0)
def fetch_data_sync():
    # Your API call here
    return external_api.get_data()
```

### 3. Graceful Degradation

```python
from app.utils.graceful_degradation import GracefulDegradation

# Try live data, fall back to cache
result = GracefulDegradation.with_cached_fallback(
    primary_func=lambda: get_live_prices(),
    cache_func=lambda key: get_cached_prices(key),
    cache_key="market_prices",
    max_cache_age_seconds=3600
)

# Return partial data if complete data unavailable
result = GracefulDegradation.with_partial_data(
    func=get_scheme_data,
    required_fields=["name", "description"],
    optional_fields=["benefits", "documents"]
)

# Use default response on failure
result = GracefulDegradation.with_default_response(
    func=get_recommendations,
    default_response={"recommendations": [], "message": "No recommendations available"}
)
```

### 4. Circuit Breaker Pattern

```python
from app.utils.retry import CircuitBreaker

# Create circuit breaker
breaker = CircuitBreaker(
    failure_threshold=5,      # Open after 5 failures
    recovery_timeout=60.0,    # Try again after 60 seconds
    expected_exception=Exception
)

# Use circuit breaker
try:
    result = breaker.call(external_api_function, arg1, arg2)
except ExternalServiceException as e:
    # Circuit is open, service unavailable
    logger.error(f"Service unavailable: {e.message}")
```

### 5. Database Error Handling

```python
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.exceptions import DatabaseException
from app.logging_config import logger

def create_record(data):
    try:
        record = Model(**data)
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error: {str(e)}")
        raise DatabaseException(
            message="Duplicate record or constraint violation",
            operation="create"
        )
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error: {str(e)}")
        raise DatabaseException(
            message="Database operation failed",
            operation="create"
        )
```

### 6. Translating Error Messages

```python
from app.services.error_translator import ErrorTranslator

# Get translated message
message = ErrorTranslator.translate("RATE_LIMIT_EXCEEDED", "hi")

# Get all translations
translations = ErrorTranslator.get_all_translations("DATA_NOT_FOUND")

# Add new translation
ErrorTranslator.add_translation(
    error_code="CUSTOM_ERROR",
    language="hi",
    message="कस्टम त्रुटि संदेश"
)
```

### 7. Configuring Rate Limits

Edit `app/middleware/rate_limiter.py`:

```python
self.limits = {
    "/api/your-endpoint": {
        "requests": 100,    # Max requests
        "window": 60,       # Time window in seconds
        "burst": 10         # Burst capacity
    }
}
```

### 8. Error Response Format

All errors return this structure:

```json
{
  "error": "ERROR_CODE",
  "message": "Human-readable message in user's language",
  "message_translations": {
    "en": "English message",
    "hi": "Hindi message",
    "bn": "Bengali message",
    "te": "Telugu message",
    "mr": "Marathi message"
  },
  "retry_allowed": true,
  "timestamp": "2024-01-20T10:30:00Z"
}
```

### 9. Testing Error Handling

```bash
# Start server
python app/main.py

# Run error handling tests
python scripts/test_error_handling.py
```

### 10. Common Patterns

**Pattern 1: Try-Catch with Custom Exception**
```python
try:
    result = risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {str(e)}")
    raise DataNotFoundException(
        message="Data unavailable",
        suggestions=["Try again later"]
    )
```

**Pattern 2: Retry with Fallback**
```python
from app.utils.retry import retry_with_fallback

result = await retry_with_fallback(
    primary_func=lambda: get_live_data(),
    fallback_func=lambda: get_cached_data(),
    max_retries=3
)
```

**Pattern 3: Offline Mode Check**
```python
from app.utils.graceful_degradation import GracefulDegradation

if not is_online():
    GracefulDegradation.offline_mode_response(
        feature_name="Market Prices",
        offline_alternatives=["View cached prices"],
        last_sync_time=last_sync
    )
```

## Error Codes Reference

| Error Code | Use Case | Retry Allowed |
|------------|----------|---------------|
| `VOICE_PROCESSING_ERROR` | Audio processing failures | Yes |
| `DATA_NOT_FOUND` | Missing data | No |
| `INSUFFICIENT_PROFILE_DATA` | Incomplete user profile | No |
| `AUTHENTICATION_FAILED` | Auth failures | Yes |
| `RATE_LIMIT_EXCEEDED` | Too many requests | Yes |
| `OFFLINE_FEATURE_UNAVAILABLE` | Requires internet | Yes |
| `EXTERNAL_SERVICE_ERROR` | External API failures | Yes |
| `VALIDATION_ERROR` | Invalid request data | No |
| `DATABASE_ERROR` | Database failures | Yes |
| `CACHE_ERROR` | Cache failures | Yes |

## Best Practices

1. ✅ Always use custom exceptions
2. ✅ Add retry logic for external APIs
3. ✅ Implement graceful degradation
4. ✅ Log errors with context
5. ✅ Provide helpful error messages
6. ✅ Include suggestions for resolution
7. ✅ Use circuit breakers for unreliable services
8. ✅ Test error scenarios
9. ✅ Monitor error rates
10. ✅ Document error handling

## Need Help?

- Full documentation: `docs/error_handling_implementation.md`
- Test examples: `scripts/test_error_handling.py`
- Implementation details: `app/middleware/`, `app/utils/`, `app/exceptions.py`
