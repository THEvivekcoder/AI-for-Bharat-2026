"""Pydantic schemas for request/response validation"""
from app.schemas.health import HealthResponse
from app.schemas.user import (
    UserRegisterRequest,
    UserRegisterResponse,
    OTPVerifyRequest,
    TokenResponse,
    UserResponse,
    UserProfileCreate,
    UserProfileUpdate,
    UserProfileResponse,
    LocationSchema
)

__all__ = [
    "HealthResponse",
    "UserRegisterRequest",
    "UserRegisterResponse",
    "OTPVerifyRequest",
    "TokenResponse",
    "UserResponse",
    "UserProfileCreate",
    "UserProfileUpdate",
    "UserProfileResponse",
    "LocationSchema"
]
