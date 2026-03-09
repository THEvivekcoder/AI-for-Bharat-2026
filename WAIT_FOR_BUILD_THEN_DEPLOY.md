# Wait for Build to Complete, Then Deploy

## Current Status

✅ **DynamoDB tables deleted** (will be recreated by SAM)
✅ **Template updated** (UsersTable now uses email as primary key)
✅ **SAM build running** in background (copying source files for 31 Lambda functions)
⏳ **Waiting for build to complete...**

## What's Happening Now

The `sam build` command is running in the background and:
1. Copying source code for all 31 Lambda functions
2. Installing Python dependencies
3. Creating deployment packages

This can take 5-10 minutes. Be patient!

## How to Check if Build is Complete

Open a new PowerShell window and run:
```powershell
Test-Path ".aws-sam/build/template.yaml"
```

If it returns `True`, the build is complete!

Or check if the build process is still running:
```powershell
Get-Process | Where-Object {$_.ProcessName -like "*sam*" -or $_.ProcessName -like "*python*"}
```

## Once Build Completes

### Step 1: Deploy
Run this command:
```powershell
.\deploy-now.ps1
```

Or manually:
```powershell
sam deploy `
  --stack-name bharatsahayak-dev `
  --region us-east-1 `
  --parameter-overrides "Environment=dev JWTSecret=YOUR-SECURE-SECRET-HERE" `
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM `
  --no-confirm-changeset `
  --resolve-s3
```

### Step 2: Note the API Endpoint
After deployment completes, you'll see output like:
```
Outputs:
  ApiEndpoint: https://XXXXXXXXXX.execute-api.us-east-1.amazonaws.com/dev
```

**SAVE THIS URL!**

### Step 3: Update Frontend Config
Edit `frontend/config.json`:
```json
{
  "apiEndpoint": "https://XXXXXXXXXX.execute-api.us-east-1.amazonaws.com/dev"
}
```

### Step 4: Test!
1. Open `frontend/login.html` in your browser
2. Register with email and password
3. Login
4. Complete profile
5. Save some schemes
6. Logout and login again
7. Verify your saved schemes are still there!

## What Will Be Created

When deployment completes, SAM will create:

### DynamoDB Tables
- `bharatsahayak-users-dev` (Primary Key: email)
- `bharatsahayak-saved-schemes-dev` (Primary Key: user_id, Sort Key: scheme_id)
- `bharatsahayak-user-profiles-dev`
- `bharatsahayak-schemes-dev`
- `bharatsahayak-interactions-dev`
- `bharatsahayak-farm-profiles-dev`
- And more...

### Lambda Functions (31 total)
Including your new ones:
- `bharatsahayak-auth-email-register-dev`
- `bharatsahayak-auth-email-login-dev`
- `bharatsahayak-dashboard-data-dev`
- `bharatsahayak-save-scheme-dev`

### API Gateway
- REST API with all endpoints
- CORS configured
- Throttling enabled

### IAM Roles
- Lambda execution roles
- DynamoDB access policies

## Troubleshooting

### Build Taking Too Long
- This is normal for first build
- 31 Lambda functions + dependencies = lots of files to copy
- Can take 10-15 minutes
- Just wait patiently

### Build Fails
Check the error message. Common issues:
- Python version mismatch (we're using 3.13)
- File permission issues (run PowerShell as Administrator)
- Disk space (need ~500MB free)

### Deployment Fails
- Check CloudFormation console for detailed errors
- Verify IAM permissions
- Check if resources already exist

## Expected Timeline

- **Build**: 5-10 minutes (currently running)
- **Deploy**: 10-15 minutes (after build completes)
- **Total**: 15-25 minutes from now

## What You'll Have

After successful deployment:

✅ Complete email/password authentication system
✅ JWT token-based sessions (7-day expiry)
✅ Persistent user data across logins
✅ Profile management
✅ Save/unsave schemes functionality
✅ Modern, responsive UI
✅ Secure password hashing
✅ Automatic session restoration

## Success Criteria

You'll know it's working when:
1. ✅ User can register with email/password
2. ✅ User can login and get JWT token
3. ✅ User completes profile (first time only)
4. ✅ User sees personalized dashboard
5. ✅ User can save schemes
6. ✅ User logs out and logs in again
7. ✅ User sees all saved data intact

## Next Steps After Deployment

1. **Test thoroughly** - Try all user flows
2. **Check CloudWatch logs** - Monitor for errors
3. **Verify DynamoDB data** - Check tables have data
4. **Test persistence** - Logout/login multiple times
5. **Update documentation** - Note your API endpoint

## Important Files

- `FINAL_SUMMARY.md` - Complete overview
- `EMAIL_PASSWORD_AUTH_IMPLEMENTATION.md` - Technical details
- `DEPLOYMENT_STATUS.md` - Current status
- `deploy-now.ps1` - Deployment script

## Commands Reference

```powershell
# Check build status
Test-Path ".aws-sam/build/template.yaml"

# Deploy after build
.\deploy-now.ps1

# Check deployment status
aws cloudformation describe-stacks --stack-name bharatsahayak-dev --region us-east-1

# View API endpoint
aws cloudformation describe-stacks --stack-name bharatsahayak-dev --region us-east-1 --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' --output text

# Test registration
$body = @{email="test@example.com"; password="SecurePass123!"; name="Test User"} | ConvertTo-Json
Invoke-RestMethod -Uri "https://YOUR-API/dev/auth/email/register" -Method Post -Body $body -ContentType "application/json"
```

---

**Current Time**: March 9, 2026
**Status**: SAM build running in background
**Action**: Wait for build to complete, then run `.\deploy-now.ps1`

**Be patient! The build is working. Once it completes, deployment will be quick and smooth.**
