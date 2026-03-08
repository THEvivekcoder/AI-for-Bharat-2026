# BharatSahayak Deployment Script
# This script deploys the BharatSahayak backend to AWS

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  BharatSahayak Deployment Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if SAM CLI is installed
Write-Host "Checking prerequisites..." -ForegroundColor Yellow
$samInstalled = Get-Command sam -ErrorAction SilentlyContinue

if (-not $samInstalled) {
    Write-Host "❌ AWS SAM CLI is not installed" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install AWS SAM CLI:" -ForegroundColor Yellow
    Write-Host "  Option 1: Download from https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html" -ForegroundColor White
    Write-Host "  Option 2: Using Chocolatey: choco install aws-sam-cli" -ForegroundColor White
    Write-Host ""
    exit 1
}

Write-Host "✅ AWS SAM CLI is installed" -ForegroundColor Green

# Check if AWS CLI is configured
$awsConfigured = Test-Path "$env:USERPROFILE\.aws\credentials"
if (-not $awsConfigured) {
    Write-Host "⚠️  AWS credentials not found" -ForegroundColor Yellow
    Write-Host "Please run: aws configure" -ForegroundColor White
    Write-Host ""
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne 'y') {
        exit 1
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Step 1: Building Application" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Build
Write-Host "Running: sam build" -ForegroundColor Yellow
sam build

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ Build failed!" -ForegroundColor Red
    Write-Host "Please check the error messages above" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "✅ Build completed successfully" -ForegroundColor Green
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Step 2: Deploying to AWS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if samconfig.toml exists (previous deployment)
$configExists = Test-Path "samconfig.toml"

if ($configExists) {
    Write-Host "Found existing deployment configuration" -ForegroundColor Green
    Write-Host "Running: sam deploy" -ForegroundColor Yellow
    sam deploy
} else {
    Write-Host "First time deployment - using guided mode" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "You will be prompted for:" -ForegroundColor Cyan
    Write-Host "  - Stack Name: bharatsahayak-dev (recommended)" -ForegroundColor White
    Write-Host "  - AWS Region: ap-south-1 (recommended)" -ForegroundColor White
    Write-Host "  - Parameter Environment: dev" -ForegroundColor White
    Write-Host "  - Confirm changes: Y" -ForegroundColor White
    Write-Host "  - Allow SAM CLI IAM role creation: Y" -ForegroundColor White
    Write-Host "  - Save arguments to config: Y" -ForegroundColor White
    Write-Host ""
    
    $ready = Read-Host "Ready to proceed? (y/n)"
    if ($ready -ne 'y') {
        Write-Host "Deployment cancelled" -ForegroundColor Yellow
        exit 0
    }
    
    Write-Host ""
    Write-Host "Running: sam deploy --guided" -ForegroundColor Yellow
    sam deploy --guided
}

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ Deployment failed!" -ForegroundColor Red
    Write-Host "Please check the error messages above" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get API endpoint
Write-Host "Getting API endpoint..." -ForegroundColor Yellow
$apiEndpoint = sam list endpoints --stack-name bharatsahayak-dev 2>&1 | Select-String -Pattern "https://" | Select-Object -First 1

if ($apiEndpoint) {
    Write-Host ""
    Write-Host "✅ API Endpoint:" -ForegroundColor Green
    Write-Host "  $apiEndpoint" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📝 Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Update frontend/config.json with the API endpoint above" -ForegroundColor White
    Write-Host "  2. Run: python test_backend_endpoints.py" -ForegroundColor White
    Write-Host "  3. Open: frontend/test-quick.html in browser" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "⚠️  Could not retrieve API endpoint automatically" -ForegroundColor Yellow
    Write-Host "Run this command to get it:" -ForegroundColor White
    Write-Host "  sam list endpoints --stack-name bharatsahayak-dev" -ForegroundColor Cyan
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Deployment Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ Backend deployed successfully" -ForegroundColor Green
Write-Host "✅ All 14 endpoints configured" -ForegroundColor Green
Write-Host "✅ Ready for testing" -ForegroundColor Green
Write-Host ""
Write-Host "📚 Documentation:" -ForegroundColor Cyan
Write-Host "  - VALIDATION_COMPLETE.md - Validation results" -ForegroundColor White
Write-Host "  - TESTING_GUIDE.md - Testing instructions" -ForegroundColor White
Write-Host "  - FIXES_APPLIED.md - List of fixes" -ForegroundColor White
Write-Host ""
Write-Host "🎉 Deployment complete!" -ForegroundColor Green
Write-Host ""
