"""Custom exception classes"""
from typing import Optional, List, Dict, Any
from datetime import datetime


class BharatSahayakException(Exception):
    """Base exception for BharatSahayak application"""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        retry_allowed: bool = False,
        status_code: int = 500,
        **kwargs
    ):
        self.message = message
        self.error_code = error_code
        self.retry_allowed = retry_allowed
        self.status_code = status_code
        self.extra_data = kwargs
        super().__init__(message)


class VoiceProcessingException(BharatSahayakException):
    """Exception for voice processing failures"""
    
    def __init__(
        self,
        message: str,
        supported_languages: Optional[List[str]] = None,
        audio_quality_score: Optional[float] = None,
        detected_language: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            error_code="VOICE_PROCESSING_ERROR",
            retry_allowed=True,
            **kwargs
        )
        self.supported_languages = supported_languages
        self.audio_quality_score = audio_quality_score
        self.detected_language = detected_language


class DataNotFoundException(BharatSahayakException):
    """Exception for missing data"""
    
    def __init__(
        self,
        message: str,
        alternative_data: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            error_code="DATA_NOT_FOUND",
            retry_allowed=False,
            status_code=404,
            **kwargs
        )
        self.alternative_data = alternative_data
        self.suggestions = suggestions
        self.details = alternative_data


class InsufficientProfileDataException(BharatSahayakException):
    """Exception for incomplete user profile"""
    
    def __init__(
        self,
        message: str,
        missing_fields: List[str],
        can_proceed_without: bool = False,
        **kwargs
    ):
        super().__init__(
            message=message,
            error_code="INSUFFICIENT_PROFILE_DATA",
            retry_allowed=False,
            **kwargs
        )
        self.missing_fields = missing_fields
        self.can_proceed_without = can_proceed_without


class AuthenticationException(BharatSahayakException):
    """Exception for authentication failures"""
    
    def __init__(
        self,
        message: str,
        remaining_attempts: Optional[int] = None,
        lockout_time: Optional[datetime] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_FAILED",
            retry_allowed=True,
            status_code=401,
            **kwargs
        )
        self.remaining_attempts = remaining_attempts
        self.lockout_time = lockout_time
        self.details = {"remaining_attempts": remaining_attempts}


class RateLimitException(BharatSahayakException):
    """Exception for rate limiting"""
    
    def __init__(
        self,
        message: str,
        retry_after_seconds: int,
        quota_reset_time: datetime,
        current_usage: Optional[int] = None,
        quota_limit: Optional[int] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            retry_allowed=True,
            status_code=429,
            **kwargs
        )
        self.retry_after_seconds = retry_after_seconds
        self.retry_after = retry_after_seconds
        self.quota_reset_time = quota_reset_time
        self.current_usage = current_usage
        self.quota_limit = quota_limit
        self.details = {"retry_after": retry_after_seconds, "quota_limit": quota_limit}


class OfflineFeatureUnavailableException(BharatSahayakException):
    """Exception for features requiring internet"""
    
    def __init__(
        self,
        message: str,
        offline_alternatives: Optional[List[str]] = None,
        last_sync_time: Optional[datetime] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            error_code="OFFLINE_FEATURE_UNAVAILABLE",
            retry_allowed=True,
            **kwargs
        )
        self.offline_alternatives = offline_alternatives
        self.last_sync_time = last_sync_time


class ExternalServiceException(BharatSahayakException):
    """Exception for external service failures"""
    
    def __init__(
        self,
        message: str,
        service_name: str,
        retry_after_seconds: Optional[int] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            error_code="EXTERNAL_SERVICE_ERROR",
            retry_allowed=True,
            status_code=503,
            **kwargs
        )
        self.service_name = service_name
        self.retry_after_seconds = retry_after_seconds
        self.details = {"service_name": service_name}


class DatabaseException(BharatSahayakException):
    """Exception for database failures"""
    
    def __init__(
        self,
        message: str,
        operation: str,
        **kwargs
    ):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            retry_allowed=True,
            **kwargs
        )
        self.operation = operation


class CacheException(BharatSahayakException):
    """Exception for cache failures"""
    
    def __init__(
        self,
        message: str,
        cache_type: str,
        fallback_available: bool = False,
        **kwargs
    ):
        super().__init__(
            message=message,
            error_code="CACHE_ERROR",
            retry_allowed=True,
            **kwargs
        )
        self.cache_type = cache_type
        self.fallback_available = fallback_available


class ValidationException(BharatSahayakException):
    """Exception for validation failures"""
    
    def __init__(
        self,
        message: str,
        field_errors: Optional[Dict[str, str]] = None,
        suggestions: Optional[List[str]] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            retry_allowed=False,
            **kwargs
        )
        self.field_errors = field_errors
        self.suggestions = suggestions
        self.status_code = 400
        self.details = field_errors
