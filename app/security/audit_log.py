"""Audit logging for data access and security events"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base
from app.logging_config import logger
import uuid


class AuditLog(Base):
    """Audit log for tracking data access and security events"""
    __tablename__ = "audit_logs"
    
    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # User information
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    user_role = Column(String(20), nullable=True)
    
    # Event information
    event_type = Column(String(50), nullable=False, index=True)  # access, create, update, delete, auth, error
    resource_type = Column(String(50), nullable=True)  # user, scheme, profile, etc.
    resource_id = Column(String(100), nullable=True)
    action = Column(String(100), nullable=False)
    
    # Request information
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    endpoint = Column(String(200), nullable=True)
    
    # Result
    success = Column(String(10), nullable=False)  # success, failure, error
    error_message = Column(Text, nullable=True)
    
    # Additional context
    event_metadata = Column(JSONB, nullable=True)


class AuditLogger:
    """Service for logging audit events"""
    
    def __init__(self, db):
        """
        Initialize audit logger
        
        Args:
            db: Database session
        """
        self.db = db
    
    def log_event(
        self,
        event_type: str,
        action: str,
        success: bool,
        user_id: Optional[str] = None,
        user_role: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        endpoint: Optional[str] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log an audit event
        
        Args:
            event_type: Type of event (access, create, update, delete, auth, error)
            action: Action performed
            success: Whether action was successful
            user_id: User ID (if applicable)
            user_role: User role (if applicable)
            resource_type: Type of resource accessed
            resource_id: ID of resource accessed
            ip_address: Client IP address
            user_agent: Client user agent
            endpoint: API endpoint
            error_message: Error message (if failed)
            metadata: Additional context
        """
        try:
            audit_log = AuditLog(
                user_id=user_id,
                user_role=user_role,
                event_type=event_type,
                resource_type=resource_type,
                resource_id=resource_id,
                action=action,
                ip_address=ip_address,
                user_agent=user_agent,
                endpoint=endpoint,
                success="success" if success else "failure",
                error_message=error_message,
                event_metadata=metadata
            )
            
            self.db.add(audit_log)
            self.db.commit()
            
            # Also log to application logger for critical events
            if event_type in ["auth", "delete", "error"]:
                log_msg = (
                    f"AUDIT: {event_type.upper()} - {action} - "
                    f"User: {user_id or 'anonymous'} - "
                    f"Success: {success}"
                )
                if error_message:
                    log_msg += f" - Error: {error_message}"
                
                if success:
                    logger.info(log_msg)
                else:
                    logger.warning(log_msg)
        
        except Exception as e:
            # Don't fail the main operation if audit logging fails
            logger.error(f"Failed to write audit log: {str(e)}")
            self.db.rollback()
    
    def log_data_access(
        self,
        user_id: str,
        user_role: str,
        resource_type: str,
        resource_id: str,
        action: str,
        success: bool = True,
        ip_address: Optional[str] = None,
        endpoint: Optional[str] = None
    ):
        """
        Log data access event
        
        Args:
            user_id: User ID
            user_role: User role
            resource_type: Type of resource
            resource_id: Resource ID
            action: Action performed (read, write, delete)
            success: Whether access was successful
            ip_address: Client IP
            endpoint: API endpoint
        """
        self.log_event(
            event_type="access",
            action=f"{action}_{resource_type}",
            success=success,
            user_id=user_id,
            user_role=user_role,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            endpoint=endpoint
        )
    
    def log_authentication(
        self,
        user_id: Optional[str],
        action: str,
        success: bool,
        ip_address: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        """
        Log authentication event
        
        Args:
            user_id: User ID (if known)
            action: Authentication action (login, logout, token_refresh)
            success: Whether authentication was successful
            ip_address: Client IP
            error_message: Error message if failed
        """
        self.log_event(
            event_type="auth",
            action=action,
            success=success,
            user_id=user_id,
            ip_address=ip_address,
            error_message=error_message
        )
    
    def log_data_modification(
        self,
        user_id: str,
        user_role: str,
        resource_type: str,
        resource_id: str,
        action: str,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log data modification event
        
        Args:
            user_id: User ID
            user_role: User role
            resource_type: Type of resource
            resource_id: Resource ID
            action: Action performed (create, update, delete)
            success: Whether modification was successful
            metadata: Additional context (e.g., fields changed)
        """
        self.log_event(
            event_type=action,
            action=f"{action}_{resource_type}",
            success=success,
            user_id=user_id,
            user_role=user_role,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata=metadata
        )


def get_audit_logger(db):
    """Get audit logger instance"""
    return AuditLogger(db)
