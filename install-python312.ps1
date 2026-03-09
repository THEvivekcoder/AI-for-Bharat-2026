# Install Python 3.12 for Windows
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Python 3.12 Installation Guide" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Step 1: Download Python 3.12" -ForegroundColor Yellow
Write-Host "Opening download page in browser..." -ForegroundColor Gray
Start-Process "https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe"

Write-Host ""
Write-Host "Step 2: Installation Instructions" -ForegroundColor Yellow
Write-Host "When the installer opens:" -ForegroundColor White
Write-Host "  1. CHECK 'Add Python 3.12 to PATH'" -ForegroundColor Green
Write-Host "  2. CHECK 'Install for all users'" -ForegroundColor Green
Write-Host "  3. Click 'Install Now'" -ForegroundColor Green
Write-Host ""

Write-Host "Step 3: After Installation" -ForegroundColor Yellow
Write-Host "Close this PowerShell window and open a NEW one" -ForegroundColor White
Write-Host "Then verify installation:" -ForegroundColor White
Write-Host "  py -3.12 --version" -ForegroundColor Cyan
Write-Host ""

Write-Host "Step 4: Continue Deployment" -ForegroundColor Yellow
Write-Host "After Python 3.12 is installed, run:" -ForegroundColor White
Write-Host "  sam build" -ForegroundColor Cyan
Write-Host "  sam deploy --stack-name bharatsahayak-dev --region us-east-1 --parameter-overrides `"Environment=dev JWTSecret=To2gBlws9qRhc8HNj7SALGfXzWdYeyZv`" --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM --no-confirm-changeset --resolve-s3" -ForegroundColor Cyan
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Waiting for you to complete installation..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
