# Create Deployment Package for Manual Upload
# Use this if you want to deploy via AWS Console

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Creating Deployment Package" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$packageName = "bharatsahayak-deployment.zip"

# Check if zip command is available
$zipInstalled = Get-Command zip -ErrorAction SilentlyContinue

if ($zipInstalled) {
    Write-Host "Creating package using zip..." -ForegroundColor Yellow
    
    # Create zip excluding unnecessary files
    zip -r $packageName . `
        -x "*.git*" `
        -x "*.hypothesis*" `
        -x ".coverage" `
        -x "*.md" `
        -x "frontend/*" `
        -x "*.sh" `
        -x "*.ps1" `
        -x "packaged-template.yaml" `
        -x "__pycache__/*" `
        -x "*.pyc"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Package created: $packageName" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to create package" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Using PowerShell Compress-Archive..." -ForegroundColor Yellow
    
    # Get all files except excluded ones
    $files = Get-ChildItem -Recurse -File | Where-Object {
        $_.FullName -notmatch '\.git' -and
        $_.FullName -notmatch '\.hypothesis' -and
        $_.FullName -notmatch '\.coverage' -and
        $_.FullName -notmatch '\.md$' -and
        $_.FullName -notmatch 'frontend' -and
        $_.FullName -notmatch '\.(sh|ps1)$' -and
        $_.FullName -notmatch 'packaged-template\.yaml' -and
        $_.FullName -notmatch '__pycache__' -and
        $_.FullName -notmatch '\.pyc$'
    }
    
    # Create zip
    Compress-Archive -Path $files -DestinationPath $packageName -Force
    
    Write-Host "✅ Package created: $packageName" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Package Ready!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$packageSize = (Get-Item $packageName).Length / 1MB
Write-Host "📦 Package: $packageName" -ForegroundColor Cyan
Write-Host "📊 Size: $([math]::Round($packageSize, 2)) MB" -ForegroundColor Cyan
Write-Host ""

Write-Host "📝 Next Steps for AWS Console Deployment:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Upload to S3:" -ForegroundColor White
Write-Host "   - Go to: https://s3.console.aws.amazon.com/" -ForegroundColor Gray
Write-Host "   - Create bucket: bharatsahayak-deployment-bucket" -ForegroundColor Gray
Write-Host "   - Upload: $packageName" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Deploy via CloudFormation:" -ForegroundColor White
Write-Host "   - Go to: https://console.aws.amazon.com/cloudformation/" -ForegroundColor Gray
Write-Host "   - Create stack → Upload template.yaml" -ForegroundColor Gray
Write-Host "   - Stack name: bharatsahayak-dev" -ForegroundColor Gray
Write-Host "   - Environment: dev" -ForegroundColor Gray
Write-Host "   - JWTSecret: (generate random 32-char string)" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Get API Endpoint:" -ForegroundColor White
Write-Host "   - Stack → Outputs tab → Copy API endpoint" -ForegroundColor Gray
Write-Host "   - Update frontend/config.json" -ForegroundColor Gray
Write-Host ""

Write-Host "🎉 Package ready for deployment!" -ForegroundColor Green
Write-Host ""
