@echo off
REM BharatSahayak AWS CLI Deployment Script (Batch version)
REM This script deploys using AWS CLI only (no SAM CLI required)

echo ========================================
echo   BharatSahayak AWS CLI Deployment
echo ========================================
echo.

REM Configuration
set BUCKET_NAME=bharatsahayak-deployment-bucket
set STACK_NAME=bharatsahayak-dev
set REGION=ap-south-1
set ENVIRONMENT=dev
set JWT_SECRET=CHANGE_ME_GENERATE_SECURE_SECRET_HERE

REM Check if AWS CLI is installed
echo Checking prerequisites...
where aws >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] AWS CLI is not installed
    echo.
    echo Please install AWS CLI:
    echo   Download: https://awscli.amazonaws.com/AWSCLIV2.msi
    echo   Or run: choco install awscli
    echo.
    echo After installation, run: aws configure
    echo.
    pause
    exit /b 1
)

echo [OK] AWS CLI is installed
echo.

REM Check AWS credentials
echo Checking AWS credentials...
aws sts get-caller-identity >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] AWS credentials not configured
    echo.
    echo Please run: aws configure
    echo You will need:
    echo   - AWS Access Key ID
    echo   - AWS Secret Access Key
    echo   - Default region: ap-south-1
    echo.
    pause
    exit /b 1
)

echo [OK] AWS credentials configured
echo.

REM Step 1: Create S3 bucket if it doesn't exist
echo ========================================
echo   Step 1: Creating S3 Bucket
echo ========================================
echo.

aws s3 ls s3://%BUCKET_NAME% >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Creating S3 bucket: %BUCKET_NAME%
    aws s3 mb s3://%BUCKET_NAME% --region %REGION%
    
    if %ERRORLEVEL% EQU 0 (
        echo [OK] S3 bucket created successfully
    ) else (
        echo [ERROR] Failed to create S3 bucket
        echo Try a different bucket name (must be globally unique)
        echo Edit this script and change BUCKET_NAME variable
        pause
        exit /b 1
    )
) else (
    echo [OK] S3 bucket already exists
)
echo.

REM Step 2: Package the application
echo ========================================
echo   Step 2: Packaging Application
echo ========================================
echo.

echo Packaging template and uploading code to S3...
aws cloudformation package ^
    --template-file template.yaml ^
    --s3-bucket %BUCKET_NAME% ^
    --output-template-file packaged-template.yaml ^
    --region %REGION%

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Packaging failed!
    pause
    exit /b 1
)

echo [OK] Application packaged successfully
echo.

REM Step 3: Deploy the stack
echo ========================================
echo   Step 3: Deploying to AWS
echo ========================================
echo.

echo Deploying CloudFormation stack...
echo This will take 10-15 minutes...
echo.

aws cloudformation deploy ^
    --template-file packaged-template.yaml ^
    --stack-name %STACK_NAME% ^
    --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM ^
    --parameter-overrides Environment=%ENVIRONMENT% JWTSecret=%JWT_SECRET% ^
    --region %REGION%

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Deployment failed!
    echo.
    echo Check CloudFormation console for details:
    echo https://console.aws.amazon.com/cloudformation/
    pause
    exit /b 1
)

echo.
echo [OK] Deployment completed successfully!
echo.

REM Step 4: Get API endpoint
echo ========================================
echo   Step 4: Getting API Endpoint
echo ========================================
echo.

echo Retrieving API endpoint...
for /f "delims=" %%i in ('aws cloudformation describe-stacks --stack-name %STACK_NAME% --query "Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue" --output text --region %REGION%') do set API_ENDPOINT=%%i

if defined API_ENDPOINT (
    echo.
    echo [OK] API Endpoint Retrieved:
    echo   %API_ENDPOINT%
    echo.
    echo API endpoint saved to api-endpoint.txt
    echo %API_ENDPOINT% > api-endpoint.txt
) else (
    echo [WARNING] Could not retrieve API endpoint
    echo Get it manually from CloudFormation console
)

echo.
echo ========================================
echo   Deployment Complete!
echo ========================================
echo.

echo Deployment Summary:
echo   Stack Name: %STACK_NAME%
echo   Region: %REGION%
echo   Environment: %ENVIRONMENT%
if defined API_ENDPOINT (
    echo   API Endpoint: %API_ENDPOINT%
)
echo.

echo Next Steps:
echo   1. Update frontend/config.json with API endpoint
echo   2. Test backend: python test_backend_endpoints.py
echo   3. Test frontend: Open frontend/test-quick.html in browser
echo.

echo All done! Your BharatSahayak backend is live!
echo.
pause
