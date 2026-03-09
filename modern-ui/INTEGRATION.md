# AWS API Integration Guide

## Overview

The modern UI is now integrated with your AWS backend API. Here's how data flows:

## Data Storage Architecture

### Backend (AWS)
- **User Accounts** → Cognito User Pool + DynamoDB UsersTable
- **User Profiles** → DynamoDB UserProfilesTable
- **Schemes Data** → DynamoDB SchemesTable
- **User Interactions** → DynamoDB InteractionsTable
- **Saved Schemes** → Can be stored in UserProfilesTable or localStorage

### Frontend (Browser)
- **Session Token** → localStorage (JWT from Cognito)
- **User Session** → localStorage (temporary, cleared on logout)
- **Saved Schemes** → localStorage (can sync with backend)
- **Schemes Cache** → Fallback to local schemes-data.js if API fails

## API Integration Points

### 1. Registration Flow
```
User fills form → POST /auth/register → Cognito creates user → OTP sent
User enters OTP → POST /auth/verify → JWT token returned → Store in localStorage
```

### 2. Login Flow
```
User enters credentials → POST /auth/login → Cognito validates → JWT returned
Store JWT → Fetch profile → Redirect to dashboard
```

### 3. Profile Management
```
Setup profile → PUT /user/profile → Store in DynamoDB UserProfilesTable
Get profile → GET /user/profile → Fetch from DynamoDB
```

### 4. Schemes Discovery
```
Search schemes → GET /schemes?q=query&category=cat → DynamoDB SchemesTable
Get details → GET /schemes/{id} → DynamoDB SchemesTable
Check eligibility → POST /schemes/check-eligibility → AI matching
```

## Files Created

1. **config.js** - Centralized configuration (API URLs, Cognito settings)
2. **js/api-client.js** - API wrapper with all backend endpoints
3. **verify-otp.html** - OTP verification page for registration

## How It Works

### Registration (register.html)
- Calls `api.register()` → AWS `/auth/register`
- Stores pending user data
- Redirects to OTP verification

### OTP Verification (verify-otp.html)
- Calls `api.verifyOTP()` → AWS `/auth/verify`
- Receives JWT token
- Stores token and creates session
- Redirects to profile setup

### Login (login.html)
- Calls `api.login()` → AWS `/auth/login`
- Receives JWT token
- Creates user session
- Redirects to dashboard

### Profile Setup (profile-setup.html)
- Calls `api.updateProfile()` → AWS `/user/profile` (PUT)
- Stores profile in DynamoDB
- Marks profile as complete

### Dashboard (dashboard.html)
- Calls `api.searchSchemes()` → AWS `/schemes`
- Displays schemes from DynamoDB
- Falls back to local data if API fails

### Search (search.html)
- Calls `api.searchSchemes(query, category)` → AWS `/schemes`
- Real-time filtering via API
- Fallback to local search

### Scheme Details (details.html)
- Calls `api.getSchemeDetails(id)` → AWS `/schemes/{id}`
- Displays full scheme information
- Save/bookmark functionality

## Fallback Strategy

The UI implements graceful degradation:
1. **Try API first** - All operations attempt AWS API calls
2. **Catch errors** - Network/API failures are caught
3. **Fallback to local** - Uses schemes-data.js (3,400 schemes)
4. **User notification** - Shows alerts for failures

## Next Steps

To fully integrate saved schemes with backend:
1. Add a `saved_schemes` field to UserProfilesTable
2. Create API endpoints: `POST /user/schemes/save` and `DELETE /user/schemes/{id}`
3. Update `savedSchemes` helper in app.js to sync with API

