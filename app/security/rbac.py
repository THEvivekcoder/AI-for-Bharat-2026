"""Role-Based Access Control (RBAC) implementation"""
from enum import Enum
from typing import List, Optional
from fastapi import HTTPException, status, Depends
from app.utils.auth import get_current_user
from app.models.user import User
from app.logging_config import logger


class Role(str, Enum):
    """User roles"""
    USER = "user"
    ADMIN = "admin"
    ANALYST = "analyst"


class Permission(str, Enum):
    """System permissions"""
    # User permissions
    READ_OWN_PROFILE = "read:own_profile"
    WRITE_OWN_PROFILE = "write:own_profile"
    DELETE_OWN_DATA = "delete:own_data"
    
    # Query permissions
    QUERY_SCHEMES = "query:schemes"
    QUERY_FARMER = "query:farmer"
    QUERY_SKILLS = "query:skills"
    QUERY_HEALTH = "query:health"
    QUERY_RAG = "query:rag"
    
    # Admin permissions
    READ_ALL_USERS = "read:all_users"
    WRITE_ALL_USERS = "write:all_users"
    DELETE_ALL_USERS = "delete:all_users"
    MANAGE_SCHEMES = "manage:schemes"
    MANAGE_CONTENT = "manage:content"
    
    # Analyst permissions
    READ_ANALYTICS = "read:analytics"
    READ_IMPACT_METRICS = "read:impact_metrics"
    EXPORT_DATA = "export:data"


# Role to permissions mapping
ROLE_PERMISSIONS = {
    Role.USER: [
        Permission.READ_OWN_PROFILE,
        Permission.WRITE_OWN_PROFILE,
        Permission.DELETE_OWN_DATA,
        Permission.QUERY_SCHEMES,
        Permission.QUERY_FARMER,
        Permission.QUERY_SKILLS,
        Permission.QUERY_HEALTH,
        Permission.QUERY_RAG,
    ],
    Role.ADMIN: [
        # All user permissions
        Permission.READ_OWN_PROFILE,
        Permission.WRITE_OWN_PROFILE,
        Permission.DELETE_OWN_DATA,
        Permission.QUERY_SCHEMES,
        Permission.QUERY_FARMER,
        Permission.QUERY_SKILLS,
        Permission.QUERY_HEALTH,
        Permission.QUERY_RAG,
        # Admin permissions
        Permission.READ_ALL_USERS,
        Permission.WRITE_ALL_USERS,
        Permission.DELETE_ALL_USERS,
        Permission.MANAGE_SCHEMES,
        Permission.MANAGE_CONTENT,
        # Analyst permissions
        Permission.READ_ANALYTICS,
        Permission.READ_IMPACT_METRICS,
        Permission.EXPORT_DATA,
    ],
    Role.ANALYST: [
        # User permissions
        Permission.READ_OWN_PROFILE,
        Permission.WRITE_OWN_PROFILE,
        Permission.QUERY_SCHEMES,
        Permission.QUERY_FARMER,
        Permission.QUERY_SKILLS,
        Permission.QUERY_HEALTH,
        Permission.QUERY_RAG,
        # Analyst permissions
        Permission.READ_ANALYTICS,
        Permission.READ_IMPACT_METRICS,
        Permission.EXPORT_DATA,
    ],
}


class RBACService:
    """Role-Based Access Control service"""
    
    @staticmethod
    def get_user_role(user: User) -> Role:
        """
        Get user's role
        
        Args:
            user: User object
            
        Returns:
            User's role (defaults to USER)
        """
        # Check if user has role attribute
        if hasattr(user, 'role') and user.role:
            try:
                return Role(user.role)
            except ValueError:
                logger.warning(f"Invalid role for user {user.user_id}: {user.role}")
        
        # Default to USER role
        return Role.USER
    
    @staticmethod
    def get_role_permissions(role: Role) -> List[Permission]:
        """
        Get permissions for a role
        
        Args:
            role: User role
            
        Returns:
            List of permissions
        """
        return ROLE_PERMISSIONS.get(role, [])
    
    @staticmethod
    def has_permission(user: User, permission: Permission) -> bool:
        """
        Check if user has a specific permission
        
        Args:
            user: User object
            permission: Permission to check
            
        Returns:
            True if user has permission, False otherwise
        """
        role = RBACService.get_user_role(user)
        permissions = RBACService.get_role_permissions(role)
        return permission in permissions
    
    @staticmethod
    def require_permission(permission: Permission):
        """
        Decorator to require a specific permission
        
        Args:
            permission: Required permission
            
        Returns:
            Dependency function
        """
        def permission_checker(current_user: User = Depends(get_current_user)):
            if not RBACService.has_permission(current_user, permission):
                logger.warning(
                    f"Permission denied for user {current_user.user_id}: {permission}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission.value}"
                )
            return current_user
        
        return permission_checker
    
    @staticmethod
    def require_role(role: Role):
        """
        Decorator to require a specific role
        
        Args:
            role: Required role
            
        Returns:
            Dependency function
        """
        def role_checker(current_user: User = Depends(get_current_user)):
            user_role = RBACService.get_user_role(current_user)
            if user_role != role:
                logger.warning(
                    f"Role check failed for user {current_user.user_id}: "
                    f"required {role}, has {user_role}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role required: {role.value}"
                )
            return current_user
        
        return role_checker


# Convenience functions for common permission checks
def require_admin(current_user: User = Depends(get_current_user)):
    """Require admin role"""
    return RBACService.require_role(Role.ADMIN)(current_user)


def require_analyst(current_user: User = Depends(get_current_user)):
    """Require analyst role"""
    return RBACService.require_role(Role.ANALYST)(current_user)


def require_analytics_access(current_user: User = Depends(get_current_user)):
    """Require analytics read permission"""
    return RBACService.require_permission(Permission.READ_ANALYTICS)(current_user)
