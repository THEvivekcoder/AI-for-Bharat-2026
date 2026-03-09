# BharatSahayak - Quick Reference

## API Endpoint
```
https://ktlbemv6uh.execute-api.us-east-1.amazonaws.com/dev/
```

## Test Credentials
```
Email: test@bharatsahayak.com
Password: Test123!
User ID: 6fb4b13b-21ff-4691-9a8f-554a83be445b
```

## Quick Test Commands

### Register
```bash
curl -X POST https://ktlbemv6uh.execute-api.us-east-1.amazonaws.com/dev/auth/email/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"Pass123!","name":"User Name"}'
```

### Login
```bash
curl -X POST https://ktlbemv6uh.execute-api.us-east-1.amazonaws.com/dev/auth/email/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"Pass123!"}'
```

### Get Profile (with JWT)
```bash
curl https://ktlbemv6uh.execute-api.us-east-1.amazonaws.com/dev/user/profile \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Frontend
```
Open: frontend/login-email.html
Config: frontend/config.json (already configured)
```

## Redeploy After Changes
```powershell
$env:PATH = "C:\Users\reeta dwivedi\AppData\Local\Programs\Python\Python312;" + $env:PATH
sam build
sam deploy --stack-name bharatsahayak-dev --region us-east-1 --parameter-overrides "Environment=dev JWTSecret=To2gBlws9qRhc8HNj7SALGfXzWdYeyZv" --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM --no-confirm-changeset --resolve-s3
```

## Key Files
- `template.yaml` - Infrastructure definition
- `src/api/auth_email_register.py` - Registration handler
- `src/api/auth_email_login.py` - Login handler
- `src/utils/jwt_auth.py` - JWT middleware
- `frontend/login-email.html` - Login UI
- `frontend/api-client-email.js` - API client

## AWS Resources
- Stack: bharatsahayak-dev
- Region: us-east-1
- Account: 390402557080
- Tables: bharatsahayak-*-dev
- Buckets: bharatsahayak-*-390402557080-dev

## Status: ✅ OPERATIONAL
