# BharatSahayak - Install Required Tools
# This script installs AWS CLI and AWS SAM CLI

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Installing Required Tools" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "❌ This script requires Administrator privileges" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please run PowerShell as Administrator and try again:" -ForegroundColor Yellow
    Write-Host "  1. Right-click PowerShell" -ForegroundColor White
    Write-Host "  2. Select 'Run as Administrator'" -ForegroundColor White
    Write-Host "  3. Run: .\install-requirements.ps1" -ForegroundColor White
    Write-Host ""
    exit 1
}

Write-Host "✅ Running as Administrator" -ForegroundColor Green
Write-Host ""

# Check Chocolatey
Write-Host "Checking Chocolatey..." -ForegroundColor Yellow
$chocoInstalled = Get-Command choco -ErrorAction SilentlyContinue

if (-not $chocoInstalled) {
    Write-Host "❌ Chocolatey is not installed" -ForegroundColor Red
    Write-Host "Installing Chocolatey..." -ForegroundColor Yellow
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install Chocolatey" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✅ Chocolatey installed" -ForegroundColor Green
} else {
    Write-Host "✅ Chocolatey is already installed" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Installing AWS CLI" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if AWS CLI is already installed
$awsInstalled = Get-Command aws -ErrorAction SilentlyContinue

if ($awsInstalled) {
    Write-Host "✅ AWS CLI is already installed" -ForegroundColor Green
    aws --version
} else {
    Write-Host "Installing AWS CLI..." -ForegroundColor Yellow
    choco install awscli -y
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install AWS CLI" -ForegroundColor Red
        exit 1
    }
    
    # Refresh environment variables
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    Write-Host "✅ AWS CLI installed successfully" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Installing AWS SAM CLI" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if SAM CLI is already installed
$samInstalled = Get-Command sam -ErrorAction SilentlyContinue

if ($samInstalled) {
    Write-Host "✅ AWS SAM CLI is already installed" -ForegroundColor Green
    sam --version
} else {
    Write-Host "Installing AWS SAM CLI..." -ForegroundColor Yellow
    choco install aws-sam-cli -y
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install AWS SAM CLI" -ForegroundColor Red
        Write-Host ""
        Write-Host "Trying alternative installation method..." -ForegroundColor Yellow
        
        # Try MSI installer as fallback
        $msiUrl = "https://github.com/aws/aws-sam-cli/releases/latest/download/AWS_SAM_CLI_64_PY3.msi"
        $msiPath = "$env:TEMP\AWS_SAM_CLI_64_PY3.msi"
        
        Write-Host "Downloading SAM CLI installer..." -ForegroundColor Yellow
        Invoke-WebRequest -Uri $msiUrl -OutFile $msiPath
        
        Write-Host "Installing SAM CLI..." -ForegroundColor Yellow
        Start-Process msiexec.exe -ArgumentList "/i `"$msiPath`" /qn /norestart" -Wait
        
        Remove-Item $msiPath -Force
    }
    
    # Refresh environment variables
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    Write-Host "✅ AWS SAM CLI installed successfully" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Verifying installations..." -ForegroundColor Yellow
Write-Host ""

# Verify AWS CLI
Write-Host "AWS CLI:" -ForegroundColor Cyan
try {
    $awsVersion = aws --version 2>&1
    Write-Host "  ✅ $awsVersion" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️  Not found in current session - restart terminal" -ForegroundColor Yellow
}

# Verify SAM CLI
Write-Host "SAM CLI:" -ForegroundColor Cyan
try {
    $samVersion = sam --version 2>&1
    Write-Host "  ✅ $samVersion" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️  Not found in current session - restart terminal" -ForegroundColor Yellow
}

# Verify Python
Write-Host "Python:" -ForegroundColor Cyan
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✅ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Not found" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Next Steps" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "1. Close and reopen your terminal (to refresh environment variables)" -ForegroundColor Yellow
Write-Host ""
Write-Host "2. Configure AWS credentials:" -ForegroundColor Yellow
Write-Host "   aws configure" -ForegroundColor White
Write-Host "   (You'll need: Access Key ID, Secret Access Key, Region)" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Deploy BharatSahayak:" -ForegroundColor Yellow
Write-Host "   .\deploy.ps1" -ForegroundColor White
Write-Host ""

Write-Host "🎉 Installation complete!" -ForegroundColor Green
Write-Host ""
