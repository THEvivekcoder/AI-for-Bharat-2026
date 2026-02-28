"""
Example: Error Handling Integration

This example demonstrates how to integrate error handling, rate limiting,
and graceful degradation in a FastAPI endpoint.
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.exceptions import (
    DataNotFoundException,
    InsufficientProfileDataException,
    ExternalServiceException,
    DatabaseException
)
from app.utils.retry import exponential_backoff, CircuitBreaker
from app.utils.graceful_degradation import GracefulDegradation
from app.logging_config import logger
from pydantic import BaseModel


router = APIRouter()


# Example 1: Basic Error Handling
@router.get("/schemes/{scheme_id}")
async def get_scheme(scheme_id: str, db: Session = Depends(get_db)):
    """
    Get scheme by ID with proper error handling
    """
    try:
        # Validate UUID format
        import uuid
        try:
            uuid.UUID(scheme_id)
        except ValueError:
            raise DataNotFoundException(
                message=f"Invalid scheme ID format: {scheme_id}",
                suggestions=["Check the scheme ID", "Search for schemes by name"]
            )
        
        # Query database
        from app.services.scheme_repository import SchemeRepository
        repo = SchemeRepository(db)
        scheme = repo.get_scheme_by_id(scheme_id)
        
        if not scheme:
            raise DataNotFoundException(
                message=f"Scheme not found: {scheme_id}",
                suggestions=[
                    "Search for schemes by category",
                    "Try browsing all schemes",
                    "Contact support if you believe this is an error"
                ]
            )
        
        return scheme
        
    except DataNotFoundException:
        # Re-raise custom exceptions
        raise
    except Exception as e:
        # Catch unexpected errors
        logger.error(f"Unexpected error in get_scheme: {str(e)}")
        raise DatabaseException(
            message="Failed to retrieve scheme",
            operation="read"
        )


# Example 2: Eligibility Check with Profile Validation
class EligibilityRequest(BaseModel):
    scheme_id: str
    user_id: str


@router.post("/schemes/check-eligibility")
async def check_eligibility(
    request: EligibilityRequest,
    db: Session = Depends(get_db)
):
    """
    Check eligibility with profile validation
    """
    try:
        # Get user profile
        from app.services.user_manager import UserManager
        user_manager = UserManager(db)
        profile = user_manager.get_profile(request.user_id)
        
        # Validate required fields
        required_fields = ["age", "income", "location"]
        missing_fields = [
            field for field in required_fields 
            if not getattr(profile, field, None)
        ]
        
        if missing_fields:
            raise InsufficientProfileDataException(
                message="Cannot check eligibility without complete profile",
                missing_fields=missing_fields,
                can_proceed_without=False
            )
        
        # Check eligibility
        from app.services.eligibility_checker import EligibilityChecker
        checker = EligibilityChecker(db)
        result = checker.check_eligibility(profile, request.scheme_id)
        
        return result
        
    except InsufficientProfileDataException:
        raise
    except Exception as e:
        logger.error(f"Error checking eligibility: {str(e)}")
        raise


# Example 3: External API with Retry and Circuit Breaker
# Circuit breaker for mandi price API
mandi_api_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60.0
)


@exponential_backoff(max_retries=3, base_delay=1.0)
async def fetch_mandi_prices_with_retry(crop: str, location: str):
    """Fetch mandi prices with retry logic"""
    # Simulated external API call
    import httpx
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.example.com/mandi-prices",
            params={"crop": crop, "location": location},
            timeout=10.0
        )
        response.raise_for_status()
        return response.json()


@router.get("/farmer/market-price")
async def get_market_price(
    crop: str,
    location: str,
    db: Session = Depends(get_db)
):
    """
    Get market prices with retry, circuit breaker, and cached fallback
    """
    try:
        # Try to fetch live prices with circuit breaker
        def fetch_live():
            return mandi_api_breaker.call(
                fetch_mandi_prices_with_retry,
                crop,
                location
            )
        
        # Fallback to cached prices
        def fetch_cached():
            from app.services.offline_cache import CacheManager
            cache = CacheManager(db)
            cached = cache.get_cached_content("mandi_prices", f"{crop}_{location}")
            if cached:
                return {
                    **cached,
                    "from_cache": True,
                    "warning": "Live prices unavailable, showing cached data"
                }
            return None
        
        # Try live with cached fallback
        result = GracefulDegradation.with_cached_fallback(
            primary_func=fetch_live,
            cache_func=lambda key: fetch_cached(),
            cache_key=f"{crop}_{location}",
            max_cache_age_seconds=3600
        )
        
        return result
        
    except DataNotFoundException:
        # No live or cached data available
        raise DataNotFoundException(
            message=f"Market prices unavailable for {crop} in {location}",
            suggestions=[
                "Try nearby locations",
                "Check again in a few minutes",
                "Contact local mandi for current prices"
            ],
            alternative_data={
                "nearby_locations": ["Location A", "Location B"],
                "last_update_attempt": "2024-01-20T10:00:00Z"
            }
        )
    except ExternalServiceException as e:
        # External service failed
        logger.error(f"Mandi API failed: {str(e)}")
        raise


# Example 4: Graceful Degradation with Partial Data
@router.get("/schemes/recommendations")
async def get_recommendations(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get personalized recommendations with graceful degradation
    """
    try:
        # Try to get full personalized recommendations
        def get_full_recommendations():
            from app.services.personalization import PersonalizationEngine
            engine = PersonalizationEngine(db)
            return engine.get_personalized_schemes(user_id)
        
        # Fallback to simplified recommendations
        def get_simplified_recommendations():
            from app.services.scheme_repository import SchemeRepository
            repo = SchemeRepository(db)
            # Just return popular schemes
            schemes = repo.get_all_schemes(limit=10)
            return {
                "schemes": schemes,
                "simplified": True,
                "message": "Showing popular schemes (personalization unavailable)"
            }
        
        result = GracefulDegradation.simplified_response(
            func=get_full_recommendations,
            simplification_func=get_simplified_recommendations
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        # Return empty recommendations as last resort
        return {
            "schemes": [],
            "message": "Recommendations temporarily unavailable",
            "suggestions": ["Browse schemes by category", "Try again later"]
        }


# Example 5: Handling Multiple Error Types
@router.post("/health/check")
async def health_check(
    symptoms: List[str],
    user_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Health check with multiple error handling scenarios
    """
    try:
        # Validate input
        if not symptoms:
            raise DataNotFoundException(
                message="No symptoms provided",
                suggestions=["Describe your symptoms", "Select from common symptoms"]
            )
        
        # Get user profile if available
        user_profile = None
        if user_id:
            try:
                from app.services.user_manager import UserManager
                user_manager = UserManager(db)
                user_profile = user_manager.get_profile(user_id)
            except Exception as e:
                logger.warning(f"Could not load user profile: {str(e)}")
                # Continue without profile
        
        # Analyze symptoms
        from app.services.health_advisor import HealthAdvisor
        advisor = HealthAdvisor(db)
        guidance = advisor.analyze_symptoms(symptoms, user_profile)
        
        return guidance
        
    except DataNotFoundException:
        raise
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        # Return safe default guidance
        return {
            "urgency_level": "routine",
            "message": "Unable to analyze symptoms. Please consult a healthcare provider.",
            "disclaimer": "This is not medical advice. Consult a doctor for proper diagnosis.",
            "error": "Analysis unavailable"
        }


# Example 6: Rate Limit Aware Endpoint
@router.get("/api/intensive-operation")
async def intensive_operation(request: Request):
    """
    Endpoint that's aware of rate limiting
    """
    # Check if we're close to rate limit
    rate_limit_remaining = request.headers.get("X-RateLimit-Remaining", "unknown")
    
    logger.info(f"Rate limit remaining: {rate_limit_remaining}")
    
    # Perform operation
    result = {"status": "success", "data": "operation completed"}
    
    # Add rate limit info to response
    result["rate_limit_info"] = {
        "remaining": rate_limit_remaining,
        "message": "You have used most of your quota" if rate_limit_remaining == "0" else None
    }
    
    return result


# Example 7: Offline Mode Detection
@router.get("/features/offline-status")
async def check_offline_status(db: Session = Depends(get_db)):
    """
    Check which features are available offline
    """
    from app.services.network_monitor import NetworkMonitor
    
    is_online = NetworkMonitor.is_online()
    
    if not is_online:
        from app.utils.graceful_degradation import GracefulDegradation
        GracefulDegradation.offline_mode_response(
            feature_name="Online Features",
            offline_alternatives=[
                "View cached schemes",
                "Access saved content",
                "Browse offline help"
            ],
            last_sync_time=NetworkMonitor.get_last_sync_time()
        )
    
    return {
        "online": is_online,
        "features": {
            "schemes": "available",
            "market_prices": "cached_only",
            "voice": "available",
            "ai_chat": "limited"
        }
    }
