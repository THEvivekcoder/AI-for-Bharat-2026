"""Graceful degradation utilities"""
from typing import Any, Optional, Callable, Dict
from datetime import datetime
from app.logging_config import logger
from app.exceptions import (
    DataNotFoundException,
    OfflineFeatureUnavailableException,
    ExternalServiceException
)


class GracefulDegradation:
    """
    Provides graceful degradation strategies for various failure scenarios
    """
    
    @staticmethod
    def with_cached_fallback(
        primary_func: Callable,
        cache_func: Callable,
        cache_key: str,
        max_cache_age_seconds: int = 3600
    ) -> Any:
        """
        Try primary function, fall back to cached data if it fails
        
        Args:
            primary_func: Primary data source function
            cache_func: Function to retrieve cached data
            cache_key: Key for cached data
            max_cache_age_seconds: Maximum age of cached data to use
            
        Returns:
            Data from primary or cache
        """
        try:
            # Try primary function
            result = primary_func()
            logger.info(f"Successfully retrieved data from primary source: {cache_key}")
            return result
        except Exception as e:
            logger.warning(f"Primary source failed for {cache_key}: {str(e)}, trying cache")
            
            try:
                # Try cache
                cached_data = cache_func(cache_key)
                
                if cached_data:
                    # Check cache age
                    cache_age = datetime.utcnow() - cached_data.get("cached_at", datetime.utcnow())
                    
                    if cache_age.total_seconds() <= max_cache_age_seconds:
                        logger.info(f"Using cached data for {cache_key} (age: {cache_age.total_seconds()}s)")
                        return {
                            **cached_data,
                            "from_cache": True,
                            "cache_age_seconds": int(cache_age.total_seconds()),
                            "warning": "Data from cache due to service unavailability"
                        }
                    else:
                        logger.warning(f"Cached data too old for {cache_key}: {cache_age.total_seconds()}s")
                
            except Exception as cache_error:
                logger.error(f"Cache also failed for {cache_key}: {str(cache_error)}")
            
            # Both primary and cache failed
            raise DataNotFoundException(
                message="Data unavailable and no recent cache available",
                suggestions=["Try again later", "Check your internet connection"]
            )
    
    @staticmethod
    def with_partial_data(
        func: Callable,
        required_fields: list,
        optional_fields: list
    ) -> Dict[str, Any]:
        """
        Return partial data if complete data is unavailable
        
        Args:
            func: Function to retrieve data
            required_fields: Fields that must be present
            optional_fields: Fields that are nice to have
            
        Returns:
            Data with at least required fields
        """
        try:
            data = func()
            return data
        except Exception as e:
            logger.warning(f"Failed to get complete data: {str(e)}")
            
            # Try to get partial data
            try:
                partial_data = {}
                
                # Attempt to get required fields individually
                for field in required_fields:
                    try:
                        partial_data[field] = func(field_name=field)
                    except:
                        raise  # Required field failed, can't proceed
                
                # Attempt to get optional fields
                for field in optional_fields:
                    try:
                        partial_data[field] = func(field_name=field)
                    except:
                        logger.debug(f"Optional field {field} unavailable")
                        partial_data[field] = None
                
                partial_data["partial_data"] = True
                partial_data["warning"] = "Some information may be incomplete"
                
                return partial_data
                
            except Exception as partial_error:
                logger.error(f"Failed to get even partial data: {str(partial_error)}")
                raise
    
    @staticmethod
    def with_default_response(
        func: Callable,
        default_response: Any,
        log_failure: bool = True
    ) -> Any:
        """
        Return default response if function fails
        
        Args:
            func: Function to execute
            default_response: Default value to return on failure
            log_failure: Whether to log the failure
            
        Returns:
            Result from function or default response
        """
        try:
            return func()
        except Exception as e:
            if log_failure:
                logger.warning(f"Function failed, using default response: {str(e)}")
            
            return default_response
    
    @staticmethod
    def offline_mode_response(
        feature_name: str,
        offline_alternatives: Optional[list] = None,
        last_sync_time: Optional[datetime] = None
    ):
        """
        Generate response for offline mode
        
        Args:
            feature_name: Name of the feature requiring internet
            offline_alternatives: List of alternative features available offline
            last_sync_time: When data was last synchronized
        """
        raise OfflineFeatureUnavailableException(
            message=f"{feature_name} requires internet connection",
            offline_alternatives=offline_alternatives or [],
            last_sync_time=last_sync_time
        )
    
    @staticmethod
    def simplified_response(
        func: Callable,
        simplification_func: Callable
    ) -> Any:
        """
        Return simplified response if full response fails
        
        Args:
            func: Function to get full response
            simplification_func: Function to simplify response
            
        Returns:
            Full or simplified response
        """
        try:
            full_response = func()
            return full_response
        except Exception as e:
            logger.warning(f"Full response failed, using simplified version: {str(e)}")
            
            try:
                simplified = simplification_func()
                simplified["simplified"] = True
                simplified["warning"] = "Showing simplified information"
                return simplified
            except Exception as simp_error:
                logger.error(f"Simplified response also failed: {str(simp_error)}")
                raise


def handle_external_service_failure(
    service_name: str,
    error: Exception,
    retry_after: int = 60
):
    """
    Handle external service failures consistently
    
    Args:
        service_name: Name of the external service
        error: The exception that occurred
        retry_after: Suggested retry delay in seconds
    """
    logger.error(f"External service {service_name} failed: {str(error)}")
    
    raise ExternalServiceException(
        message=f"{service_name} is temporarily unavailable",
        service_name=service_name,
        retry_after_seconds=retry_after
    )
