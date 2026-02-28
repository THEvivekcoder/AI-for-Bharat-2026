"""Health check endpoint"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import text  # ✅ IMPORTANT FIX
from app.schemas.health import HealthResponse
from app.database import get_db
from app.redis_client import get_redis
from app.config import get_settings
from app.logging_config import logger

router = APIRouter()
settings = get_settings()


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint
    
    Verifies:
    - API is running
    - Database connection is healthy
    - Redis connection is healthy
    
    Returns:
        HealthResponse with status and service health
    """
    services = {}
    
    # -----------------------
    # Check database
    # -----------------------
    try:
        db.execute(text("SELECT 1"))   # ✅ SQLAlchemy 2.0 FIX
        services["database"] = "healthy"
        logger.debug("Database health check: OK")
    except Exception as e:
        services["database"] = "unhealthy"
        logger.error(f"Database health check failed: {str(e)}")
    
    # -----------------------
    # Check Redis
    # -----------------------
    try:
        redis_client = get_redis()
        redis_client.ping()
        services["redis"] = "healthy"
        logger.debug("Redis health check: OK")
    except Exception as e:
        services["redis"] = "unhealthy"
        logger.error(f"Redis health check failed: {str(e)}")
    
    # -----------------------
    # Overall status
    # -----------------------
    overall_status = "healthy" if all(s == "healthy" for s in services.values()) else "degraded"
    
    return HealthResponse(
        status=overall_status,
        version=settings.app_version,
        services=services
    )