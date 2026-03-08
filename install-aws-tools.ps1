# Install AWS CLI and SAM CLI without requiring Administrator
# This script downloads and installs using MSI installers

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  BharatSahayak - Install AWS Tools" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$tempDir = $env:TEMP

# Function to check if command exists
function Test-Command {
    param($Command)
    try {
        if (Get-Command $Command -ErrorAction Stop) {
            return $true
        }
    } catch {
        return $false
    }
    return $false
}

# Check AWS CLI
Write-Host "Checking AWS CLI..." -ForegroundColor Yellow
if (Test-Command "aws") {
    $awsVersion = aws --version 2>&1
    Write-Host "✅ AWS CLI is already installed: $awsVersion" -ForegroundColor Green
    $installAWS = $false
} else {
    Write-Host "❌ AWS CLI not found" -ForegroundColor Red
    $installAWS = $true
}

Write-Host ""

# Check SAM CLI
Write-Host "Checking SAM CLI..." -ForegroundColor Yellow
if (Test-Command "sam") {
    $samVersion = sam --version 2>&1
    Write-Host "✅ SAM CLI is already installed: $samVersion" -ForegroundColor Green
    $installSAM = $false
} else {
    Write-Host "❌ SAM CLI not found" -ForegroundColor Red
    $installSAM = $true
}

Write-Host ""

if (-not $installAWS -and -not $installSAM) {
    Write-Host "🎉 All tools are already installed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next step: Configure AWS credentials" -ForegroundColor Yellow
    Write-Host "  aws configure" -ForegroundColor White
    Write-Host ""
    exit 0
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Installation Required" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($installAWS) {
    Write-Host "📥 Installing AWS CLI..." -ForegroundColor Yellow
    Write-Host ""
    
    $awsMsiUrl = "https://awscli.amazonaws.com/AWSCLIV2.msi"
    $awsMsiPath = Join-Path $tempDir "AWSCLIV2.msi"
    
    Write-Host "  Downloading AWS CLI installer..." -ForegroundColor Gray
    try {
        Invoke-WebRequest -Uri $awsMsiUrl -OutFile $awsMsiPath -UseBasicParsing
        Write-Host "  ✅ Download complete" -ForegroundColor Green
    } catch {
        Write-Host "  ❌ Download failed: $_" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "  Installing AWS CLI (this may take a minute)..." -ForegroundColor Gray
    Write-Host "  A Windows installer window will appear - please follow the prompts" -ForegroundColor Yellow
    
    try {
        Start-Process msiexec.exe -ArgumentList "/i `"$awsMsiPath`" /qb" -Wait
        Write-Host "  ✅ AWS CLI installed" -ForegroundColor Green
    } catch {
        Write-Host "  ❌ Installation failed: $_" -ForegroundColor Red
        exit 1
    }
    
    # Clean up
    Remove-Item $awsMsiPath -Force -ErrorAction SilentlyContinue
    Write-Host ""
}

if ($installSAM) {
    Write-Host "📥 Installing AWS SAM CLI..." -ForegroundColor Yellow
    Write-Host ""
    
    $samMsiUrl = "https://github.com/aws/aws-sam-cli/releases/latest/download/AWS_SAM_CLI_64_PY3.msi"
    $samMsiPath = Join-Path $tempDir "AWS_SAM_CLI_64_PY3.msi"
    
    Write-Host "  Downloading SAM CLI installer..." -ForegroundColor Gray
    try {
        Invoke-WebRequest -Uri $samMsiUrl -OutFile $samMsiPath -UseBasicParsing
        Write-Host "  ✅ Download complete" -ForegroundColor Green
    } catch {
        Write-Host "  ❌ Download failed: $_" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "  Installing SAM CLI (this may take a minute)..." -ForegroundColor Gray
    Write-Host "  A Windows installer window will appear - please follow the prompts" -ForegroundColor Yellow
    
    try {
        Start-Process msiexec.exe -ArgumentList "/i `"$samMsiPath`" /qb" -Wait
        Write-Host "  ✅ SAM CLI installed" -ForegroundColor Green
    } catch {
        Write-Host "  ❌ Installation failed: $_" -ForegroundColor Red
        exit 1
    }
    
    # Clean up
    Remove-Item $samMsiPath -Force -ErrorAction SilentlyContinue
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "⚠️  IMPORTANT: Close and reopen your terminal" -ForegroundColor Yellow
Write-Host "   (This refreshes the PATH environment variable)" -ForegroundColor Gray
Write-Host ""

Write-Host "After reopening terminal, verify installation:" -ForegroundColor Cyan
Write-Host "  aws --version" -ForegroundColor White
Write-Host "  sam --version" -ForegroundColor White
Write-Host ""

Write-Host "Then configure AWS credentials:" -ForegroundColor Cyan
Write-Host "  aws configure" -ForegroundColor White
Write-Host ""

Write-Host "Finally, deploy BharatSahayak:" -ForegroundColor Cyan
Write-Host "  .\deploy.ps1" -ForegroundColor White
Write-Host ""

Write-Host "🎉 Setup complete!" -ForegroundColor Green
Write-Host ""
