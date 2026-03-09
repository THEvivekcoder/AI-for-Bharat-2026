# BharatSahayak - Configure and Deploy Script
# Run this script to complete the setup

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "BharatSahayak Email Auth Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Add AWS CLI to PATH
$env:Path += ";C:\Program Files\Amazon\AWSCLIV2"

# Check AWS CLI
Write-Host "Checking AWS CLI..." -ForegroundColor Yellow
aws --version
Write-Host ""

# Check if AWS is configured
Write-Host "Checking AWS configuration..." -ForegroundColor Yellow
$awsConfigured = $false
try {
    aws sts get-caller-identity 2>$null | Out-Null
    $awsConfigured = $true
    Write-Host "AWS credentials are already configured!" -ForegroundColor Green
} catch {
    Write-Host "AWS credentials not configured yet." -ForegroundColor Yellow
}

if (-not $awsConfigured) {
    Write-Host ""
    Write-Host "You need to configure AWS credentials." -ForegroundColor Yellow
    Write-Host "Please run: aws configure" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "You will need:" -ForegroundColor Yellow
    Write-Host "  - AWS Access Key ID" -ForegroundColor White
    Write-Host "  - AWS Secret Access Key" -ForegroundColor White
    Write-Host "  - Default region: ap-south-1" -ForegroundColor White
    Write-Host "  - Default output format: json" -ForegroundColor White
    Write-Host ""
    Write-Host "After configuring, run this script again." -ForegroundColor Cyan
    exit
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 1: Creating DynamoDB Tables" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Create Users Table
Write-Host "Creating bharatsahayak-users-dev table..." -ForegroundColor Yellow
try {
    aws dynamodb create-table `
      --table-name bharatsahayak-users-dev `
      --attribute-definitions AttributeName=email,AttributeType=S `
      --key-schema AttributeName=email,KeyType=HASH `
      --billing-mode PAY_PER_REQUEST `
      --region ap-south-1 2>$null | Out-Null
    Write-Host "Users table created successfully!" -ForegroundColor Green
} catch {
    Write-Host "Users table already exists or error occurred" -ForegroundColor Yellow
}

# Create Saved Schemes Table
Write-Host "Creating bharatsahayak-saved-schemes-dev table..." -ForegroundColor Yellow
try {
    aws dynamodb create-table `
      --table-name bharatsahayak-saved-schemes-dev `
      --attribute-definitions AttributeName=user_id,AttributeType=S AttributeName=scheme_id,AttributeType=S `
      --key-schema AttributeName=user_id,KeyType=HASH AttributeName=scheme_id,KeyType=RANGE `
      --billing-mode PAY_PER_REQUEST `
      --region ap-south-1 2>$null | Out-Null
    Write-Host "Saved Schemes table created successfully!" -ForegroundColor Green
} catch {
    Write-Host "Saved Schemes table already exists or error occurred" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Waiting for tables to become active..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Verify tables
Write-Host ""
Write-Host "Verifying tables..." -ForegroundColor Yellow
aws dynamodb list-tables --region ap-south-1 | Select-String "bharatsahayak"
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 2: Updating Frontend Files" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Backup original files
if (Test-Path "frontend/api-client.js") {
    Copy-Item "frontend/api-client.js" "frontend/api-client.js.backup" -Force
    Write-Host "Backed up api-client.js" -ForegroundColor Green
}

if (Test-Path "frontend/login.html") {
    Copy-Item "frontend/login.html" "frontend/login.html.backup" -Force
    Write-Host "Backed up login.html" -ForegroundColor Green
}

# Replace with new files
Copy-Item "frontend/api-client-email.js" "frontend/api-client.js" -Force
Write-Host "Updated api-client.js" -ForegroundColor Green

Copy-Item "frontend/login-email.html" "frontend/login.html" -Force
Write-Host "Updated login.html" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 3: Building SAM Application" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if SAM is installed
try {
    sam --version
    Write-Host ""
} catch {
    Write-Host "SAM CLI not found! Installing..." -ForegroundColor Yellow
    Write-Host "Please install SAM CLI from:" -ForegroundColor Red
    Write-Host "https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Or use Chocolatey: choco install aws-sam-cli" -ForegroundColor Cyan
    exit
}

Write-Host "Building SAM application..." -ForegroundColor Yellow
sam build

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Build failed! Please check the errors above." -ForegroundColor Red
    exit
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 4: Deploying to AWS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "IMPORTANT: You will be prompted for deployment parameters." -ForegroundColor Yellow
Write-Host "Use these values:" -ForegroundColor Yellow
Write-Host "  - Stack Name: bharatsahayak-dev" -ForegroundColor White
Write-Host "  - AWS Region: ap-south-1" -ForegroundColor White
Write-Host "  - Confirm changes: Y" -ForegroundColor White
Write-Host "  - Allow IAM role creation: Y" -ForegroundColor White
Write-Host "  - Save arguments: Y" -ForegroundColor White
Write-Host ""
Write-Host "Press Enter to continue..." -ForegroundColor Cyan
Read-Host

sam deploy --guided

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Deployment failed! Please check the errors above." -ForegroundColor Red
    exit
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "1. Note the API Gateway endpoint URL from the output above" -ForegroundColor White
Write-Host "2. Update frontend/config.json with the API endpoint" -ForegroundColor White
Write-Host "3. Test registration at: frontend/login.html" -ForegroundColor White
Write-Host ""
Write-Host "For detailed documentation, see:" -ForegroundColor Cyan
Write-Host "  - EMAIL_PASSWORD_AUTH_IMPLEMENTATION.md" -ForegroundColor White
Write-Host "  - QUICK_START_EMAIL_AUTH.md" -ForegroundColor White
Write-Host "  - MANUAL_SETUP_GUIDE.md" -ForegroundColor White
Write-Host ""
