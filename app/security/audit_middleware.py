"""Middleware for automatic audit logging"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.database import SessionLocal
from app.security.audit_log import get_audit_logger
from app.logging_config import logger
from typing import Callable


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically log API requests"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        """
        Process request and log audit trail
        
        Args:
            request: FastAPI request
            call_next: Next middleware/handler
            
        Returns:
            Response
        """
        # Get request information
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        endpoint = request.url.path
        method = request.method
        
        # Process request
        response = await call_next(request)
        
        # Log sensitive endpoints
        sensitive_endpoints = [
            "/api/user/profile",
            "/api/user/data",
            "/api/auth/",
            "/api/impact/",
        ]
        
        should_log = any(endpoint.startswith(path) for path in sensitive_endpoints)
        
        if should_log:
            try:
                # Get user from request state (set by auth dependency)
                user_id = getattr(request.state, "user_id", None)
                user_role = getattr(request.state, "user_role", None)
                
                # Create database session for audit logging
                db = SessionLocal()
                try:
                    audit_logger = get_audit_logger(db)
                    
                    # Determine action from method and endpoint
                    action = f"{method}_{endpoint}"
                    success = 200 <= response.status_code < 400
                    
                    audit_logger.log_event(
                        event_type="access",
                        action=action,
                        success=success,
                        user_id=user_id,
                        user_role=user_role,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        endpoint=endpoint,
                        error_message=None if success else f"Status: {response.status_code}"
                    )
                finally:
                    db.close()
            
            except Exception as e:
                # Don't fail request if audit logging fails
                logger.error(f"Audit logging failed: {str(e)}")
        
        return response
