# Deployment Checklist - Email/Password Authentication

## Pre-Deployment Checklist

### ✅ Prerequisites
- [ ] AWS CLI installed and configured
- [ ] SAM CLI installed
- [ ] AWS credentials set up
- [ ] Python 3.11 installed
- [ ] Git repository up to date

### ✅ Review Files
- [ ] Review `src/api/auth_email_register.py`
- [ ] Review `src/api/auth_email_login.py`
- [ ] Review `src/api/dashboard_data.py`
- [ ] Review `src/api/save_scheme.py`
- [ ] Review `src/utils/jwt_auth.py`
- [ ] Review `frontend/api-client-email.js`
- [ ] Review `frontend/login-email.html`

## Deployment Steps

### Step 1: Backup Existing Files
- [ ] Backup `frontend/api-client.js`
  ```bash
  cp frontend/api-client.js frontend/api-client.js.backup
  ```
- [ ] Backup `frontend/login.html`
  ```bash
  cp frontend/login.html frontend/login.html.backup
  ```

### Step 2: Create DynamoDB Tables

#### Users Table
- [ ] Create users table
  ```bash
  aws dynamodb create-table \
    --table-name bharatsahayak-users-dev \
    --attribute-definitions AttributeName=email,AttributeType=S \
    --key-schema AttributeName=email,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region ap-south-1
  ```
- [ ] Verify table created
  ```bash
  aws dynamodb describe-table --table-name bharatsahayak-users-dev
  ```

#### Saved Schemes Table
- [ ] Create saved schemes table
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
- [ ] Verify table created
  ```bash
  aws dynamodb describe-table --table-name bharatsahayak-saved-schemes-dev
  ```

### Step 3: Update SAM Template

- [ ] Add new Lambda functions to `template.yaml`:
  - [ ] AuthEmailRegisterFunction
  - [ ] AuthEmailLoginFunction
  - [ ] DashboardDataFunction
  - [ ] SaveSchemeFunction

- [ ] Add environment variables:
  - [ ] USERS_TABLE
  - [ ] SAVED_SCHEMES_TABLE
  - [ ] JWT_SECRET

- [ ] Add IAM permissions for DynamoDB access

### Step 4: Update Frontend Files

- [ ] Replace api-client.js
  ```bash
  cp frontend/api-client-email.js frontend/api-client.js
  ```
- [ ] Replace login.html
  ```bash
  cp frontend/login-email.html frontend/login.html
  ```
- [ ] Verify files replaced correctly

### Step 5: Build and Deploy Backend

- [ ] Install dependencies
  ```bash
  pip install -r requirements-lambda.txt
  ```
- [ ] Build SAM application
  ```bash
  sam build
  ```
- [ ] Deploy to AWS
  ```bash
  sam deploy --guided
  ```
- [ ] Note the API Gateway endpoint URL from output

### Step 6: Update Frontend Configuration

- [ ] Update `frontend/config.json` with new API endpoint
  ```json
  {
    "apiEndpoint": "https://YOUR-API-ID.execute-api.ap-south-1.amazonaws.com/dev"
  }
  ```
- [ ] Verify config file is correct

### Step 7: Deploy Frontend

- [ ] Upload frontend files to S3 or hosting service
- [ ] Clear CDN cache if using CloudFront
- [ ] Verify files are accessible

## Testing Checklist

### Test Registration
- [ ] Open login page in browser
- [ ] Click "Register" tab
- [ ] Fill in registration form:
  - [ ] Name: Test User
  - [ ] Email: test@example.com
  - [ ] Password: SecurePass123!
  - [ ] Confirm Password: SecurePass123!
- [ ] Click "Register Now"
- [ ] Verify success message appears
- [ ] Verify redirected to login tab

### Test Login
- [ ] Enter registered email
- [ ] Enter password
- [ ] Click "Login"
- [ ] Verify JWT token stored in localStorage
- [ ] Verify redirected to profile setup (first time)

### Test Profile Setup
- [ ] Fill in profile information:
  - [ ] Age
  - [ ] Gender
  - [ ] Education
  - [ ] State
  - [ ] District
  - [ ] Occupation
- [ ] Click "Complete Profile"
- [ ] Verify redirected to dashboard

### Test Dashboard
- [ ] Verify dashboard loads
- [ ] Verify user name displayed
- [ ] Verify stats displayed
- [ ] Browse schemes
- [ ] Save a scheme (click bookmark icon)
- [ ] Verify scheme saved

### Test Persistence
- [ ] Logout from dashboard
- [ ] Login again with same email
- [ ] Verify redirected to dashboard (not profile setup)
- [ ] Verify saved scheme still appears
- [ ] Verify profile data intact

### Test Error Handling
- [ ] Try registering with existing email
  - [ ] Verify error message
- [ ] Try logging in with wrong password
  - [ ] Verify error message
- [ ] Try accessing dashboard without token
  - [ ] Verify redirected to login
- [ ] Try with expired token
  - [ ] Verify redirected to login

## Post-Deployment Checklist

### Verify Backend
- [ ] Check CloudWatch logs for errors
- [ ] Verify DynamoDB tables have data
- [ ] Test all API endpoints with Postman/curl
- [ ] Check API Gateway metrics

### Verify Frontend
- [ ] Test on Chrome
- [ ] Test on Firefox
- [ ] Test on Safari
- [ ] Test on mobile devices
- [ ] Verify responsive design
- [ ] Check browser console for errors

### Security Checks
- [ ] Verify HTTPS is enforced
- [ ] Check CORS configuration
- [ ] Verify JWT tokens expire correctly
- [ ] Test with invalid tokens
- [ ] Verify passwords are hashed in database

### Performance Checks
- [ ] Test login speed
- [ ] Test dashboard load time
- [ ] Check API response times
- [ ] Verify no memory leaks

## Rollback Plan

If something goes wrong:

### Rollback Frontend
- [ ] Restore backup files
  ```bash
  cp frontend/api-client.js.backup frontend/api-client.js
  cp frontend/login.html.backup frontend/login.html
  ```
- [ ] Redeploy frontend

### Rollback Backend
- [ ] Use SAM to rollback
  ```bash
  sam deploy --no-execute-changeset
  ```
- [ ] Or restore previous CloudFormation stack

### Delete Tables (if needed)
- [ ] Delete users table
  ```bash
  aws dynamodb delete-table --table-name bharatsahayak-users-dev
  ```
- [ ] Delete saved schemes table
  ```bash
  aws dynamodb delete-table --table-name bharatsahayak-saved-schemes-dev
  ```

## Monitoring

### Set Up Alerts
- [ ] CloudWatch alarm for Lambda errors
- [ ] CloudWatch alarm for API Gateway 5xx errors
- [ ] CloudWatch alarm for DynamoDB throttling
- [ ] SNS topic for notifications

### Regular Checks
- [ ] Monitor CloudWatch logs daily
- [ ] Check DynamoDB metrics
- [ ] Review API Gateway usage
- [ ] Check Lambda execution times

## Documentation

- [ ] Update README.md with new auth system
- [ ] Document API endpoints
- [ ] Create user guide
- [ ] Update architecture diagrams

## Production Readiness

### Security Enhancements
- [ ] Move JWT secret to AWS Secrets Manager
- [ ] Implement rate limiting
- [ ] Add email verification
- [ ] Implement password reset
- [ ] Add MFA option
- [ ] Enable AWS WAF

### Performance Optimizations
- [ ] Enable DynamoDB auto-scaling
- [ ] Configure Lambda reserved concurrency
- [ ] Set up CloudFront caching
- [ ] Optimize API Gateway caching

### Compliance
- [ ] Review data privacy requirements
- [ ] Implement audit logging
- [ ] Set up data backup
- [ ] Configure data retention policies

## Sign-Off

- [ ] Development team approval
- [ ] QA team approval
- [ ] Security team approval
- [ ] Product owner approval

## Notes

Date: _______________
Deployed by: _______________
API Endpoint: _______________
Issues encountered: _______________
Resolution: _______________

---

## Quick Commands Reference

### Check DynamoDB Tables
```bash
aws dynamodb list-tables
aws dynamodb scan --table-name bharatsahayak-users-dev --limit 5
```

### Check Lambda Functions
```bash
aws lambda list-functions | grep bharatsahayak
```

### View CloudWatch Logs
```bash
aws logs tail /aws/lambda/bharatsahayak-auth-email-login --follow
```

### Test API Endpoint
```bash
curl -X POST https://YOUR-API.execute-api.ap-south-1.amazonaws.com/dev/auth/email/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"SecurePass123!","name":"Test User"}'
```

---

**Remember**: Test thoroughly in development before deploying to production!
