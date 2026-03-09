# Quick Start: Email/Password Authentication

## What Was Implemented

✅ **Email/Password Registration** - Users can register with email and password instead of phone/OTP  
✅ **JWT Token Authentication** - Secure token-based sessions that persist across browser sessions  
✅ **Profile Setup Flow** - New users complete profile after registration  
✅ **Persistent Dashboard** - Users see their saved data when they log in again  
✅ **Save Schemes** - Users can bookmark schemes and see them on next login  
✅ **Automatic Redirects** - Smart routing based on profile completion status  

## How It Works

### User Journey

1. **Registration**
   - User visits `login.html`
   - Clicks "Register" tab
   - Enters name, email, and password
   - System creates account and stores in database
   - User redirected to login

2. **First Login**
   - User enters email and password
   - System generates JWT token (valid for 7 days)
   - Token stored in browser localStorage
   - User redirected to Profile Setup page

3. **Profile Setup**
   - User fills in age, gender, location, occupation, etc.
   - Data saved to database
   - `profile_completed` flag set to true
   - User redirected to Dashboard

4. **Subsequent Logins**
   - User enters email and password
   - System verifies credentials
   - JWT token generated and stored
   - User redirected directly to Dashboard (profile already complete)
   - Dashboard loads with all saved data

5. **Using the Dashboard**
   - User browses schemes
   - Clicks bookmark icon to save schemes
   - Saved schemes stored in database
   - On next login, saved schemes appear automatically

## Quick Setup (5 Minutes)

### Option 1: Automated Setup (Recommended)

**On Windows:**
```powershell
.\setup-email-auth.ps1
```

**On Linux/Mac:**
```bash
chmod +x setup-email-auth.sh
./setup-email-auth.sh
```

### Option 2: Manual Setup

1. **Create DynamoDB Tables**
```bash
# Users table
aws dynamodb create-table \
  --table-name bharatsahayak-users-dev \
  --attribute-definitions AttributeName=email,AttributeType=S \
  --key-schema AttributeName=email,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# Saved schemes table
aws dynamodb create-table \
  --table-name bharatsahayak-saved-schemes-dev \
  --attribute-definitions \
    AttributeName=user_id,AttributeType=S \
    AttributeName=scheme_id,AttributeType=S \
  --key-schema \
    AttributeName=user_id,KeyType=HASH \
    AttributeName=scheme_id,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST
```

2. **Update Frontend Files**
```bash
# Backup originals
cp frontend/api-client.js frontend/api-client.js.backup
cp frontend/login.html frontend/login.html.backup

# Use new files
cp frontend/api-client-email.js frontend/api-client.js
cp frontend/login-email.html frontend/login.html
```

3. **Deploy Backend**
```bash
sam build
sam deploy --guided
```

4. **Update Config**
Update `frontend/config.json` with your API endpoint:
```json
{
  "apiEndpoint": "https://YOUR-API-ID.execute-api.ap-south-1.amazonaws.com/dev"
}
```

## Testing

### Test Registration
1. Open `login.html` in browser
2. Click "Register" tab
3. Enter:
   - Name: Test User
   - Email: test@example.com
   - Password: SecurePass123!
4. Click "Register Now"
5. Should see success message

### Test Login
1. Click "Login" tab
2. Enter email and password
3. Click "Login"
4. Should redirect to profile setup (first time) or dashboard (subsequent times)

### Test Persistence
1. Login and save a scheme
2. Logout
3. Login again with same email
4. Saved scheme should still be there

## API Endpoints

### Authentication
- `POST /auth/email/register` - Register new user
- `POST /auth/email/login` - Login with email/password

### User Data
- `GET /user/profile` - Get user profile (requires JWT)
- `PUT /user/profile` - Update profile (requires JWT)
- `GET /dashboard/data` - Get dashboard data (requires JWT)

### Schemes
- `POST /schemes/save` - Save/unsave scheme (requires JWT)
- `GET /schemes/eligible` - Get eligible schemes (requires JWT)

## File Structure

```
BharatSahayak/
├── src/
│   ├── api/
│   │   ├── auth_email_register.py      # Email registration
│   │   ├── auth_email_login.py         # Email login
│   │   ├── dashboard_data.py           # Dashboard data
│   │   ├── save_scheme.py              # Save schemes
│   │   ├── user_profile_get.py         # Get profile (updated)
│   │   └── user_profile_update.py      # Update profile (updated)
│   └── utils/
│       └── jwt_auth.py                 # JWT middleware
├── frontend/
│   ├── api-client-email.js             # New API client
│   ├── login-email.html                # New login page
│   ├── dashboard.html                  # Existing dashboard
│   └── profile-setup.html              # Existing profile setup
└── requirements-lambda.txt             # Updated with PyJWT
```

## Key Features

### Security
- Passwords hashed with PBKDF2 (100,000 iterations)
- JWT tokens with 7-day expiry
- Automatic token refresh on API calls
- HTTPS-only communication

### User Experience
- Clean, modern UI
- Instant validation
- Loading indicators
- Toast notifications
- Guest mode option

### Data Persistence
- User profiles stored in DynamoDB
- Saved schemes linked to user_id
- JWT tokens in localStorage
- Automatic session restoration

## Troubleshooting

### "Module 'jwt' not found"
**Solution:** Run `sam build` to install PyJWT

### "Table does not exist"
**Solution:** Run the DynamoDB table creation commands

### "Invalid token"
**Solution:** Clear localStorage and login again

### "CORS error"
**Solution:** Check API Gateway CORS settings

## Next Steps

1. **Email Verification** - Add email confirmation step
2. **Password Reset** - Implement forgot password flow
3. **Social Login** - Add Google/Facebook login
4. **MFA** - Add two-factor authentication
5. **Session Management** - Add refresh tokens

## Support

For detailed documentation, see:
- `EMAIL_PASSWORD_AUTH_IMPLEMENTATION.md` - Complete implementation guide
- `template.yaml` - SAM template with all resources
- Backend code in `src/api/` directory
- Frontend code in `frontend/` directory

## Summary

You now have a complete email/password authentication system with:
- ✅ User registration and login
- ✅ JWT token-based sessions
- ✅ Profile management
- ✅ Persistent user data
- ✅ Saved schemes functionality
- ✅ Automatic session restoration

When users register and login again with the same email, they will see their complete dashboard with all saved data!
