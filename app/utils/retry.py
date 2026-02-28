"""Retry utilities for external API calls"""
import asyncio
import time
from typing import Callable, Any, Optional, Type, Tuple
from functools import wraps
from app.logging_config import logger
from app.exceptions import ExternalServiceException


def exponential_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorator for exponential backoff retry logic
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential calculation
        exceptions: Tuple of exception types to catch and retry
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        # Final attempt failed
                        logger.error(
                            f"Function {func.__name__} failed after {max_retries} retries: {str(e)}"
                        )
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    
                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {delay:.2f}s: {str(e)}"
                    )
                    
                    await asyncio.sleep(delay)
            
            # Should not reach here, but just in case
            if last_exception:
                raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        # Final attempt failed
                        logger.error(
                            f"Function {func.__name__} failed after {max_retries} retries: {str(e)}"
                        )
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    
                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {delay:.2f}s: {str(e)}"
                    )
                    
                    time.sleep(delay)
            
            # Should not reach here, but just in case
            if last_exception:
                raise last_exception
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


async def retry_with_fallback(
    primary_func: Callable,
    fallback_func: Optional[Callable] = None,
    max_retries: int = 3,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> Any:
    """
    Retry a function with optional fallback
    
    Args:
        primary_func: Primary function to execute
        fallback_func: Fallback function if primary fails
        max_retries: Maximum retry attempts for primary
        exceptions: Exception types to catch
        
    Returns:
        Result from primary or fallback function
    """
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            if asyncio.iscoroutinefunction(primary_func):
                return await primary_func()
            else:
                return primary_func()
        except exceptions as e:
            last_exception = e
            logger.warning(
                f"Primary function failed (attempt {attempt + 1}/{max_retries}): {str(e)}"
            )
            
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    # Primary function failed, try fallback
    if fallback_func:
        logger.info("Primary function failed, using fallback")
        try:
            if asyncio.iscoroutinefunction(fallback_func):
                return await fallback_func()
            else:
                return fallback_func()
        except Exception as e:
            logger.error(f"Fallback function also failed: {str(e)}")
            raise ExternalServiceException(
                message="Both primary and fallback services failed",
                service_name="unknown",
                retry_after_seconds=60
            )
    
    # No fallback available
    if last_exception:
        raise last_exception


class CircuitBreaker:
    """
    Circuit breaker pattern for external service calls
    Prevents cascading failures by temporarily blocking calls to failing services
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "closed"  # closed, open, half_open
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection
        
        States:
        - closed: Normal operation, calls go through
        - open: Too many failures, calls blocked
        - half_open: Testing if service recovered
        """
        if self.state == "open":
            # Check if recovery timeout has passed
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = "half_open"
                logger.info("Circuit breaker entering half-open state")
            else:
                raise ExternalServiceException(
                    message="Service temporarily unavailable (circuit breaker open)",
                    service_name=func.__name__,
                    retry_after_seconds=int(self.recovery_timeout - (time.time() - self.last_failure_time))
                )
        
        try:
            result = func(*args, **kwargs)
            
            # Success - reset failure count
            if self.state == "half_open":
                self.state = "closed"
                logger.info("Circuit breaker closed after successful call")
            
            self.failure_count = 0
            return result
            
        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            logger.warning(
                f"Circuit breaker recorded failure {self.failure_count}/{self.failure_threshold}"
            )
            
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.error(f"Circuit breaker opened after {self.failure_count} failures")
            
            raise
