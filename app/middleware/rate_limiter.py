"""Rate limiting middleware"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import time
import asyncio
from app.logging_config import logger
from app.services.error_translator import ErrorTranslator


class RateLimiter:
    """
    Token bucket rate limiter
    Tracks requests per user/IP and enforces rate limits
    """
    
    def __init__(self):
        # Storage for rate limit data: {identifier: (tokens, last_refill_time, request_count)}
        self.buckets: Dict[str, Tuple[float, float, int]] = {}
        # Lock for thread-safe operations
        self.lock = asyncio.Lock()
        
        # Rate limit configurations per endpoint pattern
        self.limits = {
            # Voice endpoints - higher limits for core functionality
            "/api/voice-to-text": {"requests": 100, "window": 60, "burst": 10},
            "/api/text-to-voice": {"requests": 100, "window": 60, "burst": 10},
            
            # AI/RAG endpoints - moderate limits
            "/api/ask": {"requests": 50, "window": 60, "burst": 5},
            "/api/session": {"requests": 30, "window": 60, "burst": 5},
            
            # Scheme endpoints - moderate limits
            "/api/schemes": {"requests": 60, "window": 60, "burst": 10},
            "/api/schemes/check-eligibility": {"requests": 40, "window": 60, "burst": 5},
            "/api/schemes/eligible": {"requests": 40, "window": 60, "burst": 5},
            
            # Farmer advisory - moderate limits
            "/api/farmer": {"requests": 50, "window": 60, "burst": 5},
            
            # Skills and jobs - moderate limits
            "/api/skills": {"requests": 50, "window": 60, "burst": 5},
            "/api/jobs": {"requests": 50, "window": 60, "burst": 5},
            
            # Health advisory - higher limits for critical service
            "/api/health": {"requests": 80, "window": 60, "burst": 10},
            
            # Authentication - strict limits to prevent abuse
            "/api/auth/register": {"requests": 5, "window": 300, "burst": 2},
            "/api/auth/verify": {"requests": 10, "window": 300, "burst": 3},
            
            # Impact tracking - moderate limits
            "/api/impact": {"requests": 30, "window": 60, "burst": 5},
            
            # Default limit for unspecified endpoints
            "default": {"requests": 60, "window": 60, "burst": 10}
        }
    
    def get_identifier(self, request: Request) -> str:
        """
        Get unique identifier for rate limiting
        Uses user_id from auth if available, otherwise IP address
        """
        # Try to get user_id from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"
        
        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"
    
    def get_limit_config(self, path: str) -> Dict:
        """Get rate limit configuration for endpoint"""
        # Check for exact match
        if path in self.limits:
            return self.limits[path]
        
        # Check for prefix match
        for pattern, config in self.limits.items():
            if path.startswith(pattern):
                return config
        
        # Return default
        return self.limits["default"]
    
    async def is_allowed(
        self, 
        identifier: str, 
        limit_config: Dict
    ) -> Tuple[bool, Optional[int], Optional[datetime]]:
        """
        Check if request is allowed under rate limit
        
        Returns:
            (allowed, retry_after_seconds, quota_reset_time)
        """
        async with self.lock:
            current_time = time.time()
            requests_per_window = limit_config["requests"]
            window_seconds = limit_config["window"]
            burst_size = limit_config["burst"]
            
            # Get or initialize bucket
            if identifier not in self.buckets:
                # Initialize with full tokens
                self.buckets[identifier] = (burst_size, current_time, 0)
            
            tokens, last_refill, request_count = self.buckets[identifier]
            
            # Calculate token refill
            time_passed = current_time - last_refill
            refill_rate = burst_size / window_seconds
            tokens = min(burst_size, tokens + (time_passed * refill_rate))
            
            # Check if request is allowed
            if tokens >= 1.0:
                # Allow request and consume token
                tokens -= 1.0
                request_count += 1
                self.buckets[identifier] = (tokens, current_time, request_count)
                return True, None, None
            else:
                # Rate limit exceeded
                retry_after = int((1.0 - tokens) / refill_rate) + 1
                quota_reset = datetime.utcnow() + timedelta(seconds=retry_after)
                return False, retry_after, quota_reset
    
    async def cleanup_old_entries(self):
        """Remove old entries to prevent memory bloat"""
        async with self.lock:
            current_time = time.time()
            to_remove = []
            
            for identifier, (tokens, last_refill, _) in self.buckets.items():
                # Remove entries inactive for more than 1 hour
                if current_time - last_refill > 3600:
                    to_remove.append(identifier)
            
            for identifier in to_remove:
                del self.buckets[identifier]
            
            if to_remove:
                logger.info(f"Cleaned up {len(to_remove)} old rate limit entries")


# Global rate limiter instance
rate_limiter = RateLimiter()


async def rate_limiting_middleware(request: Request, call_next):
    """
    Rate limiting middleware
    Enforces rate limits per user/IP based on endpoint
    """
    # Skip rate limiting for health check
    if request.url.path == "/health":
        return await call_next(request)
    
    # Get identifier and limit config
    identifier = rate_limiter.get_identifier(request)
    limit_config = rate_limiter.get_limit_config(request.url.path)
    
    # Check rate limit
    allowed, retry_after, quota_reset = await rate_limiter.is_allowed(
        identifier, 
        limit_config
    )
    
    if not allowed:
        # Rate limit exceeded
        logger.warning(
            f"Rate limit exceeded for {identifier} on {request.url.path}"
        )
        
        # Get user's preferred language
        language = request.headers.get("Accept-Language", "en").split(",")[0].split("-")[0]
        
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "RATE_LIMIT_EXCEEDED",
                "message": ErrorTranslator.translate("RATE_LIMIT_EXCEEDED", language),
                "message_translations": ErrorTranslator.get_all_translations("RATE_LIMIT_EXCEEDED"),
                "retry_after_seconds": retry_after,
                "quota_reset_time": quota_reset.isoformat() if quota_reset else None,
                "quota_limit": limit_config["requests"],
                "retry_allowed": True,
                "timestamp": datetime.utcnow().isoformat()
            },
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(limit_config["requests"]),
                "X-RateLimit-Reset": quota_reset.isoformat() if quota_reset else ""
            }
        )
    
    # Add rate limit headers to response
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(limit_config["requests"])
    response.headers["X-RateLimit-Window"] = str(limit_config["window"])
    
    return response


# Background task to cleanup old entries
async def cleanup_rate_limiter():
    """Periodic cleanup of old rate limiter entries"""
    while True:
        await asyncio.sleep(3600)  # Run every hour
        await rate_limiter.cleanup_old_entries()
