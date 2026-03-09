# Email/Password Authentication Implementation Guide

## Overview
This guide explains the implementation of email/password authentication with JWT tokens for BharatSahayak, replacing the phone-based OTP system while maintaining persistent user data across sessions.

## Architecture

### Backend Components

#### 1. Authentication Endpoints

**`src/api/auth_email_register.py`**
- Handles user registration with email and password
- Validates email format and password strength
- Hashes passwords using PBKDF2
- Stores user data in DynamoDB
- Endpoint: `POST /auth/email/register`

**`src/api/auth_email_login.py`**
- Handles user login with email and password
- Verifies credentials against database
- Generates JWT tokens (7-day expiry)
- Returns user profile completion status
- Endpoint: `POST /auth/email/login`

#### 2. JWT Authentication Middleware

**`src/utils/jwt_auth.py`**
- Decorator function `@require_jwt_auth` for protecting endpoints
- Extracts and verifies JWT tokens from Authorization header
- Passes `user_id` and `email` to protected handlers
- Handles token expiration and invalid tokens

#### 3. Dashboard and Data Persistence

**`src/api/dashboard_data.py`**
- Fetches complete dashboard data for authenticated users
- Returns user profile, saved schemes, and statistics
- Endpoint: `GET /dashboard/data`

**`src/api/save_scheme.py`**
- Allows users to save/unsave schemes
- Persists scheme preferences in DynamoDB
- Endpoint: `POST /schemes/save`

#### 4. Updated Profile Endpoints

**`src/api/user_profile_get.py`** and **`src/api/user_profile_update.py`**
- Updated to use JWT authentication instead of Cognito
- Maintains same functionality with new auth system

### Frontend Components

#### 1. API Client

**`frontend/api-client-email.js`**
- Centralized API communication layer
- Handles JWT token storage in localStorage
- Automatic token injection in requests
- Retry logic and error handling
- Key methods:
  - `registerWithEmail(email, password, name)`
  - `loginWithEmail(email, password)`
  - `getDashboardData()`
  - `saveScheme(schemeId, schemeName)`
  - `unsaveScheme(schemeId)`

#### 2. Login Page

**`frontend/login-email.html`**
- Modern UI with email/password fields
- Registration and login tabs
- Guest mode option
- Form validation
- Redirects to profile setup or dashboard based on profile completion

### Database Schema

#### Users Table (`bharatsahayak-users-dev`)
```
Primary Key: email (String)
Attributes:
- user_id: String (UUID)
- email: String
- password_hash: String (PBKDF2 hash)
- name: String
- created_at: String (ISO timestamp)
- updated_at: String (ISO timestamp)
- last_login: String (ISO timestamp)
- profile_completed: Boolean
```

#### Saved Schemes Table (`bharatsahayak-saved-schemes-dev`)
```
Primary Key: user_id (String)
Sort Key: scheme_id (String)
Attributes:
- scheme_name: String
- saved_at: String (ISO timestamp)
```

## Implementation Flow

### Registration Flow

1. User fills registration form (name, email, password)
2. Frontend validates input and calls `api.registerWithEmail()`
3. Backend validates email format and password strength
4. Password is hashed using PBKDF2 with salt
5. User record created in DynamoDB
6. Success response returned
7. User redirected to login tab

### Login Flow

1. User enters email and password
2. Frontend calls `api.loginWithEmail()`
3. Backend retrieves user from database
4. Password verified against stored hash
5. JWT token generated with 7-day expiry
6. Token and user data returned
7. Frontend stores token in localStorage
8. User redirected to:
   - Profile setup (if `profile_completed = false`)
   - Dashboard (if `profile_completed = true`)

### Profile Setup Flow

1. User completes profile information
2. Frontend calls `api.updateUserProfile(profileData)`
3. Backend validates and stores profile data
4. `profile_completed` flag set to `true`
5. User redirected to dashboard

### Dashboard Load Flow

1. Page checks for valid JWT token in localStorage
2. If no token, redirect to login
3. If token exists, call `api.getDashboardData()`
4. Backend verifies JWT and fetches:
   - User information
   - Profile data
   - Saved schemes
   - Statistics
5. Dashboard populated with user's data

### Persistent Data Flow

1. User saves a scheme by clicking bookmark icon
2. Frontend calls `api.saveScheme(schemeId, schemeName)`
3. Backend stores in `saved_schemes` table
4. On next login, saved schemes fetched and displayed
5. User can unsave schemes with `api.unsaveScheme(schemeId)`

## Deployment Steps

### 1. Update Lambda Dependencies

Add PyJWT to `requirements-lambda.txt`:
```
PyJWT
```

### 2. Create DynamoDB Tables

**Users Table:**
```bash
aws dynamodb create-table \
  --table-name bharatsahayak-users-dev \
  --attribute-definitions AttributeName=email,AttributeType=S \
  --key-schema AttributeName=email,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region ap-south-1
```

**Saved Schemes Table:**
```bash
aws dynamodb create-table \
  --table-name bharatsahayak-saved-schemes-dev \
  --attribute-definitions \
    AttributeName=user_id,AttributeType=S \
    AttributeName=scheme_id,AttributeType=S \
  --key-schema \
    AttributeName=user_id,KeyType=HASH \
    AttributeName=scheme_id,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region ap-south-1
```

### 3. Update SAM Template

Add new Lambda functions to `template.yaml`:

```yaml
  AuthEmailRegisterFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: src/
      Handler: api.auth_email_register.lambda_handler
      Runtime: python3.11
      Environment:
        Variables:
          USERS_TABLE: !Ref UsersTable
          JWT_SECRET: !Ref JWTSecret
      Events:
        RegisterAPI:
          Type: Api
          Properties:
            Path: /auth/email/register
            Method: post

  AuthEmailLoginFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: src/
      Handler: api.auth_email_login.lambda_handler
      Runtime: python3.11
      Environment:
        Variables:
          USERS_TABLE: !Ref UsersTable
          JWT_SECRET: !Ref JWTSecret
      Events:
        LoginAPI:
          Type: Api
          Properties:
            Path: /auth/email/login
            Method: post

  DashboardDataFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: src/
      Handler: api.dashboard_data.lambda_handler
      Runtime: python3.11
      Environment:
        Variables:
          USERS_TABLE: !Ref UsersTable
          PROFILES_TABLE: !Ref ProfilesTable
          SAVED_SCHEMES_TABLE: !Ref SavedSchemesTable
          JWT_SECRET: !Ref JWTSecret
      Events:
        DashboardAPI:
          Type: Api
          Properties:
            Path: /dashboard/data
            Method: get

  SaveSchemeFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: src/
      Handler: api.save_scheme.lambda_handler
      Runtime: python3.11
      Environment:
        Variables:
          SAVED_SCHEMES_TABLE: !Ref SavedSchemesTable
          JWT_SECRET: !Ref JWTSecret
      Events:
        SaveSchemeAPI:
          Type: Api
          Properties:
            Path: /schemes/save
            Method: post

Parameters:
  JWTSecret:
    Type: String
    Default: your-secret-key-change-in-production
    Description: Secret key for JWT token generation
```

### 4. Deploy Backend

```bash
sam build
sam deploy --guided
```

### 5. Update Frontend

Replace `api-client.js` with `api-client-email.js` in your HTML files:

```html
<script src="api-client-email.js"></script>
```

Or rename the file:
```bash
mv frontend/api-client-email.js frontend/api-client.js
```

### 6. Update Login Page

Replace `login.html` with `login-email.html`:
```bash
mv frontend/login-email.html frontend/login.html
```

## Security Considerations

1. **Password Hashing**: Uses PBKDF2 with 100,000 iterations and random salt
2. **JWT Expiry**: Tokens expire after 7 days
3. **HTTPS Only**: All API calls must use HTTPS
4. **CORS**: Properly configured for your domain
5. **Input Validation**: Email format and password strength validated
6. **SQL Injection**: Not applicable (using DynamoDB)
7. **XSS Protection**: Frontend sanitizes user input

## Production Recommendations

1. **JWT Secret**: Store in AWS Secrets Manager instead of environment variable
2. **Password Policy**: Enforce stronger passwords (uppercase, lowercase, numbers, symbols)
3. **Rate Limiting**: Implement API Gateway throttling
4. **Email Verification**: Add email verification step after registration
5. **Password Reset**: Implement forgot password functionality
6. **Session Management**: Add refresh tokens for better security
7. **Audit Logging**: Log all authentication attempts
8. **Multi-Factor Authentication**: Add MFA option for enhanced security

## Testing

### Test Registration
```bash
curl -X POST https://your-api.execute-api.ap-south-1.amazonaws.com/dev/auth/email/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!",
    "name": "Test User"
  }'
```

### Test Login
```bash
curl -X POST https://your-api.execute-api.ap-south-1.amazonaws.com/dev/auth/email/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'
```

### Test Dashboard (with token)
```bash
curl -X GET https://your-api.execute-api.ap-south-1.amazonaws.com/dev/dashboard/data \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Troubleshooting

### Issue: "Module 'jwt' not found"
**Solution**: Ensure PyJWT is in requirements-lambda.txt and rebuild with `sam build`

### Issue: "Invalid token"
**Solution**: Check JWT_SECRET matches between login and protected endpoints

### Issue: "User not found after login"
**Solution**: Verify DynamoDB table name matches environment variable

### Issue: "CORS error"
**Solution**: Ensure API Gateway has proper CORS configuration

## Migration from Phone Auth

If migrating from existing phone-based auth:

1. Keep both systems running in parallel
2. Add migration endpoint to convert phone users to email users
3. Send email to existing users to set password
4. Gradually deprecate phone auth
5. Update all frontend pages to use new auth

## Summary

This implementation provides:
- ✅ Email/password authentication
- ✅ JWT token-based sessions
- ✅ Persistent user data across logins
- ✅ Profile completion tracking
- ✅ Saved schemes functionality
- ✅ Secure password storage
- ✅ Modern frontend UI
- ✅ Complete dashboard with user data

The system ensures that when a user registers and later logs in with the same email, they see their saved data including profile information, saved schemes, and personalized recommendations.
