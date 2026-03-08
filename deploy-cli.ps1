# BharatSahayak AWS CLI Deployment Script
# This script deploys using AWS CLI only (no SAM CLI required)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  BharatSahayak AWS CLI Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$BUCKET_NAME = "bharatsahayak-deployment-bucket"
$STACK_NAME = "bharatsahayak-dev"
$REGION = "ap-south-1"
$ENVIRONMENT = "dev"

# Check if AWS CLI is installed
Write-Host "Checking prerequisites..." -ForegroundColor Yellow
$awsInstalled = Get-Command aws -ErrorAction SilentlyContinue

if (-not $awsInstalled) {
    Write-Host "❌ AWS CLI is not installed" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install AWS CLI:" -ForegroundColor Yellow
    Write-Host "  Download: https://awscli.amazonaws.com/AWSCLIV2.msi" -ForegroundColor White
    Write-Host "  Or run: choco install awscli" -ForegroundColor White
    Write-Host ""
    Write-Host "After installation, run: aws configure" -ForegroundColor White
    Write-Host ""
    exit 1
}

Write-Host "✅ AWS CLI is installed" -ForegroundColor Green

# Check AWS credentials
Write-Host "Checking AWS credentials..." -ForegroundColor Yellow
$awsIdentity = aws sts get-caller-identity 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ AWS credentials not configured" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please run: aws configure" -ForegroundColor Yellow
    Write-Host "You will need:" -ForegroundColor White
    Write-Host "  - AWS Access Key ID" -ForegroundColor White
    Write-Host "  - AWS Secret Access Key" -ForegroundColor White
    Write-Host "  - Default region: ap-south-1" -ForegroundColor White
    Write-Host ""
    exit 1
}

Write-Host "✅ AWS credentials configured" -ForegroundColor Green
Write-Host ""

# Generate JWT Secret
Write-Host "Generating JWT secret..." -ForegroundColor Yellow
$JWT_SECRET = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
Write-Host "✅ JWT secret generated" -ForegroundColor Green
Write-Host ""

# Step 1: Create S3 bucket if it doesn't exist
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Step 1: Creating S3 Bucket" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$bucketExists = aws s3 ls "s3://$BUCKET_NAME" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating S3 bucket: $BUCKET_NAME" -ForegroundColor Yellow
    aws s3 mb "s3://$BUCKET_NAME" --region $REGION
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ S3 bucket created successfully" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to create S3 bucket" -ForegroundColor Red
        Write-Host "Try a different bucket name (must be globally unique)" -ForegroundColor Yellow
        Write-Host "Edit this script and change BUCKET_NAME variable" -ForegroundColor White
        exit 1
    }
} else {
    Write-Host "✅ S3 bucket already exists" -ForegroundColor Green
}
Write-Host ""

# Step 2: Package the application
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Step 2: Packaging Application" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Packaging template and uploading code to S3..." -ForegroundColor Yellow
aws cloudformation package `
    --template-file template.yaml `
    --s3-bucket $BUCKET_NAME `
    --output-template-file packaged-template.yaml `
    --region $REGION

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ Packaging failed!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Application packaged successfully" -ForegroundColor Green
Write-Host ""

# Step 3: Deploy the stack
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Step 3: Deploying to AWS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Deploying CloudFormation stack..." -ForegroundColor Yellow
Write-Host "This will take 10-15 minutes..." -ForegroundColor Yellow
Write-Host ""

aws cloudformation deploy `
    --template-file packaged-template.yaml `
    --stack-name $STACK_NAME `
    --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM `
    --parameter-overrides Environment=$ENVIRONMENT JWTSecret=$JWT_SECRET `
    --region $REGION

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ Deployment failed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Check CloudFormation console for details:" -ForegroundColor Yellow
    Write-Host "https://console.aws.amazon.com/cloudformation/" -ForegroundColor Cyan
    exit 1
}

Write-Host ""
Write-Host "✅ Deployment completed successfully!" -ForegroundColor Green
Write-Host ""

# Step 4: Get API endpoint
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Step 4: Getting API Endpoint" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Retrieving API endpoint..." -ForegroundColor Yellow
$apiEndpoint = aws cloudformation describe-stacks `
    --stack-name $STACK_NAME `
    --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' `
    --output text `
    --region $REGION

if ($apiEndpoint) {
    Write-Host ""
    Write-Host "✅ API Endpoint Retrieved:" -ForegroundColor Green
    Write-Host "  $apiEndpoint" -ForegroundColor Cyan
    Write-Host ""
    
    # Update frontend config
    Write-Host "Updating frontend/config.json..." -ForegroundColor Yellow
    $configPath = "frontend/config.json"
    if (Test-Path $configPath) {
        $config = Get-Content $configPath | ConvertFrom-Json
        $config.apiEndpoint = $apiEndpoint
        $config | ConvertTo-Json -Depth 10 | Set-Content $configPath
        Write-Host "✅ Frontend config updated" -ForegroundColor Green
    }
} else {
    Write-Host "⚠️  Could not retrieve API endpoint" -ForegroundColor Yellow
    Write-Host "Get it manually from CloudFormation console" -ForegroundColor White
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Deployment Complete! 🎉" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "📊 Deployment Summary:" -ForegroundColor Cyan
Write-Host "  Stack Name: $STACK_NAME" -ForegroundColor White
Write-Host "  Region: $REGION" -ForegroundColor White
Write-Host "  Environment: $ENVIRONMENT" -ForegroundColor White
if ($apiEndpoint) {
    Write-Host "  API Endpoint: $apiEndpoint" -ForegroundColor White
}
Write-Host ""

Write-Host "📝 Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Test backend: python test_backend_endpoints.py" -ForegroundColor White
Write-Host "  2. Test frontend: Open frontend/test-quick.html in browser" -ForegroundColor White
Write-Host "  3. View logs: CloudWatch Logs in AWS Console" -ForegroundColor White
Write-Host ""

Write-Host "📚 Useful Commands:" -ForegroundColor Cyan
Write-Host "  View stack status:" -ForegroundColor White
Write-Host "    aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION" -ForegroundColor Gray
Write-Host ""
Write-Host "  View stack outputs:" -ForegroundColor White
Write-Host "    aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].Outputs' --region $REGION" -ForegroundColor Gray
Write-Host ""
Write-Host "  Delete stack (cleanup):" -ForegroundColor White
Write-Host "    aws cloudformation delete-stack --stack-name $STACK_NAME --region $REGION" -ForegroundColor Gray
Write-Host ""

Write-Host "🎉 All done! Your BharatSahayak backend is live!" -ForegroundColor Green
Write-Host ""
