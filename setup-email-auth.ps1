# BharatSahayak Email Authentication Setup Script (PowerShell)
# This script sets up the email/password authentication system

Write-Host "🚀 BharatSahayak Email Authentication Setup" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

# Check if AWS CLI is installed
try {
    aws --version | Out-Null
    Write-Host "✅ AWS CLI found" -ForegroundColor Green
} catch {
    Write-Host "❌ AWS CLI is not installed. Please install it first." -ForegroundColor Red
    exit 1
}

# Check if SAM CLI is installed
try {
    sam --version | Out-Null
    Write-Host "✅ SAM CLI found" -ForegroundColor Green
} catch {
    Write-Host "❌ SAM CLI is not installed. Please install it first." -ForegroundColor Red
    exit 1
}

Write-Host ""

# Get AWS region
$AWS_REGION = Read-Host "Enter AWS region (default: ap-south-1)"
if ([string]::IsNullOrWhiteSpace($AWS_REGION)) {
    $AWS_REGION = "ap-south-1"
}

Write-Host "📍 Using region: $AWS_REGION" -ForegroundColor Yellow
Write-Host ""

# Create DynamoDB tables
Write-Host "📦 Creating DynamoDB tables..." -ForegroundColor Cyan
Write-Host ""

# Create Users table
Write-Host "Creating bharatsahayak-users-dev table..."
try {
    aws dynamodb create-table `
      --table-name bharatsahayak-users-dev `
      --attribute-definitions AttributeName=email,AttributeType=S `
      --key-schema AttributeName=email,KeyType=HASH `
      --billing-mode PAY_PER_REQUEST `
      --region $AWS_REGION 2>$null
    Write-Host "✅ Users table created" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Users table already exists" -ForegroundColor Yellow
}

# Create Saved Schemes table
Write-Host "Creating bharatsahayak-saved-schemes-dev table..."
try {
    aws dynamodb create-table `
      --table-name bharatsahayak-saved-schemes-dev `
      --attribute-definitions AttributeName=user_id,AttributeType=S AttributeName=scheme_id,AttributeType=S `
      --key-schema AttributeName=user_id,KeyType=HASH AttributeName=scheme_id,KeyType=RANGE `
      --billing-mode PAY_PER_REQUEST `
      --region $AWS_REGION 2>$null
    Write-Host "✅ Saved Schemes table created" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Saved Schemes table already exists" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "⏳ Waiting for tables to become active..."
Start-Sleep -Seconds 5

# Update frontend files
Write-Host ""
Write-Host "📝 Updating frontend files..." -ForegroundColor Cyan

# Backup original files
if (Test-Path "frontend/api-client.js") {
    Copy-Item "frontend/api-client.js" "frontend/api-client.js.backup"
    Write-Host "✅ Backed up api-client.js" -ForegroundColor Green
}

if (Test-Path "frontend/login.html") {
    Copy-Item "frontend/login.html" "frontend/login.html.backup"
    Write-Host "✅ Backed up login.html" -ForegroundColor Green
}

# Replace with new files
Copy-Item "frontend/api-client-email.js" "frontend/api-client.js" -Force
Write-Host "✅ Updated api-client.js" -ForegroundColor Green

Copy-Item "frontend/login-email.html" "frontend/login.html" -Force
Write-Host "✅ Updated login.html" -ForegroundColor Green

# Build and deploy
Write-Host ""
Write-Host "🔨 Building SAM application..." -ForegroundColor Cyan
sam build

Write-Host ""
Write-Host "🚀 Deploying to AWS..." -ForegroundColor Cyan
Write-Host "Note: You may be prompted for deployment parameters" -ForegroundColor Yellow
Write-Host ""

sam deploy --guided

Write-Host ""
Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Note the API Gateway endpoint URL from the deployment output"
Write-Host "2. Update frontend/config.json with the new API endpoint"
Write-Host "3. Test registration at: https://your-domain/login.html"
Write-Host "4. Check the EMAIL_PASSWORD_AUTH_IMPLEMENTATION.md for detailed documentation"
Write-Host ""
Write-Host "🎉 Setup complete!" -ForegroundColor Green
