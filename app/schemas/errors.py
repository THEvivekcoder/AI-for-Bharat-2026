"""Error response models and schemas"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ErrorResponse(BaseModel):
    """Base error response model"""
    error: str = Field(..., description="Error code identifier")
    message: str = Field(..., description="Human-readable error message in English")
    message_translations: Optional[Dict[str, str]] = Field(
        None, 
        description="Translated error messages for supported languages"
    )
    retry_allowed: bool = Field(
        default=False, 
        description="Whether the client should retry the request"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the error occurred"
    )


class VoiceProcessingError(ErrorResponse):
    """Error response for voice processing failures"""
    error: str = "VOICE_PROCESSING_ERROR"
    supported_languages: Optional[List[str]] = Field(
        None,
        description="List of supported languages for voice input"
    )
    audio_quality_score: Optional[float] = Field(
        None,
        description="Quality score of the audio (0-1)"
    )
    detected_language: Optional[str] = Field(
        None,
        description="Language detected in the audio, if any"
    )


class DataNotFoundError(ErrorResponse):
    """Error response for missing data"""
    error: str = "DATA_NOT_FOUND"
    alternative_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Alternative or historical data that might be useful"
    )
    suggestions: Optional[List[str]] = Field(
        None,
        description="Suggestions for finding the requested data"
    )


class InsufficientProfileDataError(ErrorResponse):
    """Error response for incomplete user profile"""
    error: str = "INSUFFICIENT_PROFILE_DATA"
    missing_fields: List[str] = Field(
        ...,
        description="List of required fields that are missing"
    )
    can_proceed_without: bool = Field(
        default=False,
        description="Whether the operation can proceed with partial data"
    )


class AuthenticationError(ErrorResponse):
    """Error response for authentication failures"""
    error: str = "AUTHENTICATION_FAILED"
    remaining_attempts: Optional[int] = Field(
        None,
        description="Number of remaining authentication attempts"
    )
    lockout_time: Optional[datetime] = Field(
        None,
        description="When the account will be unlocked"
    )


class RateLimitError(ErrorResponse):
    """Error response for rate limiting"""
    error: str = "RATE_LIMIT_EXCEEDED"
    retry_after_seconds: int = Field(
        ...,
        description="Number of seconds to wait before retrying"
    )
    quota_reset_time: datetime = Field(
        ...,
        description="When the rate limit quota will reset"
    )
    current_usage: Optional[int] = Field(
        None,
        description="Current number of requests made"
    )
    quota_limit: Optional[int] = Field(
        None,
        description="Maximum number of requests allowed"
    )


class OfflineFeatureUnavailableError(ErrorResponse):
    """Error response for features requiring internet"""
    error: str = "OFFLINE_FEATURE_UNAVAILABLE"
    offline_alternatives: Optional[List[str]] = Field(
        None,
        description="Alternative features available offline"
    )
    last_sync_time: Optional[datetime] = Field(
        None,
        description="When data was last synchronized"
    )


class ExternalServiceError(ErrorResponse):
    """Error response for external service failures"""
    error: str = "EXTERNAL_SERVICE_ERROR"
    service_name: str = Field(
        ...,
        description="Name of the external service that failed"
    )
    retry_after_seconds: Optional[int] = Field(
        None,
        description="Suggested retry delay"
    )


class ValidationError(ErrorResponse):
    """Error response for validation failures"""
    error: str = "VALIDATION_ERROR"
    details: List[Dict[str, Any]] = Field(
        ...,
        description="Detailed validation error information"
    )


class DatabaseError(ErrorResponse):
    """Error response for database failures"""
    error: str = "DATABASE_ERROR"
    operation: str = Field(
        ...,
        description="Database operation that failed (read, write, update, delete)"
    )


class CacheError(ErrorResponse):
    """Error response for cache failures"""
    error: str = "CACHE_ERROR"
    cache_type: str = Field(
        ...,
        description="Type of cache (redis, sqlite, memory)"
    )
    fallback_available: bool = Field(
        default=False,
        description="Whether fallback data source is available"
    )


# Error code to model mapping
ERROR_MODELS = {
    "VOICE_PROCESSING_ERROR": VoiceProcessingError,
    "DATA_NOT_FOUND": DataNotFoundError,
    "INSUFFICIENT_PROFILE_DATA": InsufficientProfileDataError,
    "AUTHENTICATION_FAILED": AuthenticationError,
    "RATE_LIMIT_EXCEEDED": RateLimitError,
    "OFFLINE_FEATURE_UNAVAILABLE": OfflineFeatureUnavailableError,
    "EXTERNAL_SERVICE_ERROR": ExternalServiceError,
    "VALIDATION_ERROR": ValidationError,
    "DATABASE_ERROR": DatabaseError,
    "CACHE_ERROR": CacheError,
}
