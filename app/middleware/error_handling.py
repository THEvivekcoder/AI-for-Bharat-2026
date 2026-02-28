"""Error handling middleware for BharatSahayak"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import logging
import traceback

from app.exceptions import (
    BharatSahayakException,
    DataNotFoundException,
    RateLimitException,
    AuthenticationException,
    ValidationException,
    ExternalServiceException
)
from app.schemas.errors import ErrorResponse
from app.services.error_translator import ErrorTranslator

logger = logging.getLogger(__name__)


async def error_handling_middleware(request: Request, call_next: Callable):
    """
    Middleware to handle exceptions and return structured error responses
    
    Catches all exceptions and converts them to appropriate HTTP responses
    with multilingual error messages.
    """
    try:
        response = await call_next(request)
        return response
        
    except BharatSahayakException as e:
        # Custom application exceptions
        logger.warning(f"Application error: {str(e)}")
        
        # Get user's preferred language
        language = request.headers.get("Accept-Language", "en").split(",")[0][:2]
        
        # Translate error message if available
        translated_message = ErrorTranslator.translate(e.error_code, language) if hasattr(e, 'error_code') else str(e)
        
        error_response = ErrorResponse(
            error=getattr(e, 'error_code', 'APPLICATION_ERROR'),
            message=translated_message or str(e),
            retry_allowed=getattr(e, 'retry_allowed', False)
        )
        
        return JSONResponse(
            status_code=e.status_code,
            content=error_response.model_dump(mode='json')
        )
        
    except ValueError as e:
        # Validation errors
        logger.warning(f"Validation error: {str(e)}")
        
        error_response = ErrorResponse(
            error="VALIDATION_ERROR",
            message=str(e),
            retry_allowed=False
        )
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response.model_dump(mode='json')
        )
        
    except Exception as e:
        # Unexpected errors
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Don't expose internal error details in production
        error_response = ErrorResponse(
            error="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred. Please try again later.",
            retry_allowed=True
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump(mode='json')
        )


def setup_exception_handlers(app):
    """Setup custom exception handlers for FastAPI app"""
    
    @app.exception_handler(DataNotFoundException)
    async def data_not_found_handler(request: Request, exc: DataNotFoundException):
        """Handle data not found exceptions"""
        language = request.headers.get("Accept-Language", "en").split(",")[0][:2]
        translated_message = ErrorTranslator.translate("DATA_NOT_FOUND", language)
        
        error_response = ErrorResponse(
            error="DATA_NOT_FOUND",
            message=translated_message or exc.message,
            retry_allowed=False
        )
        
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error_response.model_dump(mode='json')
        )
    
    @app.exception_handler(RateLimitException)
    async def rate_limit_handler(request: Request, exc: RateLimitException):
        """Handle rate limit exceptions"""
        language = request.headers.get("Accept-Language", "en").split(",")[0][:2]
        translated_message = ErrorTranslator.translate("RATE_LIMIT_EXCEEDED", language)
        
        error_response = ErrorResponse(
            error="RATE_LIMIT_EXCEEDED",
            message=translated_message or exc.message,
            retry_allowed=True
        )
        
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content=error_response.model_dump(mode='json'),
            headers={"Retry-After": str(exc.retry_after)} if hasattr(exc, 'retry_after') else {}
        )
    
    @app.exception_handler(AuthenticationException)
    async def authentication_handler(request: Request, exc: AuthenticationException):
        """Handle authentication exceptions"""
        error_response = ErrorResponse(
            error="AUTHENTICATION_ERROR",
            message=exc.message,
            retry_allowed=False
        )
        
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=error_response.model_dump(mode='json'),
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    @app.exception_handler(ValidationException)
    async def validation_handler(request: Request, exc: ValidationException):
        """Handle validation exceptions"""
        error_response = ErrorResponse(
            error="VALIDATION_ERROR",
            message=exc.message,
            retry_allowed=False
        )
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response.model_dump(mode='json')
        )
    
    @app.exception_handler(ExternalServiceException)
    async def external_service_handler(request: Request, exc: ExternalServiceException):
        """Handle external service exceptions"""
        language = request.headers.get("Accept-Language", "en").split(",")[0][:2]
        translated_message = ErrorTranslator.translate("EXTERNAL_SERVICE_ERROR", language)
        
        error_response = ErrorResponse(
            error="EXTERNAL_SERVICE_ERROR",
            message=translated_message or exc.message,
            retry_allowed=True
        )
        
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=error_response.model_dump(mode='json')
        )
    
    logger.info("Exception handlers registered")
