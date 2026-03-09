# Manual Setup Guide - Email/Password Authentication

Since AWS CLI needs to be configured, here's a step-by-step manual setup guide.

## Step 1: Complete AWS CLI Installation

The AWS CLI has been downloaded and installed, but you need to either:

**Option A: Restart PowerShell**
1. Close this PowerShell window
2. Open a new PowerShell window as Administrator
3. Test: `aws --version`

**Option B: Add to PATH manually**
1. Open System Environment Variables
2. Add `C:\Program Files\Amazon\AWSCLIV2` to PATH
3. Restart PowerShell
4. Test: `aws --version`

**Option C: Use full path**
```powershell
& "C:\Program Files\Amazon\AWSCLIV2\aws.exe" --version
```

## Step 2: Configure AWS Credentials

Once AWS CLI is working, configure your credentials:

```powershell
aws configure
```

You'll be prompted for:
- AWS Access Key ID: [Your access key]
- AWS Secret Access Key: [Your secret key]
- Default region name: ap-south-1
- Default output format: json

## Step 3: Create DynamoDB Tables

### Create Users Table
```powershell
aws dynamodb create-table `
  --table-name bharatsahayak-users-dev `
  --attribute-definitions AttributeName=email,AttributeType=S `
  --key-schema AttributeName=email,KeyType=HASH `
  --billing-mode PAY_PER_REQUEST `
  --region ap-south-1
```

### Create Saved Schemes Table
```powershell
aws dynamodb create-table `
  --table-name bharatsahayak-saved-schemes-dev `
  --attribute-definitions AttributeName=user_id,AttributeType=S AttributeName=scheme_id,AttributeType=S `
  --key-schema AttributeName=user_id,KeyType=HASH AttributeName=scheme_id,KeyType=RANGE `
  --billing-mode PAY_PER_REQUEST `
  --region ap-south-1
```

### Verify Tables Created
```powershell
aws dynamodb list-tables --region ap-south-1
```

## Step 4: Update Frontend Files

### Backup Original Files
```powershell
Copy-Item frontend/api-client.js frontend/api-client.js.backup -ErrorAction SilentlyContinue
Copy-Item frontend/login.html frontend/login.html.backup -ErrorAction SilentlyContinue
```

### Replace with New Files
```powershell
Copy-Item frontend/api-client-email.js frontend/api-client.js -Force
Copy-Item frontend/login-email.html frontend/login.html -Force
```

### Verify Files Updated
```powershell
Get-Content frontend/api-client.js -First 5
Get-Content frontend/login.html -First 5
```

## Step 5: Install SAM CLI (if not installed)

Check if SAM CLI is installed:
```powershell
sam --version
```

If not installed, download from:
https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html

Or use Chocolatey:
```powershell
choco install aws-sam-cli
```

## Step 6: Update SAM Template

You need to add the new Lambda functions to your `template.yaml`. Here's what to add:

```yaml
  # Add these new functions to your template.yaml

  AuthEmailRegisterFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: src/
      Handler: api.auth_email_register.lambda_handler
      Runtime: python3.11
      Timeout: 30
      Environment:
        Variables:
          USERS_TABLE: bharatsahayak-users-dev
          JWT_SECRET: !Ref JWTSecret
      Policies:
        - DynamoDBCrudPolicy:
            TableName: bharatsahayak-users-dev
      Events:
        RegisterAPI:
          Type: Api
          Properties:
            Path: /auth/email/register
            Method: post
            RestApiId: !Ref BharatSahayakAPI

  AuthEmailLoginFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: src/
      Handler: api.auth_email_login.lambda_handler
      Runtime: python3.11
      Timeout: 30
      Environment:
        Variables:
          USERS_TABLE: bharatsahayak-users-dev
          JWT_SECRET: !Ref JWTSecret
      Policies:
        - DynamoDBCrudPolicy:
            TableName: bharatsahayak-users-dev
      Events:
        LoginAPI:
          Type: Api
          Properties:
            Path: /auth/email/login
            Method: post
            RestApiId: !Ref BharatSahayakAPI

  DashboardDataFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: src/
      Handler: api.dashboard_data.lambda_handler
      Runtime: python3.11
      Timeout: 30
      Environment:
        Variables:
          USERS_TABLE: bharatsahayak-users-dev
          PROFILES_TABLE: bharatsahayak-user-profiles-dev
          SAVED_SCHEMES_TABLE: bharatsahayak-saved-schemes-dev
          JWT_SECRET: !Ref JWTSecret
      Policies:
        - DynamoDBCrudPolicy:
            TableName: bharatsahayak-users-dev
        - DynamoDBCrudPolicy:
            TableName: bharatsahayak-user-profiles-dev
        - DynamoDBCrudPolicy:
            TableName: bharatsahayak-saved-schemes-dev
      Events:
        DashboardAPI:
          Type: Api
          Properties:
            Path: /dashboard/data
            Method: get
            RestApiId: !Ref BharatSahayakAPI

  SaveSchemeFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: src/
      Handler: api.save_scheme.lambda_handler
      Runtime: python3.11
      Timeout: 30
      Environment:
        Variables:
          SAVED_SCHEMES_TABLE: bharatsahayak-saved-schemes-dev
          JWT_SECRET: !Ref JWTSecret
      Policies:
        - DynamoDBCrudPolicy:
            TableName: bharatsahayak-saved-schemes-dev
      Events:
        SaveSchemeAPI:
          Type: Api
          Properties:
            Path: /schemes/save
            Method: post
            RestApiId: !Ref BharatSahayakAPI

# Add this parameter
Parameters:
  JWTSecret:
    Type: String
    Default: your-secret-key-change-in-production-12345
    Description: Secret key for JWT token generation
    NoEcho: true
```

## Step 7: Build and Deploy

### Build the Application
```powershell
sam build
```

### Deploy to AWS
```powershell
sam deploy --guided
```

During deployment, you'll be asked:
- Stack Name: bharatsahayak-dev (or your preferred name)
- AWS Region: ap-south-1
- Parameter JWTSecret: [Enter a secure secret key]
- Confirm changes before deploy: Y
- Allow SAM CLI IAM role creation: Y
- Disable rollback: N
- Save arguments to configuration file: Y

### Note the API Endpoint
After deployment completes, note the API Gateway endpoint URL from the output.

## Step 8: Update Frontend Configuration

Update `frontend/config.json`:
```json
{
  "apiEndpoint": "https://YOUR-API-ID.execute-api.ap-south-1.amazonaws.com/dev"
}
```

Replace `YOUR-API-ID` with the actual API ID from the deployment output.

## Step 9: Test the Implementation

### Test Registration
1. Open `frontend/login.html` in a browser
2. Click "Register" tab
3. Fill in:
   - Name: Test User
   - Email: test@example.com
   - Password: SecurePass123!
   - Confirm Password: SecurePass123!
4. Click "Register Now"
5. Should see success message

### Test Login
1. Click "Login" tab
2. Enter email: test@example.com
3. Enter password: SecurePass123!
4. Click "Login"
5. Should redirect to profile setup

### Test Profile Setup
1. Fill in profile information
2. Click "Complete Profile"
3. Should redirect to dashboard

### Test Persistence
1. Save a scheme on dashboard
2. Logout
3. Login again
4. Verify saved scheme is still there

## Step 10: Verify Backend

### Check DynamoDB Tables
```powershell
# List all tables
aws dynamodb list-tables --region ap-south-1

# Check users table
aws dynamodb scan --table-name bharatsahayak-users-dev --limit 5 --region ap-south-1

# Check saved schemes table
aws dynamodb scan --table-name bharatsahayak-saved-schemes-dev --limit 5 --region ap-south-1
```

### Check Lambda Functions
```powershell
aws lambda list-functions --region ap-south-1 | Select-String "bharatsahayak"
```

### Test API Endpoints
```powershell
# Test registration
$body = @{
    email = "test2@example.com"
    password = "SecurePass123!"
    name = "Test User 2"
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://YOUR-API-ID.execute-api.ap-south-1.amazonaws.com/dev/auth/email/register" `
  -Method Post `
  -Body $body `
  -ContentType "application/json"
```

## Troubleshooting

### Issue: AWS CLI not found after installation
**Solution**: Restart PowerShell or add to PATH manually

### Issue: AWS credentials not configured
**Solution**: Run `aws configure` and enter your credentials

### Issue: DynamoDB table already exists
**Solution**: This is fine, the table was created previously

### Issue: SAM build fails
**Solution**: 
- Check Python is installed: `python --version`
- Install dependencies: `pip install -r requirements-lambda.txt`

### Issue: Deployment fails
**Solution**: 
- Check AWS credentials are valid
- Verify IAM permissions
- Check CloudFormation console for detailed errors

### Issue: Frontend can't connect to API
**Solution**: 
- Verify API endpoint in config.json
- Check CORS settings in API Gateway
- Check browser console for errors

## Quick Commands Reference

```powershell
# Check AWS CLI
aws --version

# Configure AWS
aws configure

# List DynamoDB tables
aws dynamodb list-tables --region ap-south-1

# Build SAM app
sam build

# Deploy SAM app
sam deploy --guided

# View CloudWatch logs
aws logs tail /aws/lambda/bharatsahayak-auth-email-login --follow --region ap-south-1

# Test API endpoint
Invoke-RestMethod -Uri "https://YOUR-API.execute-api.ap-south-1.amazonaws.com/dev/auth/email/login" `
  -Method Post `
  -Body '{"email":"test@example.com","password":"SecurePass123!"}' `
  -ContentType "application/json"
```

## Summary

After completing these steps, you'll have:
- ✅ AWS CLI installed and configured
- ✅ DynamoDB tables created
- ✅ Frontend files updated
- ✅ Backend deployed to AWS
- ✅ Email/password authentication working
- ✅ Persistent user data across logins

## Next Steps

1. Test thoroughly in development
2. Add email verification
3. Implement password reset
4. Set up monitoring and alerts
5. Deploy to production

For detailed documentation, see:
- `EMAIL_PASSWORD_AUTH_IMPLEMENTATION.md`
- `QUICK_START_EMAIL_AUTH.md`
- `DEPLOYMENT_CHECKLIST.md`
