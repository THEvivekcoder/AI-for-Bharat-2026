# Pre-Deployment Comprehensive Check
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "BharatSahayak Pre-Deployment Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$allChecks = @()

# Check 1: Template Validation
Write-Host "1. Validating SAM template..." -ForegroundColor Yellow
$validateResult = sam validate 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✓ Template is valid" -ForegroundColor Green
    $allChecks += $true
} else {
    Write-Host "   ✗ Template validation failed" -ForegroundColor Red
    Write-Host "   $validateResult" -ForegroundColor Red
    $allChecks += $false
}

# Check 2: Python Runtime
Write-Host "2. Checking Python runtime version..." -ForegroundColor Yellow
$runtime = Select-String -Path "template.yaml" -Pattern "Runtime: python" | Select-Object -First 1
if ($runtime -match "python3.12") {
    Write-Host "   ✓ Using Python 3.12 (supported)" -ForegroundColor Green
    $allChecks += $true
} else {
    Write-Host "   ✗ Invalid Python runtime: $runtime" -ForegroundColor Red
    $allChecks += $false
}

# Check 3: S3 Bucket Names (must include AccountId)
Write-Host "3. Checking S3 bucket names for uniqueness..." -ForegroundColor Yellow
$bucketNames = Select-String -Path "template.yaml" -Pattern "BucketName: !Sub bharatsahayak-"
$allUnique = $true
foreach ($bucket in $bucketNames) {
    if ($bucket -match '\$\{AWS::AccountId\}') {
        Write-Host "   ✓ Bucket includes AccountId: $($bucket.Line.Trim())" -ForegroundColor Green
    } else {
        Write-Host "   ✗ Bucket missing AccountId: $($bucket.Line.Trim())" -ForegroundColor Red
        $allUnique = $false
    }
}
$allChecks += $allUnique

# Check 4: No Cognito References
Write-Host "4. Checking for removed Cognito resources..." -ForegroundColor Yellow
$cognitoRefs = Select-String -Path "template.yaml" -Pattern "UserPool:|UserPoolClient:|SNSRole:" | Where-Object { $_.Line -notmatch "^\s*#" }
if ($cognitoRefs.Count -eq 0) {
    Write-Host "   ✓ No Cognito resources found (using email/password auth)" -ForegroundColor Green
    $allChecks += $true
} else {
    Write-Host "   ✗ Found Cognito references:" -ForegroundColor Red
    $cognitoRefs | ForEach-Object { Write-Host "     Line $($_.LineNumber): $($_.Line.Trim())" -ForegroundColor Red }
    $allChecks += $false
}

# Check 5: Required Lambda Handlers Exist
Write-Host "5. Checking Lambda handler files..." -ForegroundColor Yellow
$requiredHandlers = @(
    "auth_email_register.py",
    "auth_email_login.py",
    "dashboard_data.py",
    "save_scheme.py",
    "user_profile_get.py",
    "user_profile_update.py"
)
$allExist = $true
foreach ($handler in $requiredHandlers) {
    if (Test-Path "src/api/$handler") {
        Write-Host "   ✓ Found: $handler" -ForegroundColor Green
    } else {
        Write-Host "   ✗ Missing: $handler" -ForegroundColor Red
        $allExist = $false
    }
}
$allChecks += $allExist

# Check 6: JWT Utility Exists
Write-Host "6. Checking JWT authentication utility..." -ForegroundColor Yellow
if (Test-Path "src/utils/jwt_auth.py") {
    Write-Host "   ✓ JWT auth utility exists" -ForegroundColor Green
    $allChecks += $true
} else {
    Write-Host "   ✗ JWT auth utility missing" -ForegroundColor Red
    $allChecks += $false
}

# Check 7: Requirements File
Write-Host "7. Checking requirements file..." -ForegroundColor Yellow
if (Test-Path "requirements-lambda.txt") {
    $hasJWT = Select-String -Path "requirements-lambda.txt" -Pattern "PyJWT" -Quiet
    if ($hasJWT) {
        Write-Host "   ✓ PyJWT included in requirements" -ForegroundColor Green
        $allChecks += $true
    } else {
        Write-Host "   ✗ PyJWT missing from requirements" -ForegroundColor Red
        $allChecks += $false
    }
} else {
    Write-Host "   ✗ requirements-lambda.txt not found" -ForegroundColor Red
    $allChecks += $false
}

# Check 8: AWS Credentials
Write-Host "8. Checking AWS credentials..." -ForegroundColor Yellow
$awsCheck = aws sts get-caller-identity 2>&1
if ($LASTEXITCODE -eq 0) {
    $identity = $awsCheck | ConvertFrom-Json
    Write-Host "   ✓ AWS credentials valid" -ForegroundColor Green
    Write-Host "     Account: $($identity.Account)" -ForegroundColor Gray
    Write-Host "     User: $($identity.Arn)" -ForegroundColor Gray
    $allChecks += $true
} else {
    Write-Host "   ✗ AWS credentials invalid or not configured" -ForegroundColor Red
    $allChecks += $false
}

# Check 9: Region Configuration
Write-Host "9. Checking AWS region..." -ForegroundColor Yellow
$region = aws configure get region
if ($region -eq "us-east-1") {
    Write-Host "   ✓ Region set to us-east-1" -ForegroundColor Green
    $allChecks += $true
} else {
    Write-Host "   ⚠ Region is $region (expected us-east-1)" -ForegroundColor Yellow
    Write-Host "     Deployment will use us-east-1 as specified in command" -ForegroundColor Gray
    $allChecks += $true
}

# Check 10: Frontend Files
Write-Host "10. Checking frontend files..." -ForegroundColor Yellow
$frontendFiles = @("login-email.html", "api-client-email.js")
$allFrontendExist = $true
foreach ($file in $frontendFiles) {
    if (Test-Path "frontend/$file") {
        Write-Host "   ✓ Found: $file" -ForegroundColor Green
    } else {
        Write-Host "   ✗ Missing: $file" -ForegroundColor Red
        $allFrontendExist = $false
    }
}
$allChecks += $allFrontendExist

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Check Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
$passed = ($allChecks | Where-Object { $_ -eq $true }).Count
$total = $allChecks.Count
Write-Host "Passed: $passed / $total checks" -ForegroundColor $(if ($passed -eq $total) { "Green" } else { "Yellow" })

if ($passed -eq $total) {
    Write-Host ""
    Write-Host "ALL CHECKS PASSED - READY TO DEPLOY!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Run deployment with:" -ForegroundColor Cyan
    Write-Host "  sam build" -ForegroundColor White
    Write-Host "  sam deploy --stack-name bharatsahayak-dev --region us-east-1 --parameter-overrides `"Environment=dev JWTSecret=To2gBlws9qRhc8HNj7SALGfXzWdYeyZv`" --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM --no-confirm-changeset --resolve-s3" -ForegroundColor White
    exit 0
} else {
    Write-Host ""
    Write-Host "SOME CHECKS FAILED - FIX ISSUES BEFORE DEPLOYING" -ForegroundColor Red
    exit 1
}
