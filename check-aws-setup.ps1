# Check AWS Setup and Prerequisites
# Run this to see what you need to install

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AWS Setup Checker" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$allGood = $true

# Check 1: AWS CLI
Write-Host "Checking AWS CLI..." -ForegroundColor Yellow
$awsCli = Get-Command aws -ErrorAction SilentlyContinue
if ($awsCli) {
    $awsVersion = aws --version 2>&1
    Write-Host "✅ AWS CLI installed: $awsVersion" -ForegroundColor Green
    
    # Check credentials
    Write-Host "Checking AWS credentials..." -ForegroundColor Yellow
    $identity = aws sts get-caller-identity 2>&1
    if ($LASTEXITCODE -eq 0) {
        $identityJson = $identity | ConvertFrom-Json
        Write-Host "✅ AWS credentials configured" -ForegroundColor Green
        Write-Host "   Account: $($identityJson.Account)" -ForegroundColor Gray
        Write-Host "   User: $($identityJson.Arn)" -ForegroundColor Gray
    } else {
        Write-Host "❌ AWS credentials NOT configured" -ForegroundColor Red
        Write-Host "   Run: aws configure" -ForegroundColor Yellow
        $allGood = $false
    }
} else {
    Write-Host "❌ AWS CLI NOT installed" -ForegroundColor Red
    Write-Host "   Download: https://awscli.amazonaws.com/AWSCLIV2.msi" -ForegroundColor Yellow
    Write-Host "   Or run: choco install awscli" -ForegroundColor Yellow
    $allGood = $false
}
Write-Host ""

# Check 2: SAM CLI (optional)
Write-Host "Checking SAM CLI (optional)..." -ForegroundColor Yellow
$samCli = Get-Command sam -ErrorAction SilentlyContinue
if ($samCli) {
    $samVersion = sam --version 2>&1
    Write-Host "✅ SAM CLI installed: $samVersion" -ForegroundColor Green
} else {
    Write-Host "⚠️  SAM CLI NOT installed (optional)" -ForegroundColor Yellow
    Write-Host "   Download: https://github.com/aws/aws-sam-cli/releases/latest/download/AWS_SAM_CLI_64_PY3.msi" -ForegroundColor Gray
    Write-Host "   Or run: choco install aws-sam-cli" -ForegroundColor Gray
}
Write-Host ""

# Check 3: Python
Write-Host "Checking Python..." -ForegroundColor Yellow
$python = Get-Command python -ErrorAction SilentlyContinue
if ($python) {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python installed: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "⚠️  Python NOT installed (needed for testing)" -ForegroundColor Yellow
    Write-Host "   Download: https://www.python.org/downloads/" -ForegroundColor Gray
}
Write-Host ""

# Check 4: Git
Write-Host "Checking Git..." -ForegroundColor Yellow
$git = Get-Command git -ErrorAction SilentlyContinue
if ($git) {
    $gitVersion = git --version 2>&1
    Write-Host "✅ Git installed: $gitVersion" -ForegroundColor Green
} else {
    Write-Host "⚠️  Git NOT installed (optional)" -ForegroundColor Yellow
    Write-Host "   Download: https://git-scm.com/download/win" -ForegroundColor Gray
}
Write-Host ""

# Check 5: Project files
Write-Host "Checking project files..." -ForegroundColor Yellow
$requiredFiles = @(
    "template.yaml",
    "src/api/auth_login.py",
    "src/api/health_check.py",
    "src/api/user_stats.py",
    "frontend/config.json",
    "frontend/api-client.js"
)

$filesOk = $true
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "  ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $file MISSING" -ForegroundColor Red
        $filesOk = $false
        $allGood = $false
    }
}

if ($filesOk) {
    Write-Host "✅ All required files present" -ForegroundColor Green
}
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($allGood) {
    Write-Host "🎉 All required tools are installed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "You can deploy using:" -ForegroundColor Cyan
    Write-Host "  Option 1: .\deploy-cli.ps1 (AWS CLI)" -ForegroundColor White
    if ($samCli) {
        Write-Host "  Option 2: .\deploy.ps1 (SAM CLI)" -ForegroundColor White
    }
    Write-Host "  Option 3: AWS Console (manual)" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "⚠️  Some tools are missing" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Minimum required:" -ForegroundColor Cyan
    Write-Host "  - AWS CLI (for automated deployment)" -ForegroundColor White
    Write-Host "  - AWS credentials configured" -ForegroundColor White
    Write-Host ""
    Write-Host "Alternative:" -ForegroundColor Cyan
    Write-Host "  - Deploy via AWS Console (no CLI needed)" -ForegroundColor White
    Write-Host "  - Run: .\create-package.ps1" -ForegroundColor White
    Write-Host "  - Follow manual deployment steps" -ForegroundColor White
    Write-Host ""
}

Write-Host "Documentation:" -ForegroundColor Cyan
Write-Host "  - DEPLOYMENT_ALTERNATIVES.md - All deployment methods" -ForegroundColor White
Write-Host "  - VALIDATION_COMPLETE.md - Validation results" -ForegroundColor White
Write-Host "  - ACTION_PLAN.md - Step-by-step guide" -ForegroundColor White
Write-Host ""
