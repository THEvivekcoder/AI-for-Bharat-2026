# Deploy Modern UI Frontend to S3
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deploying BharatSahayak Frontend to S3" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$BUCKET_NAME = "bharatsahayak-static-390402557080-dev"
$SOURCE_DIR = "modern-ui"
$REGION = "us-east-1"

# Step 1: Sync files to S3
Write-Host "1. Uploading files to S3..." -ForegroundColor Yellow
aws s3 sync $SOURCE_DIR s3://$BUCKET_NAME/app/ `
    --region $REGION `
    --exclude "*.md" `
    --exclude "*.sh" `
    --exclude "server.js" `
    --exclude "deploy.sh" `
    --exclude "node_modules/*" `
    --exclude ".git/*" `
    --delete

if ($LASTEXITCODE -eq 0) {
    Write-Host "   Files uploaded successfully" -ForegroundColor Green
} else {
    Write-Host "   Upload failed" -ForegroundColor Red
    exit 1
}

# Step 2: Set correct content types
Write-Host ""
Write-Host "2. Setting content types..." -ForegroundColor Yellow

# HTML files
aws s3 cp s3://$BUCKET_NAME/app/ s3://$BUCKET_NAME/app/ `
    --recursive `
    --exclude "*" `
    --include "*.html" `
    --content-type "text/html" `
    --metadata-directive REPLACE `
    --region $REGION

# CSS files
aws s3 cp s3://$BUCKET_NAME/app/ s3://$BUCKET_NAME/app/ `
    --recursive `
    --exclude "*" `
    --include "*.css" `
    --content-type "text/css" `
    --metadata-directive REPLACE `
    --region $REGION

# JavaScript files
aws s3 cp s3://$BUCKET_NAME/app/ s3://$BUCKET_NAME/app/ `
    --recursive `
    --exclude "*" `
    --include "*.js" `
    --content-type "application/javascript" `
    --metadata-directive REPLACE `
    --region $REGION

Write-Host "   Content types set" -ForegroundColor Green

# Step 3: Make files publicly readable
Write-Host ""
Write-Host "3. Setting public read permissions..." -ForegroundColor Yellow
aws s3api put-bucket-policy --bucket $BUCKET_NAME --policy @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::$BUCKET_NAME/app/*"
    }
  ]
}
"@ --region $REGION

if ($LASTEXITCODE -eq 0) {
    Write-Host "   Public access configured" -ForegroundColor Green
} else {
    Write-Host "   Warning: Could not set public access policy" -ForegroundColor Yellow
}

# Step 4: Enable static website hosting
Write-Host ""
Write-Host "4. Enabling static website hosting..." -ForegroundColor Yellow
aws s3 website s3://$BUCKET_NAME/ `
    --index-document app/index.html `
    --error-document app/index.html `
    --region $REGION

if ($LASTEXITCODE -eq 0) {
    Write-Host "   Static website hosting enabled" -ForegroundColor Green
} else {
    Write-Host "   Warning: Could not enable static website hosting" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Frontend URLs:" -ForegroundColor Cyan
Write-Host "  S3 URL: https://$BUCKET_NAME.s3.$REGION.amazonaws.com/app/index.html" -ForegroundColor White
Write-Host "  Website URL: http://$BUCKET_NAME.s3-website-$REGION.amazonaws.com/app/index.html" -ForegroundColor White
Write-Host ""
Write-Host "Pages deployed:" -ForegroundColor Cyan
Write-Host "  - Landing: /app/index.html" -ForegroundColor White
Write-Host "  - Login: /app/login.html" -ForegroundColor White
Write-Host "  - Register: /app/register.html" -ForegroundColor White
Write-Host "  - Dashboard: /app/dashboard.html" -ForegroundColor White
Write-Host "  - Profile: /app/profile.html" -ForegroundColor White
Write-Host "  - Search: /app/search.html" -ForegroundColor White
Write-Host "  - Saved: /app/saved.html" -ForegroundColor White
Write-Host ""
Write-Host "API Endpoint: https://ktlbemv6uh.execute-api.us-east-1.amazonaws.com/dev" -ForegroundColor Cyan
Write-Host ""
