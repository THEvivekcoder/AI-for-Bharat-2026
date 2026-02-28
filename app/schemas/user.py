"""User schemas for request/response validation"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import phonenumbers


class LocationSchema(BaseModel):
    """Location information schema"""
    state: str = Field(..., min_length=1, max_length=50)
    district: str = Field(..., min_length=1, max_length=50)
    block: Optional[str] = Field(None, max_length=50)
    village: Optional[str] = Field(None, max_length=100)
    pincode: str = Field(..., pattern=r'^\d{6}$')
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)

    class Config:
        from_attributes = True


class UserProfileCreate(BaseModel):
    """User profile creation schema"""
    location: Optional[LocationSchema] = None
    age: Optional[int] = Field(None, ge=1, le=150)
    gender: Optional[str] = Field(None, max_length=20)
    education_level: Optional[str] = Field(None, max_length=50)
    occupation: Optional[str] = Field(None, max_length=50)
    income_bracket: Optional[str] = Field(None, max_length=50)
    household_size: Optional[int] = Field(None, ge=1, le=100)


class UserProfileUpdate(BaseModel):
    """User profile update schema"""
    location: Optional[LocationSchema] = None
    age: Optional[int] = Field(None, ge=1, le=150)
    gender: Optional[str] = Field(None, max_length=20)
    education_level: Optional[str] = Field(None, max_length=50)
    occupation: Optional[str] = Field(None, max_length=50)
    income_bracket: Optional[str] = Field(None, max_length=50)
    household_size: Optional[int] = Field(None, ge=1, le=100)


class UserProfileResponse(BaseModel):
    """User profile response schema"""
    profile_id: str
    user_id: str
    location: Optional[LocationSchema] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    education_level: Optional[str] = None
    occupation: Optional[str] = None
    income_bracket: Optional[str] = None
    household_size: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserRegisterRequest(BaseModel):
    """User registration request"""
    phone_number: str = Field(..., description="Phone number with country code")
    language: str = Field(default="hi", pattern=r'^[a-z]{2}$')

    @validator('phone_number')
    def validate_phone_number(cls, v):
        """Validate phone number format"""
        try:
            # Parse phone number (assuming Indian numbers if no country code)
            if not v.startswith('+'):
                v = '+91' + v
            parsed = phonenumbers.parse(v, None)
            if not phonenumbers.is_valid_number(parsed):
                raise ValueError('Invalid phone number')
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            raise ValueError('Invalid phone number format')


class UserRegisterResponse(BaseModel):
    """User registration response"""
    user_id: str
    phone_number: str
    message: str
    otp_sent: bool


class OTPVerifyRequest(BaseModel):
    """OTP verification request"""
    phone_number: str
    otp: str = Field(..., pattern=r'^\d{6}$')


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    user_id: str
    expires_in: int


class UserResponse(BaseModel):
    """User response schema"""
    user_id: str
    phone_number: str
    language: str
    created_at: datetime
    updated_at: datetime
    profile: Optional[UserProfileResponse] = None

    class Config:
        from_attributes = True
