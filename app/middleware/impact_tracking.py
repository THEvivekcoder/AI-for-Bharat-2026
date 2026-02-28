"""
Middleware for automatic impact tracking
Tracks interactions with domain services automatically
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import logging
import json

from app.services.impact_tracker import ImpactTracker
from app.schemas.impact import InteractionEventCreate, InteractionEventType
from app.database import SessionLocal

logger = logging.getLogger(__name__)


class ImpactTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically track interactions with domain services
    
    Tracks:
    - Scheme access (GET /api/schemes/{id})
    - Job discovery (GET /api/jobs/{id})
    - Skill program views (GET /api/skills/{id})
    - Health checks (POST /api/health/check)
    - Farmer advisory requests
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        """Process request and track relevant interactions"""
        
        # Process the request
        response = await call_next(request)
        
        # Only track successful requests (2xx status codes)
        if 200 <= response.status_code < 300:
            await self._track_interaction(request, response)
        
        return response
    
    async def _track_interaction(self, request: Request, response):
        """Track interaction based on endpoint"""
        try:
            path = request.url.path
            method = request.method
            
            # Get user ID from request state (set by auth middleware)
            user_id = getattr(request.state, "user_id", None)
            if not user_id:
                return  # Skip tracking if no user
            
            # Get language from headers or default to English
            language = request.headers.get("Accept-Language", "en").split(",")[0][:2]
            
            # Determine event type and data based on endpoint
            event_type = None
            event_data = {}
            
            # Scheme endpoints
            if path.startswith("/api/schemes/") and method == "GET":
                if "/check-eligibility" not in path and "/eligible" not in path:
                    scheme_id = path.split("/")[-1]
                    event_type = InteractionEventType.SCHEME_ACCESSED
                    event_data = {"scheme_id": scheme_id}
            
            # Job endpoints
            elif path.startswith("/api/jobs/") and method == "GET":
                job_id = path.split("/")[-1]
                event_type = InteractionEventType.JOB_DISCOVERED
                event_data = {"job_id": job_id}
            
            # Skill program endpoints
            elif path.startswith("/api/skills/") and method == "GET":
                program_id = path.split("/")[-1]
                event_type = InteractionEventType.SKILL_PROGRAM_VIEWED
                event_data = {"program_id": program_id}
            
            # Health check endpoint
            elif path == "/api/health/check" and method == "POST":
                event_type = InteractionEventType.HEALTH_CHECK_PERFORMED
                # Note: We can't easily get request body here without consuming it
                event_data = {"endpoint": path}
            
            # Farmer advisory endpoints
            elif path == "/api/farmer/crop-advice" and method == "POST":
                event_type = InteractionEventType.CROP_ADVICE_REQUESTED
                event_data = {"endpoint": path}
            
            elif path == "/api/farmer/fertilizer-advice" and method == "POST":
                event_type = InteractionEventType.FERTILIZER_ADVICE_REQUESTED
                event_data = {"endpoint": path}
            
            elif path == "/api/farmer/market-price" and method == "GET":
                event_type = InteractionEventType.MARKET_PRICE_CHECKED
                # Get crop name from query params
                crop_name = request.query_params.get("crop_name")
                if crop_name:
                    event_data = {"crop_name": crop_name}
            
            # Health facility search
            elif path == "/api/health/facilities" and method == "GET":
                event_type = InteractionEventType.FACILITY_LOCATED
                facility_type = request.query_params.get("facility_type")
                if facility_type:
                    event_data = {"facility_type": facility_type}
            
            # Track the interaction if we identified an event type
            if event_type:
                db = SessionLocal()
                try:
                    tracker = ImpactTracker(db)
                    event = InteractionEventCreate(
                        user_id=str(user_id),
                        event_type=event_type,
                        event_data=event_data,
                        language=language
                    )
                    tracker.record_interaction(event)
                    logger.debug(f"Tracked interaction: {event_type.value} for user {user_id}")
                except Exception as e:
                    logger.error(f"Error tracking interaction: {str(e)}")
                finally:
                    db.close()
        
        except Exception as e:
            logger.error(f"Error in impact tracking middleware: {str(e)}")
            # Don't fail the request if tracking fails


def setup_impact_tracking_middleware(app):
    """Add impact tracking middleware to FastAPI app"""
    app.add_middleware(ImpactTrackingMiddleware)
    logger.info("Impact tracking middleware enabled")
