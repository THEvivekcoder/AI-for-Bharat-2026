# BharatSahayak Authentication APIs

This directory contains Lambda handlers for user authentication and profile management.

## Implemented APIs

### 1. User Registration

**Endpoint:** `POST /auth/register`

**Description:** Register a new user with phone number and send OTP via Cognito.

**Request Body:**
```json
{
  "phone_number": "+919876543210",
  "language": "hi",
  "location": {
    "state": "Maharashtra",
    "district": "Pune",
    "pincode": "411014",
    "block": "Haveli",
    "village": "Kharadi",
    "latitude": 18.5511,
    "longitude": 73.9467
  },
  "age": 35,
  "gender": "male",
  "education_level": "secondary",
  "occupation": "farmer",
  "income_bracket": "100000-300000",
  "household_size": 5
}
```

**Response (200 OK):**
```json
{
  "user_id": "uuid-string",
  "message": "OTP sent to phone number. Please verify to complete registration.",
  "session": "cognito-session-token"
}
```

**Error Responses:**
- `400 Bad Request`: Missing required fields or invalid data
- `409 Conflict`: User with phone number already exists
- `500 Internal Server Error`: Registration failed

---

### 2. OTP Verification

**Endpoint:** `POST /auth/verify`

**Description:** Verify OTP and generate JWT token for authenticated sessions.

**Request Body:**
```json
{
  "phone_number": "+919876543210",
  "otp": "123456",
  "session": "cognito-session-token"
}
```

**Response (200 OK):**
```json
{
  "user_id": "uuid-string",
  "access_token": "jwt-token-string",
  "token_type": "Bearer",
  "expires_in": 86400,
  "message": "Authentication successful"
}
```

**Error Responses:**
- `400 Bad Request`: Missing phone_number or otp
- `401 Unauthorized`: Invalid OTP, expired OTP, or authentication failed
- `404 Not Found`: User not found
- `500 Internal Server Error`: Verification failed

---

### 3. Get User Profile

**Endpoint:** `GET /user/profile`

**Description:** Retrieve the authenticated user's profile information.

**Headers:**
```
Authorization: Bearer <jwt-token>
```

**Response (200 OK):**
```json
{
  "user_id": "uuid-string",
  "phone_number": "+919876543210",
  "language": "hi",
  "location": {
    "state": "Maharashtra",
    "district": "Pune",
    "block": "Haveli",
    "village": "Kharadi",
    "pincode": "411014",
    "latitude": 18.5511,
    "longitude": 73.9467
  },
  "age": 35,
  "gender": "male",
  "education_level": "secondary",
  "occupation": "farmer",
  "income_bracket": "100000-300000",
  "household_size": 5,
  "preferences": {
    "notification_enabled": true,
    "preferred_categories": ["agriculture", "health"],
    "voice_enabled": true,
    "data_sharing_consent": false
  },
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Error Responses:**
- `401 Unauthorized`: Missing or invalid JWT token
- `403 Forbidden`: Access denied
- `404 Not Found`: Profile not found
- `500 Internal Server Error`: Retrieval failed

---

### 4. Update User Profile

**Endpoint:** `PUT /user/profile`

**Description:** Update the authenticated user's profile information.

**Headers:**
```
Authorization: Bearer <jwt-token>
```

**Request Body (all fields optional):**
```json
{
  "language": "en",
  "location": {
    "state": "Karnataka",
    "district": "Bangalore",
    "pincode": "560001"
  },
  "age": 36,
  "gender": "male",
  "education_level": "graduate",
  "occupation": "teacher",
  "income_bracket": "300000-500000",
  "household_size": 4,
  "preferences": {
    "notification_enabled": false,
    "preferred_categories": ["education", "skill_development"],
    "voice_enabled": true,
    "data_sharing_consent": true
  }
}
```

**Response (200 OK):**
```json
{
  "user_id": "uuid-string",
  "message": "Profile updated successfully",
  "profile": {
    // Updated profile object
  }
}
```

**Error Responses:**
- `400 Bad Request`: Invalid data or no fields to update
- `401 Unauthorized`: Missing or invalid JWT token
- `403 Forbidden`: Access denied
- `404 Not Found`: Profile not found
- `500 Internal Server Error`: Update failed

---

## Authentication Flow

1. **Registration:**
   - User submits phone number and basic info to `/auth/register`
   - System creates user in Cognito and sends OTP
   - System stores user profile in DynamoDB
   - Returns session token

2. **Verification:**
   - User submits phone number, OTP, and session token to `/auth/verify`
   - System verifies OTP with Cognito
   - System generates JWT token
   - Returns JWT token for subsequent requests

3. **Authenticated Requests:**
   - User includes JWT token in Authorization header
   - System verifies token and extracts user_id
   - System processes request with authenticated user context

## Environment Variables

The Lambda functions require the following environment variables:

- `USER_POOL_ID`: AWS Cognito User Pool ID
- `USER_POOL_CLIENT_ID`: AWS Cognito User Pool Client ID
- `USERS_TABLE`: DynamoDB Users table name
- `PROFILES_TABLE`: DynamoDB UserProfiles table name
- `JWT_SECRET`: Secret key for JWT token signing (stored in Secrets Manager)
- `LOG_LEVEL`: Logging level (default: INFO)
- `ENVIRONMENT`: Deployment environment (dev/staging/prod)

## Security Considerations

1. **JWT Tokens:**
   - Tokens expire after 24 hours
   - Secret key should be stored in AWS Secrets Manager
   - Tokens are signed using HS256 algorithm

2. **Phone Number Validation:**
   - Phone numbers are normalized to E.164 format
   - Indian numbers (+91) are supported by default

3. **Authorization:**
   - Users can only access and update their own profiles
   - JWT token verification is required for protected endpoints

4. **Data Privacy:**
   - Sensitive data is encrypted at rest in DynamoDB
   - All API communications use HTTPS
   - User consent is tracked for data sharing

## Testing

To test the APIs locally:

1. Set up environment variables
2. Run SAM local: `sam local start-api`
3. Use curl or Postman to test endpoints

Example:
```bash
# Register user
curl -X POST http://localhost:3000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+919876543210",
    "language": "hi",
    "location": {
      "state": "Maharashtra",
      "district": "Pune",
      "pincode": "411014"
    }
  }'

# Verify OTP
curl -X POST http://localhost:3000/auth/verify \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+919876543210",
    "otp": "123456",
    "session": "session-token"
  }'

# Get profile
curl -X GET http://localhost:3000/user/profile \
  -H "Authorization: Bearer jwt-token"

# Update profile
curl -X PUT http://localhost:3000/user/profile \
  -H "Authorization: Bearer jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "age": 36,
    "occupation": "teacher"
  }'
```

## Next Steps

- Implement unit tests for each Lambda handler
- Add integration tests for the complete authentication flow
- Set up API Gateway custom authorizer for JWT validation
- Implement refresh token mechanism
- Add rate limiting for OTP requests
- Implement password reset flow
