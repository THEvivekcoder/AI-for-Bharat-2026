"""Logging middleware for BharatSahayak"""
from fastapi import Request
from typing import Callable
import logging
import time
import uuid

logger = logging.getLogger(__name__)


async def logging_middleware(request: Request, call_next: Callable):
    """
    Middleware to log all requests and responses
    
    Logs:
    - Request ID
    - Method and path
    - Client IP
    - Response status
    - Processing time
    """
    # Generate request ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Get client IP
    client_ip = request.client.host if request.client else "unknown"
    
    # Log request
    logger.info(
        f"[{request_id}] {request.method} {request.url.path} - Client: {client_ip}"
    )
    
    # Process request and measure time
    start_time = time.time()
    
    try:
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Add custom headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.3f}s"
        
        # Log response
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} - "
            f"Status: {response.status_code} - Time: {process_time:.3f}s"
        )
        
        return response
        
    except Exception as e:
        # Log error
        process_time = time.time() - start_time
        logger.error(
            f"[{request_id}] {request.method} {request.url.path} - "
            f"Error: {str(e)} - Time: {process_time:.3f}s"
        )
        raise
