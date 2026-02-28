"""Main FastAPI application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.middleware import (
    error_handling_middleware,
    logging_middleware,
    setup_exception_handlers
)
from app.middleware.rate_limiter import rate_limiting_middleware, cleanup_rate_limiter
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.voice import router as voice_router
from app.api.rag import router as rag_router
from app.api.schemes import router as schemes_router
from app.api.farmer import router as farmer_router
from app.api.skills import router as skills_router
from app.api.health_advisory import router as health_advisory_router
from app.api.language import router as language_router
from app.api.impact import router as impact_router
from app.api.cache import router as cache_router
from app.api.integrated import router as integrated_router
from app.middleware.impact_tracking import setup_impact_tracking_middleware
from app.logging_config import logger
import asyncio

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Multilingual AI Public Assistant for Rural India",
    debug=settings.debug
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware (order matters - rate limiting before error handling)
app.middleware("http")(rate_limiting_middleware)
app.middleware("http")(logging_middleware)
app.middleware("http")(error_handling_middleware)

# Setup impact tracking middleware
setup_impact_tracking_middleware(app)

# Setup exception handlers
setup_exception_handlers(app)

# Include routers
app.include_router(health_router, tags=["Health"])
app.include_router(auth_router, tags=["Authentication"])
app.include_router(voice_router, tags=["Voice"])
app.include_router(rag_router, tags=["RAG & Conversation"])
app.include_router(schemes_router, tags=["Schemes"])
app.include_router(farmer_router, tags=["Farmer Advisory"])
app.include_router(skills_router, tags=["Skills & Employment"])
app.include_router(health_advisory_router, tags=["Health Advisory"])
app.include_router(language_router, tags=["Language Processing"])
app.include_router(impact_router, tags=["Impact Tracking"])
app.include_router(cache_router, tags=["Offline Cache"])
app.include_router(integrated_router, tags=["Integrated Flows"])

# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup"""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Log level: {settings.log_level}")
    
    # Start rate limiter cleanup task
    asyncio.create_task(cleanup_rate_limiter())
    logger.info("Rate limiter cleanup task started")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    logger.info(f"Shutting down {settings.app_name}")


if __name__ == "__main__":
    import uvicorn
    from app.security.tls_config import get_tls_config
    
    # Get TLS configuration
    tls_config = get_tls_config()
    ssl_config = tls_config.get_uvicorn_ssl_config() if settings.tls_enabled else {}
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000 if not settings.tls_enabled else 8443,
        reload=settings.debug,
        **ssl_config
    )
