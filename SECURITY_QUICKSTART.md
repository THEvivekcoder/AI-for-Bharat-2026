# Security Quick Start Guide

## Setup (5 minutes)

### 1. Generate Encryption Key

```bash
python scripts/generate_encryption_key.py
```

Copy the output and add to `.env`:

```env
ENCRYPTION_KEY=<your-generated-key>
```

### 2. Run Database Migration

```bash
alembic upgrade head
```

### 3. Test Security

```bash
python scripts/test_security.py
```

You should see: ✅ ALL TESTS PASSED!

## Optional: Enable HTTPS

### Development

```bash
# Generate self-signed certificate
python scripts/generate_self_signed_cert.py

# Add to .env
TLS_ENABLED=true
TLS_CERT_PATH=certs/cert.pem
TLS_KEY_PATH=certs/key.pem
```

### Production

Use Let's Encrypt or your CA certificate:

```env
TLS_ENABLED=true
TLS_CERT_PATH=/etc/letsencrypt/live/yourdomain.com/fullchain.pem
TLS_KEY_PATH=/etc/letsencrypt/live/yourdomain.com/privkey.pem
```

## Usage

### Protect Endpoint with Permission

```python
from fastapi import APIRouter, Depends
from app.security.rbac import RBACService, Permission

router = APIRouter()

@router.get("/analytics")
async def get_analytics(
    current_user = Depends(RBACService.require_permission(Permission.READ_ANALYTICS))
):
    return {"data": "analytics"}
```

### Protect Endpoint with Role

```python
from app.security.rbac import require_admin

@router.post("/admin/users")
async def create_user(current_user = Depends(require_admin)):
    return {"message": "User created"}
```

### Encrypt Sensitive Data

```python
from app.security.encryption import get_encryption_service

encryption = get_encryption_service()

# Encrypt
encrypted = encryption.encrypt("sensitive data")

# Decrypt
decrypted = encryption.decrypt(encrypted)
```

### Log Audit Event

```python
from app.security.audit_log import get_audit_logger

audit_logger = get_audit_logger(db)

audit_logger.log_data_access(
    user_id=str(user.user_id),
    user_role=user.role,
    resource_type="profile",
    resource_id=str(profile.profile_id),
    action="read",
    success=True
)
```

## Roles & Permissions

### Roles
- **user** - Regular users (default)
- **admin** - Administrators
- **analyst** - Data analysts

### Set User Role

```python
user.role = "admin"
db.commit()
```

### Check Permission

```python
from app.security.rbac import RBACService, Permission

if RBACService.has_permission(user, Permission.MANAGE_SCHEMES):
    # User has permission
    pass
```

## Security Checklist

- [ ] Generated encryption key
- [ ] Added ENCRYPTION_KEY to .env
- [ ] Ran database migrations
- [ ] Tested security implementation
- [ ] (Optional) Generated TLS certificates
- [ ] (Optional) Enabled HTTPS
- [ ] Never commit .env to version control
- [ ] Backup encryption key securely

## Troubleshooting

### "Encryption key not configured"
→ Generate key and add to .env: `ENCRYPTION_KEY=...`

### "Certificate file not found"
→ Generate certificates: `python scripts/generate_self_signed_cert.py`

### "Permission denied"
→ Check user role and required permission

### "Decryption failed"
→ Encryption key changed. Data encrypted with one key cannot be decrypted with another.

## Documentation

- Full guide: `docs/security_implementation.md`
- Task summary: `docs/task_19_completion_summary.md`
- Tests: `scripts/test_security.py`

## Support

For issues or questions, refer to the comprehensive documentation in `docs/security_implementation.md`.
