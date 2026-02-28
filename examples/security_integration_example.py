"""
Security Integration Example

This example demonstrates how to use the security features in BharatSahayak:
1. TLS/HTTPS configuration
2. Data encryption
3. Role-based access control
4. Audit logging
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.security.rbac import RBACService, Permission, Role, require_admin
from app.security.encryption import get_encryption_service
from app.security.hashing import hash_phone_number
from app.security.audit_log import get_audit_logger
from app.utils.auth import get_current_user
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/api/secure", tags=["Security Examples"])


# ============================================================================
# Example 1: Protected Endpoint with Permission Check
# ============================================================================

@router.get("/analytics")
async def get_analytics(
    current_user: User = Depends(RBACService.require_permission(Permission.READ_ANALYTICS)),
    db: Session = Depends(get_db)
):
    """
    Get analytics data - requires READ_ANALYTICS permission
    Only ADMIN and ANALYST roles have this permission
    """
    # Log access
    audit_logger = get_audit_logger(db)
    audit_logger.log_data_access(
        user_id=str(current_user.user_id),
        user_role=current_user.role,
        resource_type="analytics",
        resource_id="dashboard",
        action="read",
        success=True
    )
    
    return {
        "message": "Analytics data",
        "user_role": current_user.role,
        "permission": "READ_ANALYTICS"
    }


# ============================================================================
# Example 2: Admin-Only Endpoint
# ============================================================================

class UserRoleUpdate(BaseModel):
    user_id: str
    new_role: str

@router.post("/admin/update-role")
async def update_user_role(
    data: UserRoleUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update user role - admin only
    """
    # Find target user
    target_user = db.query(User).filter(User.user_id == data.user_id).first()
    
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Validate role
    try:
        Role(data.new_role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {data.new_role}"
        )
    
    # Update role
    old_role = target_user.role
    target_user.role = data.new_role
    db.commit()
    
    # Log modification
    audit_logger = get_audit_logger(db)
    audit_logger.log_data_modification(
        user_id=str(current_user.user_id),
        user_role=current_user.role,
        resource_type="user",
        resource_id=str(target_user.user_id),
        action="update",
        success=True,
        metadata={
            "field": "role",
            "old_value": old_role,
            "new_value": data.new_role
        }
    )
    
    return {
        "message": "Role updated successfully",
        "user_id": str(target_user.user_id),
        "old_role": old_role,
        "new_role": data.new_role
    }


# ============================================================================
# Example 3: Encrypted Data Storage
# ============================================================================

class SensitiveData(BaseModel):
    user_id: str
    phone_number: str
    email: str

@router.post("/store-sensitive")
async def store_sensitive_data(
    data: SensitiveData,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Store sensitive data with encryption
    """
    # Get encryption service
    encryption = get_encryption_service()
    
    # Encrypt sensitive fields
    encrypted_data = {
        "phone_number": encryption.encrypt(data.phone_number),
        "phone_number_hash": hash_phone_number(data.phone_number),
        "email": encryption.encrypt(data.email)
    }
    
    # In real implementation, store in database
    # For demo, just return encrypted data
    
    # Log data storage
    audit_logger = get_audit_logger(db)
    audit_logger.log_data_modification(
        user_id=str(current_user.user_id),
        user_role=current_user.role,
        resource_type="sensitive_data",
        resource_id=data.user_id,
        action="create",
        success=True,
        metadata={"fields": ["phone_number", "email"]}
    )
    
    return {
        "message": "Data encrypted and stored",
        "encrypted_phone": encrypted_data["phone_number"][:40] + "...",
        "phone_hash": encrypted_data["phone_number_hash"][:16] + "...",
        "encrypted_email": encrypted_data["email"][:40] + "..."
    }


# ============================================================================
# Example 4: Programmatic Permission Check
# ============================================================================

@router.get("/conditional-access")
async def conditional_access(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint with conditional access based on permissions
    """
    response = {
        "user_id": str(current_user.user_id),
        "role": current_user.role,
        "permissions": []
    }
    
    # Check various permissions
    if RBACService.has_permission(current_user, Permission.READ_ANALYTICS):
        response["permissions"].append("READ_ANALYTICS")
        response["analytics_data"] = {"users": 1000, "queries": 5000}
    
    if RBACService.has_permission(current_user, Permission.MANAGE_SCHEMES):
        response["permissions"].append("MANAGE_SCHEMES")
        response["can_edit_schemes"] = True
    
    if RBACService.has_permission(current_user, Permission.READ_ALL_USERS):
        response["permissions"].append("READ_ALL_USERS")
        response["total_users"] = db.query(User).count()
    
    # Log access
    audit_logger = get_audit_logger(db)
    audit_logger.log_data_access(
        user_id=str(current_user.user_id),
        user_role=current_user.role,
        resource_type="conditional_access",
        resource_id="dashboard",
        action="read",
        success=True
    )
    
    return response


# ============================================================================
# Example 5: Audit Log Query
# ============================================================================

@router.get("/audit-logs")
async def get_audit_logs(
    limit: int = 10,
    current_user: User = Depends(RBACService.require_permission(Permission.READ_ANALYTICS)),
    db: Session = Depends(get_db)
):
    """
    Get recent audit logs - requires analytics permission
    """
    from app.security.audit_log import AuditLog
    
    # Query recent logs
    logs = db.query(AuditLog).order_by(
        AuditLog.timestamp.desc()
    ).limit(limit).all()
    
    # Format response
    audit_entries = []
    for log in logs:
        audit_entries.append({
            "timestamp": log.timestamp.isoformat(),
            "user_id": str(log.user_id) if log.user_id else None,
            "user_role": log.user_role,
            "event_type": log.event_type,
            "action": log.action,
            "resource_type": log.resource_type,
            "success": log.success,
            "ip_address": log.ip_address
        })
    
    return {
        "total": len(audit_entries),
        "logs": audit_entries
    }


# ============================================================================
# Example 6: User Lookup with Encrypted Phone
# ============================================================================

@router.get("/lookup-user/{phone_number}")
async def lookup_user_by_phone(
    phone_number: str,
    current_user: User = Depends(RBACService.require_permission(Permission.READ_ALL_USERS)),
    db: Session = Depends(get_db)
):
    """
    Lookup user by phone number - demonstrates searchable encryption
    Only admins can access
    """
    # Hash phone number for lookup
    phone_hash = hash_phone_number(phone_number)
    
    # Find user by hash
    user = db.query(User).filter(User.phone_number_hash == phone_hash).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Log access
    audit_logger = get_audit_logger(db)
    audit_logger.log_data_access(
        user_id=str(current_user.user_id),
        user_role=current_user.role,
        resource_type="user",
        resource_id=str(user.user_id),
        action="read",
        success=True
    )
    
    # Phone number is automatically decrypted when accessed
    return {
        "user_id": str(user.user_id),
        "phone_number": user.phone_number,  # Decrypted automatically
        "language": user.language,
        "role": user.role,
        "created_at": user.created_at.isoformat()
    }


# ============================================================================
# Example 7: Role-Based Data Filtering
# ============================================================================

@router.get("/users")
async def list_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List users - data filtered based on role
    - Regular users: only see themselves
    - Admins: see all users
    """
    if RBACService.has_permission(current_user, Permission.READ_ALL_USERS):
        # Admin can see all users
        users = db.query(User).all()
        message = "All users (admin access)"
    else:
        # Regular user can only see themselves
        users = [current_user]
        message = "Your profile only"
    
    # Format response (without sensitive data for non-admins)
    user_list = []
    for user in users:
        user_data = {
            "user_id": str(user.user_id),
            "language": user.language,
            "role": user.role
        }
        
        # Only admins see phone numbers
        if RBACService.has_permission(current_user, Permission.READ_ALL_USERS):
            user_data["phone_number"] = user.phone_number
        
        user_list.append(user_data)
    
    return {
        "message": message,
        "count": len(user_list),
        "users": user_list
    }


# ============================================================================
# Usage Instructions
# ============================================================================

"""
To use these examples:

1. Include this router in your FastAPI app:
   
   from examples.security_integration_example import router as security_router
   app.include_router(security_router)

2. Test with different user roles:
   
   # Regular user (limited access)
   curl -H "Authorization: Bearer <user-token>" http://localhost:8000/api/secure/users
   
   # Admin (full access)
   curl -H "Authorization: Bearer <admin-token>" http://localhost:8000/api/secure/users
   
   # Analyst (analytics access)
   curl -H "Authorization: Bearer <analyst-token>" http://localhost:8000/api/secure/analytics

3. Check audit logs:
   
   curl -H "Authorization: Bearer <admin-token>" http://localhost:8000/api/secure/audit-logs

4. Test permission denied:
   
   # Regular user trying to access admin endpoint (should fail)
   curl -H "Authorization: Bearer <user-token>" http://localhost:8000/api/secure/admin/update-role
"""
