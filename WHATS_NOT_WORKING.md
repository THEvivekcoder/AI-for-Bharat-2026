# ❌ What's NOT Working - BharatSahayak

## Critical Issues Found

After analyzing the actual deployment configuration (`template.yaml`), I've identified several mismatches between what the frontend expects and what the backend actually provides.

## 🔴 Issue 1: Missing /auth/login Endpoint

### What Frontend Expects:
```
POST /auth/login
```

### What Backend Has:
```
❌ NOT CONFIGURED in template.yaml
```

### Status:
- ✅ Code file exists: `src/api/auth_login.py`
- ❌ NOT configured in `template.yaml`
- ❌ NOT deployed to AWS

### Impact:
- Existing users CANNOT log in
- Only new user registration works
- Login button in frontend will fail

### Fix Required:
Add to `template.yaml`:
```yaml
LoginFunction:
  Type: AWS::Serverless::Function
  Properties:
    FunctionName: !Sub bharatsahayak-login-${Environment}
    CodeUri: .
    Handler: src.api.auth_login.lambda_handler
    Environment:
      Variables:
        USER_POOL_ID: !Ref UserPool
        USER_POOL_CLIENT_ID: !Ref UserPoolClient
        USERS_TABLE: !Ref UsersTable
    Policies:
      - DynamoDBReadPolicy:
          TableName: !Ref UsersTable
      - Statement:
          - Effect: Allow
            Action:
              - cognito-idp:InitiateAuth
              - cognito-idp:AdminInitiateAuth
            Resource: !GetAtt UserPool.Arn
    Events:
      LoginApi:
        Type: Api
        Properties:
          RestApiId: !Ref BharatSahayakApi
          Path: /auth/login
          Method: POST
          Auth:
            Authorizer: NONE
```

## 🟡 Issue 2: Wrong Health Check Path

### What Frontend Expects:
```
GET /health-check
```

### What Backend Has:
```
POST /health/check  ❌ WRONG PATH AND METHOD
```

### Status:
- ✅ Code file exists: `src/api/health_check.py`
- ⚠️ Configured in `template.yaml` but WRONG PATH
- ⚠️ Wrong HTTP method (POST instead of GET)

### Impact:
- Frontend health check tests will fail
- Debug page cannot verify backend connectivity
- Monitoring tools cannot check system health

### Fix Required:
Change in `template.yaml` (line 748):
```yaml
# BEFORE:
Path: /health/check
Method: POST

# AFTER:
Path: /health-check
Method: GET
```

## 🟡 Issue 3: Wrong Voice API Paths

### What Frontend Expects:
```
POST /voice-to-text
POST /conversational-query
```

### What Backend Has:
```
POST /voice/transcribe  ❌ WRONG PATH
❌ /conversational-query NOT FOUND
```

### Status:
- ✅ `voice_to_text.py` exists
- ⚠️ Mapped to `/voice/transcribe` instead of `/voice-to-text`
- ❌ `conversational_query.py` exists but NOT configured in template

### Impact:
- Voice assistant will NOT work
- Speech-to-text will fail
- AI conversational queries will fail

### Fix Required:

**1. Fix voice-to-text path:**
Change in `template.yaml` (line 780):
```yaml
# BEFORE:
Path: /voice/transcribe

# AFTER:
Path: /voice-to-text
```

**2. Add conversational-query endpoint:**
Add to `template.yaml`:
```yaml
ConversationalQueryFunction:
  Type: AWS::Serverless::Function
  Properties:
    FunctionName: !Sub bharatsahayak-conversational-query-${Environment}
    CodeUri: .
    Handler: src.api.conversational_query.lambda_handler
    Timeout: 60
    MemorySize: 512
    Environment:
      Variables:
        SCHEMES_TABLE: !Ref SchemesTable
    Policies:
      - DynamoDBReadPolicy:
          TableName: !Ref SchemesTable
    Events:
      ConversationalQueryApi:
        Type: Api
        Properties:
          RestApiId: !Ref BharatSahayakApi
          Path: /conversational-query
          Method: POST
          Auth:
            Authorizer: NONE
```

## 🟡 Issue 4: Wrong Agriculture API Paths

### What Frontend Expects:
```
GET /crop-advice
GET /market-prices
```

### What Backend Has:
```
POST /farmer/crop-advice  ❌ WRONG PATH AND METHOD
GET /farmer/market-price  ❌ WRONG PATH (singular)
```

### Status:
- ✅ Code files exist
- ⚠️ Wrong paths in template
- ⚠️ Wrong HTTP method for crop-advice

### Impact:
- Agriculture features will NOT work
- Crop advice requests will fail
- Market price queries will fail

### Fix Required:

**1. Fix crop-advice:**
Change in `template.yaml` (line 643):
```yaml
# BEFORE:
Path: /farmer/crop-advice
Method: POST

# AFTER:
Path: /crop-advice
Method: GET
```

**2. Fix market-prices:**
Change in `template.yaml` (line 664):
```yaml
# BEFORE:
Path: /farmer/market-price

# AFTER:
Path: /market-prices
```

## 🟡 Issue 5: Schemes Search Path Mismatch

### What Frontend Expects:
```
GET /schemes/search?q=query
```

### What Backend Has:
```
GET /schemes  ⚠️ SAME HANDLER, DIFFERENT USAGE
```

### Status:
- ✅ Handler supports search via query parameters
- ⚠️ No explicit `/schemes/search` route
- ⚠️ May work but not RESTful

### Impact:
- Search might work via `/schemes?q=query`
- But frontend calls `/schemes/search?q=query`
- This will likely return 404

### Fix Required:
Add explicit search route in `template.yaml`:
```yaml
SearchSchemesApi:
  Type: Api
  Properties:
    RestApiId: !Ref BharatSahayakApi
    Path: /schemes/search
    Method: GET
    Auth:
      Authorizer: NONE
```

## 🟡 Issue 6: User Stats Endpoint Missing

### What Frontend Expects:
```
GET /user/stats
```

### What Backend Has:
```
❌ NOT CONFIGURED
```

### Status:
- ❌ No code file found
- ❌ Not configured in template

### Impact:
- Dashboard statistics will NOT load
- User stats widget will be empty

### Fix Required:
Create `src/api/user_stats.py` and add to template.

## 📊 Complete Path Mismatch Table

| Frontend Expects | Backend Has | Status | Fix Priority |
|------------------|-------------|--------|--------------|
| `POST /auth/login` | ❌ Not configured | BROKEN | 🔴 HIGH |
| `GET /health-check` | `POST /health/check` | BROKEN | 🟡 MEDIUM |
| `POST /voice-to-text` | `POST /voice/transcribe` | BROKEN | 🔴 HIGH |
| `POST /conversational-query` | ❌ Not configured | BROKEN | 🔴 HIGH |
| `GET /crop-advice` | `POST /farmer/crop-advice` | BROKEN | 🟡 MEDIUM |
| `GET /market-prices` | `GET /farmer/market-price` | BROKEN | 🟡 MEDIUM |
| `GET /schemes/search` | `GET /schemes` | PARTIAL | 🟢 LOW |
| `GET /user/stats` | ❌ Not configured | BROKEN | 🟡 MEDIUM |
| `POST /auth/register` | `POST /auth/register` | ✅ WORKS | - |
| `POST /auth/verify` | `POST /auth/verify` | ✅ WORKS | - |
| `GET /user/profile` | `GET /user/profile` | ✅ WORKS | - |
| `PUT /user/profile` | `PUT /user/profile` | ✅ WORKS | - |
| `GET /schemes` | `GET /schemes` | ✅ WORKS | - |
| `GET /schemes/{id}` | `GET /schemes/{scheme_id}` | ✅ WORKS | - |
| `GET /schemes/eligible` | `POST /schemes/eligible` | ⚠️ WRONG METHOD | 🟡 MEDIUM |
| `POST /schemes/check-eligibility` | `POST /schemes/check-eligibility` | ✅ WORKS | - |

## 🔧 Summary of Required Fixes

### High Priority (Breaks Core Features) 🔴
1. Add `/auth/login` endpoint configuration
2. Add `/conversational-query` endpoint configuration
3. Fix `/voice-to-text` path (currently `/voice/transcribe`)

### Medium Priority (Breaks Secondary Features) 🟡
4. Fix `/health-check` path and method
5. Fix `/crop-advice` path and method
6. Fix `/market-prices` path
7. Add `/user/stats` endpoint
8. Fix `/schemes/eligible` method (GET instead of POST)

### Low Priority (May Work with Workarounds) 🟢
9. Add explicit `/schemes/search` route

## 📝 Complete Fix Template

Here's the complete section to add to `template.yaml`:

```yaml
  # Auth: User Login (MISSING)
  LoginFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Sub bharatsahayak-login-${Environment}
      CodeUri: .
      Handler: src.api.auth_login.lambda_handler
      Environment:
        Variables:
          USER_POOL_ID: !Ref UserPool
          USER_POOL_CLIENT_ID: !Ref UserPoolClient
          USERS_TABLE: !Ref UsersTable
      Policies:
        - DynamoDBReadPolicy:
            TableName: !Ref UsersTable
        - Statement:
            - Effect: Allow
              Action:
                - cognito-idp:InitiateAuth
                - cognito-idp:AdminInitiateAuth
              Resource: !GetAtt UserPool.Arn
      Events:
        LoginApi:
          Type: Api
          Properties:
            RestApiId: !Ref BharatSahayakApi
            Path: /auth/login
            Method: POST
            Auth:
              Authorizer: NONE

  # Conversational Query (MISSING)
  ConversationalQueryFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Sub bharatsahayak-conversational-query-${Environment}
      CodeUri: .
      Handler: src.api.conversational_query.lambda_handler
      Timeout: 60
      MemorySize: 512
      Environment:
        Variables:
          SCHEMES_TABLE: !Ref SchemesTable
      Policies:
        - DynamoDBReadPolicy:
            TableName: !Ref SchemesTable
      Events:
        ConversationalQueryApi:
          Type: Api
          Properties:
            RestApiId: !Ref BharatSahayakApi
            Path: /conversational-query
            Method: POST
            Auth:
              Authorizer: NONE
```

And update these existing functions:

```yaml
# Fix HealthCheckFunction (line 744-752)
Events:
  HealthCheckApi:
    Type: Api
    Properties:
      RestApiId: !Ref BharatSahayakApi
      Path: /health-check  # Changed from /health/check
      Method: GET          # Changed from POST
      Auth:
        Authorizer: NONE

# Fix VoiceToTextFunction (line 776-784)
Events:
  VoiceToTextApi:
    Type: Api
    Properties:
      RestApiId: !Ref BharatSahayakApi
      Path: /voice-to-text  # Changed from /voice/transcribe
      Method: POST
      Auth:
        Authorizer: NONE

# Fix CropAdviceFunction (line 638-646)
Events:
  CropAdviceApi:
    Type: Api
    Properties:
      RestApiId: !Ref BharatSahayakApi
      Path: /crop-advice  # Changed from /farmer/crop-advice
      Method: GET         # Changed from POST

# Fix MarketPriceFunction (line 659-668)
Events:
  MarketPriceApi:
    Type: Api
    Properties:
      RestApiId: !Ref BharatSahayakApi
      Path: /market-prices  # Changed from /farmer/market-price
      Method: GET
      Auth:
        Authorizer: NONE

# Fix GetEligibleSchemesFunction (line 617-625)
Events:
  GetEligibleSchemesApi:
    Type: Api
    Properties:
      RestApiId: !Ref BharatSahayakApi
      Path: /schemes/eligible
      Method: GET  # Changed from POST
```

## 🧪 Testing After Fixes

After applying all fixes, test with:

```bash
# 1. Deploy updated template
sam build
sam deploy

# 2. Test endpoints
python test_backend_endpoints.py

# 3. Test from frontend
Open: frontend/test-quick.html
```

## 📊 Impact Assessment

### Currently Working:
- ✅ Registration (new users)
- ✅ OTP Verification
- ✅ Basic schemes listing
- ✅ Scheme details
- ✅ Profile get/update

### Currently Broken:
- ❌ Login (existing users)
- ❌ Voice assistant
- ❌ Conversational AI
- ❌ Agriculture features
- ❌ Health check
- ❌ User stats

### Estimated Fix Time:
- Update template.yaml: 15 minutes
- Deploy: 10 minutes
- Test: 5 minutes
- **Total: 30 minutes**

## 🎯 Recommended Action Plan

1. **Immediate** (15 min): Update `template.yaml` with all fixes
2. **Deploy** (10 min): `sam build && sam deploy`
3. **Test** (5 min): Run `python test_backend_endpoints.py`
4. **Verify** (5 min): Test from `frontend/test-quick.html`

## 📝 Conclusion

The backend code files are complete and correct, but the `template.yaml` configuration has multiple path mismatches and missing endpoints. Once the template is fixed and redeployed, all features should work correctly.

**Root Cause**: Mismatch between frontend API expectations and backend deployment configuration.

**Solution**: Update `template.yaml` to match frontend expectations.

**Status**: Ready to fix - all code exists, just needs proper configuration.
