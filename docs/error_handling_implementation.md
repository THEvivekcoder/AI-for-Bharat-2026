# Error Handling and Rate Limiting Implementation

## Overview

This document describes the comprehensive error handling and rate limiting implementation for BharatSahayak, including multilingual error messages, graceful degradation, and retry logic.

## Components

### 1. Error Response Models (`app/schemas/errors.py`)

Structured error response models for different error categories:

- `ErrorResponse`: Base error response with common fields
- `VoiceProcessingError`: Voice-specific errors
- `DataNotFoundError`: Missing data errors
- `InsufficientProfileDataError`: Incomplete profile errors
- `AuthenticationError`: Authentication failures
- `RateLimitError`: Rate limiting errors
- `OfflineFeatureUnavailableError`: Offline mode errors
- `ExternalServiceError`: External service failures
- `ValidationError`: Request validation errors
- `DatabaseError`: Database operation errors
- `CacheError`: Cache operation errors

### 2. Error Translation Service (`app/services/error_translator.py`)

Provides multilingual error messages for supported languages:

- English (en)
- Hindi (hi)
- Bengali (bn)
- Telugu (te)
- Marathi (mr)

**Usage:**
```python
from app.services.error_translator import ErrorTranslator

# Get translated message
message = ErrorTranslator.translate("RATE_LIMIT_EXCEEDED", "hi")

# Get all translations
translations = ErrorTranslator.get_all_translations("DATA_NOT_FOUND")
```

### 3. Custom Exceptions (`app/exceptions.py`)

Custom exception classes that map to error response models:

```python
from app.exceptions import DataNotFoundException, RateLimitException

# Raise custom exception
raise DataNotFoundException(
    message="Scheme not found",
    suggestions=["Search by category", "Try different keywords"]
)
```

### 4. Rate Limiting Middleware (`app/middleware/rate_limiter.py`)

Token bucket rate limiter with configurable limits per endpoint:

**Default Limits:**
- Voice endpoints: 100 requests/minute
- AI/RAG endpoints: 50 requests/minute
- Scheme endpoints: 60 requests/minute
- Authentication: 5 requests/5 minutes
- Health endpoints: 80 requests/minute

**Features:**
- Per-user and per-IP rate limiting
- Burst capacity for short spikes
- Automatic cleanup of old entries
- Rate limit headers in responses

**Response Headers:**
```
X-RateLimit-Limit: 60
X-RateLimit-Window: 60
Retry-After: 30
```

### 5. Retry Utilities (`app/utils/retry.py`)

Exponential backoff retry logic for external API calls:

```python
from app.utils.retry import exponential_backoff

@exponential_backoff(max_retries=3, base_delay=1.0)
async def call_external_api():
    # API call that may fail
    pass
```

**Circuit Breaker Pattern:**
```python
from app.utils.retry import CircuitBreaker

breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60.0)
result = breaker.call(external_function, arg1, arg2)
```

### 6. Graceful Degradation (`app/utils/graceful_degradation.py`)

Strategies for handling failures gracefully:

**Cached Fallback:**
```python
from app.utils.graceful_degradation import GracefulDegradation

result = GracefulDegradation.with_cached_fallback(
    primary_func=get_live_data,
    cache_func=get_cached_data,
    cache_key="market_prices",
    max_cache_age_seconds=3600
)
```

**Partial Data:**
```python
result = GracefulDegradation.with_partial_data(
    func=get_scheme_data,
    required_fields=["name", "description"],
    optional_fields=["benefits", "documents"]
)
```

**Default Response:**
```python
result = GracefulDegradation.with_default_response(
    func=get_recommendations,
    default_response={"recommendations": [], "message": "Using defaults"}
)
```

## Error Response Format

All errors follow a consistent structure:

```json
{
  "error": "ERROR_CODE",
  "message": "Human-readable message in requested language",
  "message_translations": {
    "en": "English message",
    "hi": "Hindi message",
    "bn": "Bengali message",
    "te": "Telugu message",
    "mr": "Marathi message"
  },
  "retry_allowed": true,
  "timestamp": "2024-01-20T10:30:00Z",
  // Additional error-specific fields
}
```

## Error Categories

### 1. Voice Processing Errors

**Error Code:** `VOICE_PROCESSING_ERROR`

**Scenarios:**
- Audio quality too poor
- Unsupported language
- Invalid audio format
- TTS synthesis failure

**Response:**
```json
{
  "error": "VOICE_PROCESSING_ERROR",
  "message": "Unable to process audio...",
  "supported_languages": ["hi", "en", "bn", "te", "mr"],
  "audio_quality_score": 0.45,
  "retry_allowed": true
}
```

### 2. Data Not Found Errors

**Error Code:** `DATA_NOT_FOUND`

**Scenarios:**
- Scheme not found
- Market prices unavailable
- Health facilities not in area
- Job postings expired

**Response:**
```json
{
  "error": "DATA_NOT_FOUND",
  "message": "No market prices available...",
  "alternative_data": {
    "last_available_date": "2024-01-15",
    "last_available_price": 2500
  },
  "suggestions": ["Try nearby districts", "Check again tomorrow"],
  "retry_allowed": false
}
```

### 3. Rate Limiting Errors

**Error Code:** `RATE_LIMIT_EXCEEDED`

**Response:**
```json
{
  "error": "RATE_LIMIT_EXCEEDED",
  "message": "Too many requests...",
  "retry_after_seconds": 60,
  "quota_reset_time": "2024-01-20T10:30:00Z",
  "current_usage": 65,
  "quota_limit": 60,
  "retry_allowed": true
}
```

### 4. Authentication Errors

**Error Code:** `AUTHENTICATION_FAILED`

**Response:**
```json
{
  "error": "AUTHENTICATION_FAILED",
  "message": "Invalid OTP...",
  "remaining_attempts": 2,
  "retry_allowed": true
}
```

### 5. Offline Feature Errors

**Error Code:** `OFFLINE_FEATURE_UNAVAILABLE`

**Response:**
```json
{
  "error": "OFFLINE_FEATURE_UNAVAILABLE",
  "message": "This feature requires internet...",
  "offline_alternatives": ["View cached schemes", "Access saved content"],
  "last_sync_time": "2024-01-19T08:00:00Z",
  "retry_allowed": true
}
```

## Middleware Order

Middleware is applied in this order (important for proper error handling):

1. CORS Middleware
2. Rate Limiting Middleware
3. Logging Middleware
4. Error Handling Middleware

## Testing

### Run Error Handling Tests

```bash
# Start the server
python app/main.py

# In another terminal, run tests
python scripts/test_error_handling.py
```

### Test Scenarios

1. **Error Translations**: Verify multilingual error messages
2. **Rate Limiting**: Trigger rate limits with rapid requests
3. **Validation Errors**: Send invalid data to endpoints
4. **Error Structure**: Verify all required fields present
5. **Graceful Degradation**: Test fallback mechanisms

## Best Practices

### 1. Always Use Custom Exceptions

```python
# Good
from app.exceptions import DataNotFoundException

raise DataNotFoundException(
    message="Scheme not found",
    suggestions=["Search by category"]
)

# Avoid
raise Exception("Scheme not found")
```

### 2. Add Retry Logic for External APIs

```python
from app.utils.retry import exponential_backoff

@exponential_backoff(max_retries=3)
async def fetch_mandi_prices():
    # External API call
    pass
```

### 3. Implement Graceful Degradation

```python
from app.utils.graceful_degradation import GracefulDegradation

# Try live data, fall back to cache
result = GracefulDegradation.with_cached_fallback(
    primary_func=get_live_prices,
    cache_func=get_cached_prices,
    cache_key="prices"
)
```

### 4. Log Errors Appropriately

```python
from app.logging_config import logger

try:
    result = risky_operation()
except Exception as e:
    logger.error(f"Operation failed: {str(e)}")
    raise
```

### 5. Provide Helpful Error Messages

```python
# Good - actionable message
raise DataNotFoundException(
    message="No schemes found for your location",
    suggestions=[
        "Try searching in nearby districts",
        "Check central government schemes",
        "Contact support for assistance"
    ]
)

# Avoid - vague message
raise Exception("Not found")
```

## Configuration

### Rate Limit Configuration

Edit `app/middleware/rate_limiter.py` to adjust limits:

```python
self.limits = {
    "/api/voice-to-text": {"requests": 100, "window": 60, "burst": 10},
    "/api/ask": {"requests": 50, "window": 60, "burst": 5},
    # Add more endpoints...
}
```

### Retry Configuration

Adjust retry parameters in decorators:

```python
@exponential_backoff(
    max_retries=3,        # Number of retries
    base_delay=1.0,       # Initial delay
    max_delay=60.0,       # Maximum delay
    exponential_base=2.0  # Backoff multiplier
)
```

## Monitoring

### Key Metrics to Monitor

1. **Error Rates**: Track errors by type and endpoint
2. **Rate Limit Hits**: Monitor rate limiting frequency
3. **Retry Attempts**: Track external API retry rates
4. **Response Times**: Monitor impact of error handling
5. **Cache Hit Rates**: Track graceful degradation usage

### Logging

All errors are logged with appropriate levels:

- `logger.error()`: Unexpected errors, failures
- `logger.warning()`: Expected errors, rate limits
- `logger.info()`: Normal operations, recoveries

## Future Enhancements

1. **Distributed Rate Limiting**: Use Redis for multi-instance rate limiting
2. **Error Analytics Dashboard**: Visualize error patterns
3. **Adaptive Rate Limits**: Adjust limits based on load
4. **More Languages**: Add support for additional Indian languages
5. **Error Recovery Suggestions**: AI-powered error resolution hints
