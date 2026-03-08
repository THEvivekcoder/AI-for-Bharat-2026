# 🧪 Testing Guide - BharatSahayak Integration

## Quick Start (5 Minutes)

### Step 1: Open Test Page
1. Open `frontend/test-quick.html` in your browser
2. Tests will run automatically
3. Look for ✅ green checkmarks

### Step 2: Check Results
- **All Green (✅)**: Everything is working! Go to Step 3
- **Any Red (❌)**: See "Troubleshooting" section below

### Step 3: Test Registration
1. Open `frontend/login.html`
2. Click "Register" tab
3. Fill in the form:
   ```
   Phone: +919876543210
   Language: Hindi
   State: Maharashtra
   District: Pune
   Pincode: 411014
   ```
4. Click "Register Now"
5. You should see: "Registration successful! Please verify OTP to continue."

### Step 4: Verify OTP
1. Check your phone for OTP (or check backend logs if using test number)
2. Enter the OTP
3. Click "Verify & Continue"
4. Should redirect to profile setup

## What Was Fixed

### ✅ Fixed Issues

1. **Wrong API Endpoint**
   - Before: `https://api.bharatsahayak.gov.in/dev` (doesn't exist)
   - After: `https://dvt82zj0c4.execute-api.ap-south-1.amazonaws.com/dev` (correct AWS endpoint)

2. **Token Field Mismatch**
   - Backend returns: `access_token`
   - Frontend was looking for: `token`
   - Fixed: Updated API client to use `access_token`

3. **API Client Initialization**
   - All pages now wait for `api-ready` event
   - Proper error handling and retry logic

### ⚠️ Known Limitations

1. **No Separate Login Endpoint**
   - Backend only has `/auth/register` and `/auth/verify`
   - No `/auth/login` for existing users
   - **Workaround**: Users must use "Register" even if they have an account
   - **Backend TODO**: Add `/auth/login` endpoint

2. **OTP Delivery**
   - Depends on AWS Cognito configuration
   - May not work if Cognito SMS is not configured
   - Check backend logs for OTP if not receiving SMS

## Troubleshooting

### ❌ Test 1 Failed: "API Client NOT Loaded"

**Problem**: `api-client.js` not loading

**Solutions**:
1. Check file exists: `frontend/api-client.js`
2. Check browser console for 404 errors
3. Clear browser cache (Ctrl+Shift+Delete)
4. Try different browser

### ❌ Test 2 Failed: "Wrong API Endpoint"

**Problem**: `config.json` has wrong endpoint

**Solutions**:
1. Open `frontend/config.json`
2. Verify `apiEndpoint` is: `https://dvt82zj0c4.execute-api.ap-south-1.amazonaws.com/dev`
3. Clear browser cache
4. Reload page

### ❌ Test 3 Failed: "Connection Failed"

**Problem**: Cannot reach backend

**Possible Causes**:
1. **Backend is down**: Check if AWS Lambda is running
2. **CORS not configured**: Backend must allow frontend origin
3. **Network issue**: Check internet connection
4. **Wrong endpoint**: Verify endpoint in config.json

**Solutions**:
1. Check backend logs in AWS CloudWatch
2. Verify CORS headers in backend responses:
   ```
   Access-Control-Allow-Origin: *
   Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
   Access-Control-Allow-Headers: Content-Type, Authorization
   ```
3. Test endpoint directly:
   ```bash
   curl https://dvt82zj0c4.execute-api.ap-south-1.amazonaws.com/dev/schemes?limit=1
   ```

### ❌ Test 4 Failed: "Schemes API Failed"

**Problem**: Schemes endpoint not working

**Solutions**:
1. Check backend logs for errors
2. Verify DynamoDB table exists: `bharatsahayak-schemes-dev`
3. Check IAM permissions for Lambda to access DynamoDB
4. Verify schemes data is populated in DynamoDB

### ❌ "OTP not received"

**Problem**: SMS not delivered

**Solutions**:
1. Check AWS Cognito SMS configuration
2. Check AWS SNS (SMS service) is configured
3. Verify phone number format: `+919876543210`
4. Check backend logs for OTP (for testing):
   ```
   Look for: "OTP sent to +919876543210: 123456"
   ```
5. Use AWS Cognito test user if available

### ❌ "Invalid OTP"

**Problem**: OTP verification failing

**Solutions**:
1. Check OTP hasn't expired (usually 5 minutes)
2. Verify phone number matches exactly
3. Check backend logs for actual OTP sent
4. Try requesting new OTP

### ❌ "Authentication required"

**Problem**: Token not stored or expired

**Solutions**:
1. Log in again
2. Check localStorage has token:
   ```javascript
   // In browser console:
   localStorage.getItem('bharatsahayak-auth-token')
   ```
3. Clear localStorage and log in fresh:
   ```javascript
   localStorage.clear()
   ```

## Testing Each Feature

### 1. Registration ✅
```
Page: frontend/login.html
Tab: Register
Required: Phone, Language, State, District, Pincode
Expected: "Registration successful! Please verify OTP"
```

### 2. OTP Verification ✅
```
Page: After registration
Required: 6-digit OTP
Expected: Redirect to profile-setup.html
```

### 3. Schemes Search ✅
```
Page: frontend/schemes.html
Test: Search for "agriculture"
Expected: List of agriculture schemes
```

### 4. Scheme Details ✅
```
Page: frontend/scheme-details.html?id=SCHEME_ID
Expected: Full scheme information
```

### 5. Eligible Schemes ✅
```
Page: frontend/eligible-schemes.html
Required: Must be logged in
Expected: List of schemes user is eligible for
```

### 6. Voice Assistant ⚠️
```
Page: frontend/voice-assistant.html
Required: Microphone permission
Test: Click mic, say "Show me agriculture schemes"
Expected: Transcript + AI response
Note: Requires backend voice API to be configured
```

### 7. Profile Management ✅
```
Page: frontend/profile.html
Required: Must be logged in
Expected: User profile information
```

### 8. Dashboard ✅
```
Page: frontend/dashboard.html
Required: Must be logged in
Expected: User stats, eligible schemes, quick actions
```

## Browser Console Checks

### Good Signs ✅
```
✅ BharatSahayak API Client initialized
📍 API Endpoint: https://dvt82zj0c4.execute-api.ap-south-1.amazonaws.com/dev
🔐 Authenticated: false
🚀 API Client ready
```

### Bad Signs ❌
```
❌ Failed to initialize API client
❌ API Error: 404 Not Found
❌ Network error
❌ CORS error
❌ api is not defined
```

## Backend Requirements

For full functionality, backend must have:

### Required Endpoints ✅
- `POST /auth/register` - Register user (sends OTP)
- `POST /auth/verify` - Verify OTP (returns token)
- `GET /schemes` - Get all schemes
- `GET /schemes/search` - Search schemes
- `GET /schemes/{id}` - Get scheme details
- `GET /schemes/eligible` - Get eligible schemes (auth required)
- `GET /user/profile` - Get user profile (auth required)
- `PUT /user/profile` - Update profile (auth required)
- `POST /voice-to-text` - Voice to text conversion
- `POST /conversational-query` - AI conversational query

### Missing Endpoints ❌
- `POST /auth/login` - Login existing user (sends OTP)
- `GET /health-check` - Health check endpoint

### Required Configuration
1. **CORS Headers**: All endpoints must return:
   ```
   Access-Control-Allow-Origin: *
   Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
   Access-Control-Allow-Headers: Content-Type, Authorization
   ```

2. **AWS Cognito**: Configured for SMS OTP
3. **DynamoDB Tables**: 
   - `bharatsahayak-schemes-dev`
   - `bharatsahayak-users-dev`
   - `bharatsahayak-user-profiles-dev`

4. **IAM Permissions**: Lambda functions need access to:
   - Cognito
   - DynamoDB
   - SNS (for SMS)

## Next Steps

### For Testing:
1. ✅ Run `frontend/test-quick.html`
2. ✅ Test registration flow
3. ✅ Test schemes search
4. ✅ Test each page individually

### For Development:
1. ⚠️ Add `/auth/login` endpoint in backend
2. ⚠️ Add `/health-check` endpoint
3. ⚠️ Configure AWS Cognito for SMS
4. ⚠️ Populate schemes data in DynamoDB

### For Production:
1. ⚠️ Change JWT secret in backend
2. ⚠️ Update CORS to specific origin
3. ⚠️ Enable HTTPS only
4. ⚠️ Add rate limiting
5. ⚠️ Add monitoring and logging

## Support

If you encounter issues:

1. **Check browser console** (F12) for errors
2. **Check backend logs** in AWS CloudWatch
3. **Run debug page**: `frontend/debug-test.html`
4. **Check this guide** for troubleshooting steps

## Summary

✅ **What's Working**: API client, configuration, schemes API, profile management, voice assistant integration

⚠️ **What Needs Work**: Login endpoint for existing users, OTP SMS delivery (depends on AWS Cognito)

🎯 **Next Action**: Open `frontend/test-quick.html` and verify all tests pass!
