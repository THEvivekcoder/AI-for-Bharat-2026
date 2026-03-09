# Quick Deploy - Skip build and deploy directly
Write-Host "Quick Deployment (using existing build)" -ForegroundColor Cyan
Write-Host ""

# Generate JWT secret
$JWTSecret = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
Write-Host "JWT Secret: $JWTSecret" -ForegroundColor Green
Write-Host ""

# Deploy without building
sam deploy `
  --stack-name bharatsahayak-dev `
  --region us-east-1 `
  --parameter-overrides "Environment=dev JWTSecret=$JWTSecret" `
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM `
  --no-confirm-changeset `
  --no-fail-on-empty-changeset `
  --resolve-s3

Write-Host ""
Write-Host "JWT Secret (save this): $JWTSecret" -ForegroundColor Yellow
