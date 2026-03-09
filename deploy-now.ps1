# Quick Deployment Script for BharatSahayak Email Auth
# Run this script to deploy without interactive prompts

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "BharatSahayak Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Generate a secure JWT secret
$JWTSecret = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
Write-Host "Generated JWT Secret: $JWTSecret" -ForegroundColor Green
Write-Host ""

Write-Host "Deploying to AWS..." -ForegroundColor Yellow
Write-Host ""

# Deploy without guided mode
sam deploy `
  --stack-name bharatsahayak-dev `
  --region us-east-1 `
  --parameter-overrides "Environment=dev JWTSecret=$JWTSecret" `
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM `
  --no-confirm-changeset `
  --no-fail-on-empty-changeset

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Deployment Successful!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Cyan
    Write-Host "1. Check the output above for the API Gateway endpoint URL" -ForegroundColor White
    Write-Host "2. Update frontend/config.json with the API endpoint" -ForegroundColor White
    Write-Host "3. Test at frontend/login.html" -ForegroundColor White
    Write-Host ""
    Write-Host "JWT Secret (save this securely): $JWTSecret" -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "Deployment failed. Check the errors above." -ForegroundColor Red
    Write-Host ""
}
