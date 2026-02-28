# Security Implementation Guide

## Overview

This document describes the security features implemented in BharatSahayak, including TLS/HTTPS configuration, data encryption at rest, and role-based access control (RBAC).

## 1. TLS/HTTPS Configuration

### Setup

The application supports TLS 1.3 (or TLS 1.2 as fallback) for secure communication.

#### Generate Self-Signed Certificate (Development)

```bash
python scripts/generate_self_signed_cert.py
```

This creates:
- `certs/cert.pem` - SSL certificate
- `certs/key.pem` - Private key

#### Configure Environment

Add to `.env`:

```env
TLS_ENABLED=true
TLS_CERT_PATH=certs/cert.pem
TLS_KEY_PATH=certs/key.pem
```

#### Run with HTTPS

```bash
python app/main.py
```

The server will run on port 8443 with HTTPS enabled.

#### Production Certificates

For production, use certificates from a trusted CA (Let's Encrypt, etc.):

```env
TLS_ENABLED=true
TLS_CERT_PATH=/etc/letsencrypt/live/yourdomain.com/fullchain.pem
TLS_KEY_PATH=/etc/letsencrypt/live/yourdomain.com/privkey.pem
```

## 2. Data Encryption at Rest

### AES-256 Encryption

Sensitive PII fields are encrypted using AES-256-CBC before storing in the database.

#### Generate Encryption Key

```bash
python scripts/generate_encryption_key.py
```

Add the generated key to `.env`:

```env
ENCRYPTION_KEY=<base64-encoded-key>
```

#### Encrypted Fields

The following fields are automatically encrypted:

- `User.phone_number` - Encrypted phone number
- Additional PII fields can be added using `EncryptedString` type

#### Usage in Models

```python
from app.security.encrypted_types import EncryptedString

class User(Base):
    phone_number = Column(EncryptedString(15), nullable=False)
```

#### Searchable Encrypted Fields

For fields that need to be searchable (like phone numbers), we use a hash:

```python
from app.security.hashing import hash_phone_number

# Store both encrypted value and hash
user.phone_number = "1234567890"  # Automatically encrypted
user.phone_number_hash = hash_phone_number("1234567890")  # For lookups
```

#### Manual Encryption

```python
from app.security.encryption import get_encryption_service

encryption = get_encryption_service()

# Encrypt
encrypted = encryption.encrypt("sensitive data")

# Decrypt
decrypted = encryption.decrypt(encrypted)

# Encrypt dictionary fields
data = {"name": "John", "phone": "1234567890"}
encrypted_data = encryption.encrypt_dict(data, ["phone"])
```

## 3. Role-Based Access Control (RBAC)

### Roles

Three roles are defined:

1. **USER** - Regular users (default)
   - Access own profile
   - Query all services
   - Delete own data

2. **ADMIN** - Administrators
   - All user permissions
   - Manage all users
   - Manage schemes and content
   - Access analytics

3. **ANALYST** - Data analysts
   - User permissions
   - Read analytics
   - Export data

### Permissions

Permissions are granular and mapped to roles:

```python
from app.security.rbac import Permission

# User permissions
Permission.READ_OWN_PROFILE
Permission.WRITE_OWN_PROFILE
Permission.DELETE_OWN_DATA
Permission.QUERY_SCHEMES
Permission.QUERY_FARMER
Permission.QUERY_SKILLS
Permission.QUERY_HEALTH
Permission.QUERY_RAG

# Admin permissions
Permission.READ_ALL_USERS
Permission.WRITE_ALL_USERS
Permission.DELETE_ALL_USERS
Permission.MANAGE_SCHEMES
Permission.MANAGE_CONTENT

# Analyst permissions
Permission.READ_ANALYTICS
Permission.READ_IMPACT_METRICS
Permission.EXPORT_DATA
```

### Usage in Endpoints

#### Require Specific Permission

```python
from fastapi import APIRouter, Depends
from app.security.rbac import RBACService, Permission

router = APIRouter()

@router.get("/analytics")
async def get_analytics(
    current_user = Depends(RBACService.require_permission(Permission.READ_ANALYTICS))
):
    # Only users with READ_ANALYTICS permission can access
    return {"data": "analytics"}
```

#### Require Specific Role

```python
from app.security.rbac import require_admin

@router.post("/admin/users")
async def create_user(
    current_user = Depends(require_admin)
):
    # Only admins can access
    return {"message": "User created"}
```

#### Check Permission Programmatically

```python
from app.security.rbac import RBACService, Permission

if RBACService.has_permission(current_user, Permission.MANAGE_SCHEMES):
    # User has permission
    pass
```

### Setting User Roles

Roles are stored in the `users.role` field:

```python
# Set user role (admin only)
user.role = "admin"
db.commit()
```

## 4. Audit Logging

All sensitive operations are automatically logged for security auditing.

### Audit Log Fields

- `timestamp` - When the event occurred
- `user_id` - User who performed the action
- `user_role` - User's role
- `event_type` - Type of event (access, create, update, delete, auth, error)
- `resource_type` - Type of resource accessed
- `resource_id` - ID of resource
- `action` - Action performed
- `ip_address` - Client IP
- `user_agent` - Client user agent
- `endpoint` - API endpoint
- `success` - Whether action succeeded
- `error_message` - Error message if failed
- `metadata` - Additional context

### Manual Audit Logging

```python
from app.security.audit_log import get_audit_logger

audit_logger = get_audit_logger(db)

# Log data access
audit_logger.log_data_access(
    user_id=str(user.user_id),
    user_role=user.role,
    resource_type="profile",
    resource_id=str(profile.profile_id),
    action="read",
    success=True,
    ip_address=request.client.host,
    endpoint="/api/user/profile"
)

# Log authentication
audit_logger.log_authentication(
    user_id=str(user.user_id),
    action="login",
    success=True,
    ip_address=request.client.host
)

# Log data modification
audit_logger.log_data_modification(
    user_id=str(user.user_id),
    user_role=user.role,
    resource_type="scheme",
    resource_id=str(scheme.scheme_id),
    action="update",
    success=True,
    metadata={"fields_changed": ["name", "description"]}
)
```

### Automatic Audit Logging

The `AuditMiddleware` automatically logs requests to sensitive endpoints:

- `/api/user/profile`
- `/api/user/data`
- `/api/auth/*`
- `/api/impact/*`

To enable, add to `app/main.py`:

```python
from app.security.audit_middleware import AuditMiddleware

app.add_middleware(AuditMiddleware)
```

### Querying Audit Logs

```python
from app.security.audit_log import AuditLog

# Get recent authentication attempts
auth_logs = db.query(AuditLog).filter(
    AuditLog.event_type == "auth"
).order_by(AuditLog.timestamp.desc()).limit(100).all()

# Get failed access attempts
failed_access = db.query(AuditLog).filter(
    AuditLog.event_type == "access",
    AuditLog.success == "failure"
).all()

# Get user's activity
user_activity = db.query(AuditLog).filter(
    AuditLog.user_id == user_id
).order_by(AuditLog.timestamp.desc()).all()
```

## 5. Security Best Practices

### Environment Variables

Never commit sensitive values to version control:

```env
# .env (add to .gitignore)
SECRET_KEY=<random-secret-key>
ENCRYPTION_KEY=<base64-encoded-key>
TLS_CERT_PATH=certs/cert.pem
TLS_KEY_PATH=certs/key.pem
```

### Password/Secret Generation

```bash
# Generate random secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate encryption key
python scripts/generate_encryption_key.py
```

### Database Migrations

After adding security fields, run migrations:

```bash
alembic upgrade head
```

### Populate Phone Number Hashes

For existing users, populate phone_number_hash:

```python
from app.security.hashing import hash_phone_number

users = db.query(User).all()
for user in users:
    if not user.phone_number_hash:
        # Decrypt phone number, hash it
        user.phone_number_hash = hash_phone_number(user.phone_number)
db.commit()
```

## 6. Testing Security

### Test Encryption

```python
from app.security.encryption import get_encryption_service

encryption = get_encryption_service()

# Test round-trip
original = "sensitive data"
encrypted = encryption.encrypt(original)
decrypted = encryption.decrypt(encrypted)

assert original == decrypted
assert encrypted != original
```

### Test RBAC

```python
from app.security.rbac import RBACService, Role, Permission

# Test permission check
user.role = "user"
assert RBACService.has_permission(user, Permission.READ_OWN_PROFILE)
assert not RBACService.has_permission(user, Permission.READ_ALL_USERS)

# Test admin permissions
admin.role = "admin"
assert RBACService.has_permission(admin, Permission.READ_ALL_USERS)
```

### Test Audit Logging

```python
from app.security.audit_log import get_audit_logger

audit_logger = get_audit_logger(db)

# Log event
audit_logger.log_data_access(
    user_id=str(user.user_id),
    user_role="user",
    resource_type="profile",
    resource_id=str(profile.profile_id),
    action="read",
    success=True
)

# Verify log created
logs = db.query(AuditLog).filter(AuditLog.user_id == user.user_id).all()
assert len(logs) > 0
```

## 7. Compliance

### GDPR Compliance

- **Data Encryption**: PII is encrypted at rest
- **Data Deletion**: Users can delete all their data via `/api/user/data`
- **Audit Trail**: All data access is logged
- **Consent**: Users must consent during registration

### Security Standards

- **TLS 1.3**: Secure communication
- **AES-256**: Strong encryption
- **RBAC**: Principle of least privilege
- **Audit Logging**: Accountability and traceability

## 8. Troubleshooting

### Encryption Key Not Set

```
ValueError: Encryption key not configured
```

Solution: Generate and set `ENCRYPTION_KEY` in `.env`

### TLS Certificate Not Found

```
FileNotFoundError: Certificate file not found
```

Solution: Generate certificates or set correct paths in `.env`

### Permission Denied

```
HTTPException: 403 Forbidden - Permission denied
```

Solution: Check user role and required permissions

### Decryption Failed

```
ValueError: Decryption failed
```

Solution: Verify encryption key hasn't changed. Data encrypted with one key cannot be decrypted with another.
