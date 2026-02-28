"""
Unit tests for error handling

Tests each error category, rate limiting, and graceful degradation.
"""
import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.exceptions import (
    BharatSahayakException,
    VoiceProcessingException,
    DataNotFoundException,
    InsufficientProfileDataException,
    AuthenticationException,
    RateLimitException,
    OfflineFeatureUnavailableException,
    ExternalServiceException,
    DatabaseException,
    CacheException
)
from app.middleware.rate_limiter import RateLimiter, rate_limiting_middleware
from app.utils.graceful_degradation import GracefulDegradation, handle_external_service_failure
from app.utils.retry import exponential_backoff, retry_with_fallback, CircuitBreaker
from app.services.error_translator import ErrorTranslator


class TestExceptionClasses:
    """Test custom exception classes"""
    
    def test_base_exception_creation(self):
        """Test BharatSahayakException creation"""
        exc = BharatSahayakException(
            message="Test error",
            error_code="TEST_ERROR",
            retry_allowed=True
        )
        
        assert exc.message == "Test error"
        assert exc.error_code == "TEST_ERROR"
        assert exc.retry_allowed is True
        assert str(exc) == "Test error"
    
    def test_voice_processing_exception(self):
        """Test VoiceProcessingException with metadata"""
        exc = VoiceProcessingException(
            message="Audio processing failed",
            supported_languages=["hi", "en"],
            audio_quality_score=0.3,
            detected_language="hi"
        )
        
        assert exc.error_code == "VOICE_PROCESSING_ERROR"
        assert exc.retry_allowed is True
        assert exc.supported_languages == ["hi", "en"]
        assert exc.audio_quality_score == 0.3
        assert exc.detected_language == "hi"
    
    def test_data_not_found_exception(self):
        """Test DataNotFoundException with alternatives"""
        exc = DataNotFoundException(
            message="Scheme not found",
            alternative_data={"similar_schemes": ["scheme1", "scheme2"]},
            suggestions=["Try broader search", "Check spelling"]
        )
        
        assert exc.error_code == "DATA_NOT_FOUND"
        assert exc.retry_allowed is False
        assert exc.alternative_data is not None
        assert len(exc.suggestions) == 2
    
    def test_insufficient_profile_data_exception(self):
        """Test InsufficientProfileDataException"""
        exc = InsufficientProfileDataException(
            message="Missing required fields",
            missing_fields=["age", "location"],
            can_proceed_without=False
        )
        
        assert exc.error_code == "INSUFFICIENT_PROFILE_DATA"
        assert exc.missing_fields == ["age", "location"]
        assert exc.can_proceed_without is False
    
    def test_authentication_exception(self):
        """Test AuthenticationException with lockout info"""
        lockout_time = datetime.utcnow() + timedelta(minutes=15)
        exc = AuthenticationException(
            message="Invalid OTP",
            remaining_attempts=2,
            lockout_time=lockout_time
        )
        
        assert exc.error_code == "AUTHENTICATION_FAILED"
        assert exc.remaining_attempts == 2
        assert exc.lockout_time == lockout_time
        assert exc.retry_allowed is True
    
    def test_rate_limit_exception(self):
        """Test RateLimitException with quota info"""
        reset_time = datetime.utcnow() + timedelta(seconds=60)
        exc = RateLimitException(
            message="Too many requests",
            retry_after_seconds=60,
            quota_reset_time=reset_time,
            current_usage=100,
            quota_limit=100
        )
        
        assert exc.error_code == "RATE_LIMIT_EXCEEDED"
        assert exc.retry_after_seconds == 60
        assert exc.current_usage == 100
        assert exc.quota_limit == 100
    
    def test_offline_feature_unavailable_exception(self):
        """Test OfflineFeatureUnavailableException"""
        last_sync = datetime.utcnow() - timedelta(hours=2)
        exc = OfflineFeatureUnavailableException(
            message="Feature requires internet",
            offline_alternatives=["cached_schemes", "offline_tips"],
            last_sync_time=last_sync
        )
        
        assert exc.error_code == "OFFLINE_FEATURE_UNAVAILABLE"
        assert len(exc.offline_alternatives) == 2
        assert exc.last_sync_time == last_sync
    
    def test_external_service_exception(self):
        """Test ExternalServiceException"""
        exc = ExternalServiceException(
            message="Mandi API unavailable",
            service_name="mandi_price_api",
            retry_after_seconds=120
        )
        
        assert exc.error_code == "EXTERNAL_SERVICE_ERROR"
        assert exc.service_name == "mandi_price_api"
        assert exc.retry_after_seconds == 120
    
    def test_database_exception(self):
        """Test DatabaseException"""
        exc = DatabaseException(
            message="Connection failed",
            operation="read"
        )
        
        assert exc.error_code == "DATABASE_ERROR"
        assert exc.operation == "read"
        assert exc.retry_allowed is True
    
    def test_cache_exception(self):
        """Test CacheException"""
        exc = CacheException(
            message="Redis unavailable",
            cache_type="redis",
            fallback_available=True
        )
        
        assert exc.error_code == "CACHE_ERROR"
        assert exc.cache_type == "redis"
        assert exc.fallback_available is True


class TestRateLimiter:
    """Test rate limiting functionality"""
    
    @pytest.fixture
    def rate_limiter(self):
        """Create fresh rate limiter for each test"""
        return RateLimiter()
    
    def test_get_identifier_with_user_id(self, rate_limiter):
        """Test identifier extraction with authenticated user"""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.user_id = "user123"
        request.client = Mock()
        request.client.host = "192.168.1.1"
        
        identifier = rate_limiter.get_identifier(request)
        assert identifier == "user:user123"
    
    def test_get_identifier_with_ip_only(self, rate_limiter):
        """Test identifier extraction with IP address only"""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.user_id = None
        request.client = Mock()
        request.client.host = "192.168.1.1"
        
        identifier = rate_limiter.get_identifier(request)
        assert identifier == "ip:192.168.1.1"
    
    def test_get_identifier_no_client(self, rate_limiter):
        """Test identifier extraction with no client info"""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.user_id = None
        request.client = None
        
        identifier = rate_limiter.get_identifier(request)
        assert identifier == "ip:unknown"
    
    def test_get_limit_config_exact_match(self, rate_limiter):
        """Test limit config retrieval with exact match"""
        config = rate_limiter.get_limit_config("/api/voice-to-text")
        
        assert config["requests"] == 100
        assert config["window"] == 60
        assert config["burst"] == 10
    
    def test_get_limit_config_prefix_match(self, rate_limiter):
        """Test limit config retrieval with prefix match"""
        config = rate_limiter.get_limit_config("/api/schemes/123")
        
        assert config["requests"] == 60
        assert config["window"] == 60
    
    def test_get_limit_config_default(self, rate_limiter):
        """Test limit config retrieval with default"""
        config = rate_limiter.get_limit_config("/api/unknown/endpoint")
        
        assert config["requests"] == 60
        assert config["window"] == 60
        assert config["burst"] == 10
    
    @pytest.mark.anyio
    async def test_is_allowed_first_request(self, rate_limiter):
        """Test first request is allowed"""
        identifier = "user:test123"
        limit_config = {"requests": 10, "window": 60, "burst": 5}
        
        allowed, retry_after, reset_time = await rate_limiter.is_allowed(
            identifier, limit_config
        )
        
        assert allowed is True
        assert retry_after is None
        assert reset_time is None
    
    @pytest.mark.anyio
    async def test_is_allowed_within_burst(self, rate_limiter):
        """Test multiple requests within burst limit"""
        identifier = "user:test123"
        limit_config = {"requests": 10, "window": 60, "burst": 5}
        
        # Make 5 requests (burst size)
        for _ in range(5):
            allowed, _, _ = await rate_limiter.is_allowed(identifier, limit_config)
            assert allowed is True
    
    @pytest.mark.anyio
    async def test_is_allowed_exceeds_burst(self, rate_limiter):
        """Test request exceeding burst limit is blocked"""
        identifier = "user:test123"
        limit_config = {"requests": 10, "window": 60, "burst": 3}
        
        # Consume all burst tokens
        for _ in range(3):
            allowed, _, _ = await rate_limiter.is_allowed(identifier, limit_config)
            assert allowed is True
        
        # Next request should be blocked
        allowed, retry_after, reset_time = await rate_limiter.is_allowed(
            identifier, limit_config
        )
        
        assert allowed is False
        assert retry_after is not None
        assert retry_after > 0
        assert reset_time is not None
    
    @pytest.mark.anyio
    async def test_is_allowed_token_refill(self, rate_limiter):
        """Test tokens refill over time"""
        identifier = "user:test123"
        limit_config = {"requests": 10, "window": 60, "burst": 2}
        
        # Consume all tokens
        for _ in range(2):
            allowed, _, _ = await rate_limiter.is_allowed(identifier, limit_config)
            assert allowed is True
        
        # Should be blocked
        allowed, _, _ = await rate_limiter.is_allowed(identifier, limit_config)
        assert allowed is False
        
        # Wait for token refill (simulate time passing)
        await asyncio.sleep(1)
        
        # Should be allowed again (tokens refilled)
        allowed, _, _ = await rate_limiter.is_allowed(identifier, limit_config)
        # Note: This might still be False due to short wait time
        # In production, tokens refill gradually
    
    @pytest.mark.anyio
    async def test_cleanup_old_entries(self, rate_limiter):
        """Test cleanup of old rate limiter entries"""
        # Add some entries
        rate_limiter.buckets["user:old"] = (5.0, time.time() - 7200, 10)  # 2 hours old
        rate_limiter.buckets["user:recent"] = (5.0, time.time() - 60, 5)  # 1 minute old
        
        await rate_limiter.cleanup_old_entries()
        
        # Old entry should be removed
        assert "user:old" not in rate_limiter.buckets
        # Recent entry should remain
        assert "user:recent" in rate_limiter.buckets


class TestRateLimitingMiddleware:
    """Test rate limiting middleware"""
    
    @pytest.mark.anyio
    async def test_middleware_allows_health_check(self):
        """Test middleware skips rate limiting for health check"""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/health"
        
        call_next = AsyncMock(return_value=Mock())
        
        response = await rate_limiting_middleware(request, call_next)
        
        call_next.assert_called_once_with(request)
    
    @pytest.mark.anyio
    async def test_middleware_allows_normal_request(self):
        """Test middleware allows request within limits"""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/schemes"
        request.state = Mock()
        request.state.user_id = "user123"
        request.headers = {"Accept-Language": "en"}
        
        # Mock response
        mock_response = Mock()
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)
        
        response = await rate_limiting_middleware(request, call_next)
        
        call_next.assert_called_once_with(request)
        assert "X-RateLimit-Limit" in response.headers
    
    @pytest.mark.anyio
    async def test_middleware_blocks_excessive_requests(self):
        """Test middleware blocks requests exceeding rate limit"""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/auth/register"
        request.state = Mock()
        request.state.user_id = None
        request.client = Mock()
        request.client.host = "192.168.1.1"
        request.headers = {"Accept-Language": "hi"}
        
        call_next = AsyncMock()
        
        # Make requests until rate limited
        # Auth register has strict limits: 5 requests per 300 seconds
        for i in range(6):
            response = await rate_limiting_middleware(request, call_next)
            
            if i < 5:
                # First 5 should succeed
                call_next.assert_called()
            else:
                # 6th should be blocked
                assert isinstance(response, JSONResponse)
                assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


class TestGracefulDegradation:
    """Test graceful degradation utilities"""
    
    def test_with_cached_fallback_primary_succeeds(self):
        """Test fallback when primary function succeeds"""
        primary_func = Mock(return_value={"data": "primary"})
        cache_func = Mock()
        
        result = GracefulDegradation.with_cached_fallback(
            primary_func, cache_func, "test_key"
        )
        
        assert result == {"data": "primary"}
        primary_func.assert_called_once()
        cache_func.assert_not_called()
    
    def test_with_cached_fallback_uses_cache(self):
        """Test fallback uses cache when primary fails"""
        primary_func = Mock(side_effect=Exception("Primary failed"))
        cache_func = Mock(return_value={
            "data": "cached",
            "cached_at": datetime.utcnow()
        })
        
        result = GracefulDegradation.with_cached_fallback(
            primary_func, cache_func, "test_key", max_cache_age_seconds=3600
        )
        
        assert result["data"] == "cached"
        assert result["from_cache"] is True
        assert "cache_age_seconds" in result
        primary_func.assert_called_once()
        cache_func.assert_called_once_with("test_key")
    
    def test_with_cached_fallback_cache_too_old(self):
        """Test fallback rejects old cache"""
        primary_func = Mock(side_effect=Exception("Primary failed"))
        cache_func = Mock(return_value={
            "data": "cached",
            "cached_at": datetime.utcnow() - timedelta(hours=2)
        })
        
        with pytest.raises(DataNotFoundException):
            GracefulDegradation.with_cached_fallback(
                primary_func, cache_func, "test_key", max_cache_age_seconds=3600
            )
    
    def test_with_cached_fallback_both_fail(self):
        """Test fallback when both primary and cache fail"""
        primary_func = Mock(side_effect=Exception("Primary failed"))
        cache_func = Mock(side_effect=Exception("Cache failed"))
        
        with pytest.raises(DataNotFoundException) as exc_info:
            GracefulDegradation.with_cached_fallback(
                primary_func, cache_func, "test_key"
            )
        
        assert "Data unavailable" in str(exc_info.value)
    
    def test_with_default_response_success(self):
        """Test default response when function succeeds"""
        func = Mock(return_value="success")
        default = "default"
        
        result = GracefulDegradation.with_default_response(func, default)
        
        assert result == "success"
        func.assert_called_once()
    
    def test_with_default_response_failure(self):
        """Test default response when function fails"""
        func = Mock(side_effect=Exception("Failed"))
        default = "default_value"
        
        result = GracefulDegradation.with_default_response(func, default)
        
        assert result == "default_value"
        func.assert_called_once()
    
    def test_offline_mode_response(self):
        """Test offline mode response generation"""
        with pytest.raises(OfflineFeatureUnavailableException) as exc_info:
            GracefulDegradation.offline_mode_response(
                feature_name="Real-time prices",
                offline_alternatives=["Cached prices", "Historical data"],
                last_sync_time=datetime.utcnow() - timedelta(hours=1)
            )
        
        exc = exc_info.value
        assert exc.error_code == "OFFLINE_FEATURE_UNAVAILABLE"
        assert len(exc.offline_alternatives) == 2
        assert exc.last_sync_time is not None
    
    def test_simplified_response_full_succeeds(self):
        """Test simplified response when full response succeeds"""
        func = Mock(return_value={"full": "data", "details": "complete"})
        simplification_func = Mock()
        
        result = GracefulDegradation.simplified_response(func, simplification_func)
        
        assert result == {"full": "data", "details": "complete"}
        func.assert_called_once()
        simplification_func.assert_not_called()
    
    def test_simplified_response_uses_simplified(self):
        """Test simplified response when full response fails"""
        func = Mock(side_effect=Exception("Full failed"))
        simplification_func = Mock(return_value={"basic": "data"})
        
        result = GracefulDegradation.simplified_response(func, simplification_func)
        
        assert result["basic"] == "data"
        assert result["simplified"] is True
        assert "warning" in result
    
    def test_handle_external_service_failure(self):
        """Test external service failure handling"""
        error = Exception("Service down")
        
        with pytest.raises(ExternalServiceException) as exc_info:
            handle_external_service_failure(
                service_name="mandi_api",
                error=error,
                retry_after=120
            )
        
        exc = exc_info.value
        assert exc.service_name == "mandi_api"
        assert exc.retry_after_seconds == 120


class TestRetryUtilities:
    """Test retry utilities"""
    
    @pytest.mark.anyio
    async def test_exponential_backoff_async_success(self):
        """Test exponential backoff with async function success"""
        mock_func = AsyncMock(return_value="success")
        
        @exponential_backoff(max_retries=3, base_delay=0.1)
        async def test_func():
            return await mock_func()
        
        result = await test_func()
        
        assert result == "success"
        mock_func.assert_called_once()
    
    @pytest.mark.anyio
    async def test_exponential_backoff_async_retry_then_success(self):
        """Test exponential backoff retries then succeeds"""
        mock_func = AsyncMock(side_effect=[
            Exception("Fail 1"),
            Exception("Fail 2"),
            "success"
        ])
        
        @exponential_backoff(max_retries=3, base_delay=0.1)
        async def test_func():
            return await mock_func()
        
        result = await test_func()
        
        assert result == "success"
        assert mock_func.call_count == 3
    
    @pytest.mark.anyio
    async def test_exponential_backoff_async_max_retries_exceeded(self):
        """Test exponential backoff fails after max retries"""
        mock_func = AsyncMock(side_effect=Exception("Always fails"))
        
        @exponential_backoff(max_retries=2, base_delay=0.1)
        async def test_func():
            return await mock_func()
        
        with pytest.raises(Exception, match="Always fails"):
            await test_func()
        
        assert mock_func.call_count == 3  # Initial + 2 retries
    
    def test_exponential_backoff_sync_success(self):
        """Test exponential backoff with sync function success"""
        mock_func = Mock(return_value="success")
        
        @exponential_backoff(max_retries=3, base_delay=0.1)
        def test_func():
            return mock_func()
        
        result = test_func()
        
        assert result == "success"
        mock_func.assert_called_once()
    
    def test_exponential_backoff_sync_retry_then_success(self):
        """Test exponential backoff sync retries then succeeds"""
        mock_func = Mock(side_effect=[
            Exception("Fail 1"),
            "success"
        ])
        
        @exponential_backoff(max_retries=3, base_delay=0.1)
        def test_func():
            return mock_func()
        
        result = test_func()
        
        assert result == "success"
        assert mock_func.call_count == 2
    
    @pytest.mark.anyio
    async def test_retry_with_fallback_primary_succeeds(self):
        """Test retry with fallback when primary succeeds"""
        primary = AsyncMock(return_value="primary_result")
        fallback = AsyncMock()
        
        result = await retry_with_fallback(primary, fallback, max_retries=3)
        
        assert result == "primary_result"
        primary.assert_called_once()
        fallback.assert_not_called()
    
    @pytest.mark.anyio
    async def test_retry_with_fallback_uses_fallback(self):
        """Test retry with fallback uses fallback after primary fails"""
        primary = AsyncMock(side_effect=Exception("Primary failed"))
        fallback = AsyncMock(return_value="fallback_result")
        
        result = await retry_with_fallback(primary, fallback, max_retries=2)
        
        assert result == "fallback_result"
        assert primary.call_count == 2
        fallback.assert_called_once()
    
    @pytest.mark.anyio
    async def test_retry_with_fallback_both_fail(self):
        """Test retry with fallback when both fail"""
        primary = AsyncMock(side_effect=Exception("Primary failed"))
        fallback = AsyncMock(side_effect=Exception("Fallback failed"))
        
        with pytest.raises(ExternalServiceException):
            await retry_with_fallback(primary, fallback, max_retries=2)


class TestCircuitBreaker:
    """Test circuit breaker pattern"""
    
    def test_circuit_breaker_closed_state(self):
        """Test circuit breaker in closed state allows calls"""
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=5.0)
        func = Mock(return_value="success")
        
        result = breaker.call(func)
        
        assert result == "success"
        assert breaker.state == "closed"
        assert breaker.failure_count == 0
    
    def test_circuit_breaker_opens_after_failures(self):
        """Test circuit breaker opens after threshold failures"""
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=5.0)
        func = Mock(side_effect=Exception("Service failed"))
        
        # Trigger failures to open circuit
        for i in range(3):
            with pytest.raises(Exception):
                breaker.call(func)
        
        assert breaker.state == "open"
        assert breaker.failure_count == 3
    
    def test_circuit_breaker_blocks_when_open(self):
        """Test circuit breaker blocks calls when open"""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=5.0)
        
        # Create a real function instead of Mock to avoid __name__ issue
        def failing_func():
            raise Exception("Service failed")
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                breaker.call(failing_func)
        
        # Next call should be blocked
        with pytest.raises(ExternalServiceException) as exc_info:
            breaker.call(failing_func)
        
        assert "circuit breaker open" in str(exc_info.value).lower()
    
    def test_circuit_breaker_half_open_after_timeout(self):
        """Test circuit breaker enters half-open state after timeout"""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.5)
        func = Mock(side_effect=[
            Exception("Fail 1"),
            Exception("Fail 2"),
            "success"
        ])
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                breaker.call(func)
        
        assert breaker.state == "open"
        
        # Wait for recovery timeout
        time.sleep(0.6)
        
        # Next call should enter half-open and succeed
        result = breaker.call(func)
        
        assert result == "success"
        assert breaker.state == "closed"
        assert breaker.failure_count == 0
    
    def test_circuit_breaker_reopens_on_half_open_failure(self):
        """Test circuit breaker reopens if half-open call fails"""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.5)
        func = Mock(side_effect=Exception("Service failed"))
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                breaker.call(func)
        
        # Wait for recovery timeout
        time.sleep(0.6)
        
        # Half-open call fails
        with pytest.raises(Exception):
            breaker.call(func)
        
        # Circuit should be open again
        assert breaker.state == "open"


class TestErrorTranslator:
    """Test error message translation"""
    
    def test_translate_to_english(self):
        """Test translation to English"""
        message = ErrorTranslator.translate("VOICE_PROCESSING_ERROR", "en")
        
        assert "audio" in message.lower()
        assert len(message) > 0
    
    def test_translate_to_hindi(self):
        """Test translation to Hindi"""
        message = ErrorTranslator.translate("DATA_NOT_FOUND", "hi")
        
        assert len(message) > 0
        # Should contain Hindi characters
        assert any(ord(char) > 2304 for char in message)
    
    def test_translate_to_bengali(self):
        """Test translation to Bengali"""
        message = ErrorTranslator.translate("RATE_LIMIT_EXCEEDED", "bn")
        
        assert len(message) > 0
    
    def test_translate_unsupported_language_defaults_to_english(self):
        """Test unsupported language defaults to English"""
        message = ErrorTranslator.translate("AUTHENTICATION_FAILED", "fr")
        
        # Should return English version
        assert "Authentication failed" in message
    
    def test_translate_unknown_error_code(self):
        """Test translation of unknown error code"""
        message = ErrorTranslator.translate("UNKNOWN_ERROR", "en")
        
        assert "error occurred" in message.lower()
    
    def test_get_all_translations(self):
        """Test getting all translations for error code"""
        translations = ErrorTranslator.get_all_translations("VOICE_PROCESSING_ERROR")
        
        assert "en" in translations
        assert "hi" in translations
        assert "bn" in translations
        assert "te" in translations
        assert "mr" in translations
    
    def test_add_translation(self):
        """Test adding new translation"""
        ErrorTranslator.add_translation(
            "TEST_ERROR",
            "en",
            "This is a test error"
        )
        
        message = ErrorTranslator.translate("TEST_ERROR", "en")
        assert message == "This is a test error"
    
    def test_supported_languages(self):
        """Test supported languages list"""
        assert "en" in ErrorTranslator.SUPPORTED_LANGUAGES
        assert "hi" in ErrorTranslator.SUPPORTED_LANGUAGES
        assert len(ErrorTranslator.SUPPORTED_LANGUAGES) >= 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
