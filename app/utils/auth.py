"""Authentication utilities for JWT and OTP"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from app.config import get_settings
import random
import string

settings = get_settings()


class JWTManager:
    """JWT token management"""
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT access token
        
        Args:
            data: Data to encode in token
            expires_delta: Token expiration time
            
        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.secret_key,
            algorithm=settings.algorithm
        )
        
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """
        Verify and decode JWT token
        
        Args:
            token: JWT token to verify
            
        Returns:
            Decoded token payload or None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[settings.algorithm]
            )
            return payload
        except JWTError:
            return None


class OTPManager:
    """OTP generation and verification"""
    
    OTP_LENGTH = 6
    OTP_EXPIRY_MINUTES = 10
    
    @staticmethod
    def generate_otp() -> str:
        """
        Generate a 6-digit OTP
        
        Returns:
            6-digit OTP string
        """
        return ''.join(random.choices(string.digits, k=OTPManager.OTP_LENGTH))
    
    @staticmethod
    def get_otp_key(phone_number: str) -> str:
        """
        Get Redis key for OTP storage
        
        Args:
            phone_number: User's phone number
            
        Returns:
            Redis key for OTP
        """
        return f"otp:{phone_number}"
    
    @staticmethod
    def get_otp_attempts_key(phone_number: str) -> str:
        """
        Get Redis key for OTP attempt tracking
        
        Args:
            phone_number: User's phone number
            
        Returns:
            Redis key for OTP attempts
        """
        return f"otp_attempts:{phone_number}"



# Dependency for getting current user from JWT token
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token
    
    Args:
        credentials: HTTP authorization credentials
        db: Database session
        
    Returns:
        Current user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    
    # Verify token
    payload = JWTManager.verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user ID from token
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = db.query(User).filter(User.user_id == user_id).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user
