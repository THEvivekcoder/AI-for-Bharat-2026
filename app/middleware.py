"""Middleware for error handling and logging"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.logging_config import logger
from app.exceptions import BharatSahayakException
from app.services.error_translator import ErrorTranslator
from datetime import datetime
import time
import traceback


async def error_handling_middleware(request: Request, call_next):
    """
    Global error handling middleware
    Catches all unhandled exceptions and returns structured error responses
    """
    try:
        response = await call_next(request)
        return response
    except BharatSahayakException as exc:
        # Handle custom application exceptions
        logger.warning(f"Application exception: {exc.error_code} - {exc.message}")
        
        # Get user's preferred language from request
        language = request.headers.get("Accept-Language", "en").split(",")[0].split("-")[0]
        
        # Build error response
        error_response = {
            "error": exc.error_code,
            "message": ErrorTranslator.translate(exc.error_code, language),
            "message_translations": ErrorTranslator.get_all_translations(exc.error_code),
            "retry_allowed": exc.retry_allowed,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add exception-specific data
        error_response.update(exc.extra_data)
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response
        )
    except Exception as exc:
        logger.error(f"Unhandled exception: {str(exc)}\n{traceback.format_exc()}")
        
        # Get user's preferred language
        language = request.headers.get("Accept-Language", "en").split(",")[0].split("-")[0]
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "INTERNAL_SERVER_ERROR",
                "message": ErrorTranslator.translate("INTERNAL_SERVER_ERROR", language),
                "message_translations": ErrorTranslator.get_all_translations("INTERNAL_SERVER_ERROR"),
                "retry_allowed": True,
                "timestamp": datetime.utcnow().isoformat()
            }
        )


async def logging_middleware(request: Request, call_next):
    """
    Request/response logging middleware
    Logs all incoming requests and their processing time
    """
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url.path}")
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Log response
    logger.info(
        f"Response: {request.method} {request.url.path} "
        f"- Status: {response.status_code} - Time: {process_time:.3f}s"
    )
    
    # Add processing time header
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


def setup_exception_handlers(app):
    """Setup custom exception handlers"""
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle HTTP exceptions"""
        logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
        
        # Get user's preferred language
        language = request.headers.get("Accept-Language", "en").split(",")[0].split("-")[0]
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": f"HTTP_{exc.status_code}",
                "message": exc.detail,
                "retry_allowed": exc.status_code >= 500,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle request validation errors"""
        logger.warning(f"Validation error: {exc.errors()}")
        
        # Get user's preferred language
        language = request.headers.get("Accept-Language", "en").split(",")[0].split("-")[0]
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "VALIDATION_ERROR",
                "message": ErrorTranslator.translate("VALIDATION_ERROR", language),
                "message_translations": ErrorTranslator.get_all_translations("VALIDATION_ERROR"),
                "details": exc.errors(),
                "retry_allowed": False,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
